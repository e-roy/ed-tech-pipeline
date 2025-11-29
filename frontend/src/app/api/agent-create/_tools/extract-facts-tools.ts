import { type Tool } from "ai";
import type { ToolCallOptions } from "@ai-sdk/provider-utils";
import z from "zod";
import { FactExtractionAgent } from "@/server/agents/fact-extraction";

export const extractFactsTool: Tool = {
  description:
    "Extract educational facts from learning materials (PDF, URL, or text). Returns facts pending user review.",
  inputSchema: z.object({
    content: z.string().describe("The user's message text"),
    pdfUrl: z.string().optional().describe("PDF URL from file attachment"),
    websiteUrl: z
      .string()
      .optional()
      .describe("Website URL to fetch and extract facts from"),
  }),
  execute: async (
    {
      content,
      pdfUrl,
      websiteUrl,
    }: {
      content: string;
      pdfUrl?: string;
      websiteUrl?: string;
    },
    _options: ToolCallOptions,
  ) => {
    try {
      // Use FactExtractionAgent for better fact extraction quality
      const agent = new FactExtractionAgent();

      const result = await agent.process({
        data: {
          content,
          pdfUrl,
          websiteUrl,
        },
      });

      if (!result.success) {
        return {
          success: false,
          facts: [],
          message: `Failed to extract facts: ${result.error ?? "Unknown error"}`,
        };
      }

      // Return object directly (AI SDK will handle serialization)
      return {
        success: true,
        facts: result.data.facts ?? [],
        message: result.data.message ?? "Facts extracted successfully",
        topic: result.data.topic,
        learningObjective: result.data.learningObjective,
      };
    } catch (error) {
      console.error("Error extracting facts:", error);
      return {
        success: false,
        facts: [],
        message: `Failed to extract facts: ${error instanceof Error ? error.message : "Unknown error"}`,
      };
    }
  },
};
