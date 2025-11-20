import { text, timestamp, varchar, pgTableCreator } from "drizzle-orm/pg-core";

/**
 * Table creator for error report tables with error_report_ prefix.
 */
export const createErrorReportTable = pgTableCreator(
  (name) => `error_report_${name}`,
);

export const errorReports = createErrorReportTable("report", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  errorName: varchar("error_name", { length: 255 }).notNull(),
  errorMessage: text("error_message").notNull(),
  userId: varchar("user_id", { length: 255 }), // Optional - errors can occur before auth
  userAgent: text("user_agent"),
  url: text("url"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});
