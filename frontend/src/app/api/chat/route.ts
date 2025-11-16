import { auth } from "@/server/auth";
import { env } from "@/env";
import type { UIMessage } from "ai";
import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages } from "ai";

export const runtime = "nodejs";

const systemMessage = `You are a helpful AI assistant helping a teacher build a facts set for a lesson plan.

Have a conversation with the teacher to understand what they want to teach. Be conversational and ask clarifying questions.`;

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

    const result = streamText({
      model: openai("gpt-4o-mini"),
      messages: convertToModelMessages(messages),
      system: systemMessage,
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
