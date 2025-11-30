import { db } from "@/server/db";
import { webhookLogs, videoSessions } from "@/server/db/schema";
import { env } from "@/env";
import { nanoid } from "nanoid";
import { type NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { eq } from "drizzle-orm";

export const runtime = "nodejs";

/**
 * Webhook payload validation schema
 */
const webhookPayloadSchema = z.object({
  sessionId: z.string(),
  videoUrl: z.union([
    z.string().url(), // Valid URL for successful cases
    z.literal(""), // Empty string for failed cases or processing_started
  ]),
  status: z.enum(["video_complete", "video_failed", "processing_started"]),
});

/**
 * POST /api/webhooks/video-complete
 *
 * Webhook endpoint for external video processing service to notify
 * when a video process is complete or failed.
 *
 * Headers:
 * - x-webhook-secret: Secret token for authentication
 *
 * Body:
 * {
 *   "sessionId": "string",
 *   "videoUrl": "string (URL or empty string for failed/started cases)",
 *   "status": "video_complete" | "video_failed" | "processing_started"
 * }
 */
export async function POST(req: NextRequest) {
  try {
    // Verify webhook secret
    const webhookSecret = req.headers.get("x-webhook-secret");
    const expectedSecret = env.WEBHOOK_SECRET;

    if (
      expectedSecret &&
      (!webhookSecret || webhookSecret !== expectedSecret)
    ) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse and validate the webhook payload
    let payload: unknown;
    try {
      payload = await req.json();
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (parseError) {
      const logId = nanoid();
      await db.insert(webhookLogs).values({
        id: logId,
        eventType: "unknown",
        sessionId: null,
        videoUrl: null,
        status: "failed",
        payload: { error: "Failed to parse JSON payload" },
        errorMessage: "Invalid JSON payload",
        createdAt: new Date(),
      });
      return NextResponse.json(
        { error: "Invalid JSON payload" },
        { status: 400 },
      );
    }

    // Validate payload structure
    const validationResult = webhookPayloadSchema.safeParse(payload);
    if (!validationResult.success) {
      const logId = nanoid();
      await db.insert(webhookLogs).values({
        id: logId,
        eventType: "unknown",
        sessionId: null,
        videoUrl: null,
        status: "failed",
        payload: payload as Record<string, unknown>,
        errorMessage: `Validation error: ${validationResult.error.message}`,
        createdAt: new Date(),
      });
      return NextResponse.json(
        {
          error: "Invalid payload",
          details: validationResult.error.errors,
        },
        { status: 400 },
      );
    }

    const { sessionId, videoUrl, status } = validationResult.data;
    const eventType = status; // video_complete, video_failed, or processing_started

    // Additional validation: video_complete must have a non-empty URL
    // processing_started and video_failed don't require a URL
    if (status === "video_complete" && !videoUrl) {
      const logId = nanoid();
      await db.insert(webhookLogs).values({
        id: logId,
        eventType: "unknown",
        sessionId,
        videoUrl: null,
        status: "failed",
        payload: payload as Record<string, unknown>,
        errorMessage: "video_complete status requires a non-empty videoUrl",
        createdAt: new Date(),
      });
      return NextResponse.json(
        {
          error: "Invalid payload",
          details: "video_complete status requires a non-empty videoUrl",
        },
        { status: 400 },
      );
    }

    // Normalize empty string to null for database consistency
    const normalizedVideoUrl = videoUrl === "" ? null : videoUrl;

    // Log the webhook to database
    const logId = nanoid();
    await db.insert(webhookLogs).values({
      id: logId,
      eventType,
      sessionId,
      videoUrl: normalizedVideoUrl,
      status: "received",
      payload: payload as Record<string, unknown>,
      createdAt: new Date(),
    });

    // Update session status based on webhook event
    try {
      if (eventType === "video_complete") {
        await db
          .update(videoSessions)
          .set({
            status: "video_complete",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));
      } else if (eventType === "video_failed") {
        await db
          .update(videoSessions)
          .set({
            status: "video_failed",
            updatedAt: new Date(),
          })
          .where(eq(videoSessions.id, sessionId));
      }
    } catch (updateError) {
      console.error("Failed to update session status:", updateError);
      // Don't fail the webhook - we've logged it, session update is secondary
    }

    return NextResponse.json(
      {
        success: true,
        message: "Webhook received and logged",
        logId,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error("Webhook error:", error);

    // Log the error
    try {
      const logId = nanoid();
      await db.insert(webhookLogs).values({
        id: logId,
        eventType: "unknown",
        sessionId: null,
        videoUrl: null,
        status: "failed",
        payload: { error: "Internal server error" },
        errorMessage: error instanceof Error ? error.message : "Unknown error",
        createdAt: new Date(),
      });
    } catch (logError) {
      console.error("Failed to log webhook error:", logError);
    }

    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
