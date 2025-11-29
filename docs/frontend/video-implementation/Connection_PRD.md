---
date: 2025-11-18T15:43:43-06:00
researcher: nani
branch: ClassCut
repository: Pipeline
topic: "Video Editing Page Implementation - Codebase Research"
tags: [research, codebase, frontend, backend, s3, video-display, routing, api]
status: complete
last_updated: 2025-11-18
last_updated_by: nani
---

# Research: Video Editing Page Implementation

**Date**: 2025-11-18 15:43:43 CST
**Researcher**: nani
**Git Commit**: not-a-git-repo
**Branch**: ClassCut
**Repository**: Pipeline

## Research Question

I need to implement a new page in the UI part of the project that will pull the completed generated video from the backend process and then display it in a new editing route. The frontend needs to request an API/editing call to the AWS S3 bucket to get the video and display it to the user.

## Summary

The codebase is a full-stack AI video generation platform using **Next.js 16** (frontend) with **FastAPI** (backend). The system already has established patterns for:

- Creating new dashboard pages using Next.js App Router
- Fetching data via tRPC (for S3 storage) and direct fetch calls (to FastAPI backend)
- Displaying videos using native HTML5 `<video>` elements with presigned S3 URLs
- Backend endpoints that return video URLs from S3

Key integration points for a new editing page exist in the routing structure, API patterns, S3 service, and video display components.

## Detailed Findings

### 1. Frontend Routing and Page Structure

**Location**: `/Users/nanis/dev/Gauntlet/PipelineTest/pipeline/frontend/src/app/`

#### App Router Structure

- Pages defined by file system structure: `app/{route}/page.tsx`
- Dashboard routes at `/src/app/dashboard/`
- Dynamic routes use `[param]` folder naming (e.g., `history/[id]/page.tsx`)

#### Layout Hierarchy

- **Root Layout** (`src/app/layout.tsx:19-29`): Wraps with `TRPCReactProvider`
- **Dashboard Layout** (`src/app/dashboard/layout.tsx:14-22`): Wraps with ThemeProvider, SidebarProvider
- **Dashboard Layout Client** (`src/app/dashboard/layout-client.tsx:15-21`): Conditionally renders double-panel layout for `/dashboard/create` and `/dashboard/history/*`

#### Standard Page Pattern

```tsx
export default function NewPage() {
  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Page Title</h1>
        <p className="text-muted-foreground text-sm">Description</p>
      </div>
      {/* Page content */}
    </div>
  );
}
```

#### Authentication Pattern (Server Components)

```tsx
const session = await auth();
const userEmail = session?.user?.email ?? null;

if (!userEmail) {
  return (/* unauthorized UI */);
}
```

**Relevant Files**:

- `src/app/dashboard/history/[id]/page.tsx:1-15` - Dynamic route pattern
- `src/app/dashboard/hardcode-create/page.tsx:6-15` - Auth check pattern
- `src/app/dashboard/layout-client.tsx:18-21` - Double panel condition

### 2. API Call Patterns

#### tRPC Setup

- **Client**: `src/trpc/react.tsx:25` - `export const api = createTRPCReact<AppRouter>()`
- **Server**: `src/trpc/server.ts:27-31` - Server-side caller for RSC
- **Routers**: `src/server/api/routers/` - storage.ts, script.ts

#### tRPC Query Pattern (Client Component)

```tsx
const { data, isLoading, refetch } = api.storage.listFiles.useQuery({
  folder: "output",
  limit: 1000,
  offset: 0,
});
```

**Example**: `src/components/content/ContentGallery.tsx:23-27`

#### Direct Fetch Pattern (to FastAPI)

```typescript
const response = await fetch(
  `${API_URL}/api/story-images/${sessionIdToFetch}`,
  {
    headers: {
      "X-User-Email": userEmail,
    },
  }
);
```

**Example**: `src/app/dashboard/hardcode-create/hardcode-create-form.tsx:84-95`

#### ApiClient Class

**Location**: `src/lib/api.ts:10-151`

