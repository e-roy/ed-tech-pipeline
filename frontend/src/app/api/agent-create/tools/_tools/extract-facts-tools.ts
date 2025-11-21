import { type Tool } from "ai";
import z from "zod";
import { FactExtractionAgent } from "@/server/agents/fact-extraction";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

export const extractFactsTool: Tool = {
  description:
    "Extract educational facts from learning materials (PDF, URL, or text). Returns facts pending user review.",
  inputSchema: z.object({
    content: z
      .string()
      .describe(
        "The content to extract facts from (text, PDF content, or URL)",
      ),
    sessionId: z
      .string()
      .optional()
      .describe("Session ID to access existing session data from database"),
  }),
  execute: async ({
    content,
    sessionId,
  }: {
    content: string;
    sessionId?: string;
  }) => {
    try {
      // If sessionId provided, optionally load existing extractedFacts for context
      // (not for replacement, just for reference)
      if (sessionId) {
        try {
          const [session] = await db
            .select({
              extractedFacts: videoSessions.extractedFacts,
            })
            .from(videoSessions)
            .where(eq(videoSessions.id, sessionId))
            .limit(1);

          // Could use existing facts for context if needed in the future
          // For now, we just ensure the session exists
          if (session) {
            // Session exists, continue with extraction
          }
        } catch (error) {
          console.error("Error loading session for extractFactsTool:", error);
          // Continue with extraction even if session load fails
        }
      }

      // Use FactExtractionAgent for better fact extraction quality
      const agent = new FactExtractionAgent();

      const result = await agent.process({
        sessionId: sessionId ?? "",
        data: {
          content,
        },
      });

      if (!result.success) {
        return JSON.stringify({
          facts: [],
          message: `Failed to extract facts: ${result.error ?? "Unknown error"}`,
        });
      }

      // Return in the expected tool format
      return JSON.stringify({
        facts: result.data.facts ?? [],
        message: result.data.message ?? "Facts extracted successfully",
        topic: result.data.topic,
        learningObjective: result.data.learningObjective,
      });
    } catch (error) {
      console.error("Error extracting facts:", error);
      return JSON.stringify({
        facts: [],
        message: `Failed to extract facts: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    }
  },
};
