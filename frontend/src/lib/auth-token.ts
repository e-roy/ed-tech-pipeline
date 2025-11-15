/**
 * Backend token management utility.
 * 
 * Handles token exchange from NextAuth session to backend JWT token.
 * Caches tokens to avoid repeated exchanges.
 */

import { env } from "@/env";
import { auth } from "@/server/auth";

interface TokenCache {
  token: string;
  expiresAt: number;
}

// In-memory cache for backend tokens
// Key: user email, Value: cached token info
const tokenCache = new Map<string, TokenCache>();

/**
 * Get backend JWT token from NextAuth session.
 * 
 * This function:
 * 1. Gets the current NextAuth session (or uses provided session)
 * 2. Checks if we have a valid cached token
 * 3. If not, exchanges NextAuth session for backend JWT via /api/auth/exchange
 * 4. Caches the token for future use
 * 
 * @param session - Optional session object. If not provided, will fetch from auth()
 * @returns Backend JWT token or null if not authenticated
 */
export async function getBackendToken(
  session?: { user?: { email?: string | null } | null } | null
): Promise<string | null> {
  // Use provided session or fetch from auth()
  const currentSession = session ?? (await auth());
  
  if (!currentSession?.user?.email) {
    return null;
  }
  
  const email = currentSession.user.email;
  
  // Check cache first
  const cached = tokenCache.get(email);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.token;
  }
  
  // Exchange token
  try {
    const response = await fetch(`${env.NEXT_PUBLIC_API_URL}/api/auth/exchange`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });
    
    if (!response.ok) {
      console.error("Token exchange failed:", response.status, response.statusText);
      return null;
    }
    
    const data = (await response.json()) as { access_token: string; token_type: string };
    
    // Cache the token (expires in 30 minutes, refresh 5 minutes early)
    const expiresIn = 25 * 60 * 1000; // 25 minutes in milliseconds
    tokenCache.set(email, {
      token: data.access_token,
      expiresAt: Date.now() + expiresIn,
    });
    
    return data.access_token;
  } catch (error) {
    console.error("Error exchanging token:", error);
    return null;
  }
}

/**
 * Clear cached token for a user.
 * Useful when user logs out or token is invalidated.
 */
export function clearBackendToken(email?: string): void {
  if (email) {
    tokenCache.delete(email);
  } else {
    tokenCache.clear();
  }
}

