import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { listUserFiles } from "@/server/services/storage";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq, desc } from "drizzle-orm";

export const finalVideosRouter = createTRPCRouter({
  list: protectedProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(50).default(20),
        offset: z.number().min(0).default(0),
      }),
    )
    .query(async ({ ctx, input }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Get all user sessions ordered by creation date
      const sessions = await db
        .select({
          id: videoSessions.id,
          topic: videoSessions.topic,
          status: videoSessions.status,
          createdAt: videoSessions.createdAt,
        })
        .from(videoSessions)
        .where(eq(videoSessions.userId, ctx.session.user.id))
        .orderBy(desc(videoSessions.createdAt));

      // Get final videos from S3
      const filesResult = await listUserFiles(ctx.session.user.id, "output", {
        asset_type: "final",
        limit: 1000,
        offset: 0,
      });

      // Match files to sessions based on sessionId in the S3 key
      // S3 key format: users/{userId}/{sessionId}/final/{filename}
      const videosWithSessions = filesResult.files
        .map((file) => {
          const parts = file.key.split("/");
          const sessionId = parts[2]; // Extract sessionId from key
          const session = sessions.find((s) => s.id === sessionId);

          if (!session) return null;

          return {
            sessionId: session.id,
            topic: session.topic,
            status: session.status,
            createdAt: session.createdAt,
            videoUrl: file.presigned_url,
            fileKey: file.key,
            size: file.size,
            lastModified: file.last_modified,
          };
        })
        .filter((item): item is NonNullable<typeof item> => item !== null)
        .sort((a, b) => {
          // Sort by creation date descending (newest first)
          if (!a.createdAt || !b.createdAt) return 0;
          return b.createdAt.getTime() - a.createdAt.getTime();
        });

      // Apply pagination
      const paginatedVideos = videosWithSessions.slice(
        input.offset,
        input.offset + input.limit,
      );

      return {
        videos: paginatedVideos,
        total: videosWithSessions.length,
        limit: input.limit,
        offset: input.offset,
      };
    }),
});

