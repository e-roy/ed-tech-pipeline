import { auth } from "@/server/auth";
import { UserRole } from "@/types";

/**
 * Requires the user to be authenticated.
 * Throws an error if not authenticated.
 * @returns The authenticated session
 */
export async function requireAuth() {
  const session = await auth();
  if (!session?.user) {
    throw new Error("Unauthorized");
  }
  return session;
}

/**
 * Requires the user to be an admin.
 * Throws an error if not authenticated or not an admin.
 * @returns The authenticated admin session
 */
export async function requireAdmin() {
  const session = await requireAuth();
  if (session.user.role !== UserRole.ADMIN) {
    throw new Error("Forbidden: Admin access required");
  }
  return session;
}

/**
 * Checks if the current user has a specific role.
 * @param role - The role to check
 * @returns True if user has the role, false otherwise
 */
export async function hasRole(role: UserRole) {
  const session = await auth();
  return session?.user?.role === role;
}

/**
 * Checks if the current user is an admin.
 * @returns True if user is an admin, false otherwise
 */
export async function isAdmin() {
  return await hasRole(UserRole.ADMIN);
}

