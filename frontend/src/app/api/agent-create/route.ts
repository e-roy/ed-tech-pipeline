import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages, type UIMessage } from "ai";
import type { ToolCallOptions } from "@ai-sdk/provider-utils";

import type { Fact } from "@/types";
import { auth } from "@/server/auth";
import {
  getSessionIdFromRequest,
  getOrCreateSession,
} from "@/server/utils/session-utils";
import {
  saveConversationMessage,
  saveNewConversationMessages,
} from "@/server/utils/message-utils";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { parseToolResult } from "@/lib/ai-utils";
import { extractFactsTool } from "./_tools/extract-facts-tools";
import { saveStudentInfoTool } from "./_tools/save-student-info-tool";

export const runtime = "nodejs";

interface RequestBody {
  messages: UIMessage[];
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
      // AI SDK wraps tool results in an object with 'output' field
      // Extract the actual result from the wrapper
      let actualResult: unknown = toolResult;

      if (typeof toolResult === "object" && toolResult !== null) {
        const wrapped = toolResult as { output?: unknown; type?: string };
        if (wrapped.type === "tool-result" && wrapped.output !== undefined) {
          actualResult = wrapped.output;
        }
      }

      // Parse tool result - handle both string and object formats
      // The tool returns JSON strings, so we need to parse them
      let resultData: {
        facts?: Fact[];
        narration?: unknown;
        topic?: string;
        learningObjective?: string;
      };

      if (typeof actualResult === "string") {
        try {
          resultData = JSON.parse(actualResult) as typeof resultData;
        } catch {
          // If parsing fails, the string might already be the data structure
          // or it's malformed - try to continue
          resultData = actualResult as typeof resultData;
        }
      } else if (actualResult !== null && typeof actualResult === "object") {
        // Already an object, use it directly
        resultData = actualResult as typeof resultData;
      } else {
        // Fallback: try to treat as the result data directly
        resultData = actualResult as typeof resultData;
      }

