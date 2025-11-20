import { nanoid } from "nanoid";
import { db } from "@/server/db";
import { videoSessions } from "@/server/db/schema";
import { eq } from "drizzle-orm";

/**
 * Extract sessionId from request.
 * Priority: Header (x-session-id) > Body (sessionId) > Query Param > null
 */
export function getSessionIdFromRequest(
  req: Request,
  body?: { sessionId?: string | null },
): string | null {
  // Try header first (for history resumption)
  const sessionIdFromHeader = req.headers.get("x-session-id");
  if (sessionIdFromHeader) {
    return sessionIdFromHeader;
  }

  // Try request body (for normal chat continuation)
  if (body?.sessionId) {
    return body.sessionId;
  }

  // Try query parameter (fallback)
  try {
    const url = new URL(req.url);
    const querySessionId = url.searchParams.get("sessionId");
    if (querySessionId) {
      return querySessionId;
    }
  } catch {
    // If URL parsing fails, continue
  }

  return null;
}

/**
 * Validate that a session exists and belongs to the user.
 */
export async function validateSession(
  sessionId: string,
  userId: string,
): Promise<boolean> {
  const [session] = await db
    .select()
    .from(videoSessions)
    .where(eq(videoSessions.id, sessionId))
    .limit(1);

  if (!session) {
    return false;
  }

  return session.userId === userId;
}

/**
 * Get existing session or create a new one.
 * If sessionId is provided, validates it belongs to the user.
 * If sessionId is missing or invalid, creates a new session.
 */
export async function getOrCreateSession(
  userId: string,
  sessionId?: string | null,
): Promise<string> {
  // If sessionId provided, validate and return it
  if (sessionId) {
    const isValid = await validateSession(sessionId, userId);
    if (isValid) {
      return sessionId;
    }
    // If invalid, fall through to create new session
  }

  // Create new session
  const newSessionId = nanoid();
  const now = new Date();

  await db.insert(videoSessions).values({
    id: newSessionId,
    userId,
    status: "created",
    createdAt: now,
    updatedAt: now,
  });

  return newSessionId;
}
