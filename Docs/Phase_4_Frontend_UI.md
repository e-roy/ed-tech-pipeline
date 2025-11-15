# Phase 4: Frontend & User Interface

## Document Purpose
This phase implements the complete Next.js 14 frontend with all user-facing screens, components, and real-time progress tracking.

**Estimated Time:** 8 hours (Hour 32-40 of 48-hour sprint)

---

## 1. Frontend Project Structure

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout
│   ├── page.tsx                   # Landing/Login page
│   ├── generate/
│   │   ├── images/page.tsx        # Image generation screen
│   │   ├── clips/page.tsx         # Clip generation screen
│   │   └── final/page.tsx         # Final composition screen
│   └── result/
│       └── [sessionId]/page.tsx   # Final output screen
├── components/
│   ├── auth/
│   │   └── LoginForm.tsx
│   ├── generation/
│   │   ├── PromptInput.tsx
│   │   ├── ImageGrid.tsx
│   │   ├── VideoGrid.tsx
│   │   ├── ProgressIndicator.tsx
│   │   └── MoodBoard.tsx
│   ├── composition/
│   │   ├── TextOverlayForm.tsx
│   │   ├── AudioSelector.tsx
│   │   └── FinalPreview.tsx
│   └── ui/
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       ├── checkbox.tsx
│       └── progress.tsx
├── lib/
│   ├── api.ts                     # API client
│   ├── websocket.ts               # WebSocket manager
│   └── types.ts                   # TypeScript interfaces
└── hooks/
    ├── useSession.ts              # Session management hook
    ├── useWebSocket.ts            # WebSocket hook
    └── useGeneration.ts           # Generation state hook
```

---

## 2. Core Types & Interfaces

### 2.1 TypeScript Types (lib/types.ts)

```typescript
// lib/types.ts

export enum SessionStage {
  CREATED = "created",
  IMAGE_GENERATION = "image_generation",
  IMAGE_SELECTION = "image_selection",
  CLIP_GENERATION = "clip_generation",
  CLIP_SELECTION = "clip_selection",
  FINAL_COMPOSITION = "final_composition",
  COMPLETE = "complete",
  FAILED = "failed",
}

export interface ImageAsset {
  id: string;
  url: string;
  view_type: string;
  seed: number;
  cost: number;
  created_at: string;
}

export interface VideoAsset {
  id: string;
  url: string;
  source_image_id: string;
  duration: number;
  resolution: string;
  fps: number;
  cost: number;
  created_at: string;
}

export interface FinalVideo {
  url: string;
  duration: number;
  resolution: string;
  fps: number;
  file_size_mb: number;
  format: string;
}

export interface Session {
  id: string;
  user_id: number;
  stage: SessionStage;
  product_prompt?: string;
  video_prompt?: string;
  consistency_seed?: number;
  generated_images: ImageAsset[];
  approved_images: string[];
  generated_clips: VideoAsset[];
  approved_clips: string[];
  final_video?: FinalVideo;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface ProgressUpdate {
  session_id: string;
  stage: string;
  progress: number;
  message: string;
  current_cost?: number;
  timestamp: string;
  data?: any;
  error?: string;
}

export interface TextOverlay {
  product_name: string;
  cta: string;
  font: string;
  color: string;
}

export interface AudioConfig {
  enabled: boolean;
  genre: string;
}
```

---

## 3. API Client & WebSocket

### 3.1 API Client (lib/api.ts)

```typescript
// lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "API request failed");
    }

    return response.json();
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
  async createSession(userId: number = 1) {
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
    numImages: number = 6,
    styleKeywords: string[] = []
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
    clipDuration: number = 3.0
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
    clipOrder: string[]
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
    introDuration: number = 1.0,
    outroDuration: number = 1.0
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
```

### 3.2 WebSocket Hook (hooks/useWebSocket.ts)

```typescript
// hooks/useWebSocket.ts
"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { ProgressUpdate } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useWebSocket(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ProgressUpdate | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    // Connect to WebSocket
    const ws = new WebSocket(`${WS_URL}/ws/${sessionId}`);

    ws.onopen = () => {
      console.log("✅ WebSocket connected");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: ProgressUpdate = JSON.parse(event.data);
        console.log("📥 WebSocket message:", data);
        setLastMessage(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("❌ WebSocket disconnected");
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(message);
    }
  }, [isConnected]);

  return { isConnected, lastMessage, sendMessage };
}
```

---

## 4. Key Components

### 4.1 Login Form (components/auth/LoginForm.tsx)

```typescript
// components/auth/LoginForm.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.login(email, password);
      apiClient.setToken(response.session_token);

      // Create new session
      const session = await apiClient.createSession(response.user_id);

      // Redirect to image generation
      router.push(`/generate/images?session=${session.session_id}`);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md p-8">
      <h1 className="text-3xl font-bold text-center mb-6">
        AI Ad Video Generator
      </h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Email</label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Password</label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && (
          <div className="text-red-500 text-sm">{error}</div>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Logging in..." : "Start Creating"}
        </Button>
      </form>

      <p className="text-sm text-gray-500 text-center mt-4">
        Demo credentials are pre-filled
      </p>
    </Card>
  );
}
```

### 4.2 Progress Indicator (components/generation/ProgressIndicator.tsx)

```typescript
// components/generation/ProgressIndicator.tsx
"use client";

