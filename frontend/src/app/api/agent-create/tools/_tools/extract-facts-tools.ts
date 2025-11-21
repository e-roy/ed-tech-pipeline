import { openai } from "@ai-sdk/openai";
import { generateObject, type Tool } from "ai";
import z from "zod";

export const extractFactsTool: Tool = {
  description:
    "Extract educational facts from learning materials (PDF, URL, or text). Returns facts pending user review.",
  inputSchema: z.object({
    content: z
      .string()
      .describe(
        "The content to extract facts from (text, PDF content, or URL)",
      ),
  }),
  execute: async ({ content }: { content: string }) => {
    try {
      const { object } = await generateObject({
        model: openai("gpt-4o-mini"),
        system: `You are an expert fact extractor. Extract 5-15 key educational facts that are:
  - Clear and well-defined concepts
  - Relevant to teaching and learning
  - Suitable for use in an educational video script
  - Accurate and educational`,
        prompt: `Extract educational facts from this content:\n\n${content}`,
        schema: z.object({
          facts: z
            .array(
              z.object({
                concept: z.string().describe("Main concept or term"),
                details: z.string().describe("Clear explanation or definition"),
                confidence: z
                  .number()
                  .min(0)
                  .max(1)
                  .describe("Confidence score between 0 and 1"),
              }),
            )
            .describe("Array of extracted educational facts"),
          message: z
            .string()
            .describe("Friendly message explaining what was extracted"),
        }),
      });

      return JSON.stringify(object);
    } catch (error) {
      console.error("Error extracting facts:", error);
      return JSON.stringify({
        facts: [],
        message: `Failed to extract facts: ${error instanceof Error ? error.message : "Unknown error"}`,
      });
    }
  },
};
