import { type Session } from "next-auth";

/**
 * Logs user details to the console in development mode only.
 *
 * @param session - The NextAuth session object containing user information
 */
export function logUserDetails(session: Session | null): void {
  // Only log in development mode
  if (process.env.NODE_ENV !== "development") {
    return;
  }

  if (!session?.user) {
    console.groupCollapsed("🔐 User Session");
    console.log("No user logged in");
    console.groupEnd();
    return;
  }

  const { user } = session;

  console.groupCollapsed("🔐 User Session Details");
  console.log("ID:", user.id ?? "N/A");
  console.log("Email:", user.email ?? "N/A");
  console.log("Name:", user.name ?? "N/A");
  console.log("Username:", (user as { username?: string }).username ?? "N/A");
  console.log("Image:", user.image ?? "N/A");
  console.groupEnd();
}
