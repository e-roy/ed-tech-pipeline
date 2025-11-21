import { type Tool } from "ai";
import z from "zod";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

export const generateNarrationTool: Tool = {
  description:
    "Generate a structured narration/script for an educational video based on confirmed facts. Returns a complete narration with segments.",
  inputSchema: z.object({
    facts: z
      .array(
        z.object({
          concept: z.string(),
          details: z.string(),
          confidence: z.number().optional(),
        }),
      )
      .describe("The confirmed facts to base the narration on"),
    topic: z
      .string()
      .optional()
      .describe(
        "The main topic/subject of the video (optional, will be inferred if not provided)",
      ),
    target_duration: z
      .number()
      .optional()
      .default(60)
      .describe("Target duration in seconds (default: 60)"),
    child_age: z
      .string()
      .optional()
      .describe("Child's age for age-appropriate content"),
    child_interest: z
      .string()
      .optional()
      .describe("Child's interest to incorporate into examples"),
    sessionId: z
      .string()
      .optional()
      .describe(
        "Session ID to load confirmedFacts and session data from database",
      ),
  }),
  execute: async ({
    facts,
    topic,
    target_duration = 60,
    child_age,
    child_interest,
    sessionId,
  }: {
    facts: Array<{ concept: string; details: string; confidence?: number }>;
    topic?: string;
    target_duration?: number;
    child_age?: string;
    child_interest?: string;
    sessionId?: string;
  }) => {
    try {
      // If sessionId provided, load confirmedFacts and session data from DB
      let factsToUse = facts;
      let topicToUse = topic;
      let childAge = child_age;
      let childInterest = child_interest;

      if (sessionId) {
        try {
          const [session] = await db
            .select({
              confirmedFacts: videoSessions.confirmedFacts,
              topic: videoSessions.topic,
              childAge: videoSessions.childAge,
              childInterest: videoSessions.childInterest,
            })
            .from(videoSessions)
            .where(eq(videoSessions.id, sessionId))
            .limit(1);

          if (session) {
            // Use confirmedFacts from DB if available, otherwise use request facts
            if (
              session.confirmedFacts &&
              Array.isArray(session.confirmedFacts) &&
              session.confirmedFacts.length > 0
            ) {
              factsToUse = session.confirmedFacts as typeof facts;
            }

            // Use topic from DB if not provided in request
            if (!topicToUse && session.topic) {
              topicToUse = session.topic;
            }

            // Use child_age and child_interest from DB if not provided in request
            if (!childAge && session.childAge) {
              childAge = session.childAge;
            }
            if (!childInterest && session.childInterest) {
              childInterest = session.childInterest;
            }
          }
        } catch (error) {
          console.error(
            "Error loading session for generateNarrationTool:",
            error,
          );
          // Continue with request parameters if DB load fails
        }
      }

      // Use NarrativeBuilderAgent for better narration quality
      const agent = new NarrativeBuilderAgent();

      // Extract topic from facts if not provided
      const inferredTopic =
        topicToUse ?? factsToUse[0]?.concept ?? "Educational Content";

      // Convert facts to the format expected by NarrativeBuilderAgent
      const agentFacts = factsToUse.map((f) => ({
        concept: f.concept,
        details: f.details,
      }));

      const result = await agent.process({
        sessionId: sessionId ?? "",
        data: {
          topic: inferredTopic,
          facts: agentFacts,
          target_duration: target_duration,
          child_age: childAge ?? null,
          child_interest: childInterest ?? null,
        },
      });

      if (!result.success) {
        return JSON.stringify({
          narration: null,
          message: `Failed to generate narration: ${result.error ?? "Unknown error"}`,
        });
      }

      // Return in the expected tool format
      const narrationData = result.data.script;
      const segmentCount =
        narrationData &&
        typeof narrationData === "object" &&
        "segments" in narrationData &&
        Array.isArray(narrationData.segments)
          ? narrationData.segments.length
          : 0;

      return JSON.stringify({
        narration: narrationData,
        message: `Successfully generated narration with ${segmentCount} segments`,
      });
    } catch (error) {
      console.error("Error generating narration:", error);
      return JSON.stringify({
        narration: null,
        message: `Failed to generate narration: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    }
  },
};
