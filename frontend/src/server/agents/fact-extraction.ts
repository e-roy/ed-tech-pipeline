import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { env } from "@/env";
import type { AgentInput, AgentOutput } from "@/types/agent";

export class FactExtractionAgent {
  async process(input: AgentInput): Promise<AgentOutput> {
    const startTime = Date.now();

    try {
      if (!env.OPENAI_API_KEY) {
        throw new Error("OPENAI_API_KEY is not configured");
      }

      const content = input.data.content as string;
      if (!content || content.trim().length === 0) {
        throw new Error("Content is required for fact extraction");
      }

      const systemPrompt = this.buildSystemPrompt();
      const userPrompt = this.buildUserPrompt(content);

      const result = await generateText({
        model: openai("gpt-4o-mini"),
        system: systemPrompt,
        prompt: userPrompt,
        temperature: 0.7,
      });

      const responseText = result.text;
      if (!responseText) {
        throw new Error("No content in LLM response");
      }

      // Extract JSON from response (may be wrapped in markdown code blocks)
      const jsonBlockRegex = /```json\s*([\s\S]*?)\s*```/;
      const jsonObjectRegex = /\{[\s\S]*\}/;
      const jsonBlockMatch = jsonBlockRegex.exec(responseText);
      const jsonObjectMatch = jsonObjectRegex.exec(responseText);
      const jsonStr = jsonBlockMatch
        ? (jsonBlockMatch[1] ?? jsonBlockMatch[0])
        : jsonObjectMatch
          ? jsonObjectMatch[0]
          : responseText;
      const factData = JSON.parse(jsonStr) as {
        facts?: Array<{
          concept: string;
          details: string;
          confidence: number;
        }>;
        message?: string;
        topic?: string;
        learningObjective?: string;
      };

      // Calculate cost (GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
      const inputTokens = result.usage?.inputTokens ?? 0;
      const outputTokens = result.usage?.outputTokens ?? 0;
      const cost =
        (inputTokens * 0.15) / 1_000_000 + (outputTokens * 0.6) / 1_000_000;

      const duration = (Date.now() - startTime) / 1000;

      return {
        success: true,
        data: {
          facts: factData.facts ?? [],
          message: factData.message ?? "Facts extracted successfully",
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
    return `You are an expert educational fact extractor helping teachers create personalized biology videos for individual students.

Your task:
1. Extract 5-15 key educational facts from the provided biology lesson content
2. Identify the main topic and learning objective
3. Ensure facts are clear, accurate, and suitable for creating engaging educational video scripts

Fact Quality Criteria:
- Clear and well-defined biology concepts
- Relevant to biology education and teaching
- Suitable for use in a personalized video script
- Accurate and age-appropriate
- Can be made engaging through real-world examples and connections
- Educational value for student learning

For each fact, provide:
- concept: The main concept or term (concise, 1-5 words)
- details: A clear explanation suitable for students (2-4 sentences)
- confidence: A confidence score between 0 and 1 based on clarity and accuracy

Output ONLY valid JSON, no additional text.

Required JSON structure:
{
  "facts": [
    {
      "concept": "Main concept or term",
      "details": "Clear explanation or definition",
      "confidence": 0.9
    }
  ],
  "topic": "Main biology topic (e.g., Photosynthesis, Cell Division, DNA)",
  "learningObjective": "What the student should learn from this content",
  "message": "Friendly message to the teacher explaining what was extracted"
}`;
  }

  private buildUserPrompt(content: string): string {
    return `Extract educational facts from this content:

${content}

Provide a comprehensive analysis with 5-15 key facts, the main topic, and a learning objective. Return the result in JSON format.`;
  }
}
