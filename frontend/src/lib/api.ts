import type { Session } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface UserInfo {
  id?: string;
  email?: string;
}

export class ApiClient {
  private baseUrl: string;
  private userInfo?: UserInfo;

  constructor() {
    this.baseUrl = API_URL;
  }

  /**
   * Set user information from NextAuth session.
   * This replaces the previous JWT token approach.
   */
  setUser(user: UserInfo) {
    this.userInfo = user;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    // Add user information from NextAuth session to headers
    if (this.userInfo?.email) {
      headers["X-User-Email"] = this.userInfo.email;
    }
    if (this.userInfo?.id) {
      headers["X-User-Id"] = this.userInfo.id;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = (await response.json().catch(() => ({}))) as {
        detail?: string;
      };
      throw new Error(error.detail ?? "API request failed");
    }

    return response.json() as Promise<T>;
  }

  // Sessions
  async createSession(userId = 1) {
    return this.request<{
      session_id: string;
      stage: string;
      created_at: string;
    }>("/api/sessions/create", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async getSession(sessionId: string) {
    return this.request<Session>(`/api/sessions/${sessionId}`);
  }

}

export const apiClient = new ApiClient();
