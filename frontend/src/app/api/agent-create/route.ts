import { openai } from "@ai-sdk/openai";
import { streamObject, type ModelMessage } from "ai";
import { z } from "zod";
import type { Fact } from "@/types";
import { auth } from "@/server/auth";
import {
  getSessionIdFromRequest,
  getOrCreateSession,
} from "@/server/utils/session-utils";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

export const maxDuration = 30;

interface RequestBody {
  messages: ModelMessage[];
  documentContent?: string;
  mode?: "extract" | "narrate" | "edit";
  selectedFacts?: Fact[];
  sessionId?: string | null;
}

export async function POST(req: Request) {
  // Get authenticated user session
  const session = await auth();
  if (!session) {
    return new Response("Unauthorized", { status: 401 });
  }

  const body = (await req.json()) as RequestBody;
  const { messages, documentContent, mode, selectedFacts } = body;

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

  if (mode === "extract") {
    const result = streamObject({
      model: openai("gpt-4o-mini"),
      system: `You are an expert fact extractor. Your goal is to analyze the user's story and extract a list of key facts.
      
      For each fact, provide:
      - concept: The main concept or term.
      - details: A clear explanation or definition based on the story.
      - confidence: A number between 0 and 1 indicating your confidence in this fact.
      
      Return a JSON object with a "facts" array.`,
      messages,
      schema: z.object({
        facts: z.array(
          z.object({
            concept: z.string().describe("Main concept or term"),
            details: z.string().describe("Clear explanation or definition"),
            confidence: z.number().describe("Confidence score between 0 and 1"),
          }),
        ),
      }),
      onFinish: async (result) => {
        if (result.object?.facts) {
          // Save extracted facts to database
          try {
            await db
              .update(videoSessions)
              .set({
                // Type casting as we're saving raw JSON
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                extractedFacts: result.object.facts as any,
                status: "facts_extracted",
                updatedAt: new Date(),
              })
              .where(eq(videoSessions.id, sessionId));
          } catch (error) {
            console.error("Error saving extracted facts:", error);
          }
        }
      },
    });

    const response = result.toTextStreamResponse();

    // Set sessionId header if this is a new session (first message)
    if (isFirstMessage && isNewSession) {
      response.headers.set("x-session-id", sessionId);
    }

    return response;
  } else if (mode === "narrate") {
    const result = streamObject({
      model: openai("gpt-4o-mini"),
      system: `You are a creative narrator for educational videos. 
      Your task is to create a structured narration based on the provided facts.
      
      The user has selected the following facts:
      ${JSON.stringify(selectedFacts, null, 2)}
      
      Create a cohesive and engaging narration that incorporates these facts.
      Return a structured object with the following fields:
      - total_duration: Estimated total duration in seconds.
      - reading_level: Reading level (e.g., "6.5").
      - key_terms_count: Number of key terms used.
      - segments: An array of narration segments for 4 segments: hook, concept_introduction, process_explanation, conclusion.
      
      Each segment should have:
      - id: Unique ID (e.g., "seg_001").
      - type: Type of segment (e.g., "hook", "concept_introduction", "process_explanation", "conclusion").
      - start_time: Start time in seconds.
      - duration: Duration in seconds.
      - narration: The script text.
      - visual_guidance: Description of what should be shown.
      - key_concepts: Array of key concepts covered in this segment.
      - educational_purpose: Why this segment matters.`,
      messages: [
        ...messages,
        {
          role: "user" as const,
          content: "Create a structured narration based on the selected facts.",
        },
      ],
      schema: z.object({
        total_duration: z
          .number()
          .describe("Estimated total duration in seconds"),
        reading_level: z.string().describe("Reading level (e.g., '6.5')"),
        key_terms_count: z.number().describe("Number of key terms used"),
        segments: z.array(
          z.object({
            id: z.string().describe("Unique ID (e.g., 'seg_001')"),
            type: z.string().describe("Type of segment"),
            start_time: z.number().describe("Start time in seconds"),
            duration: z.number().describe("Duration in seconds"),
            narration: z.string().describe("The script text"),
            visual_guidance: z
              .string()
              .describe("Description of what should be shown"),
            key_concepts: z
              .array(z.string())
              .describe("Array of key concepts covered"),
            educational_purpose: z
              .string()
              .describe("Why this segment matters"),
          }),
        ),
      }),
      onFinish: async (result) => {
        if (result.object) {
          // Save generated script to database
          try {
            await db
              .update(videoSessions)
              .set({
                // Type casting as we're saving raw JSON
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                generatedScript: result.object as any,
                status: "script_generated",
                updatedAt: new Date(),
              })
              .where(eq(videoSessions.id, sessionId));

            // Also save selected facts if they were provided
            if (selectedFacts) {
              await db
                .update(videoSessions)
                .set({
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  confirmedFacts: selectedFacts as any,
                })
                .where(eq(videoSessions.id, sessionId));
            }
          } catch (error) {
            console.error("Error saving generated script:", error);
          }
        }
      },
    });

    const response = result.toTextStreamResponse();

    // Set sessionId header if this is a new session (first message)
    if (isFirstMessage && isNewSession) {
      response.headers.set("x-session-id", sessionId);
    }

    return response;
  } else {
    // Default behavior (edit mode)
    const result = streamObject({
      model: openai("gpt-4o-mini"),
      system: `You are a helpful assistant that edits markdown documents based on user requests.
      Current document content:
      ${documentContent ?? ""}`,
      messages,
      schema: z.object({
        documentContent: z
          .string()
          .describe("The updated markdown document content."),
        reply: z.string().describe("Your conversational response to the user."),
      }),
    });

    const response = result.toTextStreamResponse();

    // Set sessionId header if this is a new session (first message)
    if (isFirstMessage && isNewSession) {
      response.headers.set("x-session-id", sessionId);
    }

    return response;
  }
}
