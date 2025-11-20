import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { db } from "@/server/db";
import { videoSessions, videoAssets } from "@/server/db/schema";
import { eq, desc } from "drizzle-orm";
import {
  createSessionWithScript,
  updateSessionWithScript,
  generateScript,
} from "@/server/utils/generate-script";
import { env } from "@/env";

export const scriptRouter = createTRPCRouter({
  getSession: protectedProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      const [session] = await db
        .select()
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      if (!session || session.userId !== ctx.session.user.id) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Session not found",
        });
      }

      return session;
    }),

  get: protectedProcedure
    .input(z.object({ sessionId: z.string() }))
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      const [session] = await db
        .select()
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      if (!session || session.userId !== ctx.session.user.id) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Session not found",
        });
      }

      // Get script asset
      const scriptAssets = await db
        .select()
        .from(videoAssets)
        .where(eq(videoAssets.sessionId, input.sessionId));

      const scriptAsset = scriptAssets.find(
        (asset) => asset.assetType === "script",
      );

      if (!scriptAsset) {
        return null;
      }

      const metadata = scriptAsset.metadata as
        | {
            script?: unknown;
            cost?: number;
            duration?: number;
          }
        | null;

      return {
        script: metadata?.script,
        cost: metadata?.cost,
        duration: metadata?.duration,
      };
    }),

  list: protectedProcedure.query(async ({ ctx }) => {
    if (!ctx.session?.user?.id) {
      throw new TRPCError({
        code: "UNAUTHORIZED",
        message: "User not authenticated",
      });
    }

    const sessions = await db
      .select({
        id: videoSessions.id,
        topic: videoSessions.topic,
        createdAt: videoSessions.createdAt,
      })
      .from(videoSessions)
      .where(eq(videoSessions.userId, ctx.session.user.id))
      .orderBy(desc(videoSessions.createdAt));

    return sessions;
  }),

  getLatestSession: protectedProcedure.query(async ({ ctx }) => {
    if (!ctx.session?.user?.id) {
      throw new TRPCError({
        code: "UNAUTHORIZED",
        message: "User not authenticated",
      });
    }

    const userSessions = await db
      .select()
      .from(videoSessions)
      .where(eq(videoSessions.userId, ctx.session.user.id));

    const latestSession = userSessions
      .sort((a, b) => {
        const aTime =
          a.createdAt instanceof Date ? a.createdAt.getTime() : 0;
        const bTime =
          b.createdAt instanceof Date ? b.createdAt.getTime() : 0;
        return bTime - aTime;
      })[0];

    return latestSession ? { sessionId: latestSession.id } : null;
  }),

  generate: protectedProcedure
    .input(
      z.object({
        topic: z.string(),
        facts: z.array(
          z.object({ concept: z.string(), details: z.string() }),
        ),
        targetDuration: z.number().default(60),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      const result = await generateScript(
        input.topic,
        input.facts,
        input.targetDuration,
      );

      return result;
    }),

  approve: protectedProcedure
    .input(
      z.object({
        script: z.any(),
        topic: z.string(),
        facts: z.array(
          z.object({ concept: z.string(), details: z.string() }),
        ),
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
        const apiUrl = `${env.VIDEO_PROCESSING_API_URL}/api/process`;
        const scriptString = JSON.stringify(input.script);

        const response = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            sessionId,
            script: scriptString,
          }),
        });

        if (!response.ok) {
          throw new Error(
            `Video processing API returned status ${response.status}`,
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

  delete: protectedProcedure
    .input(z.object({ sessionId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Verify session belongs to the authenticated user
      const [session] = await db
        .select()
        .from(videoSessions)
        .where(eq(videoSessions.id, input.sessionId))
        .limit(1);

      if (!session || session.userId !== ctx.session.user.id) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Session not found",
        });
      }

      // Delete associated assets first (to respect foreign key constraints)
      await db
        .delete(videoAssets)
        .where(eq(videoAssets.sessionId, input.sessionId));

      // Delete the session
      await db
        .delete(videoSessions)
        .where(eq(videoSessions.id, input.sessionId));

      return { success: true };
    }),
});

