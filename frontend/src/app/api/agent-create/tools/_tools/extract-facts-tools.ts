import { type Tool } from "ai";
import z from "zod";
import { FactExtractionAgent } from "@/server/agents/fact-extraction";

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
      // Use FactExtractionAgent for better fact extraction quality
      const agent = new FactExtractionAgent();

      const result = await agent.process({
        sessionId: "", // Not needed for tool execution
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
