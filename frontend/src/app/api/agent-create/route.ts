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
import { buildStandardResponse } from "@/lib/api-response";
import type { StandardApiResponse } from "@/lib/api-response";
import { extractFactsTool } from "./_tools/extract-facts-tools";
import { saveStudentInfoTool } from "./_tools/save-student-info-tool";

export const runtime = "nodejs";

interface RequestBody {
  messages: UIMessage[];
  selectedFacts?: Fact[];
  sessionId?: string | null;
}

/**
 * Process tool results and save to database (non-blocking)
 */
function processToolResult(
  toolName: string,
  toolResult: unknown,
  sessionId: string,
) {
  const savePromise = (async () => {
    try {
      const data = buildStandardResponse(toolResult);

      if (toolName === "extractFactsTool" && data.facts) {
        const updateData: {
          extractedFacts: Fact[];
          status: string;
          updatedAt: Date;
          topic?: string;
          learningObjective?: string;
        } = {
          extractedFacts: data.facts,
          status: "facts_extracted",
          updatedAt: new Date(),
        };

        if (data.topic) updateData.topic = data.topic;
        if (data.learningObjective) {
          updateData.learningObjective = data.learningObjective;
        }

        await db
          .update(videoSessions)
          .set(updateData)
          .where(eq(videoSessions.id, sessionId));
      }

      // Save assistant message if present
      if (data.message) {
        await saveConversationMessage(sessionId, {
          role: "assistant",
          content: data.message,
        });
      }
    } catch (error) {
      // Silently fail - database save is optional
      console.error("Failed to process tool result:", error);
    }
  })();

  savePromise.catch(() => {
    /* already handled */
  });
}

/**
 * Helper to build JSON response with proper headers
 */
function buildJsonResponse(
  data: StandardApiResponse,
  isFirstMessage: boolean,
  isNewSession: boolean,
  sessionId: string,
) {
  const response = new Response(JSON.stringify(data), {
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

/**
 * Strip file parts from messages before sending to LLM
 * Files are handled separately via tool parameters, so LLM doesn't need them
 */
function stripFileParts(messages: UIMessage[]): UIMessage[] {
  return messages.map((msg) => ({
    ...msg,
    parts:
      msg.parts?.filter(
        (part) =>
          typeof part === "object" &&
          part !== null &&
          "type" in part &&
          part.type !== "file",
      ) ?? [],
  }));
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

  // Build system prompt
  const systemPrompt = `You are an AI assistant helping teachers create educational videos.

CRITICAL RULES - Follow these EXACTLY:

1. If user mentions student age/interests → call saveStudentInfoTool
2. If user provides any of the following → IMMEDIATELY call extractFactsTool:
   - PDF materials uploaded for analysis
   - A website URL to extract facts from
   - Lesson content text
3. DO NOT just acknowledge uploads or URLs - you MUST call extractFactsTool

When calling extractFactsTool:
- Pass the user's message text as the content parameter
- If user provides a URL, pass it as the websiteUrl parameter
- The tool will automatically access PDFs from file attachments
- The tool will fetch and analyze website content from URLs

After extracting facts, the user will select which ones to use.`;

  // Extract PDF URL from last user message for tools to access
  const lastUserMessage = [...messages]
    .reverse()
    .find((m) => m.role === "user");
  let pdfUrl: string | undefined;
  if (lastUserMessage?.parts) {
    const filePart = lastUserMessage.parts.find(
      (p) =>
        typeof p === "object" && p !== null && "type" in p && p.type === "file",
    );
    if (filePart && "url" in filePart) {
      pdfUrl = filePart.url;
    }
  }

  // Simplified tool wrappers - just inject sessionId and pdfUrl
  const toolsWithContext = {
    saveStudentInfoTool: {
      ...saveStudentInfoTool,
      execute: async (
        args: { child_age: string; child_interest: string },
        options: ToolCallOptions,
      ): Promise<{
        success: boolean;
        message: string;
        child_age?: string;
        child_interest?: string;
      }> => {
        return (await saveStudentInfoTool.execute!(
          { ...args, sessionId },
          options,
        )) as {
          success: boolean;
          message: string;
          child_age?: string;
          child_interest?: string;
        };
      },
    } as typeof saveStudentInfoTool,
    extractFactsTool: {
      ...extractFactsTool,
      execute: async (
        args: { content: string; pdfUrl?: string; websiteUrl?: string },
        options: ToolCallOptions,
      ): Promise<{
        success: boolean;
        facts: Fact[];
        message: string;
        topic?: string;
        learningObjective?: string;
      }> => {
        return (await extractFactsTool.execute!(
          {
            content: args.content,
            pdfUrl: args.pdfUrl ?? pdfUrl,
            websiteUrl: args.websiteUrl,
          },
          options,
        )) as {
          success: boolean;
          facts: Fact[];
          message: string;
          topic?: string;
          learningObjective?: string;
        };
      },
    } as typeof extractFactsTool,
  };

  try {
    let toolResults: unknown[] = [];
    let assistantText = "";

    const result = streamText({
      model: openai("gpt-4.1-mini-2025-04-14"),
      system: systemPrompt,
      messages: convertToModelMessages(stripFileParts(messages)),
      tools: toolsWithContext,
      onFinish: async (finishResult) => {
        toolResults = finishResult.toolResults ?? [];
        assistantText = finishResult.text;

        // Process all tool calls
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

    // Consume stream to trigger onFinish
    await result.text;

    // Build standardized response
    let responseData: StandardApiResponse;

    if (toolResults.length > 0) {
      // Return first tool result as standardized response
      responseData = buildStandardResponse(toolResults[0]);
    } else if (assistantText) {
      // AI responded with text but didn't call tool
      responseData = {
        success: false,
        message: assistantText,
        error:
          "AI did not call the appropriate tool. Please try rephrasing your request.",
      };
    } else {
      responseData = {
        success: false,
        message: "No response generated",
        error: "Please try again",
      };
    }

    return buildJsonResponse(
      responseData,
      isFirstMessage,
      isNewSession,
      sessionId,
    );
  } catch (error) {
    return new Response(
      JSON.stringify({
        success: false,
        error: "Failed to process request",
        message: error instanceof Error ? error.message : "Unknown error",
      } as StandardApiResponse),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}
