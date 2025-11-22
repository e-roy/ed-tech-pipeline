# Phase 10: Testing & Deployment (Hours 46-48)

**Timeline:** Day 2, Hours 46-48
**Dependencies:** Phase 09 (Final Output & Polish)
**Completion:** 0% (0/26 tasks complete)

---

## Overview

Comprehensive end-to-end testing of all features, deployment to Railway (backend) and Vercel (frontend), production database setup, and final verification.

---

## Tasks

### 1. End-to-End Testing (Hour 46-47)

#### 1.1 Test Case 1: Happy Path (Full Flow)
- [ ] Clear database (create fresh test session)
- [ ] **Step 1:** Navigate to `/login`
- [ ] **Step 2:** Login with demo@example.com / demo123
- [ ] **Step 3:** Verify redirect to `/dashboard`
- [ ] **Step 4:** Click "Create New Video"
- [ ] **Step 5:** Enter topic: "Photosynthesis"
- [ ] **Step 6:** Upload sample PDF or paste text about photosynthesis
- [ ] **Step 7:** Verify facts extracted (at least 5 facts)
- [ ] **Step 8:** Edit one fact
- [ ] **Step 9:** Click "Continue to Script Generation"
- [ ] **Step 10:** Watch WebSocket messages
- [ ] **Step 11:** Verify script generated with 4 segments
- [ ] **Step 12:** Edit narration in one segment
- [ ] **Step 13:** Click "Approve Script"
- [ ] **Step 14:** Watch visual generation progress
- [ ] **Step 15:** Verify 8-12 visuals generated
- [ ] **Step 16:** Verify mix of templates and AI-generated
- [ ] **Step 17:** Check cost calculation
- [ ] **Step 18:** Review visuals, deselect one, re-select
- [ ] **Step 19:** Click final approval
- [ ] **Step 20:** Confirm in modal (check checkbox)
- [ ] **Step 21:** Select TTS audio option
- [ ] **Step 22:** Choose voice from dropdown
- [ ] **Step 23:** Click "Confirm & Start Composition"
- [ ] **Step 24:** Watch composition progress
- [ ] **Step 25:** Verify redirect to video page
- [ ] **Step 26:** Verify video plays
- [ ] **Step 27:** Check cost breakdown
- [ ] **Step 28:** Click "Download Video"
- [ ] **Step 29:** Verify video downloads

**Dependencies:** All phases complete
**Testing:** Record time for full flow (should be < 3 minutes excluding AI generation)

#### 1.2 Test Case 2: Self-Healing
- [ ] Manually inject a failing Gemini validation:
  ```sql
  UPDATE gemini_validations SET all_criteria_pass = false WHERE id = 1;
  ```
- [ ] Trigger composition
- [ ] Check logs for self-healing action
- [ ] Verify Ed Compositor detected mismatch
- [ ] Verify healing decision made (substitute/regenerate/text_slide)
- [ ] Verify healed visual used in final video
- [ ] Check composition log in database

**Dependencies:** Phase 08 complete
**Testing:** Self-healing should work automatically

#### 1.3 Test Case 3: Text Slide Fallback
- [ ] Disable DALL-E API (set invalid key)
- [ ] Generate visuals
- [ ] Verify text slides created as fallback
- [ ] Check that video still completes
- [ ] Verify text slides appear in final video
- [ ] Re-enable DALL-E API

**Dependencies:** Phase 08 Task 2.3
**Testing:** Text slides should be created

#### 1.4 Test Case 4: Different Audio Options
- [ ] **Test A:** Create video with TTS audio
  - Verify audio plays in final video
- [ ] **Test B:** Create video with "No Audio" option
  - Verify silent video created
- [ ] **Test C:** Create video with "Instrumental" option
  - Verify background music plays (if implemented)

**Dependencies:** Phase 07 complete
**Testing:** All audio options should work

#### 1.5 Test Case 5: Error Handling
- [ ] Test login with wrong password
  - Verify error message displays
- [ ] Test creating session without topic
  - Verify validation error
- [ ] Test PDF upload with non-PDF file
  - Verify error handling
- [ ] Test with network disconnected
  - Verify graceful error messages

**Dependencies:** All phases
**Testing:** Errors should be handled gracefully

#### 1.6 Test Case 6: Cost Tracking
- [ ] Create complete video
- [ ] Query database for all assets:
  ```sql
  SELECT asset_type, SUM((metadata->>'cost')::float) as total_cost
  FROM assets
  WHERE session_id = 1
  GROUP BY asset_type;
  ```