      // Debug: log what we're processing
      if (toolName === "extractFactsTool") {
        // Check if facts exist and is an array (even if empty)
        if (resultData.facts && Array.isArray(resultData.facts)) {
          const updateData: {
            extractedFacts: Fact[];
            status: string;
            updatedAt: Date;
            topic?: string;
            learningObjective?: string;
          } = {
            extractedFacts: resultData.facts,
            status: "facts_extracted",
            updatedAt: new Date(),
          };

          // Add topic and learningObjective if provided
          if (resultData.topic) {
            updateData.topic = resultData.topic;
          }
          if (resultData.learningObjective) {
            updateData.learningObjective = resultData.learningObjective;
          }

          await db
            .update(videoSessions)
            .set(updateData)
            .where(eq(videoSessions.id, sessionId));
        }
      }
    } catch {
      // Silently fail - errors are expected in fire-and-forget operations
      // The database update will be retried on next request if needed
    }
  })();

  // Don't await, but prevent unhandled rejections
  savePromise.catch(() => {
    /* already handled in try-catch */
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

  // Save confirmedFacts if selectedFacts are provided
  if (selectedFacts && selectedFacts.length > 0) {
    try {
      await db
        .update(videoSessions)
        .set({
          confirmedFacts: selectedFacts,
          updatedAt: new Date(),
        })
        .where(eq(videoSessions.id, sessionId));
    } catch {
      // Continue even if save fails
    }
  }

  // Save messages to database for persistence (fire-and-forget, non-blocking)
  if (messages.length > 0) {
    saveNewConversationMessages(sessionId, messages, {
      isFirstMessage,
    }).catch(() => {
      // Silent fail - database save is optional for persistence
    });
  }

  // Note: PDF source materials are now accessed directly via pdfUrl in extractFactsTool
  // The extracted text in the database serves only as a fallback if PDF is unavailable
  // We no longer inject it into the system prompt to keep messages clean

  // Store tool results and assistant response
  let capturedToolResults: Array<unknown> = [];
  let assistantTextResponse = "";

  // Build system prompt based on context
  const systemPrompt = `You are an AI assistant helping teachers create educational videos.

CRITICAL RULES - Follow these EXACTLY:

1. If user mentions student age/interests → call saveStudentInfoTool
2. If user message says "PDF materials uploaded" OR provides lesson content → IMMEDIATELY call extractFactsTool
3. DO NOT just acknowledge uploads - you MUST call extractFactsTool

When calling extractFactsTool:
- Pass the user's message text as the content parameter
- The tool will automatically extract PDF URLs from file attachments in the message

After extracting facts, the user will select which ones to use.`;

  // Wrap tools to inject sessionId and extract PDF URL from message parts
  const toolsWithSessionId = {
    saveStudentInfoTool: {
      ...saveStudentInfoTool,
      execute: async (
        args: { child_age: string; child_interest: string },
        options: ToolCallOptions,
      ): Promise<string> => {
        return (await saveStudentInfoTool.execute!(
          { ...args, sessionId },
          options,
        )) as string;
      },
    } as typeof saveStudentInfoTool,
    extractFactsTool: {
      ...extractFactsTool,
      execute: async (
        args: { content: string; pdfUrl?: string },
        options: ToolCallOptions,
      ): Promise<string> => {
        // Extract PDF URL from last user message if not provided
        let pdfUrl = args.pdfUrl;
        if (!pdfUrl) {
          const lastUserMessage = [...messages]
            .reverse()
            .find((m) => m.role === "user");
          if (lastUserMessage?.parts) {
            const filePart = lastUserMessage.parts.find(
              (p) =>
                typeof p === "object" &&
                p !== null &&
                "type" in p &&
                p.type === "file",
            );
            if (filePart && "url" in filePart) {
              pdfUrl = filePart.url;
            }
          }
        }
        return (await extractFactsTool.execute!(
          { content: args.content, pdfUrl },
          options,
        )) as string;
      },
    } as typeof extractFactsTool,
  };

  try {
    // Create a promise to track when onFinish completes
    let onFinishComplete: (() => void) | null = null;
    const onFinishPromise = new Promise<void>((resolve) => {
      onFinishComplete = resolve;
    });

    const result = streamText({
      // model: openai("gpt-4o-mini"),
      model: openai("gpt-4.1-mini-2025-04-14"),
      system: systemPrompt,
      messages: convertToModelMessages(messages),
      tools: toolsWithSessionId,
      onFinish: async (finishResult) => {
        try {
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
            }).catch(() => {
              // Silently fail - non-blocking operation
            });
          }

          // Process tool results and save to database (non-blocking)
          if (finishResult.toolCalls && finishResult.toolResults) {
            for (let i = 0; i < finishResult.toolCalls.length; i++) {
              const toolCall = finishResult.toolCalls[i];
              const toolResult = finishResult.toolResults[i];
              if (toolCall?.toolName && toolResult) {
                processToolResult(toolCall.toolName, toolResult, sessionId);

                // Extract and save assistant message from tool result if present
                try {
                  // Unwrap AI SDK tool result wrapper
                  let actualResult: unknown = toolResult;
                  if (typeof toolResult === "object" && toolResult !== null) {
                    const wrapped = toolResult as {
                      output?: unknown;
                      type?: string;
                    };
                    if (
                      wrapped.type === "tool-result" &&
                      wrapped.output !== undefined
                    ) {
                      actualResult = wrapped.output;
                    }
                  }

                  // Parse the actual tool result
                  const toolResultData = parseToolResult<{
                    message?: string;
                    facts?: unknown;
                    narration?: unknown;
                  }>(actualResult);

                  if (toolResultData.message) {
                    saveConversationMessage(sessionId, {
                      role: "assistant",
                      content: toolResultData.message,
                    }).catch(() => {
                      // Silently fail - non-blocking operation
                    });
                  }
                } catch {
                  // Silently fail if tool result doesn't have message
                }
              }
            }
          }
        } finally {
          // Signal that onFinish has completed
          onFinishComplete?.();
        }
      },
    });

    // Consume the stream to trigger onFinish
    await result.text;

    // Wait for onFinish to complete before proceeding
    await onFinishPromise;

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
