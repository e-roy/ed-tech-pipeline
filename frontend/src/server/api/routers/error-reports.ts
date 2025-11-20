/**
 * tRPC router for error reporting.
 *
 * Allows users to report errors that occur in the application.
 * Errors are sanitized to prevent exposure of sensitive information.
 */

import { z } from "zod";
import { TRPCError } from "@trpc/server";

import { createTRPCRouter, publicProcedure } from "@/server/api/trpc";
import { errorReports } from "@/server/db/error-reports/schema";

/**
 * Sanitize error message to remove sensitive information.
 * Removes stack traces, file paths, and other potentially sensitive data.
 */
function sanitizeErrorMessage(message: string): string {
  // Remove stack traces (lines that look like "at ...")
  let sanitized = message.replace(/at\s+[\w.]+.*/g, "");

  // Remove file paths (common patterns)
  sanitized = sanitized.replace(/\/[^\s]+\.(ts|tsx|js|jsx|mjs|cjs)/g, "");
  sanitized = sanitized.replace(/[A-Z]:\\[^\s]+\.(ts|tsx|js|jsx|mjs|cjs)/g, "");

  // Remove line numbers in parentheses
  sanitized = sanitized.replace(/\(\d+:\d+\)/g, "");

  // Remove common sensitive patterns
  sanitized = sanitized.replace(/password[=:]\s*[\w]+/gi, "password=***");
  sanitized = sanitized.replace(/token[=:]\s*[\w]+/gi, "token=***");
  sanitized = sanitized.replace(/api[_-]?key[=:]\s*[\w]+/gi, "api_key=***");
  sanitized = sanitized.replace(/secret[=:]\s*[\w]+/gi, "secret=***");

  // Trim and limit length
  sanitized = sanitized.trim();

  // Limit to 5000 characters to prevent abuse
  if (sanitized.length > 5000) {
    sanitized = sanitized.substring(0, 5000) + "... (truncated)";
  }

  return sanitized;
}

export const errorReportsRouter = createTRPCRouter({
  /**
   * Report an error that occurred in the application.
   * Uses publicProcedure since errors can occur before authentication.
   */
  reportError: publicProcedure
    .input(
      z.object({
        error_name: z.string().min(1).max(255),
        error_message: z.string().min(1).max(10000), // Allow longer input, will be sanitized
        url: z.string().url().optional().or(z.literal("")),
        user_agent: z.string().max(1000).optional(),
      }),
    )
    .mutation(async ({ input, ctx }) => {
      try {
        // Sanitize error message on server
        const sanitizedMessage = sanitizeErrorMessage(input.error_message);

        // Get user ID from session if available (optional)
        const userId = ctx.session?.user?.id ?? null;

        // Insert error report into database
        const [errorReport] = await ctx.db
          .insert(errorReports)
          .values({
            errorName: input.error_name,
            errorMessage: sanitizedMessage,
            userId: userId ?? undefined,
            userAgent: input.user_agent ?? undefined,
            url: input.url && input.url !== "" ? input.url : undefined,
          })
          .returning();

        if (!errorReport) {
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message: "Failed to save error report.",
          });
        }

        return {
          success: true,
          id: errorReport.id,
        };
      } catch (error) {
        // Don't expose database errors to client
        // Log server-side for debugging
        console.error("Failed to save error report:", error);

        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Failed to report error. Please try again later.",
        });
      }
    }),
});
