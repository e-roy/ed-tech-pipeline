import { openai } from "@ai-sdk/openai";
import { generateObject, type Tool } from "ai";
import z from "zod";

export const generateNarrationTool: Tool = {
  description:
    "Generate a structured narration/script for an educational video based on confirmed facts. Returns a complete narration with segments.",
  inputSchema: z.object({
    facts: z
      .array(
        z.object({
          concept: z.string(),
          details: z.string(),
          confidence: z.number(),
        }),
      )
      .describe("The confirmed facts to base the narration on"),
  }),
  execute: async ({
    facts,
  }: {
    facts: Array<{ concept: string; details: string; confidence: number }>;
  }) => {
    try {
      const { object } = await generateObject({
        model: openai("gpt-4o-mini"),
        system: `You are a creative narrator for educational videos. Create a cohesive and engaging narration that incorporates the provided facts.
  
  Create 4 segments with types: hook, concept_introduction, process_explanation, and conclusion.`,
        prompt: `Create a structured narration based on these facts:\n\n${JSON.stringify(facts, null, 2)}`,
        schema: z.object({
          total_duration: z
            .number()
            .describe("Estimated total duration in seconds"),
          reading_level: z.string().describe("Reading level (e.g., '6.5')"),
          key_terms_count: z.number().describe("Number of key terms used"),
          segments: z.array(
            z.object({
              id: z.string().describe("Unique segment ID (e.g., 'seg_001')"),
              type: z
                .string()
                .describe(
                  "Segment type (hook, concept_introduction, process_explanation, conclusion)",
                ),
              start_time: z.number().describe("Start time in seconds"),
              duration: z.number().describe("Duration in seconds"),
              narration: z.string().describe("The script text"),
              visual_guidance: z
                .string()
                .describe("Description of what should be shown"),
              key_concepts: z
                .array(z.string())
                .describe("Key concepts covered"),
              educational_purpose: z
                .string()
                .describe("Why this segment matters"),
            }),
          ),
          message: z
            .string()
            .describe("Friendly message explaining what was created"),
        }),
      });

      // Extract message and return narration separately
      const { message, ...narrationData } = object;
      return JSON.stringify({ narration: narrationData, message });
    } catch (error) {
      console.error("Error generating narration:", error);
      return JSON.stringify({
        narration: null,
        message: `Failed to generate narration: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    }
  },
};
