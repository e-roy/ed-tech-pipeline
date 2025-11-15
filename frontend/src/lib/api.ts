import type { Session, TextOverlay, AudioConfig } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiClient {
  private baseUrl: string;
  private token?: string;

  constructor() {
    this.baseUrl = API_URL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
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

  // Auth
  async login(email: string, password: string) {
    return this.request<{
      success: boolean;
      user_id: number;
      email: string;
      session_token: string;
    }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
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

  // Image Generation
  async generateImages(
    sessionId: string,
    productPrompt: string,
    numImages = 6,
    styleKeywords: string[] = [],
  ) {
    return this.request("/api/generate-images", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        product_prompt: productPrompt,
        num_images: numImages,
        style_keywords: styleKeywords,
      }),
    });
  }

  async saveApprovedImages(sessionId: string, imageIds: string[]) {
    return this.request("/api/save-approved-images", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        approved_image_ids: imageIds,
      }),
    });
  }

  // Video Generation
  async generateClips(
    sessionId: string,
    videoPrompt: string,
    clipDuration = 3.0,
  ) {
    return this.request("/api/generate-clips", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        video_prompt: videoPrompt,
        clip_duration: clipDuration,
      }),
    });
  }

  async saveApprovedClips(
    sessionId: string,
    clipIds: string[],
    clipOrder: string[],
  ) {
    return this.request("/api/save-approved-clips", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        approved_clip_ids: clipIds,
        clip_order: clipOrder,
      }),
    });
  }

  // Final Composition
  async composeFinalVideo(
    sessionId: string,
    textOverlay: TextOverlay,
    audio: AudioConfig,
    introDuration = 1.0,
    outroDuration = 1.0,
  ) {
    return this.request("/api/compose-final-video", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        text_overlay: textOverlay,
        audio,
        intro_duration: introDuration,
        outro_duration: outroDuration,
      }),
    });
  }
}

export const apiClient = new ApiClient();
