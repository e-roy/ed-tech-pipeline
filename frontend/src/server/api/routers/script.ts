import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { db } from "@/server/db";
import { videoSessions, videoAssets } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { createSessionWithScript, generateScript } from "@/server/utils/generate-script";

export const scriptRouter = createTRPCRouter({
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
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      const sessionId = await createSessionWithScript(
        ctx.session.user.id,
        input.topic,
        input.facts,
        input.script,
        input.cost,
        input.duration,
      );

      return { sessionId };
    }),
});

