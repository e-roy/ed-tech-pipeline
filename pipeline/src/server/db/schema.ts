/**
 * Main schema file that re-exports all table definitions.
 * Tables are organized by feature in their own schema files.
 */

// Re-export auth tables from auth schema
export {
  accounts,
  accountsRelations,
  sessions,
  sessionsRelations,
  users,
  usersRelations,
  verificationTokens,
} from "./auth/schema";
