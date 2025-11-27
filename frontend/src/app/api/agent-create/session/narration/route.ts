import { auth } from "@/server/auth";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { selectAndCopyDiagrams } from "@/server/services/diagram-selector";
import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import type { Narration } from "@/types";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const body = (await req.json()) as {
    sessionId: string;
    selectedFacts: Array<{ concept: string; details: string }>;
  };

  // Load session data to get topic, child age/interest
  const [sessionData] = await db
    .select({
      topic: videoSessions.topic,
      childAge: videoSessions.childAge,
      childInterest: videoSessions.childInterest,
    })
    .from(videoSessions)
    .where(eq(videoSessions.id, body.sessionId))
    .limit(1);

  // Save selectedFacts as confirmedFacts
  await db
    .update(videoSessions)
    .set({
      confirmedFacts: body.selectedFacts,
      updatedAt: new Date(),
    })
    .where(eq(videoSessions.id, body.sessionId));

  // Call NarrativeBuilderAgent directly (no tool wrapper overhead)
  const agent = new NarrativeBuilderAgent();
  const result = await agent.process({
    sessionId: body.sessionId,
    data: {
      topic:
        sessionData?.topic ??
        body.selectedFacts[0]?.concept ??
        "Educational Content",
      facts: body.selectedFacts,
      target_duration: 60,
      child_age: sessionData?.childAge ?? null,
      child_interest: sessionData?.childInterest ?? null,
    },
  });

  if (!result.success) {
    return new Response(
      JSON.stringify({
        success: false,
        error: result.error ?? "Failed to generate narration",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  const narration = result.data.script as Narration;

  return new Response(
    JSON.stringify({
      success: true,
      narration,
      message: `Successfully generated narration with ${narration.segments?.length ?? 0} segments`,
    }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    },
  );
}

export async function PATCH(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const body = (await req.json()) as {
    sessionId: string;
    narration: Narration;
  };

  // Verify session belongs to user and load confirmed facts
  const [sessionData] = await db
    .select({
      id: videoSessions.id,
      userId: videoSessions.userId,
      confirmedFacts: videoSessions.confirmedFacts,
    })
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

  // Extract confirmed facts for diagram selection
  const confirmedFacts =
    sessionData.confirmedFacts && Array.isArray(sessionData.confirmedFacts)
      ? (sessionData.confirmedFacts as Array<{
          concept: string;
          details: string;
        }>)
      : [];

  // Trigger diagram selection in the background (fire and forget)
  // Pass facts to improve image matching accuracy
  selectAndCopyDiagrams(
    session.user.id,
    body.sessionId,
    body.narration,
    confirmedFacts,
  )
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
}