- `createSession()`: POST `/api/sessions/create`
- `getSession()`: GET `/api/sessions/${sessionId}`
- `composeFinalVideo()`: POST `/api/compose-final-video`

### 3. S3 Integration

#### Frontend S3 Service

**Location**: `src/server/services/storage.ts`

**Key Functions**:

- `listUserFiles()` (lines 41-243): Lists S3 objects and generates presigned URLs
- `deleteUserFile()` (lines 248-275): Deletes files with ownership check
- `getPresignedUrl()` (lines 280-309): Generates presigned URL for specific file

**Presigned URL Generation** (lines 215-234):

```typescript
const presignedUrl = await getSignedUrl(
  client,
  new GetObjectCommand({
    Bucket: env.S3_BUCKET_NAME,
    Key: key,
  }),
  { expiresIn: 3600 } // 1 hour
);
```

#### tRPC Storage Router

**Location**: `src/server/api/routers/storage.ts`

**Endpoints**:

- `listFiles` (lines 22-54): List files with presigned URLs
- `deleteFile` (lines 59-82): Delete file
- `getPresignedUrl` (lines 87-117): Get presigned URL for specific file

#### Backend S3 Service

**Location**: `/pipeline/backend/app/services/storage.py`

**Key Functions**:

- `generate_presigned_url()` (lines 57-95): Creates presigned GET URLs
- `upload_local_file()` (lines 579-687): Uploads local files to S3
- `list_files_by_prefix()` (lines 788-837): Lists and generates presigned URLs

**S3 Key Structure**:

```
users/{user_id}/{session_id}/
  images/          # Generated images
  videos/          # Video clips
  audio/           # Narration audio
  final/           # Final composed videos
```

### 4. Video Handling and Display

#### Video Type Definitions

**Location**: `src/types/index.ts`

**VideoAsset** (lines 21-30):

```typescript
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
```

**FinalVideo** (lines 32-39):

```typescript
export interface FinalVideo {
  url: string;
  duration: number;
  resolution: string;
  fps: number;
  file_size_mb: number;
  format: string;
}
```

#### Video Display Pattern

**Location**: `src/app/dashboard/hardcode-create/hardcode-create-form.tsx:919-942`

```tsx
{
  finalVideoUrl && (
    <div className="space-y-2 border-t pt-3">
      <p className="text-foreground text-sm font-medium">Final Video</p>
      <div className="bg-muted/50 overflow-hidden rounded-lg border">
        <video
          controls
          className="h-auto w-full"
          src={finalVideoUrl}
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
      </div>
      <a
        href={finalVideoUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block text-xs text-blue-600 underline hover:text-blue-800"
      >
        Open video in new tab
      </a>
    </div>
  );
}
```

#### VideoGrid Component

**Location**: `src/components/generation/VideoGrid.tsx:51-56`

- Displays selectable video clips
- Uses native `<video>` with `controls`

#### ContentCard Component

**Location**: `src/components/content/ContentCard.tsx:47-53`

- Generic media card for images/videos/audio
- Detects content type via `contentType.startsWith("video/")`
- Uses `file.presigned_url` for src

#### WebSocket for Real-time Updates

**Location**: `src/hooks/useWebSocket.ts`

- Receives `ProgressUpdate` with `video_url` field
- Connection: `new WebSocket(`${WS_URL}/ws/${sessionId}`)`

### 5. Backend API Endpoints

#### Video-Related Endpoints

**Location**: `/pipeline/backend/app/routes/generation.py`

| Endpoint                               | Method | Line      | Returns                         |
| -------------------------------------- | ------ | --------- | ------------------------------- |
| `/compose-video`                       | POST   | 494-551   | `video_url`                     |
| `/compose-final-video`                 | POST   | 554-597   | `video_url`                     |
| `/compose-hardcode-video/{session_id}` | POST   | 1910-2174 | `video_url`                     |
| `/story-images/{session_id}`           | GET    | 1555-1708 | Presigned URLs for images/audio |

#### Session Endpoints

**Location**: `/pipeline/backend/app/routes/sessions.py`

