/**
 * tRPC router for storage/file management.
 * 
 * Proxies requests to the backend REST API with proper authentication.
 */

import { z } from "zod";
import { TRPCError } from "@trpc/server";

import { createTRPCRouter, protectedProcedure } from "@/server/api/trpc";
import { getBackendToken } from "@/lib/auth-token";
import { env } from "@/env";
import type { FileListResponse, PresignedUrlResponse } from "@/lib/types/storage";

/**
 * Helper to make authenticated requests to backend API.
 */
async function fetchWithAuth(
  endpoint: string,
  session: { user?: { email?: string | null } | null } | null,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getBackendToken(session);
  
  if (!token) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "Not authenticated with backend",
    });
  }
  
  const url = `${env.NEXT_PUBLIC_API_URL}${endpoint}`;
  
  return fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
}

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
      })
    )
    .query(async ({ input, ctx }): Promise<FileListResponse> => {
      const params = new URLSearchParams({
        folder: input.folder,
        limit: input.limit.toString(),
        offset: input.offset.toString(),
      });
      
      if (input.asset_type) {
        params.append("asset_type", input.asset_type);
      }
      
      const response = await fetchWithAuth(
        `/api/storage/files?${params.toString()}`,
        ctx.session
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new TRPCError({
          code: response.status === 401 ? "UNAUTHORIZED" : "INTERNAL_SERVER_ERROR",
          message: `Failed to list files: ${errorText}`,
        });
      }
      
      return (await response.json()) as FileListResponse;
    }),

  /**
   * Delete a file from user's folders.
   */
  deleteFile: protectedProcedure
    .input(
      z.object({
        file_key: z.string(),
      })
    )
    .mutation(
      async ({
        input,
        ctx,
      }): Promise<{ status: string; message: string; key: string }> => {
        const response = await fetchWithAuth(
          `/api/storage/files/${encodeURIComponent(input.file_key)}`,
          ctx.session,
          {
            method: "DELETE",
          }
        );
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new TRPCError({
          code: response.status === 401 ? "UNAUTHORIZED" : "INTERNAL_SERVER_ERROR",
          message: `Failed to delete file: ${errorText}`,
        });
      }
      
      return (await response.json()) as { status: string; message: string; key: string };
    }),

  /**
   * Get a presigned URL for accessing a file.
   */
  getPresignedUrl: protectedProcedure
    .input(
      z.object({
        file_key: z.string(),
        expires_in: z.number().min(60).max(3600).default(3600),
      })
    )
    .query(async ({ input, ctx }): Promise<PresignedUrlResponse> => {
      const params = new URLSearchParams({
        expires_in: input.expires_in.toString(),
      });
      
      const response = await fetchWithAuth(
        `/api/storage/files/${encodeURIComponent(input.file_key)}/presigned-url?${params.toString()}`,
        ctx.session
      );
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new TRPCError({
          code: response.status === 401 ? "UNAUTHORIZED" : "INTERNAL_SERVER_ERROR",
          message: `Failed to get presigned URL: ${errorText}`,
        });
      }
      
      return (await response.json()) as PresignedUrlResponse;
    }),
});