- [ ] Verify costs sum correctly
- [ ] Check against expected costs:
  - Script: ~$0.01
  - Visuals (templates): $0.00
  - Visuals (DALL-E): ~$0.16 (4 x $0.04)
  - Gemini validation: ~$0.01
  - Audio (TTS): ~$0.30
  - **Total Expected:** ~$4.28

**Dependencies:** All phases
**Testing:** Costs should match estimates

---

### 2. Backend Deployment (Hour 47-48)

#### 2.1 Prepare Backend for Deployment
- [ ] Create `backend/Procfile` for Railway:
  ```
  web: uvicorn main:app --host 0.0.0.0 --port $PORT
  ```
- [ ] Create `backend/runtime.txt`:
  ```
  python-3.11
  ```
- [ ] Update `requirements.txt` with all dependencies
- [ ] Freeze requirements:
  ```bash
  pip freeze > requirements.txt
  ```
- [ ] Create `.gitignore`:
  ```
  venv/
  __pycache__/
  *.pyc
  .env
  *.log
  /tmp/
  ```

**Dependencies:** All backend code complete
**Testing:** Verify requirements.txt has all packages

#### 2.2 Deploy Backend to Railway
- [ ] Log in to Railway.app
- [ ] Create new project: "Educational Video Generator Backend"
- [ ] Connect GitHub repository
- [ ] Select backend directory
- [ ] Add environment variables:
  ```
  DATABASE_URL=<provided by Railway PostgreSQL>
  JWT_SECRET_KEY=<generate secure key>
  LLAMA_API_KEY=<your key>
  DALLE_API_KEY=<your key>
  GEMINI_API_KEY=<your key>
  ELEVENLABS_API_KEY=<your key>
  STORAGE_ACCESS_KEY=<your key>
  STORAGE_SECRET_KEY=<your key>
  STORAGE_BUCKET=educational-videos
  STORAGE_ENDPOINT=<your storage endpoint>
  ```
