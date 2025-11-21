import { type Tool } from "ai";
import z from "zod";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";

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
  }),
  execute: async ({
    facts,
    topic,
    target_duration = 60,
    child_age,
    child_interest,
  }: {
    facts: Array<{ concept: string; details: string; confidence?: number }>;
    topic?: string;
    target_duration?: number;
    child_age?: string;
    child_interest?: string;
  }) => {
    try {
      // Use NarrativeBuilderAgent for better narration quality
      const agent = new NarrativeBuilderAgent();

      // Extract topic from facts if not provided
      const inferredTopic = topic ?? facts[0]?.concept ?? "Educational Content";

      // Convert facts to the format expected by NarrativeBuilderAgent
      const agentFacts = facts.map((f) => ({
        concept: f.concept,
        details: f.details,
      }));

      const result = await agent.process({
        sessionId: "", // Not needed for tool execution
        data: {
          topic: inferredTopic,
          facts: agentFacts,
          target_duration: target_duration,
          child_age: child_age ?? null,
          child_interest: child_interest ?? null,
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
