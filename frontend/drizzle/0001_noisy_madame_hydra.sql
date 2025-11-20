CREATE TABLE "webhook_log" (
	"id" text PRIMARY KEY NOT NULL,
	"event_type" varchar(100) NOT NULL,
	"session_id" text,
	"video_url" text,
	"status" varchar(50) DEFAULT 'received' NOT NULL,
	"payload" jsonb NOT NULL,
	"error_message" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);