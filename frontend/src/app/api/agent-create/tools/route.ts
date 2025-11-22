import { openai } from "@ai-sdk/openai";
import { type ModelMessage, streamText } from "ai";

import type { Fact } from "@/types";
import { auth } from "@/server/auth";
import {
  getSessionIdFromRequest,
  getOrCreateSession,
} from "@/server/utils/session-utils";
import {
  saveConversationMessage,
  loadConversationMessages,
  saveNewConversationMessages,
} from "@/server/utils/message-utils";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { parseToolResult } from "@/lib/ai-utils";
import { generateNarrationTool } from "./_tools/generate-narration-tool";
import { extractFactsTool } from "./_tools/extract-facts-tools";
import { saveStudentInfoTool } from "./_tools/save-student-info-tool";

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
      } else if (toolName === "generateNarrationTool") {
        // Check if narration exists (not null/undefined)
        if (resultData.narration != null) {
          await db
            .update(videoSessions)
            .set({
              generatedScript: resultData.narration,
              status: "script_generated",
              updatedAt: new Date(),
            })
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

  // Load existing conversation messages from database
  let dbMessages: ModelMessage[] = [];
  try {
    dbMessages = await loadConversationMessages(sessionId);
  } catch {
    // Continue with empty array if load fails
  }

  // Merge DB messages with request messages, deduplicating by content
  // Create a set of existing message content for deduplication
  const existingContent = new Set(
    dbMessages.map((m) => {
      const content =
        typeof m.content === "string" ? m.content : JSON.stringify(m.content);
      return `${m.role}:${content}`;
    }),
  );

  // Filter out duplicate messages from request
  const newMessages = messages.filter((msg) => {
    const content =
      typeof msg.content === "string"
        ? msg.content
        : JSON.stringify(msg.content);
    const key = `${msg.role}:${content}`;
    return !existingContent.has(key);
  });

  // Save all new messages (not just the last one)
  if (newMessages.length > 0) {
    try {
      await saveNewConversationMessages(sessionId, newMessages, {
        isFirstMessage,
      });
    } catch {
      // Continue even if save fails
    }
  }

  // Merge DB messages with new messages for AI context
  // DB messages are already in chronological order
  const allMessages = [...dbMessages, ...newMessages];

  // Store tool results and assistant response
  let capturedToolResults: Array<unknown> = [];
  let assistantTextResponse = "";

  // Build system prompt based on context
  let systemPrompt = `You are an expert educational AI assistant helping teachers create personalized biology videos for individual students.

Your role:
- Help teachers create engaging biology videos tailored to specific students
- Gather student information (age and interests) when provided to personalize content
- Extract key facts from lesson materials
- Generate age-appropriate, personalized narration scripts

Available Tools:
1. saveStudentInfoTool - Save student age and interest for personalization (OPTIONAL - use if teacher provides this info)
2. extractFactsTool - Extract educational facts from learning materials (text, PDF, or lesson content)
3. generateNarrationTool - Generate a structured narration/script from confirmed facts

Conversation Flow (FLEXIBLE):
- If the teacher mentions student age or interests, use saveStudentInfoTool to save it
- When the teacher provides lesson content/materials, ALWAYS use extractFactsTool to analyze it
- After facts are extracted and selected, use generateNarrationTool (will automatically use saved student info if available)
- The teacher can skip providing student info - personalization is OPTIONAL but recommended

Key Guidelines:
- Be warm, conversational, and helpful
- Gently encourage personalization but don't require it
- If generating narration without student info, you can prompt: "Would you like to personalize this for a specific student? I can tailor the language and examples if you share their age and interests."
- Always extract facts when content is provided - don't just acknowledge

Be supportive and guide the teacher through the process naturally.`;

  // If selectedFacts are provided, add a concise instruction
  if (selectedFacts && selectedFacts.length > 0) {
    systemPrompt += `\n\nThe user has selected ${selectedFacts.length} facts. Use generateNarrationTool to create a narration from them.`;
  }

  // Wrap tools to inject sessionId
  // The AI SDK Tool type expects execute to take 2 args, but our tools only take 1
  // We use type assertion to work around this mismatch
  const toolsWithSessionId = {
    saveStudentInfoTool: {
      ...saveStudentInfoTool,
      execute: async (
        args: { child_age: string; child_interest: string; sessionId?: string },
        _options?: unknown,
      ): Promise<string> => {
        if (!saveStudentInfoTool.execute) {
          throw new Error("saveStudentInfoTool.execute is not defined");
        }
        const originalExecute = saveStudentInfoTool.execute as (args: {
          child_age: string;
          child_interest: string;
          sessionId?: string;
        }) => Promise<string>;
        const result = await originalExecute({
          ...args,
          sessionId,
        });
        return result;
      },
    } as typeof saveStudentInfoTool,
    extractFactsTool: {
      ...extractFactsTool,
      execute: async (
        args: { content: string; sessionId?: string },
        _options?: unknown,
      ): Promise<string> => {
        if (!extractFactsTool.execute) {
          throw new Error("extractFactsTool.execute is not defined");
        }
        // Call original execute with injected sessionId
        // Type assertion needed because Tool.execute signature expects 2 args
        const originalExecute = extractFactsTool.execute as (args: {
          content: string;
          sessionId?: string;
        }) => Promise<string>;
        const result = await originalExecute({
          ...args,
          sessionId,
        });
        return result;
      },
    } as typeof extractFactsTool,
    generateNarrationTool: {
      ...generateNarrationTool,
      execute: async (
        args: {
          facts: Array<{
            concept: string;
            details: string;
            confidence?: number;
          }>;
          topic?: string;
          target_duration?: number;
          child_age?: string;
          child_interest?: string;
          sessionId?: string;
        },
        _options?: unknown,
      ): Promise<string> => {
        if (!generateNarrationTool.execute) {
          throw new Error("generateNarrationTool.execute is not defined");
        }
        // Call original execute with injected sessionId
        // Type assertion needed because Tool.execute signature expects 2 args
        const originalExecute = generateNarrationTool.execute as (args: {
          facts: Array<{
            concept: string;
            details: string;
            confidence?: number;
          }>;
          topic?: string;
          target_duration?: number;
          child_age?: string;
          child_interest?: string;
          sessionId?: string;
        }) => Promise<string>;
        const result = await originalExecute({
          ...args,
          sessionId,
        });
        return result;
      },
    } as typeof generateNarrationTool,
  };

  try {
    const result = streamText({
      model: openai("gpt-4o-mini"),
      system: systemPrompt,
      messages: allMessages,
      tools: toolsWithSessionId,
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
                const toolResultData = parseToolResult<{
                  message?: string;
                  facts?: unknown;
                  narration?: unknown;
                }>(toolResult);
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
