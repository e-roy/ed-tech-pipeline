import { auth } from "@/server/auth";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import type { Narration } from "@/types";
import { selectAndCopyDiagrams } from "@/server/services/diagram-selector";

export const runtime = "nodejs";

export async function PATCH(req: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return new Response("Unauthorized", { status: 401 });
    }

    const body = (await req.json()) as {
      sessionId: string;
      narration: Narration;
    };

    // Verify session belongs to user
    const [sessionData] = await db
      .select()
      .from(videoSessions)
      .where(eq(videoSessions.id, body.sessionId))
      .limit(1);

    if (!sessionData || sessionData.userId !== session.user.id) {
      return new Response("Session not found", { status: 404 });
    }

    // Update the generated script with edited version and mark as verified
    await db
      .update(videoSessions)
      .set({
        generatedScript: body.narration,
        status: "narration_verified",
        updatedAt: new Date(),
      })
      .where(eq(videoSessions.id, body.sessionId));

    // Trigger diagram selection in the background (fire and forget)
    // This won't block the response to the user
    selectAndCopyDiagrams(session.user.id, body.sessionId, body.narration)
      .then((result) => {
        console.log("[narration/route] Diagram selection completed:", result);
      })
      .catch((error) => {
        console.error("[narration/route] Diagram selection failed:", error);
      });

    return new Response(
      JSON.stringify({
        success: true,
        message: "Narration saved successfully",
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      },
    );
  } catch (error) {
    console.error("Error saving narration:", error);
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

