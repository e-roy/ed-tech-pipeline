import { auth } from "@/server/auth";
import { env } from "@/env";
import type { UIMessage } from "ai";
import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages } from "ai";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import { parseFactsFromMessage } from "@/lib/factParsing";

export const runtime = "nodejs";

const systemMessage = `You are a helpful AI assistant helping a teacher build educational video content.

When the teacher provides learning materials (topic, learning objective, key points, PDFs, or URLs), your task is to:

1. Extract key educational facts from the materials
2. Return the facts in a structured JSON format embedded in your response
3. Be conversational and helpful

When you extract facts, include them in your response using this format:
\`\`\`json
{
  "facts": [
    {
      "concept": "Main concept or term",
      "details": "Clear explanation or definition",
      "confidence": 0.9
    }
  ]
}
\`\`\`

Extract 5-15 key educational facts that are:
- Clear and well-defined concepts
- Relevant to teaching and learning
- Suitable for use in an educational video script
- Accurate and educational

After extracting facts, confirm with the teacher and wait for their approval before moving to the next step.`;

/**
 * POST /api/chat
 *
 * Simple AI chat endpoint for multi-turn conversation.
 */
export async function POST(req: Request) {
  try {
    // Get authenticated user session
    const session = await auth();
    if (!session) {
      return new Response("Unauthorized", { status: 401 });
    }

    // Check for OpenAI API key
    if (!env.OPENAI_API_KEY) {
      return new Response(
        "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
        { status: 500 },
      );
    }

    // Parse request body (AI SDK format)
    const body = (await req.json()) as { messages?: UIMessage[] };
    const { messages } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response("Messages array is required", { status: 400 });
    }

    // Check for fact confirmation and trigger script generation in background
    const lastUserMessage = messages.filter((m) => m.role === "user").pop();
    const confirmationPatterns = [
      /yes/i,
      /approve/i,
      /confirm/i,
      /continue/i,
      /proceed/i,
      /go ahead/i,
      /that's correct/i,
      /looks good/i,
    ];

    if (lastUserMessage) {
      // Extract text content from UIMessage using parts
      const userTextPart = lastUserMessage.parts?.find(
        (part): part is { type: "text"; text: string } => part.type === "text",
      );
      const userContent = userTextPart?.text ?? "";

      if (
        userContent &&
        confirmationPatterns.some((pattern) => pattern.test(userContent))
      ) {
        // Extract facts from assistant messages
        const assistantMessages = messages.filter(
          (m) => m.role === "assistant",
        );
        let extractedFacts: Array<{ concept: string; details: string }> | null =
          null;
        let topic = "";

        for (const msg of assistantMessages.reverse()) {
          const assistantTextPart = msg.parts?.find(
            (part): part is { type: "text"; text: string } =>
              part.type === "text",
          );
          const assistantContent = assistantTextPart?.text ?? "";

          if (assistantContent) {
            const facts = parseFactsFromMessage(assistantContent);
            if (facts && facts.length > 0) {
              extractedFacts = facts.map((f) => ({
                concept: f.concept,
                details: f.details,
              }));
              // Try to extract topic from the message or use a default
              const topicRegex = /topic[:\s]+([^\n]+)/i;
              const topicMatch = topicRegex.exec(assistantContent);
              topic = topicMatch?.[1]?.trim() ?? "Educational Content";
              break;
            }
          }
        }

        if (extractedFacts && extractedFacts.length > 0 && session.user?.id) {
          // Generate script without creating a session yet
          // Script will be saved to DB when user approves it
          const agent = new NarrativeBuilderAgent();
          agent
            .process({
              sessionId: "temp", // Temporary, session will be created on approval
              data: {
                topic,
                facts: extractedFacts,
                target_duration: 60,
              },
            })
            .catch((error) => {
              console.error("Error generating script:", error);
            });
        }
      }
    }

    const result = streamText({
      model: openai("gpt-4o-mini"),
      messages: convertToModelMessages(messages),
      system: systemMessage,
      // onFinish: async (completion) => {
      //   console.log("Streamed Text Completion ===>", completion);
      // },
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error("Chat API error:", error);
    return new Response(
      JSON.stringify({
        error: "An error occurred while processing your request.",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
