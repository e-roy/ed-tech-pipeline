# Phase 09: Final Output & Polish (Hours 42-46)

**Timeline:** Day 2, Hours 42-46
**Dependencies:** Phase 08 (Educational Compositor)
**Completion:** 0% (0/22 tasks complete)

---

## Overview

Implement final video output with upload to storage, video player page with download options, cost breakdown, composition log, and UI polish across all pages.

---

## Tasks

### 1. Final Video Output Backend (Hours 42-44)

#### 1.1 Set Up Cloud Storage for Videos
- [ ] Choose storage provider (Cloudflare R2, S3, or Firebase)
- [ ] Create bucket for videos: `educational-videos`
- [ ] Configure CORS for video playback
- [ ] Add storage credentials to `.env`:
  ```
  STORAGE_ACCESS_KEY=your-access-key
  STORAGE_SECRET_KEY=your-secret-key
  STORAGE_BUCKET=educational-videos
  STORAGE_ENDPOINT=https://...
  ```

**Dependencies:** Phase 08 complete
**Testing:** Upload test file to storage

#### 1.2 Create Video Upload Utility
- [ ] Install boto3 (for S3-compatible storage):
  ```bash
  pip install boto3
  ```
- [ ] Create `backend/utils/storage.py`:
  ```python
  import boto3
  import os
  from botocore.client import Config

  class StorageClient:
      def __init__(self):
          self.client = boto3.client(
              's3',
              endpoint_url=os.getenv('STORAGE_ENDPOINT'),
              aws_access_key_id=os.getenv('STORAGE_ACCESS_KEY'),
              aws_secret_access_key=os.getenv('STORAGE_SECRET_KEY'),
              config=Config(signature_version='s3v4')
          )
          self.bucket = os.getenv('STORAGE_BUCKET')

      def upload_video(self, file_path: str, object_name: str = None) -> str:
          """
          Upload video to storage
          Returns: Public URL
          """
          if not object_name:
              object_name = os.path.basename(file_path)

          try:
              self.client.upload_file(
                  file_path,
                  self.bucket,
                  object_name,
                  ExtraArgs={'ContentType': 'video/mp4', 'ACL': 'public-read'}
              )

              url = f"{os.getenv('STORAGE_ENDPOINT')}/{self.bucket}/{object_name}"
              return url

          except Exception as e:
              print(f"Upload error: {e}")
              return None

      def upload_file(self, file_path: str, object_name: str = None, content_type: str = None) -> str:
          """Generic file upload"""
          if not object_name:
              object_name = os.path.basename(file_path)

          extra_args = {'ACL': 'public-read'}
          if content_type:
              extra_args['ContentType'] = content_type

          try:
              self.client.upload_file(file_path, self.bucket, object_name, ExtraArgs=extra_args)
              url = f"{os.getenv('STORAGE_ENDPOINT')}/{self.bucket}/{object_name}"
              return url
          except Exception as e:
              print(f"Upload error: {e}")
              return None
  ```

**Dependencies:** Task 1.1
**Testing:** Upload sample video file

#### 1.3 Update Compositor to Upload Video
- [ ] Update `backend/agents/ed_compositor.py` to upload after composition:
  ```python
  from utils.storage import StorageClient

  async def compose_video(self, timeline: Dict, session_id: int) -> str:
      # ... existing composition code ...

      # After creating final_path
      storage = StorageClient()
      video_url = storage.upload_video(
          final_path,
          object_name=f"videos/session_{session_id}_final.mp4"
      )

      # Save video URL to database
      video_asset = Asset(
          session_id=session_id,
          asset_type="video",
          url=video_url,
          metadata={
              "local_path": final_path,
              "duration": timeline["total_duration"],
              "segments_count": len(timeline["segments"])
          }
      )
      self.db.add(video_asset)
      self.db.commit()

      return video_url  # Return URL instead of path
  ```

**Dependencies:** Tasks 1.2, Phase 08
**Testing:** Composition should upload video

#### 1.4 Create Composition Log Generator
- [ ] Add method to `EducationalCompositor`:
  ```python
  def generate_composition_log(self, healing_decisions: List[Dict], timeline: Dict) -> Dict:
      """Generate detailed composition log"""

      log = {
          "timestamp": datetime.utcnow().isoformat(),
          "total_duration": timeline["total_duration"],
          "segments_count": len(timeline["segments"]),
          "healing_actions": {
              "total": len(healing_decisions),
              "substitutions": sum(1 for d in healing_decisions if d['action'] == 'substitute'),
              "regenerations": sum(1 for d in healing_decisions if d['action'] == 'regenerate'),
              "text_slides": sum(1 for d in healing_decisions if d['action'] == 'text_slide')
          },
          "decisions": healing_decisions,
          "timeline": timeline["segments"]
      }

      return log
  ```

