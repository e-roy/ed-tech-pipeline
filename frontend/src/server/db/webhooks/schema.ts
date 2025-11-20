import {
  text,
  timestamp,
  jsonb,
  varchar,
  pgTableCreator,
} from "drizzle-orm/pg-core";

/**
 * Table creator for webhook tables with webhook_ prefix.
 */
export const createWebhookTable = pgTableCreator((name) => `webhook_${name}`);

export const webhookLogs = createWebhookTable("log", {
  id: text("id").primaryKey(),
  eventType: varchar("event_type", { length: 100 }).notNull(), // video_complete or video_failed
  sessionId: text("session_id"), // Reference to video session
  videoUrl: text("video_url"), // URL of the completed/failed video
  status: varchar("status", { length: 50 }).notNull().default("received"), // received, failed
  payload: jsonb("payload").notNull(), // Full webhook payload
  errorMessage: text("error_message"), // Error message if processing failed
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
