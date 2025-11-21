import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { env } from "@/env";
import type { AgentInput, AgentOutput } from "@/types/agent";

export class NarrativeBuilderAgent {
  async process(input: AgentInput): Promise<AgentOutput> {
    const startTime = Date.now();

    try {
      if (!env.OPENAI_API_KEY) {
        throw new Error("OPENAI_API_KEY is not configured");
      }

      const topic = input.data.topic as string;
      const facts = input.data.facts as Array<{
        concept: string;
        details: string;
      }>;
      const targetDuration = (input.data.target_duration as number) ?? 60;
      // New optional fields - backward compatible
      const childAge = input.data.child_age as string | null | undefined;
      const childInterest = input.data.child_interest as
        | string
        | null
        | undefined;

      const systemPrompt = this.buildSystemPrompt(
        targetDuration,
        childAge,
        childInterest,
      );
      const userPrompt = this.buildUserPrompt(
        topic,
        facts,
        targetDuration,
        childAge,
        childInterest,
      );

      const result = await generateText({
        model: openai("gpt-4o-mini"),
        system: systemPrompt,
        prompt: userPrompt,
        temperature: 0.7,
      });

      const content = result.text;
      if (!content) {
        throw new Error("No content in LLM response");
      }

      // Extract JSON from response (may be wrapped in markdown code blocks)
      const jsonBlockRegex = /```json\s*([\s\S]*?)\s*```/;
      const jsonObjectRegex = /\{[\s\S]*\}/;
      const jsonBlockMatch = jsonBlockRegex.exec(content);
      const jsonObjectMatch = jsonObjectRegex.exec(content);
      const jsonStr = jsonBlockMatch
        ? (jsonBlockMatch[1] ?? jsonBlockMatch[0])
        : jsonObjectMatch
          ? jsonObjectMatch[0]
          : content;
      const scriptData = JSON.parse(jsonStr) as unknown;

      // Calculate cost (GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
      const inputTokens = result.usage?.inputTokens ?? 0;
      const outputTokens = result.usage?.outputTokens ?? 0;
      const cost =
        (inputTokens * 0.15) / 1_000_000 + (outputTokens * 0.6) / 1_000_000;

      const duration = (Date.now() - startTime) / 1000;

      return {
        success: true,
        data: { script: scriptData },
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

  private buildSystemPrompt(
    targetDuration: number,
    childAge?: string | null,
    childInterest?: string | null,
  ): string {
    // Determine age-appropriate language
    let ageContext = "grades 6-7 (reading level ~6.5)";
    let readingLevel = "6.5";

    if (childAge) {
      // Parse age and adjust context
      const ageNum = parseInt(childAge, 10);
      if (!isNaN(ageNum)) {
        if (ageNum < 6) {
          ageContext = "early elementary (ages 4-6, reading level ~2-3)";
          readingLevel = "2.5";
        } else if (ageNum < 9) {
          ageContext = "elementary (ages 6-8, reading level ~3-4)";
          readingLevel = "3.5";
        } else if (ageNum < 12) {
          ageContext = "upper elementary (ages 9-11, reading level ~4-5)";
          readingLevel = "4.5";
        } else if (ageNum < 15) {
          ageContext = "middle school (ages 12-14, reading level ~6-7)";
          readingLevel = "6.5";
        } else {
          ageContext = "high school (ages 15+, reading level ~8-9)";
          readingLevel = "8.5";
        }
      }
    }

    // Build interest context if provided
    const interestContext = childInterest
      ? `\n\nChild's Interest: ${childInterest}\n- Incorporate this interest into examples and connections where relevant\n- Make the content relatable to this interest`
      : "";

    return `You are an expert educational video script creator specializing in creating engaging, accurate educational content for ${ageContext}.

Your task:

1. Create a 4-part educational script (Hook → Concept → Process → Conclusion)
2. Each part has specific timing and purpose
3. Use age-appropriate language for ${ageContext}
4. Include all provided facts and key concepts
5. Provide visual guidance for each segment
6. Ensure scientific accuracy${interestContext}

Structure:

- Hook (0-10s): Engage with question or surprising fact
- Concept Introduction (10-25s): Introduce key vocabulary and ideas
- Process Explanation (25-45s): Explain how/why it works with details
- Conclusion (45-60s): Real-world connection and summary

Rules:

- Total duration must be ${targetDuration} seconds
- Use conversational, enthusiastic tone
- Define technical terms when first introduced
- Include concrete examples
- End with memorable takeaway
- Output ONLY valid JSON, no additional text

Required JSON structure:
{
"total_duration": ${targetDuration},
"reading_level": "${readingLevel}",
"key_terms_count": <number>,
"segments": [
{
"id": "seg_001",
"type": "hook",
"start_time": 0,
"duration": 10,
"narration": "<script text>",
"visual_guidance": "<description of what should be shown>",
"key_concepts": ["<concept1>", "<concept2>"],
"educational_purpose": "<why this segment matters>"
},
{
"id": "seg_002",
"type": "concept_introduction",
"start_time": 10,
"duration": 15,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
},
{
"id": "seg_003",
"type": "process_explanation",
"start_time": 25,
"duration": 20,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
},
{
"id": "seg_004",
"type": "conclusion",
"start_time": 45,
"duration": 15,
"narration": "<script text>",
"visual_guidance": "<description>",
"key_concepts": [],
"educational_purpose": "<purpose>"
}
]
}`;
  }

  private buildUserPrompt(
    topic: string,
    facts: Array<{ concept: string; details: string }>,
    targetDuration: number,
    childAge?: string | null,
    childInterest?: string | null,
  ): string {
    const factsStr = facts
      .map((f) => `- ${f.concept}: ${f.details}`)
      .join("\n");

    let ageInfo = "";
    if (childAge) {
      ageInfo = `\nChild's Age: ${childAge} years old`;
    }

    let interestInfo = "";
    if (childInterest) {
      interestInfo = `\nChild's Interest: ${childInterest}`;
    }

    return `Topic: ${topic}${ageInfo}${interestInfo}

Key Facts to Include:
${factsStr}

Target Duration: ${targetDuration} seconds

Generate an engaging, scientifically accurate educational script in JSON format.`;
  }
}
