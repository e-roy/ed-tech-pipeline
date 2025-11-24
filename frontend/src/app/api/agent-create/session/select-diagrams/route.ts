import { auth } from "@/server/auth";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { selectAndCopyDiagrams } from "@/server/services/diagram-selector";
import type { Narration } from "@/types";

export const runtime = "nodejs";
export const maxDuration = 60; // Vision analysis can take time

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return new Response("Unauthorized", { status: 401 });
    }

    const body = (await req.json()) as {
      sessionId: string;
    };

    // Verify session belongs to user and get narration
    const [sessionData] = await db
      .select()
      .from(videoSessions)
      .where(eq(videoSessions.id, body.sessionId))
      .limit(1);

    if (!sessionData || sessionData.userId !== session.user.id) {
      return new Response("Session not found", { status: 404 });
    }

    if (!sessionData.generatedScript) {
      return new Response("Narration not found", { status: 400 });
    }

    const narration = sessionData.generatedScript as Narration;

    // Run diagram selection
    const result = await selectAndCopyDiagrams(
      session.user.id,
      body.sessionId,
      narration,
    );

    return Response.json(result);
  } catch (error) {
    console.error("Error selecting diagrams:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}

