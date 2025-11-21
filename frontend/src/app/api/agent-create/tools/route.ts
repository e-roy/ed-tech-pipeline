import { openai } from "@ai-sdk/openai";
import { type ModelMessage, streamText } from "ai";

import type { Fact } from "@/types";
import { auth } from "@/server/auth";
import {
  getSessionIdFromRequest,
  getOrCreateSession,
} from "@/server/utils/session-utils";
import { saveConversationMessage } from "@/server/utils/message-utils";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { parseToolResult } from "@/lib/ai-utils";
import { generateNarrationTool } from "./_tools/generate-narration-tool";
import { extractFactsTool } from "./_tools/extract-facts-tools";

export const maxDuration = 30;

interface RequestBody {
  messages: ModelMessage[];
  selectedFacts?: Fact[];
  sessionId?: string | null;
}

/**
 * Helper to process tool results and save to database (non-blocking)
 */
function processToolResult(
  toolName: string,
  toolResult: unknown,
  sessionId: string,
) {
  // Fire-and-forget: don't await, but handle errors gracefully
  const savePromise = (async () => {
    try {
      const resultData = parseToolResult<{
        facts?: Fact[];
        narration?: unknown;
      }>(toolResult);

      if (toolName === "extractFactsTool" && resultData.facts) {
        await db
          .update(videoSessions)
          .set({
            extractedFacts: resultData.facts,
            status: "facts_extracted",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));
      } else if (toolName === "generateNarrationTool" && resultData.narration) {
        await db
          .update(videoSessions)
          .set({
            generatedScript: resultData.narration,
            status: "script_generated",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));
      }
    } catch (error) {
      console.error(`Error processing ${toolName} result:`, error);
    }
  })();

  // Don't await, but prevent unhandled rejections
  savePromise.catch(() => {
    /* already logged */
  });
}

/**
 * Helper to build JSON response with proper headers
 */
function buildJsonResponse(
  data: unknown,
  isFirstMessage: boolean,
  isNewSession: boolean,
  sessionId: string,
) {
  const responseData = typeof data === "string" ? data : JSON.stringify(data);
  const response = new Response(responseData, {
    headers: {
      "Content-Type": "application/json",
      "X-Content-Type-Options": "nosniff",
    },
  });

  if (isFirstMessage && isNewSession) {
    response.headers.set("x-session-id", sessionId);
  }

  return response;
}

export async function POST(req: Request) {
  // Get authenticated user session
  const session = await auth();
  if (!session) {
    return new Response("Unauthorized", { status: 401 });
  }

  const body = (await req.json()) as RequestBody;
  const { messages, selectedFacts } = body;

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
  const isFirstMessage = messages.length === 1 && messages[0]?.role === "user";
  const isNewSession = !requestedSessionId || requestedSessionId !== sessionId;

  // Save only the last user message (the new one in this request)
  const userMessages = messages.filter((m) => m.role === "user");
  const lastUserMessage = userMessages[userMessages.length - 1];
  if (lastUserMessage) {
    try {
      await saveConversationMessage(sessionId, lastUserMessage, {
        isFirstMessage,
      });
    } catch (error) {
      console.error("Error saving user message:", error);
    }
  }

  // Store tool results and assistant response
  let capturedToolResults: Array<unknown> = [];
  let assistantTextResponse = "";

  // Build system prompt based on context
  let systemPrompt = `You are a helpful AI assistant that helps create educational videos.

You have access to two tools:
1. extractFactsTool - Extract educational facts from learning materials (text, PDF, or URL)
2. generateNarrationTool - Generate a structured narration/script from confirmed facts

IMPORTANT: When the user provides ANY content (text, stories, learning materials, documents), you MUST use extractFactsTool to analyze it. Do not just acknowledge - always call the tool.

Instructions:
- ALWAYS use extractFactsTool when content is provided
- After facts are extracted, the user will review and select the ones they want
- When the user confirms facts or asks to create a narration, use generateNarrationTool with the selected facts

Be conversational and guide the user through the process naturally.`;

  // If selectedFacts are provided, add a concise instruction
  if (selectedFacts && selectedFacts.length > 0) {
    systemPrompt += `\n\nThe user has selected ${selectedFacts.length} facts. Use generateNarrationTool to create a narration from them.`;
  }

  try {
    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: systemPrompt,
      messages,
      tools: { extractFactsTool, generateNarrationTool },
      onFinish: async (finishResult) => {
        // Capture tool results for response
        if (finishResult.toolResults) {
          capturedToolResults = [...finishResult.toolResults];
        }

        // Capture assistant text response
        assistantTextResponse = finishResult.text;

        // Save assistant response to database (non-blocking)
        if (assistantTextResponse) {
          saveConversationMessage(sessionId, {
            role: "assistant",
            content: assistantTextResponse,
          }).catch((error) => {
            console.error("Error saving assistant message:", error);
          });
        }

        // Process tool results and save to database (non-blocking)
        if (finishResult.toolCalls && finishResult.toolResults) {
          for (let i = 0; i < finishResult.toolCalls.length; i++) {
            const toolCall = finishResult.toolCalls[i];
            const toolResult = finishResult.toolResults[i];
            if (toolCall?.toolName && toolResult) {
              processToolResult(toolCall.toolName, toolResult, sessionId);
            }
          }
        }
      },
    });

    // Consume the stream to trigger onFinish
    await result.text;

    // Return tool results or default response
    if (capturedToolResults?.length > 0) {
      return buildJsonResponse(
        capturedToolResults[0],
        isFirstMessage,
        isNewSession,
        sessionId,
      );
    }

    // If AI responded with text but didn't call tool, return informative message
    if (assistantTextResponse && capturedToolResults.length === 0) {
      return buildJsonResponse(
        {
          message: assistantTextResponse,
          facts: [],
          error:
            "AI did not extract facts. Please try rephrasing your request.",
        },
        isFirstMessage,
        isNewSession,
        sessionId,
      );
    }

    return buildJsonResponse(
      { message: "No facts extracted", facts: [] },
      isFirstMessage,
      isNewSession,
      sessionId,
    );
  } catch (error) {
    console.error("Error in streamText:", error);
    return new Response(
      JSON.stringify({
        error: "Failed to process request",
        message: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