import { ProgressUpdate } from "@/lib/types";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";

interface Props {
  update: ProgressUpdate | null;
  isConnected: boolean;
}

export function ProgressIndicator({ update, isConnected }: Props) {
  if (!update) return null;

  return (
    <Card className="fixed bottom-4 right-4 w-96 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-lg">
          {update.stage === "complete" ? "Complete!" : "Generating..."}
        </h3>
        <span className="text-sm text-gray-500">{update.progress}%</span>
      </div>

      <Progress value={update.progress} className="mb-3" />

      <p className="text-sm text-gray-700 mb-2">{update.message}</p>

      {update.current_cost && (
        <p className="text-xs text-gray-500">
          Cost so far: ${update.current_cost.toFixed(2)}
        </p>
      )}

      {update.error && (
        <div className="mt-2 text-sm text-red-600">
          Error: {update.error}
        </div>
      )}

      <div className="flex items-center mt-3">
        <div
          className={`w-2 h-2 rounded-full mr-2 ${
            isConnected ? "bg-green-500" : "bg-red-500"
          }`}
        />
        <span className="text-xs text-gray-500">
          {isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>
    </Card>
  );
}
```

### 4.3 Image Grid (components/generation/ImageGrid.tsx)

```typescript
// components/generation/ImageGrid.tsx
"use client";

import { useState } from "react";
import Image from "next/image";
import { ImageAsset } from "@/lib/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  images: ImageAsset[];
  onApprove: (imageIds: string[]) => void;
  minSelection?: number;
}

export function ImageGrid({ images, onApprove, minSelection = 2 }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (imageId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(imageId)) {
      newSelected.delete(imageId);
    } else {
      newSelected.add(imageId);
    }
    setSelected(newSelected);
  };

  const handleApprove = () => {
    onApprove(Array.from(selected));
  };

  const totalCost = images.reduce((sum, img) => sum + img.cost, 0);

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-6">
        {images.map((image) => (
          <Card
            key={image.id}
            className={`relative aspect-square cursor-pointer transition-all overflow-hidden ${
              selected.has(image.id)
                ? "ring-4 ring-blue-500"
                : "hover:ring-2 hover:ring-gray-300"
            }`}
            onClick={() => toggleSelect(image.id)}
          >
            <Image
              src={image.url}
              alt={`Product ${image.view_type}`}
              fill
              className="object-cover"
            />

            <div className="absolute top-2 right-2">
              <Checkbox checked={selected.has(image.id)} />
            </div>

            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              ${image.cost.toFixed(2)}
            </div>

            <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded capitalize">
              {image.view_type}
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selected.size} of {images.length}
          </p>
          <p className="text-xs text-gray-500">
            Total cost: ${totalCost.toFixed(2)}
          </p>
        </div>

        <Button
          onClick={handleApprove}
          disabled={selected.size < minSelection}
          size="lg"
        >
          Add to Mood Board ({selected.size})
        </Button>
      </div>
    </div>
  );
}
```

### 4.4 Video Grid (components/generation/VideoGrid.tsx)

```typescript
// components/generation/VideoGrid.tsx
"use client";

import { useState } from "react";
import { VideoAsset } from "@/lib/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Props {
  clips: VideoAsset[];
  onApprove: (clipIds: string[], order: string[]) => void;
  minSelection?: number;
}

export function VideoGrid({ clips, onApprove, minSelection = 2 }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSelect = (clipId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(clipId)) {
      newSelected.delete(clipId);
    } else {
      newSelected.add(clipId);
    }
    setSelected(newSelected);
  };

  const handleApprove = () => {
    const selectedIds = Array.from(selected);
    onApprove(selectedIds, selectedIds); // Order same as selection for now
  };

  const totalCost = clips.reduce((sum, clip) => sum + clip.cost, 0);
  const totalDuration = clips
    .filter((c) => selected.has(c.id))
    .reduce((sum, clip) => sum + clip.duration, 0);

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {clips.map((clip) => (
          <Card
            key={clip.id}
            className={`relative cursor-pointer transition-all overflow-hidden ${
              selected.has(clip.id)
                ? "ring-4 ring-blue-500"
                : "hover:ring-2 hover:ring-gray-300"
            }`}
            onClick={() => toggleSelect(clip.id)}
          >
            <video
              src={clip.url}
              controls
              className="w-full aspect-video"
              onClick={(e) => e.stopPropagation()}
            />

            <div className="absolute top-2 right-2">
              <Checkbox checked={selected.has(clip.id)} />
            </div>

            <div className="p-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">
                  Duration: {clip.duration.toFixed(1)}s
                </span>
                <span className="text-gray-600">Cost: ${clip.cost.toFixed(2)}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">
            Selected: {selected.size} of {clips.length}
          </p>
          <p className="text-xs text-gray-500">
            Total duration: {totalDuration.toFixed(1)}s | Cost: ${totalCost.toFixed(2)}
          </p>
        </div>

        <Button
          onClick={handleApprove}
          disabled={selected.size < minSelection}
          size="lg"
        >
          Continue to Final Composition
        </Button>
      </div>
    </div>
  );
}
```

---

## 5. Page Implementation

### 5.1 Image Generation Page (app/generate/images/page.tsx)

```typescript
// app/generate/images/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ImageGrid } from "@/components/generation/ImageGrid";
import { ProgressIndicator } from "@/components/generation/ProgressIndicator";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ImageAsset } from "@/lib/types";

