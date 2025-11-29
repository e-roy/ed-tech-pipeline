import { NarrativeBuilderAgent } from "@/server/agents/narrative-builder";
import { db } from "@/server/db";
import { videoSessions, videoAssets } from "@/server/db/schema";
import { eq } from "drizzle-orm";
import { nanoid } from "nanoid";

/**
 * Generate a script without saving to database.
 * Script will be saved when user approves it.
 */
export async function generateScript(
  topic: string,
  facts: Array<{ concept: string; details: string }>,
  targetDuration = 60,
) {
  const agent = new NarrativeBuilderAgent();
  const result = await agent.process({
    data: {
      topic,
      facts,
      target_duration: targetDuration,
    },
    metadata: { sessionId: "temp" },
  });

  if (!result.success) {
    throw new Error(result.error ?? "Script generation failed");
  }

  return {
    script: result.data.script,
    cost: result.cost,
    duration: result.duration,
  };
}

/**
 * Update an existing session with the approved script.
 */
export async function updateSessionWithScript(
  sessionId: string,
  userId: string,
  topic: string,
  facts: Array<{ concept: string; details: string }>,
  script: unknown,
  cost: number,
  duration: number,
) {
  // Validate session exists and belongs to user
  const [session] = await db
    .select()
    .from(videoSessions)
    .where(eq(videoSessions.id, sessionId))
    .limit(1);

  if (!session?.userId || session.userId !== userId) {
    throw new Error("Session not found or does not belong to user");
  }

  // Update session
  await db
    .update(videoSessions)
    .set({
      status: "script_approved",
      topic,
      confirmedFacts: facts,
      generatedScript: script,
      updatedAt: new Date(),
    })
    .where(eq(videoSessions.id, sessionId));

  // Check if script asset already exists
  const existingAssets = await db
    .select()
    .from(videoAssets)
    .where(eq(videoAssets.sessionId, sessionId));

  const existingScriptAsset = existingAssets.find(
    (asset) => asset.assetType === "script",
  );

  if (existingScriptAsset) {
    // Update existing script asset
    await db
      .update(videoAssets)
      .set({
        metadata: {
          script,
          cost,
          duration,
        },
      })
      .where(eq(videoAssets.id, existingScriptAsset.id));
  } else {
    // Create new script asset
    const assetId = nanoid();
    await db.insert(videoAssets).values({
      id: assetId,
      sessionId,
      assetType: "script",
      url: "",
      metadata: {
        script,
        cost,
        duration,
      },
      createdAt: new Date(),
    });
  }

  return sessionId;
}

/**
 * Create a session and save the approved script to it.
 */
export async function createSessionWithScript(
  userId: string,
  topic: string,
  facts: Array<{ concept: string; details: string }>,
  script: unknown,
  cost: number,
  duration: number,
) {
  const sessionId = nanoid();

  // Create session
  await db.insert(videoSessions).values({
    id: sessionId,
    userId,
    status: "script_approved",
    topic,
    confirmedFacts: facts,
    generatedScript: script,
    createdAt: new Date(),
    updatedAt: new Date(),
  });

  // Save script as asset
  const assetId = nanoid();
  await db.insert(videoAssets).values({
    id: assetId,
    sessionId,
    assetType: "script",
    url: "",
    metadata: {
      script,
      cost,
      duration,
    },
    createdAt: new Date(),
  });

  return sessionId;
}
