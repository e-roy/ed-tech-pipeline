import { handlers } from "@/server/auth";

// Ensure this route runs in Node.js runtime (not edge) for database access
export const runtime = "nodejs";

export const { GET, POST } = handlers;
