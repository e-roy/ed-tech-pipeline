import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { db } from "@/server/db";
import { videoSessions, conversationMessages } from "@/server/db/schema";
import { eq, asc } from "drizzle-orm";
import {
  createSessionWithScript,
  updateSessionWithScript,
} from "@/server/utils/generate-script";
import { env } from "@/env";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import { selectAndCopyDiagrams } from "@/server/services/diagram-selector";
import type { Narration } from "@/types";

export const sessionRouter = createTRPCRouter({
  get: protectedProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      const [sessionData] = await db
        .select()
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      if (!sessionData || sessionData.userId !== ctx.session.user.id) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Session not found",
        });
      }

      // Load conversation messages
      const dbMessages = await db
        .select()
        .from(conversationMessages)
        .where(eq(conversationMessages.sessionId, input.sessionId))
        .orderBy(asc(conversationMessages.createdAt));

      return {
        session: {
          id: sessionData.id,
          status: sessionData.status,
          extractedFacts: sessionData.extractedFacts,
          confirmedFacts: sessionData.confirmedFacts,
          generatedScript: sessionData.generatedScript,
          topic: sessionData.topic,
          childAge: sessionData.childAge,
          childInterest: sessionData.childInterest,
        },
        messages: dbMessages.map((m) => ({
          role: m.role,
          content: m.content,
          id: m.id,
          parts: m.parts ?? undefined,
        })),
      };
    }),

  approve: protectedProcedure
    .input(
      z.object({
        script: z.any(),
        topic: z.string(),
        facts: z.array(z.object({ concept: z.string(), details: z.string() })),
        cost: z.number(),
        duration: z.number(),
        sessionId: z.string().optional(),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Update existing session or create new one
      const sessionId = input.sessionId
        ? await updateSessionWithScript(
            input.sessionId,
            ctx.session.user.id,
            input.topic,
            input.facts,
            input.script,
            input.cost,
            input.duration,
          )
        : await createSessionWithScript(
            ctx.session.user.id,
            input.topic,
            input.facts,
            input.script,
            input.cost,
            input.duration,
          );

      // Call external video processing API
      try {
        const apiUrl = `${env.VIDEO_PROCESSING_API_URL}/api/startprocessing`;

        const response = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sessionID: sessionId,
            userID: ctx.session.user.id,
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `Video processing API returned status ${response.status}: ${errorText}`,
          );
        }

        const result = (await response.json()) as {
          success: boolean;
          message: string;
        };

        if (!result.success) {
          throw new Error(result.message || "Video processing failed");
        }

        // Update session status to video_generating on success
        await db
          .update(videoSessions)
          .set({
            status: "video_generating",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));
      } catch (error) {
        // Update session status to video_failed on error
        await db
          .update(videoSessions)
          .set({
            status: "video_failed",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));

        // Re-throw error to be handled by client
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Failed to process video generation request",
        });
      }

      return { sessionId };
    }),

  generateNarration: protectedProcedure
    .input(
      z.object({
        sessionId: z.string(),
        selectedFacts: z.array(
          z.object({ concept: z.string(), details: z.string() }),
        ),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Load session data to get topic, child age/interest
      const [sessionData] = await db
        .select({
          topic: videoSessions.topic,
          childAge: videoSessions.childAge,
          childInterest: videoSessions.childInterest,
        })
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      // Save selectedFacts as confirmedFacts
      await db
        .update(videoSessions)
        .set({
          confirmedFacts: input.selectedFacts,
          updatedAt: new Date(),
        })
        .where(eq(videoSessions.id, input.sessionId));

      // Call NarrativeBuilderAgent directly
      const agent = new NarrativeBuilderAgent();
      const result = await agent.process({
        data: {
          topic:
            sessionData?.topic ??
            input.selectedFacts[0]?.concept ??
            "Educational Content",
          facts: input.selectedFacts,
          target_duration: 60,
          child_age: sessionData?.childAge ?? null,
          child_interest: sessionData?.childInterest ?? null,
        },
        metadata: { sessionId: input.sessionId },
      });

      if (!result.success) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: result.error ?? "Failed to generate narration",
        });
      }

      const narration = result.data.script as Narration;

      return {
        narration,
        message: `Successfully generated narration with ${narration.segments?.length ?? 0} segments`,
      };
    }),

  verifyNarration: protectedProcedure
    .input(
      z.object({
        sessionId: z.string(),
        narration: z.any(),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Verify session belongs to user and load confirmed facts
      const [sessionData] = await db
        .select({
          id: videoSessions.id,
          userId: videoSessions.userId,
          confirmedFacts: videoSessions.confirmedFacts,
        })
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      if (!sessionData || sessionData.userId !== ctx.session.user.id) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Session not found",
        });
      }

      // Update the generated script with edited version and mark as verified
      await db
        .update(videoSessions)
        .set({
          generatedScript: input.narration,
          status: "narration_verified",
          updatedAt: new Date(),
        })
        .where(eq(videoSessions.id, input.sessionId));

      // Extract confirmed facts for diagram selection
      const confirmedFacts =
        sessionData.confirmedFacts && Array.isArray(sessionData.confirmedFacts)
          ? (sessionData.confirmedFacts as Array<{
              concept: string;
              details: string;
            }>)
          : [];

      // Trigger diagram selection in the background (fire and forget)
      selectAndCopyDiagrams(
        ctx.session.user.id,
        input.sessionId,
        input.narration as Narration,
        confirmedFacts,
      )
        .then((result) => {
          console.log(
            "[session.verifyNarration] Diagram selection completed:",
            result,
          );
        })
        .catch((error) => {
          console.error(
            "[session.verifyNarration] Diagram selection failed:",
            error,
          );
        });

      return {
        success: true,
        message: "Narration saved successfully",
      };
    }),
});
