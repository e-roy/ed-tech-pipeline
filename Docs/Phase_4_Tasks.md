# Phase 4: Frontend & User Interface - Tasks

## Overview

This phase implements the complete Next.js 14 frontend with all user-facing screens, components, and real-time progress tracking.

**Estimated Time:** 8 hours
**Dependencies:** Phase 3 completed (backend ready)

---

## Task Checklist

### 1. Core Types & API Client (Hour 32-33)

**Estimated Time:** 1 hour | **Dependencies:** Phase 3 completed

- ✅ **1.1 TypeScript Type Definitions**

  - ✅ 1.1.1 Create `types/index.ts` file
  - ✅ 1.1.2 Define SessionStage enum with all states
  - ✅ 1.1.3 Define ImageAsset interface
  - ✅ 1.1.4 Add all required fields (id, url, view_type, seed, cost, created_at)
  - ✅ 1.1.5 Define VideoAsset interface
  - ✅ 1.1.6 Add all fields (id, url, source_image_id, duration, resolution, fps, cost)
  - ✅ 1.1.7 Define FinalVideo interface
  - ✅ 1.1.8 Define Session interface
  - ✅ 1.1.9 Define ProgressUpdate interface
  - ✅ 1.1.10 Define TextOverlay interface
  - ✅ 1.1.11 Define AudioConfig interface
  - ✅ 1.1.12 Export all types

- ✅ **1.2 API Client Implementation**
  - ✅ 1.2.1 Create `lib/api.ts` file
  - ✅ 1.2.2 Define API_URL from environment variable
  - ✅ 1.2.3 Create ApiClient class
  - ✅ 1.2.4 Add baseUrl and token properties
  - ✅ 1.2.5 Implement setToken() method
  - ✅ 1.2.6 Implement private request<T>() method
  - ✅ 1.2.7 Add headers with Content-Type
  - ✅ 1.2.8 Add Authorization header if token exists
  - ✅ 1.2.9 Make fetch request
  - ✅ 1.2.10 Handle errors and parse JSON
  - ✅ 1.2.11 Implement login() method
  - ✅ 1.2.12 Implement createSession() method
  - ✅ 1.2.13 Implement getSession() method
  - ✅ 1.2.14 Implement generateImages() method
  - ✅ 1.2.15 Implement saveApprovedImages() method
  - ✅ 1.2.16 Implement generateClips() method
  - ✅ 1.2.17 Implement saveApprovedClips() method
  - ✅ 1.2.18 Implement composeFinalVideo() method
  - ✅ 1.2.19 Create and export apiClient instance
  - [ ] 1.2.20 Test API client with mock calls

---

### 2. WebSocket Hook & Custom Hooks (Hour 33-34)

**Estimated Time:** 1 hour | **Dependencies:** Task 1 completed

- ✅ **2.1 WebSocket Hook**

  - ✅ 2.1.1 Create `hooks/useWebSocket.ts` file
  - ✅ 2.1.2 Add "use client" directive
  - ✅ 2.1.3 Import necessary React hooks
  - ✅ 2.1.4 Import ProgressUpdate type
  - ✅ 2.1.5 Define WS_URL from environment
  - ✅ 2.1.6 Create useWebSocket function
  - ✅ 2.1.7 Accept sessionId parameter (nullable)
  - ✅ 2.1.8 Add isConnected state
  - ✅ 2.1.9 Add lastMessage state (ProgressUpdate)
  - ✅ 2.1.10 Add wsRef for WebSocket instance
  - ✅ 2.1.11 Implement useEffect for connection
  - ✅ 2.1.12 Return early if no sessionId
  - ✅ 2.1.13 Create WebSocket connection
  - ✅ 2.1.14 Handle onopen event
  - ✅ 2.1.15 Set isConnected true
  - ✅ 2.1.16 Handle onmessage event
  - ✅ 2.1.17 Parse JSON message
  - ✅ 2.1.18 Update lastMessage state
  - ✅ 2.1.19 Handle onerror event
  - ✅ 2.1.20 Handle onclose event
  - ✅ 2.1.21 Clean up on unmount
  - ✅ 2.1.22 Add sessionId to dependency array
  - ✅ 2.1.23 Implement sendMessage callback
  - ✅ 2.1.24 Return isConnected, lastMessage, sendMessage

- ✅ **2.2 Session Management Hook**
  - ✅ 2.2.1 Create `hooks/useVideoSession.ts` (optional)
  - ✅ 2.2.2 Implement session state management
  - ✅ 2.2.3 Add methods for session operations

---

### 3. UI Components (Hour 34-35.5)

**Estimated Time:** 1.5 hours | **Dependencies:** Task 2 completed

