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
  targetDuration: number = 60,
) {
  const agent = new NarrativeBuilderAgent();
  const result = await agent.process({
    sessionId: "temp",
    data: {
      topic,
      facts,
      target_duration: targetDuration,
    },
  });

  if (!result.success) {
    throw new Error(result.error || "Script generation failed");
  }

  return {
    script: result.data.script,
    cost: result.cost,
    duration: result.duration,
  };
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