- [ ] Deploy
- [ ] Wait for deployment to complete
- [ ] Note deployed URL (e.g., https://your-app.railway.app)

**Dependencies:** Task 2.1
**Testing:** Check Railway logs for successful startup

#### 2.3 Test Deployed Backend
- [ ] Test health endpoint:
  ```bash
  curl https://your-app.railway.app/health
  ```
- [ ] Test login endpoint:
  ```bash
  curl -X POST https://your-app.railway.app/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"demo@example.com","password":"demo123"}'
  ```
- [ ] Verify response contains JWT token

**Dependencies:** Task 2.2
**Testing:** API should be accessible

---

### 3. Database Migration (Production)

#### 3.1 Run Migrations on Production Database
- [ ] Connect to production database:
  ```bash
  psql $RAILWAY_DATABASE_URL
  ```
- [ ] Verify tables don't exist yet:
  ```sql
  \dt
  ```
- [ ] Run migration script remotely:
  ```bash
  DATABASE_URL=$RAILWAY_DATABASE_URL python backend/create_tables.py
  ```
- [ ] Verify tables created:
  ```sql
  \dt
  ```

**Dependencies:** Task 2.2
**Testing:** Should see 5 tables created

#### 3.2 Seed Production Database
- [ ] Insert demo user:
  ```bash
  DATABASE_URL=$RAILWAY_DATABASE_URL python backend/seed_demo_user.py
  ```
- [ ] Insert template metadata (from Phase 00):
  ```bash
  DATABASE_URL=$RAILWAY_DATABASE_URL python backend/seed_templates.py
  ```
- [ ] Verify:
  ```sql
  SELECT COUNT(*) FROM users;  -- Should be 1
  SELECT COUNT(*) FROM templates;  -- Should be 10
  ```

**Dependencies:** Task 3.1
**Testing:** Demo user and templates should exist

---

### 4. Frontend Deployment

#### 4.1 Prepare Frontend for Deployment
- [ ] Update `frontend/.env.local` → `.env.production`:
  ```
  NEXT_PUBLIC_API_URL=https://your-app.railway.app
  NEXT_PUBLIC_WS_URL=wss://your-app.railway.app
  ```
- [ ] Test build locally:
  ```bash
  cd frontend
  npm run build
  ```
- [ ] Verify build succeeds
- [ ] Test production build:
  ```bash
  npm run start
  ```

**Dependencies:** All frontend code complete
**Testing:** Production build should work locally

#### 4.2 Deploy Frontend to Vercel
- [ ] Log in to Vercel
- [ ] Import GitHub repository
- [ ] Configure project:
  - Framework: Next.js
  - Root Directory: frontend
  - Build Command: `npm run build`
  - Output Directory: `.next`
- [ ] Add environment variables:
  ```
  NEXT_PUBLIC_API_URL=https://your-app.railway.app
  NEXT_PUBLIC_WS_URL=wss://your-app.railway.app
  ```
- [ ] Deploy
- [ ] Note deployed URL (e.g., https://your-app.vercel.app)

**Dependencies:** Task 4.1
**Testing:** Check Vercel logs for successful deployment

#### 4.3 Update CORS in Backend
- [ ] Update `backend/main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "http://localhost:3000",
          "https://your-app.vercel.app"  # Add Vercel URL
      ],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- [ ] Redeploy backend to Railway

**Dependencies:** Task 4.2
**Testing:** Frontend should be able to call backend

---

### 5. Final Production Testing

#### 5.1 Test Deployed Application
- [ ] Visit deployed frontend URL
- [ ] Complete full video creation flow
- [ ] **Step 1:** Login
- [ ] **Step 2:** Create session
- [ ] **Step 3:** Extract facts
- [ ] **Step 4:** Generate script
- [ ] **Step 5:** Generate visuals
- [ ] **Step 6:** Review and approve
- [ ] **Step 7:** Select audio
- [ ] **Step 8:** Composition completes
- [ ] **Step 9:** Video plays
- [ ] **Step 10:** Download works

**Dependencies:** Tasks 2.2, 4.2, 4.3
**Testing:** Full flow should work in production

#### 5.2 Create Demo Video
- [ ] Create video on topic: "How Photosynthesis Works"
- [ ] Download final video
- [ ] Review video quality
- [ ] Share video URL for demo

**Dependencies:** Task 5.1
**Testing:** Demo video should be high quality

#### 5.3 Performance Testing
- [ ] Test page load times (should be < 2s)
- [ ] Test API response times:
  - Login: < 500ms
  - Script generation: < 15s
  - Visual generation: < 90s
  - Composition: < 120s
- [ ] Test WebSocket connection stability
- [ ] Test concurrent users (2-3 simultaneous sessions)

**Dependencies:** Task 5.1
**Testing:** Performance should be acceptable

#### 5.4 Mobile Testing
- [ ] Test on mobile device (iOS/Android)
- [ ] Verify responsive design
- [ ] Test all interactions work on touch
- [ ] Verify video playback on mobile
- [ ] Test download on mobile

**Dependencies:** Task 5.1
**Testing:** Should work on mobile devices

---

### 6. Final Checklist

#### 6.1 Feature Verification
- [ ] ✅ Login works
- [ ] ✅ Fact extraction (Next.js) works
- [ ] ✅ Script generation works
- [ ] ✅ Visual generation (templates + AI) works
- [ ] ✅ Gemini validation works (frame-by-frame)
- [ ] ✅ Audio generation works (TTS)
- [ ] ✅ Self-healing composition works
- [ ] ✅ Text slide fallback works
- [ ] ✅ Final video output works
- [ ] ✅ Download works
- [ ] ✅ Cost tracking works
- [ ] ✅ WebSocket progress works
- [ ] ✅ Deployed and accessible
- [ ] ✅ Demo video created

**Dependencies:** All phases
**Testing:** All features must work

#### 6.2 Documentation Check
- [ ] README.md has deployment instructions
- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Common issues documented
- [ ] Demo credentials provided

**Dependencies:** All phases
**Testing:** Documentation should be complete

---

## Phase Checklist

**Before declaring MVP complete, verify:**

- [ ] All 6 test cases pass
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Production database seeded
- [ ] Full flow works in production
- [ ] Demo video created and reviewed
- [ ] Performance acceptable
- [ ] Mobile testing complete
- [ ] All 14 features verified
- [ ] Documentation complete

---

## Completion Status

**Total Tasks:** 26
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## MVP COMPLETE ✅

Once all tasks are checked off, the Educational Video Generator MVP is complete and ready for use!

---

## Post-MVP Recommendations

### Immediate Improvements:
1. Add video thumbnail generation
2. Implement user registration (beyond demo account)
3. Add session history view
4. Implement video sharing links
5. Add more template categories

### Future Enhancements:
1. Multi-language support
2. Custom branding options
3. Batch video generation
4. Analytics dashboard
5. Teacher collaboration features
6. Student viewing analytics
7. Video editing capabilities
8. Export to multiple formats
9. Integration with LMS platforms
10. Mobile app

---

## Notes

- Expected total cost per video: $4-5
- Full flow completion time: ~5-7 minutes
- Backend response times should be monitored
- Consider implementing caching for common topics
- Monitor API usage to prevent cost overruns
- Set up error monitoring (Sentry)
- Configure backups for production database
- Set up CI/CD pipeline for future updates