- ✅ **3.1 Progress Indicator Component**

  - ✅ 3.1.1 Create `components/generation/ProgressIndicator.tsx`
  - ✅ 3.1.2 Add "use client" directive
  - ✅ 3.1.3 Import ProgressUpdate type
  - ✅ 3.1.4 Import UI components (Progress, Card)
  - ✅ 3.1.5 Define Props interface (update, isConnected)
  - ✅ 3.1.6 Create component function
  - ✅ 3.1.7 Return null if no update
  - ✅ 3.1.8 Render fixed position card
  - ✅ 3.1.9 Display progress percentage
  - ✅ 3.1.10 Render Progress bar
  - ✅ 3.1.11 Display progress message
  - ✅ 3.1.12 Show current cost if available
  - ✅ 3.1.13 Show error if present
  - ✅ 3.1.14 Display connection status indicator
  - ✅ 3.1.15 Style with Tailwind CSS
  - ✅ 3.1.16 Export component

- ✅ **3.2 Image Grid Component**

  - ✅ 3.2.1 Create `components/generation/ImageGrid.tsx`
  - ✅ 3.2.2 Add "use client" directive
  - ✅ 3.2.3 Import useState from React
  - ✅ 3.2.4 Import Next Image component
  - ✅ 3.2.5 Import ImageAsset type
  - ✅ 3.2.6 Import UI components (Checkbox, Button, Card)
  - ✅ 3.2.7 Define Props interface
  - ✅ 3.2.8 Create component with images and onApprove props
  - ✅ 3.2.9 Add selected state (Set<string>)
  - ✅ 3.2.10 Implement toggleSelect function
  - ✅ 3.2.11 Implement handleApprove function
  - ✅ 3.2.12 Calculate total cost
  - ✅ 3.2.13 Render grid with 2-3 columns
  - ✅ 3.2.14 Map over images array
  - ✅ 3.2.15 Render Card for each image
  - ✅ 3.2.16 Add click handler to toggle selection
  - ✅ 3.2.17 Apply ring styling for selected
  - ✅ 3.2.18 Render Image with Next.js Image component
  - ✅ 3.2.19 Add Checkbox overlay
  - ✅ 3.2.20 Show cost badge
  - ✅ 3.2.21 Show view_type badge
  - ✅ 3.2.22 Render footer with selection count
  - ✅ 3.2.23 Add "Add to Mood Board" button
  - ✅ 3.2.24 Disable button if < minSelection
  - ✅ 3.2.25 Export component

- ✅ **3.3 Video Grid Component**

  - ✅ 3.3.1 Create `components/generation/VideoGrid.tsx`
  - ✅ 3.3.2 Similar structure to ImageGrid
  - ✅ 3.3.3 Use HTML video element instead of Image
  - ✅ 3.3.4 Add controls to video
  - ✅ 3.3.5 Show duration and cost
  - ✅ 3.3.6 Implement selection logic
  - ✅ 3.3.7 Calculate total duration
  - ✅ 3.3.8 Export component

- ✅ **3.4 Login Form Component**
  - ✅ 3.4.1 Create `components/auth/LoginForm.tsx`
  - ✅ 3.4.2 Add "use client" directive
  - ✅ 3.4.3 Import useState, useRouter
  - ✅ 3.4.4 Import apiClient
  - ✅ 3.4.5 Import UI components
  - ✅ 3.4.6 Add email state (default: "demo@example.com")
  - ✅ 3.4.7 Add password state (default: "demo123")
  - ✅ 3.4.8 Add loading state
  - ✅ 3.4.9 Add error state
  - ✅ 3.4.10 Implement handleSubmit async function
  - ✅ 3.4.11 Prevent default form submission
  - ✅ 3.4.12 Set loading true
  - ✅ 3.4.13 Call apiClient.login()
  - ✅ 3.4.14 Set token in apiClient
  - ✅ 3.4.15 Create new session
  - ✅ 3.4.16 Redirect to /generate/images
  - ✅ 3.4.17 Handle errors
  - ✅ 3.4.18 Render Card with form
  - ✅ 3.4.19 Add email Input field
  - ✅ 3.4.20 Add password Input field
  - ✅ 3.4.21 Show error message if present
  - ✅ 3.4.22 Add submit Button
  - ✅ 3.4.23 Disable during loading
  - ✅ 3.4.24 Export component

---

### 4. Page Implementations (Hour 35.5-37.5)

**Estimated Time:** 2 hours | **Dependencies:** Task 3 completed

- [ ] **4.1 Landing/Login Page**

  - ✅ 4.1.1 Open or create `app/page.tsx`
  - ✅ 4.1.2 Create simple centered layout
  - ✅ 4.1.3 Add styling with Tailwind
  - ✅ 4.1.4 Test page loads correctly

