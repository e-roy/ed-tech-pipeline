CREATE TABLE "error_report_report" (
	"id" text PRIMARY KEY NOT NULL,
	"error_name" varchar(255) NOT NULL,
	"error_message" text NOT NULL,
	"user_id" varchar(255),
	"user_agent" text,
	"url" text,
	"created_at" timestamp DEFAULT now() NOT NULL
);
