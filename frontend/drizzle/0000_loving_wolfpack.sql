-- Only create the new video_* tables
-- auth_* tables already exist in the database

CREATE TABLE IF NOT EXISTS "video_asset" (
	"id" text PRIMARY KEY NOT NULL,
	"session_id" text NOT NULL,
	"asset_type" varchar(50) NOT NULL,
	"url" text,
	"metadata" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "video_session" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" text NOT NULL,
	"status" varchar(50) DEFAULT 'created' NOT NULL,
	"topic" varchar(200),
	"learning_objective" text,
	"confirmed_facts" jsonb,
	"generated_script" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
-- Foreign key constraints (auth_user already exists)
-- Use DO block to conditionally add constraints
DO $$ 
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint 
		WHERE conname = 'video_asset_session_id_video_session_id_fk'
	) THEN
		ALTER TABLE "video_asset" ADD CONSTRAINT "video_asset_session_id_video_session_id_fk" 
		FOREIGN KEY ("session_id") REFERENCES "public"."video_session"("id") 
		ON DELETE no action ON UPDATE no action;
	END IF;
END $$;
--> statement-breakpoint
DO $$ 
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint 
		WHERE conname = 'video_session_user_id_auth_user_id_fk'
	) THEN
		ALTER TABLE "video_session" ADD CONSTRAINT "video_session_user_id_auth_user_id_fk" 
		FOREIGN KEY ("user_id") REFERENCES "public"."auth_user"("id") 
		ON DELETE no action ON UPDATE no action;
	END IF;
END $$;