| Endpoint        | Method | Line    | Returns                             |
| --------------- | ------ | ------- | ----------------------------------- |
| `/{session_id}` | GET    | 52-97   | `final_video_url`                   |
| `/`             | GET    | 148-193 | All sessions with `final_video_url` |

#### Storage Endpoints

**Location**: `/pipeline/backend/app/routes/storage.py`

| Endpoint                               | Method | Line    | Returns                                 |
| -------------------------------------- | ------ | ------- | --------------------------------------- |
| `/files`                               | GET    | 149-204 | Files with presigned URLs               |
| `/files/{file_key:path}/presigned-url` | GET    | 207-241 | Presigned URL for specific file         |
| `/directory`                           | GET    | 279-326 | Directory structure with presigned URLs |

#### Database Models

**Location**: `/pipeline/backend/app/models/database.py`

**Session Model** (lines 30-69):

- `final_video_url`: String(500) - stores completed video URL (line 55)

**Asset Model** (lines 72-94):

- `type`: String - 'image', 'clip', 'audio', 'final'
- `url`: String(500) - S3 URL or presigned URL

### 6. Existing Editing/History Pages

#### History Dynamic Route

**Location**: `src/app/dashboard/history/[id]/page.tsx:1-15`

- Minimal implementation currently
- Uses async params pattern: `const { id } = await params;`
- Renders `JobDetail` component

## Code References

### Frontend - Routing

- `src/app/dashboard/layout.tsx:14-22` - Dashboard layout with providers
- `src/app/dashboard/layout-client.tsx:15-21` - Conditional panel rendering
- `src/app/dashboard/history/[id]/page.tsx:1-15` - Dynamic route pattern

### Frontend - API Calls

- `src/trpc/react.tsx:25` - tRPC client creation
- `src/server/api/routers/storage.ts:22-54` - listFiles endpoint
- `src/server/api/routers/storage.ts:87-117` - getPresignedUrl endpoint
- `src/lib/api.ts:58-72` - Session API methods
- `src/components/content/ContentGallery.tsx:23-27` - tRPC query usage

### Frontend - S3 Integration

- `src/server/services/storage.ts:41-243` - listUserFiles with presigned URLs
- `src/server/services/storage.ts:280-309` - getPresignedUrl function
- `src/env.js:20-23` - AWS environment variables

### Frontend - Video Display

- `src/app/dashboard/hardcode-create/hardcode-create-form.tsx:919-942` - Final video display
- `src/components/generation/VideoGrid.tsx:51-56` - Video clip display
- `src/components/content/ContentCard.tsx:47-53` - Generic video card
- `src/types/index.ts:21-39` - VideoAsset and FinalVideo types

### Backend - API Endpoints

- `backend/app/routes/generation.py:554-597` - /compose-final-video endpoint
- `backend/app/routes/sessions.py:52-97` - Get session with final_video_url
- `backend/app/routes/storage.py:207-241` - Get presigned URL endpoint

### Backend - S3 Service

- `backend/app/services/storage.py:57-95` - generate_presigned_url
- `backend/app/services/storage.py:788-837` - list_files_by_prefix

### Backend - Database

- `backend/app/models/database.py:55` - Session.final_video_url field
- `backend/app/models/database.py:72-94` - Asset model

## Architecture Documentation

### Data Flow for Video Retrieval

1. **Frontend initiates request**: Component calls tRPC `api.storage.getPresignedUrl` or fetches from backend API
2. **Backend generates presigned URL**: `storage_service.generate_presigned_url()` creates time-limited S3 URL
3. **Frontend displays video**: Native `<video>` element with `src={presignedUrl}`

### Authentication Flow

- **tRPC routes**: Use `protectedProcedure` which checks `ctx.session?.user?.id`
- **FastAPI routes**: Use `X-User-Email` header with `get_current_user` dependency

### Panel Layout System

The dashboard uses conditional double-panel layout:

- Routes `/dashboard/create` and `/dashboard/history/*` get ChatPreview panel on left
- Other routes get single-panel layout
- Configured in `layout-client.tsx:18-21`

## Related Research

No existing research documents found in `thoughts/shared/research/`.

## Open Questions

None - all questions have been clarified.
