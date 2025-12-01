import {
  text,
  timestamp,
  jsonb,
  varchar,
  pgTableCreator,
} from "drizzle-orm/pg-core";
import { users } from "../auth/schema";

/**
 * Table creator for video generation tables with video_ prefix.
 */
export const createVideoTable = pgTableCreator((name) => `video_${name}`);

/**
 * Video session table - source of truth for content creation.
 *
 * Architecture:
 * - video_session: Source of truth for content (topic, script, facts, learning objectives)
 * - backend sessions table: Source of truth for media production (video generation, music, assets)
 * - Both tables share the same session ID (video_session.id = sessions.id)
 */
export const videoSessions = createVideoTable("session", {
  id: text("id").primaryKey(),
  userId: text("user_id")
    .notNull()
    .references(() => users.id),
  status: varchar("status", { length: 50 }).notNull().default("created"),
  topic: varchar("topic", { length: 200 }),
  childAge: varchar("child_age", { length: 50 }),
  childInterest: varchar("child_interest", { length: 200 }),
  learningObjective: text("learning_objective"),
  extractedFacts: jsonb("extracted_facts"),
  confirmedFacts: jsonb("confirmed_facts"),
  generatedScript: jsonb("generated_script"),
  sourceMaterials: jsonb("source_materials"), // Stores extracted PDF text separately from conversation
  // Final video URL from backend (populated by webhook when video is complete)
  finalVideoUrl: text("final_video_url"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const videoAssets = createVideoTable("asset", {
  id: text("id").primaryKey(),
  sessionId: text("session_id")
    .notNull()
    .references(() => videoSessions.id),
  assetType: varchar("asset_type", { length: 50 }).notNull(),
  url: text("url"),
  metadata: jsonb("metadata"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const conversationMessages = createVideoTable("conversation_message", {
  id: text("id").primaryKey(),
  sessionId: text("session_id")
    .notNull()
    .references(() => videoSessions.id, { onDelete: "cascade" }),
  role: varchar("role", { length: 20 }).notNull(), // 'user' | 'assistant' | 'system'
  content: text("content").notNull(),
  parts: jsonb("parts"), // Store UIMessage parts structure
  metadata: jsonb("metadata"), // Store workflow context, structured outputs reference, etc.
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
