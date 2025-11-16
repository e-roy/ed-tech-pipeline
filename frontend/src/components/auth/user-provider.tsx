"use client";

import { useEffect } from "react";
import { apiClient } from "@/lib/api";

interface UserProviderProps {
  userId?: string;
  userEmail?: string | null;
  children: React.ReactNode;
}

/**
 * Provides user information to the API client.
 *
 * Sets user ID and email from NextAuth session on the API client,
 * which will be sent as headers in all backend requests.
 */
export function UserProvider({ userId, userEmail, children }: UserProviderProps) {
  useEffect(() => {
    if (userEmail) {
      apiClient.setUser({
        id: userId,
        email: userEmail,
      });
      console.log("[UserProvider] User info set on API client:", { userId, userEmail });
    } else {
      console.warn("[UserProvider] No user email available");
    }
  }, [userId, userEmail]);

  return <>{children}</>;
}
