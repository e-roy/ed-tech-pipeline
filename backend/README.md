# Gauntlet Pipeline Backend - Orchestrator

**Person A's Work - COMPLETED ✅**

This is the FastAPI backend orchestrator for the Gauntlet AI Video Generation Pipeline. This component was built in the first 4 hours of the 48-hour sprint and successfully unblocks the entire team.

## Status: HOUR 4 CHECKPOINT PASSED ✅

All critical path deliverables completed:
- ✅ Server starts: `uvicorn app.main:app --reload` works
- ✅ Database has all 5 tables (users, sessions, assets, generation_costs, websocket_connections)
- ✅ Login works: Returns JWT token for demo@example.com
- ✅ All generation endpoints return 200 OK
- ✅ WebSocket endpoint functional

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Test endpoints
curl http://localhost:8000/health
```

## Demo Credentials

- **Email:** demo@example.com
- **Password:** demo123

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (protected)

### Generation Workflow
1. `POST /api/generate-images` - Generate images (stub)
2. `POST /api/save-approved-images` - Save approved images
3. `POST /api/generate-clips` - Generate video clips (stub)
4. `POST /api/save-approved-clips` - Save approved clips
5. `POST /api/compose-final-video` - Compose final video (stub)

### Session Management
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/sessions/{session_id}/costs` - Get cost breakdown
- `GET /api/sessions/` - List all sessions (paginated)

### WebSocket
- `ws://localhost:8000/ws/{session_id}` - Real-time progress updates

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy setup
│   ├── models/
│   │   └── database.py      # Database models
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── generation.py    # Generation workflow endpoints
│   │   └── sessions.py      # Session management endpoints
│   └── services/
│       ├── orchestrator.py  # CRITICAL: Orchestrator with stub methods
│       └── websocket_manager.py  # WebSocket manager
├── alembic/                 # Database migrations
├── requirements.txt
└── .env                     # Environment variables
```

## Orchestrator Stub Methods

The orchestrator currently has **stub implementations** that return success immediately. This unblocks the team:

### For Person B (Prompt Parser Agent):
Replace `orchestrator.generate_images()` stub with actual Flux integration via Replicate.

Location: `app/services/orchestrator.py:31`

### For Person C (Video Generator & Composition Agents):
Replace these stubs:
- `orchestrator.generate_clips()` - Luma integration via Replicate
- `orchestrator.compose_final_video()` - FFmpeg composition

Locations: `app/services/orchestrator.py:76` and `app/services/orchestrator.py:126`

## Database Models

All tables created successfully:

1. **users** - User authentication
2. **sessions** - Video generation sessions
3. **assets** - Generated images and clips
4. **generation_costs** - Cost tracking
5. **websocket_connections** - Active WebSocket connections

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
DATABASE_URL=postgresql+psycopg://your_user@localhost:5432/gauntlet_pipeline
JWT_SECRET_KEY=your-secret-key
REPLICATE_API_KEY=your-replicate-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET_NAME=your-bucket
```

## Testing

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=demo123"
```

### Test Image Generation (with auth)
```bash
curl -X POST http://localhost:8000/api/generate-images \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A futuristic city","num_images":2}'
```

### Test WebSocket
```bash
# Using wscat (npm install -g wscat)
wscat -c ws://localhost:8000/ws/test-session
```

## Next Steps for Team Integration

### Person B (Agent Developer 1):
- Import `VideoGenerationOrchestrator` from `app.services.orchestrator`
- Replace the stub in `generate_images()` method
- Integrate Prompt Parser Agent

### Person C (Agent Developer 2):
- Import `VideoGenerationOrchestrator` from `app.services.orchestrator`
- Replace stubs in `generate_clips()` and `compose_final_video()`
- Integrate Video Generator and Composition Agents

### Person D (Frontend Lead):
- Backend is running on `http://localhost:8000`
- Use `/api/auth/login` to get JWT token
- All generation endpoints are ready to receive requests
- WebSocket at `ws://localhost:8000/ws/{session_id}` for progress updates

### Person E (DevOps):
- Docker-ready structure
- Database migrations via Alembic
- Ready for containerization

## Tech Stack

- **Framework:** FastAPI 0.109.0
- **Database:** PostgreSQL with SQLAlchemy 2.0.44
- **Migrations:** Alembic 1.17.2
- **Auth:** JWT tokens (simplified SHA256 for MVP)
- **WebSocket:** FastAPI WebSocket support
- **CORS:** Configured for `http://localhost:3000` (Next.js frontend)

## Notes

- **Authentication:** Using SHA256 for MVP (replace with bcrypt/argon2 in production)
- **Stub Methods:** All orchestrator methods return success immediately
- **Database:** PostgreSQL running locally on port 5432
- **WebSocket:** Real-time progress updates working
- **CORS:** Configured for Next.js frontend on localhost:3000

## Success! 🎉

**Person A's critical path work is complete.** The team is now unblocked and can proceed with agent integration and frontend development. All Hour 4 checkpoint criteria have been met.

---

Built for the Gauntlet Pipeline 48-hour sprint.
