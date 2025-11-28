import { type Tool } from "ai";
import type { ToolCallOptions } from "@ai-sdk/provider-utils";
import z from "zod";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

export const saveStudentInfoTool: Tool = {
  description:
    "Save student information (age and interest) to the session for personalization. Use this when the teacher provides information about their student.",
  inputSchema: z.object({
    child_age: z
      .string()
      .describe(
        "The student's age as a string (e.g., '7', '10', '12 years old')",
      ),
    child_interest: z
      .string()
      .describe(
        "The student's special interest (e.g., 'soccer', 'Minecraft', 'dinosaurs', 'reading')",
      ),
    sessionId: z
      .string()
      .optional()
      .describe("Session ID to save the information to"),
  }),
  execute: async (
    {
      child_age,
      child_interest,
      sessionId,
    }: {
      child_age: string;
      child_interest: string;
      sessionId?: string;
    },
    _options: ToolCallOptions,
  ) => {
    try {
      if (!sessionId) {
        return JSON.stringify({
          success: false,
          message: "Session ID is required to save student information.",
        });
      }

      // Save to database
      await db
        .update(videoSessions)
        .set({
          childAge: child_age,
          childInterest: child_interest,
          updatedAt: new Date(),
        })
        .where(eq(videoSessions.id, sessionId));

      return JSON.stringify({
        success: true,
        message: `Perfect! I'll personalize the video for a ${child_age}-year-old who loves ${child_interest}. Now, please share your history lesson material - you can type it in, paste text, or upload a PDF.`,
        child_age,
        child_interest,
      });
    } catch (error) {
      console.error("Error saving student info:", error);
      return JSON.stringify({
        success: false,
        message: `Failed to save student information: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    }
  },
};