**Dependencies:** Phase 08
**Testing:** Generate log for completed composition

#### 1.5 Create Video Endpoint
- [ ] Create `backend/routes/video.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session, Asset
  from routes.sessions import get_current_user_id, get_db

  router = APIRouter(prefix="/api/video", tags=["video"])

  @router.get("/{session_id}")
  async def get_video(
      session_id: int,
      user_id: int = Depends(get_current_user_id),
      db: DBSession = Depends(get_db)
  ):
      # Verify session ownership
      session = db.query(Session).filter(
          Session.id == session_id,
          Session.user_id == user_id
      ).first()

      if not session:
          raise HTTPException(status_code=404, detail="Session not found")

      # Get video asset
      video_asset = db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "video"
      ).first()

      if not video_asset:
          raise HTTPException(status_code=404, detail="Video not ready")

      # Get all assets for cost calculation
      all_assets = db.query(Asset).filter(Asset.session_id == session_id).all()

      total_cost = 0.0
      cost_breakdown = {}

      for asset in all_assets:
          asset_cost = asset.metadata.get('cost', 0.0) if asset.metadata else 0.0
          total_cost += asset_cost

          if asset.asset_type not in cost_breakdown:
              cost_breakdown[asset.asset_type] = 0.0
          cost_breakdown[asset.asset_type] += asset_cost

      return {
          "video_url": video_asset.url,
          "duration": video_asset.metadata.get('duration', 0),
          "segments_count": video_asset.metadata.get('segments_count', 0),
          "total_cost": total_cost,
          "cost_breakdown": cost_breakdown,
          "created_at": video_asset.created_at.isoformat()
      }
  ```
- [ ] Register router in `backend/main.py`

**Dependencies:** Tasks 1.3, 1.4
**Testing:** GET /api/video/1

---

### 2. Final Video Page (Frontend)

#### 2.1 Create Final Video Page
- [ ] Create `frontend/app/session/[id]/video/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams } from 'next/navigation';
  import apiClient from '@/lib/api';

  interface VideoData {
    video_url: string;
    duration: number;
    segments_count: number;
    total_cost: number;
    cost_breakdown: Record<string, number>;
    created_at: string;
  }

  export default function VideoPage() {
    const params = useParams();
    const sessionId = parseInt(params.id as string);

    const [videoData, setVideoData] = useState<VideoData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
      fetchVideo();
    }, [sessionId]);

    const fetchVideo = async () => {
      try {
        const response = await apiClient.get(`/api/video/${sessionId}`);
        setVideoData(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load video');
      } finally {
        setLoading(false);
      }
    };

    const handleDownload = () => {
      if (videoData) {
        window.open(videoData.video_url, '_blank');
      }
    };

    if (loading) {
      return (
        <div className="min-h-screen bg-gray-50 p-8">
          <h1 className="text-3xl font-bold mb-6">Loading Video...</h1>
          <div className="animate-pulse bg-white p-6 rounded-lg shadow">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
            <div className="aspect-video bg-gray-200 rounded"></div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="min-h-screen bg-gray-50 p-8">
          <h1 className="text-3xl font-bold mb-6 text-red-600">Error</h1>
          <div className="bg-red-50 p-6 rounded-lg">
            <p>{error}</p>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">🎉 Your Video is Ready!</h1>

          {/* Video Player */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <video
              src={videoData?.video_url}
              controls
              className="w-full rounded"
              style={{ maxHeight: '600px' }}
            >
              Your browser does not support the video tag.
            </video>
          </div>

          {/* Video Info */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">Duration</div>
              <div className="text-2xl font-bold">{videoData?.duration}s</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">Segments</div>
              <div className="text-2xl font-bold">{videoData?.segments_count}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">Total Cost</div>
              <div className="text-2xl font-bold">${videoData?.total_cost.toFixed(2)}</div>
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="bg-white p-6 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold mb-4">Cost Breakdown</h2>
            <div className="space-y-2">
              {Object.entries(videoData?.cost_breakdown || {}).map(([type, cost]) => (
                <div key={type} className="flex justify-between items-center">
                  <span className="capitalize">{type.replace('_', ' ')}</span>
                  <span className="font-medium">${(cost as number).toFixed(2)}</span>
                </div>
              ))}
              <div className="border-t pt-2 flex justify-between items-center font-bold">
                <span>Total</span>
                <span>${videoData?.total_cost.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handleDownload}
              className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 text-lg font-medium"
            >
              Download Video
            </button>
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="bg-gray-200 text-gray-800 px-8 py-3 rounded-lg hover:bg-gray-300 text-lg font-medium"
            >
              Create Another Video
            </button>
          </div>
        </div>
      </div>
    );
  }
  ```