export default function ImagesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");

  const [prompt, setPrompt] = useState("");
  const [numImages, setNumImages] = useState(6);
  const [images, setImages] = useState<ImageAsset[]>([]);
  const [generating, setGenerating] = useState(false);

  const { isConnected, lastMessage } = useWebSocket(sessionId);

  useEffect(() => {
    if (lastMessage && lastMessage.stage === "complete" && lastMessage.data?.images) {
      setImages(lastMessage.data.images);
      setGenerating(false);
    }
  }, [lastMessage]);

  const handleGenerate = async () => {
    if (!sessionId || !prompt) return;

    setGenerating(true);
    try {
      await apiClient.generateImages(sessionId, prompt, numImages);
    } catch (error) {
      console.error("Generation failed:", error);
      setGenerating(false);
    }
  };

  const handleApprove = async (imageIds: string[]) => {
    if (!sessionId) return;

    try {
      await apiClient.saveApprovedImages(sessionId, imageIds);
      router.push(`/generate/clips?session=${sessionId}`);
    } catch (error) {
      console.error("Save failed:", error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Step 1: Generate Product Images</h1>

      {images.length === 0 ? (
        <div className="max-w-2xl mx-auto">
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Describe your product
            </label>
            <Input
              placeholder="pink tennis shoes with white laces"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={200}
              disabled={generating}
            />
            <p className="text-xs text-gray-500 mt-1">
              {prompt.length}/200 characters
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Number of images: {numImages}
            </label>
            <input
              type="range"
              min="4"
              max="8"
              value={numImages}
              onChange={(e) => setNumImages(parseInt(e.target.value))}
              className="w-full"
              disabled={generating}
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={!prompt || generating}
            className="w-full"
            size="lg"
          >
            {generating ? "Generating..." : "Generate Images"}
          </Button>
        </div>
      ) : (
        <ImageGrid images={images} onApprove={handleApprove} />
      )}

      <ProgressIndicator update={lastMessage} isConnected={isConnected} />
    </div>
  );
}
```

### 5.2 Final Video Result Page (app/result/[sessionId]/page.tsx)

```typescript
// app/result/[sessionId]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "@/lib/api";
import { FinalVideo } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function ResultPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [video, setVideo] = useState<FinalVideo | null>(null);
  const [totalCost, setTotalCost] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const session = await apiClient.getSession(sessionId);
        setVideo(session.final_video || null);
        setTotalCost(session.total_cost);
      } catch (error) {
        console.error("Failed to load session:", error);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [sessionId]);

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  if (!video) {
    return <div className="container mx-auto px-4 py-8">Video not found</div>;
  }

  const handleDownload = () => {
    window.open(video.url, "_blank");
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">
        Your Video is Ready! 🎉
      </h1>

      <Card className="max-w-4xl mx-auto p-8">
        <video
          src={video.url}
          controls
          autoPlay
          loop
          className="w-full rounded-lg mb-6"
        />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-500">Duration</p>
            <p className="font-semibold">{video.duration.toFixed(1)}s</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Resolution</p>
            <p className="font-semibold">{video.resolution}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">File Size</p>
            <p className="font-semibold">{video.file_size_mb.toFixed(1)} MB</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Cost</p>
            <p className="font-semibold">${totalCost.toFixed(2)}</p>
          </div>
        </div>

        <div className="flex gap-4">
          <Button onClick={handleDownload} size="lg" className="flex-1">
            Download MP4
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="flex-1"
            onClick={() => (window.location.href = "/")}
          >
            Generate Another Video
          </Button>
        </div>
      </Card>
    </div>
  );
}
```

---

## 6. Deployment Checklist

- [ ] All frontend components implemented
- [ ] WebSocket connection working
- [ ] Image generation flow functional
- [ ] Clip generation flow functional
- [ ] Final composition flow functional
- [ ] Result page displays video
- [ ] Progress indicators working
- [ ] Responsive design verified
- [ ] Error handling implemented

---

## 7. Next Steps

**Phase 4 Complete! ✅**

You should now have:
- ✅ Complete Next.js 14 frontend
- ✅ All user-facing screens
- ✅ Real-time WebSocket progress tracking
- ✅ Image and video selection UIs
- ✅ Final video display and download

**Proceed to:** [Phase_5_Testing_Deployment.md](Phase_5_Testing_Deployment.md)

---

## Document Metadata

- **Phase:** 4 (Frontend & User Interface)
- **Dependencies:** Phase 3 (completed)
- **Next Phase:** Phase 5 (Testing, Deployment & Optimization)
- **Estimated Duration:** 8 hours
- **Last Updated:** November 14, 2025