- [ ] **4.2 Image Generation Page**

  - [ ] 4.2.1 Create `app/generate/images/page.tsx`
  - [ ] 4.2.2 Add "use client" directive
  - [ ] 4.2.3 Import useState, useEffect
  - [ ] 4.2.4 Import useSearchParams, useRouter
  - [ ] 4.2.5 Import apiClient
  - [ ] 4.2.6 Import useWebSocket hook
  - [ ] 4.2.7 Import ImageGrid, ProgressIndicator
  - [ ] 4.2.8 Import UI components
  - [ ] 4.2.9 Import ImageAsset type
  - [ ] 4.2.10 Get sessionId from search params
  - [ ] 4.2.11 Add prompt state
  - [ ] 4.2.12 Add numImages state (default 6)
  - [ ] 4.2.13 Add images state (ImageAsset[])
  - [ ] 4.2.14 Add generating state
  - [ ] 4.2.15 Call useWebSocket with sessionId
  - [ ] 4.2.16 Add useEffect to watch lastMessage
  - [ ] 4.2.17 Check if stage is "complete"
  - [ ] 4.2.18 Update images from message data
  - [ ] 4.2.19 Set generating false
  - [ ] 4.2.20 Implement handleGenerate async function
  - [ ] 4.2.21 Validate sessionId and prompt
  - [ ] 4.2.22 Set generating true
  - [ ] 4.2.23 Call apiClient.generateImages()
  - [ ] 4.2.24 Handle errors
  - [ ] 4.2.25 Implement handleApprove async function
  - [ ] 4.2.26 Call apiClient.saveApprovedImages()
  - [ ] 4.2.27 Redirect to /generate/clips
  - [ ] 4.2.28 Render page header
  - [ ] 4.2.29 Show prompt input if no images
  - [ ] 4.2.30 Add textarea for prompt
  - [ ] 4.2.31 Add character counter
  - [ ] 4.2.32 Add slider for numImages
  - [ ] 4.2.33 Add Generate button
  - [ ] 4.2.34 Show ImageGrid if images exist
  - [ ] 4.2.35 Render ProgressIndicator
  - [ ] 4.2.36 Export page

- [ ] **4.3 Clip Generation Page**

  - [ ] 4.3.1 Create `app/generate/clips/page.tsx`
  - [ ] 4.3.2 Similar structure to images page
  - [ ] 4.3.3 Add video prompt input
  - [ ] 4.3.4 Add clip duration selector
  - [ ] 4.3.5 Use VideoGrid component
  - [ ] 4.3.6 Handle clip generation
  - [ ] 4.3.7 Redirect to /generate/final on approve
  - [ ] 4.3.8 Export page

- [ ] **4.4 Final Composition Page**

  - [ ] 4.4.1 Create `app/generate/final/page.tsx`
  - [ ] 4.4.2 Add text overlay form
  - [ ] 4.4.3 Product name input
  - [ ] 4.4.4 CTA input
  - [ ] 4.4.5 Font selector (optional)
  - [ ] 4.4.6 Color picker (optional)
  - [ ] 4.4.7 Add audio toggle
  - [ ] 4.4.8 Add genre selector if audio enabled
  - [ ] 4.4.9 Implement handleCompose function
  - [ ] 4.4.10 Call apiClient.composeFinalVideo()
  - [ ] 4.4.11 Redirect to /result/[sessionId] on complete
  - [ ] 4.4.12 Export page

- [ ] **4.5 Result Page**
  - [ ] 4.5.1 Create `app/result/[sessionId]/page.tsx`
  - [ ] 4.5.2 Get sessionId from params
  - [ ] 4.5.3 Add video and totalCost states
  - [ ] 4.5.4 Add loading state
  - [ ] 4.5.5 Implement useEffect to load session
  - [ ] 4.5.6 Call apiClient.getSession()
  - [ ] 4.5.7 Extract final_video and total_cost
  - [ ] 4.5.8 Show loading state
  - [ ] 4.5.9 Show error if video not found
  - [ ] 4.5.10 Render page header with emoji
  - [ ] 4.5.11 Render video player with controls
  - [ ] 4.5.12 Set autoPlay and loop
  - [ ] 4.5.13 Show video metadata (duration, resolution, size, cost)
  - [ ] 4.5.14 Add Download button
  - [ ] 4.5.15 Add "Generate Another" button
  - [ ] 4.5.16 Export page

---

### 5. Layout & Styling (Hour 37.5-38.5)

**Estimated Time:** 1 hour | **Dependencies:** Task 4 completed

- [ ] **5.1 Root Layout**

  - ✅ 5.1.1 Update `app/layout.tsx`
  - ✅ 5.1.2 Add proper metadata
  - ✅ 5.1.3 Set title: "AI Ad Video Generator"
  - ✅ 5.1.4 Add description
  - ✅ 5.1.5 Configure fonts (optional)
  - ✅ 5.1.6 Apply global styles
  - [ ] 5.1.7 Test layout renders correctly

