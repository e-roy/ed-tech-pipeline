"use client";

import { useEffect } from "react";
import { apiClient } from "@/lib/api";

interface BackendTokenProviderProps {
  token: string | null;
  children: React.ReactNode;
}

/**
 * Initializes the API client with the backend JWT token.
 *
 * This component should wrap authenticated pages to ensure
 * the API client has the necessary token before making requests.
 */
export function BackendTokenProvider({ token, children }: BackendTokenProviderProps) {
  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
      console.log("[BackendTokenProvider] Backend token initialized");
    } else {
      console.warn("[BackendTokenProvider] No backend token available");
    }
  }, [token]);

  return <>{children}</>;
}
