import { db } from "@/server/db";
import { webhookLogs } from "@/server/db/schema";
import { env } from "@/env";
import { nanoid } from "nanoid";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

export const runtime = "nodejs";

/**
 * Webhook payload validation schema
 */
const webhookPayloadSchema = z.object({
  sessionId: z.string(),
  videoUrl: z.string().url(),
  status: z.enum(["video_complete", "video_failed"]),
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
 *   "videoUrl": "string (URL)",
 *   "status": "video_complete" | "video_failed"
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
    const eventType = status; // video_complete or video_failed

    // Log the webhook to database
    const logId = nanoid();
    await db.insert(webhookLogs).values({
      id: logId,
      eventType,
      sessionId,
      videoUrl,
      status: "received",
      payload: payload as Record<string, unknown>,
      createdAt: new Date(),
    });

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