- ✅ **5.2 Tailwind Configuration**

  - ✅ 5.2.1 Review `tailwind.config.ts`
  - ✅ 5.2.2 Add custom colors if needed
  - ✅ 5.2.3 Configure content paths
  - ✅ 5.2.4 Add custom utilities if needed
  - ✅ 5.2.5 Test Tailwind classes work

- ✅ **5.3 Global Styles**

  - ✅ 5.3.1 Update `app/globals.css`
  - ✅ 5.3.2 Import Tailwind directives
  - ✅ 5.3.3 Add custom CSS if needed
  - [ ] 5.3.4 Configure scrollbar styling (optional)

- [ ] **5.4 Responsive Design**
  - [ ] 5.4.1 Test all pages on mobile viewport
  - [ ] 5.4.2 Adjust grid columns for mobile
  - [ ] 5.4.3 Test tablet viewport
  - [ ] 5.4.4 Ensure buttons are touch-friendly
  - [ ] 5.4.5 Test navigation on small screens

---

### 6. Integration & Testing (Hour 38.5-40)

**Estimated Time:** 1.5 hours | **Dependencies:** All above tasks completed

- [ ] **6.1 Environment Configuration**

  - [ ] 6.1.1 Verify `.env.local` has correct API_URL
  - [ ] 6.1.2 Verify WS_URL is correct
  - [ ] 6.1.3 Test environment variables load
  - [ ] 6.1.4 Check no hardcoded URLs in code

- [ ] **6.2 End-to-End Frontend Test**

  - [ ] 6.2.1 Start frontend: `bun run dev`
  - [ ] 6.2.2 Start backend server
  - [ ] 6.2.3 Open http://localhost:3000
  - [ ] 6.2.4 Test login flow
  - [ ] 6.2.5 Test session creation
  - [ ] 6.2.6 Test image generation UI
  - [ ] 6.2.7 Monitor WebSocket in browser DevTools
  - [ ] 6.2.8 Verify progress updates appear
  - [ ] 6.2.9 Test image selection
  - [ ] 6.2.10 Test navigation to clips page
  - [ ] 6.2.11 Test clip generation UI
  - [ ] 6.2.12 Test clip selection
  - [ ] 6.2.13 Test final composition UI
  - [ ] 6.2.14 Test result page
  - [ ] 6.2.15 Test video playback
  - [ ] 6.2.16 Test download button

- [ ] **6.3 Error Handling Test**

  - [ ] 6.3.1 Test with invalid credentials
  - [ ] 6.3.2 Test with network disconnection
  - [ ] 6.3.3 Test WebSocket reconnection
  - [ ] 6.3.4 Test API error responses
  - [ ] 6.3.5 Verify error messages are user-friendly

- [ ] **6.4 Performance Test**

  - [ ] 6.4.1 Check page load times
  - [ ] 6.4.2 Test with slow network (DevTools)
  - [ ] 6.4.3 Check bundle size: `bun run build`
  - [ ] 6.4.4 Verify images load efficiently
  - [ ] 6.4.5 Check for console errors
  - [ ] 6.4.6 Test memory usage
  - [ ] 6.4.7 Verify no memory leaks

- [ ] **6.5 Cross-Browser Testing**

  - [ ] 6.5.1 Test in Chrome
  - [ ] 6.5.2 Test in Firefox
  - [ ] 6.5.3 Test in Safari
  - [ ] 6.5.4 Test in Edge (if available)
  - [ ] 6.5.5 Fix any browser-specific issues

- [ ] **6.6 Code Quality**
  - [ ] 6.6.1 Run ESLint: `bun run lint`
  - [ ] 6.6.2 Fix linting issues
  - [ ] 6.6.3 Format code with Prettier (if configured)
  - [ ] 6.6.4 Review TypeScript errors
  - [ ] 6.6.5 Add missing type definitions
  - [ ] 6.6.6 Remove unused imports
  - [ ] 6.6.7 Remove console.logs (or use proper logging)
  - [ ] 6.6.8 Commit all changes
  - [ ] 6.6.9 Push to repository
  - [ ] 6.6.10 Tag: `git tag phase-4-complete`

---

## Phase 4 Completion Criteria

✅ All TypeScript types defined
✅ API client working for all endpoints
✅ WebSocket hook connecting and receiving updates
✅ All UI components implemented
✅ Login page functional
✅ Image generation page functional
✅ Clip generation page functional
✅ Final composition page functional
✅ Result page functional
✅ Progress indicators working
✅ Real-time updates displaying correctly
✅ Responsive design working on mobile
✅ Error handling implemented
✅ Cross-browser compatibility verified
✅ Code linted and formatted
✅ All changes committed

---

## Next Steps

**Proceed to:** [Phase_5_Tasks.md](Phase_5_Tasks.md)

---

## Notes

```
[Your notes]
```

---

**Last Updated:** November 14, 2025