**Dependencies:** Task 1.5
**Testing:** Navigate to page after video completion

#### 2.2 Update Composition Page to Redirect
- [ ] Update `frontend/app/session/[id]/composition/page.tsx`:
  ```typescript
  useEffect(() => {
    const compositionComplete = messages.find(
      m => m.stage === 'composition' && m.status === 'complete'
    );

    if (compositionComplete) {
      // Redirect to video page
      router.push(`/session/${sessionId}/video`);
    }
  }, [messages, sessionId, router]);
  ```

**Dependencies:** Task 2.1
**Testing:** Should auto-redirect after composition

---

### 3. UI Polish (Hours 44-46)

#### 3.1 Add Loading States
- [ ] Review all pages and add proper loading states:
  - Login page: Disable button during submission
  - Topic input: Show spinner during PDF extraction
  - Script review: Show skeleton during generation
  - Visual generation: Show progress bar
  - All API calls: Show loading indicators

**Dependencies:** All previous phases
**Testing:** Test loading states on slow network

#### 3.2 Add Error Handling
- [ ] Add error boundaries to pages:
  ```typescript
  'use client';
  import { useEffect } from 'react';

  export default function Error({
    error,
    reset,
  }: {
    error: Error;
    reset: () => void;
  }) {
    useEffect(() => {
      console.error(error);
    }, [error]);

    return (
      <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong!</h2>
          <p className="text-gray-600 mb-6">{error.message}</p>
          <button
            onClick={reset}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }
  ```
- [ ] Add error.tsx to each route folder

**Dependencies:** All pages created
**Testing:** Trigger errors, verify error boundaries work

#### 3.3 Add Empty States
- [ ] Add empty state to dashboard when no sessions:
  ```typescript
  {sessions.length === 0 && (
    <div className="bg-white p-12 rounded-lg shadow text-center">
      <h3 className="text-xl font-semibold mb-2">No videos yet</h3>
      <p className="text-gray-600 mb-6">Create your first educational video</p>
      <button className="bg-blue-600 text-white px-6 py-2 rounded">
        Get Started
      </button>
    </div>
  )}
  ```

**Dependencies:** Dashboard page
**Testing:** View dashboard with no sessions

#### 3.4 Responsive Design Fixes
- [ ] Test all pages on mobile (375px width)
- [ ] Fix grid layouts to be responsive:
  ```typescript
  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
  ```
- [ ] Ensure video player is responsive
- [ ] Test on tablet (768px width)

**Dependencies:** All pages created
**Testing:** Test on various screen sizes

#### 3.5 Accessibility Improvements
- [ ] Add ARIA labels to interactive elements:
  ```typescript
  <button aria-label="Download video" onClick={handleDownload}>
    Download
  </button>
  ```
- [ ] Ensure keyboard navigation works
- [ ] Add focus states to all interactive elements
- [ ] Use semantic HTML (header, main, section)
- [ ] Add alt text to all images

**Dependencies:** All pages created
**Testing:** Test with screen reader, keyboard-only navigation

#### 3.6 Typography & Spacing Polish
- [ ] Standardize heading sizes across pages
- [ ] Ensure consistent spacing (mb-4, mb-6, mb-8)
- [ ] Use consistent color scheme
- [ ] Polish button styles (consistent padding, rounded corners)
- [ ] Add subtle animations to transitions:
  ```typescript
  className="transition-all duration-200 hover:scale-105"
  ```

**Dependencies:** All pages created
**Testing:** Visual review of all pages

---

## Phase Checklist

**Before moving to Phase 10, verify:**

- [ ] Cloud storage configured and working
- [ ] Video uploads to storage successfully
- [ ] Video endpoint returns video data
- [ ] Video player page displays video
- [ ] Cost breakdown shows correct amounts
- [ ] Download button works
- [ ] Composition log generated
- [ ] Loading states present on all pages
- [ ] Error handling works
- [ ] Empty states display correctly
- [ ] Responsive design tested
- [ ] Accessibility improvements implemented
- [ ] Typography and spacing consistent

---

## Completion Status

**Total Tasks:** 22
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Video files can be large (5-20MB for 60s video)
- Consider adding video compression step
- Add social sharing buttons in future iteration
- Consider adding video thumbnail generation
- Store composition logs for analytics
- Add user feedback collection
