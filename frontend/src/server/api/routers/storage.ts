/**
 * tRPC router for storage/file management.
 *
 * Directly accesses S3 without going through FastAPI backend.
 */

import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { eq, desc } from "drizzle-orm";

import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import type { FileListResponse, PresignedUrlResponse } from "@/types/storage";
import {
  listUserFiles,
  deleteUserFile,
  getPresignedUrl,
  listSessionFiles,
  listDirectoryStructure,
} from "@/server/services/storage";
import { db } from "@/server/db";
import { webhookLogs } from "@/server/db/schema";
import { UserRole } from "@/types";

export const storageRouter = createTRPCRouter({
  /**
   * List files in user's input or output folder.
   */
  listFiles: protectedProcedure
    .input(
      z.object({
        folder: z.enum(["input", "output"]),
        asset_type: z.enum(["images", "videos", "audio", "final"]).optional(),
        limit: z.number().min(1).max(1000).default(100),
        offset: z.number().min(0).default(0),
      }),
    )
    .query(async ({ input, ctx }): Promise<FileListResponse> => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      try {
        const result = await listUserFiles(ctx.session.user.id, input.folder, {
          asset_type: input.asset_type,
          limit: input.limit,
          offset: input.offset,
        });

        return result;
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error ? error.message : "Failed to list files",
        });
      }
    }),

  /**
   * Delete a file from user's folders.
   */
  deleteFile: protectedProcedure
    .input(
      z.object({
        file_key: z.string(),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      try {
        return await deleteUserFile(ctx.session.user.id, input.file_key);
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error ? error.message : "Failed to delete file",
        });
      }
    }),

  /**
   * Get a presigned URL for accessing a file.
   */
  getPresignedUrl: protectedProcedure
    .input(
      z.object({
        file_key: z.string(),
        expires_in: z.number().min(60).max(3600).default(3600),
      }),
    )
    .query(async ({ input, ctx }): Promise<PresignedUrlResponse> => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      try {
        return await getPresignedUrl(
          ctx.session.user.id,
          input.file_key,
          input.expires_in,
        );
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Failed to get presigned URL",
        });
      }
    }),

  /**
   * List files from a session-specific folder (e.g., users/{userId}/{sessionId}/final/).
   */
  listSessionFiles: protectedProcedure
    .input(
      z.object({
        sessionId: z.string(),
        subfolder: z.string().optional(), // e.g., "final", "images", etc.
      }),
    )
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      try {
        const files = await listSessionFiles(
          ctx.session.user.id,
          input.sessionId,
          input.subfolder,
        );

        return files;
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Failed to list session files",
        });
      }
    }),

  /**
   * List directory structure for a session (folders and files).
   * Returns folders and files organized hierarchically.
   * Admin-only endpoint for debugging.
   */
  listSessionDirectory: protectedProcedure
    .input(
      z.object({
        sessionId: z.string(),
        subfolder: z.string().optional(), // e.g., "process", "images", etc.
      }),
    )
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      // Admin-only endpoint
      if (ctx.session.user.role !== UserRole.ADMIN) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "Admin access required",
        });
      }

      try {
        const prefix = input.subfolder ?? "";
        const result = await listDirectoryStructure(
          ctx.session.user.id,
          `${input.sessionId}/${prefix}`,
        );

        return result;
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Failed to list session directory",
        });
      }
    }),

  /**
   * Check webhook table for video completion status.
   * Returns the most recent webhook event for the given session.
   */
  checkVideoWebhook: protectedProcedure
    .input(
      z.object({
        sessionId: z.string(),
      }),
    )
    .query(async ({ input, ctx }) => {
      if (!ctx.session?.user?.id) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "User not authenticated",
        });
      }

      try {
        // Get the most recent webhook for this session
        const [webhookLog] = await db
          .select()
          .from(webhookLogs)
          .where(eq(webhookLogs.sessionId, input.sessionId))
          .orderBy(desc(webhookLogs.createdAt))
          .limit(1);

        return webhookLog ?? null;
      } catch (error) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Failed to check webhook status",
        });
      }
    }),
});
