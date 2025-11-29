import { openai } from "@ai-sdk/openai";
import { generateObject } from "ai";
import { z } from "zod";
import { env } from "@/env";
import type { AgentInput, AgentOutput } from "@/types/agent";

const factExtractionSchema = z.object({
  facts: z.array(
    z.object({
      concept: z.string(),
      details: z.string(),
      confidence: z.number().min(0).max(1),
    }),
  ),
  topic: z.string(),
  learningObjective: z.string(),
  message: z.string(),
});

export class FactExtractionAgent {
  async process(input: AgentInput): Promise<AgentOutput> {
    const startTime = Date.now();

    try {
      if (!env.OPENAI_API_KEY) {
        throw new Error("OPENAI_API_KEY is not configured");
      }

      const content = input.data.content as string | undefined;
      const pdfUrl = input.data.pdfUrl as string | undefined;
      const websiteUrl = input.data.websiteUrl as string | undefined;

      // Either content, pdfUrl, or websiteUrl must be provided
      if ((!content || content.trim().length === 0) && !pdfUrl && !websiteUrl) {
        throw new Error(
          "Either content, PDF URL, or website URL is required for fact extraction",
        );
      }

      const systemPrompt = this.buildSystemPrompt();
      const userPrompt = this.buildUserPrompt(content ?? "", websiteUrl);

      // Build message content - AI SDK handles PDF fetching
      const messageContent: Array<
        | { type: "text"; text: string }
        | { type: "file"; data: URL; mediaType: string }
      > = [{ type: "text", text: userPrompt }];

      // Add PDF URL directly (AI SDK fetches it)
      if (pdfUrl) {
        messageContent.push({
          type: "file",
          data: new URL(pdfUrl),
          mediaType: "application/pdf",
        });
      }

      const result = await generateObject({
        // model: openai("gpt-4o-mini"),
        model: openai("gpt-5-mini-2025-08-07"),
        schema: factExtractionSchema,
        messages: [
          {
            role: "system",
            content: systemPrompt,
          },
          {
            role: "user",
            content: messageContent,
          },
        ],
      });

      const factData = result.object;

      // Calculate cost (GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
      const inputTokens = result.usage?.inputTokens ?? 0;
      const outputTokens = result.usage?.outputTokens ?? 0;
      const cost =
        (inputTokens * 0.15) / 1_000_000 + (outputTokens * 0.6) / 1_000_000;

      const duration = (Date.now() - startTime) / 1000;

      return {
        success: true,
        data: {
          facts: factData.facts,
          message: factData.message,
          topic: factData.topic,
          learningObjective: factData.learningObjective,
        },
        cost,
        duration,
      };
    } catch (error) {
      return {
        success: false,
        data: {},
        cost: 0.0,
        duration: (Date.now() - startTime) / 1000,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  private buildSystemPrompt(): string {
    return `You are an expert educational fact extractor helping teachers create personalized history videos for individual students.

Your task:
1. Extract 5-15 key educational facts from the provided history lesson content
2. Identify the main topic and learning objective
3. Ensure facts are clear, accurate, and suitable for creating engaging educational video scripts

Fact Quality Criteria:
- Clear and well-defined historical concepts, events, or figures
- Relevant to history education and teaching
- Suitable for use in a personalized video script
- Accurate and age-appropriate
- Can be made engaging through real-world connections and contemporary relevance
- Educational value for student learning

For each fact, provide:
- concept: The main concept, event, or figure (concise, 1-5 words)
- details: A clear explanation suitable for students (2-4 sentences)
- confidence: A confidence score between 0 and 1 based on clarity and accuracy

Also provide:
- topic: The main history topic (e.g., American Revolution, Ancient Rome, World War II)
- learningObjective: What the student should learn from this content
- message: A friendly message to the teacher explaining what was extracted`;
  }

  private buildUserPrompt(content: string, websiteUrl?: string): string {
    let prompt = "";

    if (websiteUrl) {
      prompt += `Fetch and analyze the educational content from this URL: ${websiteUrl}\n\n`;
    }

    if (content?.trim()) {
      prompt += `Extract educational facts from this content:\n\n${content}\n\n`;
    }

    prompt += "Provide a comprehensive analysis with 5-15 key facts, the main topic, and a learning objective.";

    return prompt;
  }
}
