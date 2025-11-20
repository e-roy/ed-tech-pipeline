import {
  pgTable,
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

export const videoSessions = createVideoTable("session", {
  id: text("id").primaryKey(),
  userId: text("user_id")
    .notNull()
    .references(() => users.id),
  status: varchar("status", { length: 50 }).notNull().default("created"),
  topic: varchar("topic", { length: 200 }),
  learningObjective: text("learning_objective"),
  extractedFacts: jsonb("extracted_facts"),
  confirmedFacts: jsonb("confirmed_facts"),
  generatedScript: jsonb("generated_script"),
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
