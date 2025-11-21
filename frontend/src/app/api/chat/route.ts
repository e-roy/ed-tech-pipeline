import { auth } from "@/server/auth";
import { env } from "@/env";
import type { UIMessage } from "ai";
import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages } from "ai";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import { parseFactsFromMessage } from "@/lib/factParsing";
import {
  getSessionIdFromRequest,
  getOrCreateSession,
} from "@/server/utils/session-utils";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

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
    const body = (await req.json()) as {
      messages?: UIMessage[];
      sessionId?: string | null;
    };
    const { messages } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response("Messages array is required", { status: 400 });
    }

    // Get or create session ID
    if (!session.user?.id) {
      return new Response("User ID not found in session", { status: 401 });
    }

    const requestedSessionId = getSessionIdFromRequest(req, body);
    const sessionId = await getOrCreateSession(
      session.user.id,
      requestedSessionId,
    );

    // Detect if this is the first message (new conversation)
    const isFirstMessage =
      messages.length === 1 && messages[0]?.role === "user";
    const isNewSession =
      !requestedSessionId || requestedSessionId !== sessionId;

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

      let extractedFacts: Array<{ concept: string; details: string }> | null =
        null;
      let topic = "Educational Content";
      let shouldGenerate = false;

      // 1. Try to get facts directly from user message (UI confirmation)
      const userFacts = parseFactsFromMessage(userContent);
      if (userFacts && userFacts.length > 0) {
        extractedFacts = userFacts.map((f) => ({
          concept: f.concept,
          details: f.details,
        }));
        shouldGenerate = true;
      }

      // 2. If no facts in user message, check for confirmation keywords
      if (
        !shouldGenerate &&
        userContent &&
        confirmationPatterns.some((pattern) => pattern.test(userContent))
      ) {
        shouldGenerate = true;
      }

      if (shouldGenerate) {
        // Scan assistant history for topic and fallback facts
        const assistantMessages = messages.filter(
          (m) => m.role === "assistant",
        );

        for (const msg of assistantMessages.reverse()) {
          const assistantTextPart = msg.parts?.find(
            (part): part is { type: "text"; text: string } =>
              part.type === "text",
          );
          const assistantContent = assistantTextPart?.text ?? "";

          if (assistantContent) {
            // If we still need facts, look for them here
            if (!extractedFacts) {
              const facts = parseFactsFromMessage(assistantContent);
              if (facts && facts.length > 0) {
                extractedFacts = facts.map((f) => ({
                  concept: f.concept,
                  details: f.details,
                }));
              }
            }

            // Look for topic
            const topicRegex = /topic[:\s]+([^\n]+)/i;
            const topicMatch = topicRegex.exec(assistantContent);
            if (topicMatch?.[1]) {
              topic = topicMatch[1].trim();
            }

            // If we have both facts and found a topic (or if we have facts and are deep in history),
            // we can stop. But since topic might be further back, we might want to keep looking for topic.
            // For simplicity, if we have facts and found a topic, break.
            if (extractedFacts && topic !== "Educational Content") break;
          }
        }

        if (extractedFacts && extractedFacts.length > 0 && session.user?.id) {
          // Fetch session to get child_age and child_interest
          const [sessionData] = await db
            .select({
              childAge: videoSessions.childAge,
              childInterest: videoSessions.childInterest,
            })
            .from(videoSessions)
            .where(eq(videoSessions.id, sessionId))
            .limit(1);

          // Save confirmed facts immediately
          await db
            .update(videoSessions)
            .set({
              confirmedFacts: extractedFacts,
              updatedAt: new Date(),
            })
            .where(eq(videoSessions.id, sessionId));

          // Generate script using the session ID
          const agent = new NarrativeBuilderAgent();
          agent
            .process({
              sessionId,
              data: {
                topic,
                facts: extractedFacts,
                target_duration: 60,
                // Pass child_age and child_interest if available
                child_age: sessionData?.childAge ?? null,
                child_interest: sessionData?.childInterest ?? null,
              },
            })
            .then(async (result) => {
              if (result.success && result.data.script) {
                // Save generated script to database
                await db
                  .update(videoSessions)
                  .set({
                    generatedScript: result.data.script,
                    status: "script_generated",
                    updatedAt: new Date(),
                  })
                  .where(eq(videoSessions.id, sessionId));
              }
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
      onFinish: async (completion) => {
        const text = completion.text;
        if (text) {
          const facts = parseFactsFromMessage(text);
          if (facts && facts.length > 0) {
            await db
              .update(videoSessions)
              .set({
                extractedFacts: facts,
                updatedAt: new Date(),
              })
              .where(eq(videoSessions.id, sessionId));
          }
        }
      },
    });

    const response = result.toUIMessageStreamResponse();

    // Set sessionId header if this is a new session (first message on create page)
    // Only set for new sessions, not when resuming from history
    if (isFirstMessage && isNewSession) {
      response.headers.set("Access-Control-Expose-Headers", "x-session-id");
      response.headers.set("x-session-id", sessionId);
    }

    return response;
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
