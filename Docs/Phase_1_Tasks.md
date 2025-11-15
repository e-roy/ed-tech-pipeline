# Phase 1: Foundation & Infrastructure Setup - Tasks

## Overview
This phase establishes the foundational infrastructure including database setup, data models, API framework, authentication, and session management.

**Estimated Time:** 6 hours
**Dependencies:** Phase 0 completed

---

## Task Checklist

### 1. Project Initialization (Hour 0-2)
**Estimated Time:** 2 hours | **Dependencies:** Phase 0 completed

- [ ] **1.1 Backend Project Structure**
  - [ ] 1.1.1 Create `backend/` directory
  - [ ] 1.1.2 Create Python virtual environment: `python -m venv venv`
  - [ ] 1.1.3 Activate virtual environment: `source venv/bin/activate`
  - [ ] 1.1.4 Create `backend/requirements.txt` with all dependencies
  - [ ] 1.1.5 Install dependencies: `pip install -r requirements.txt`
  - [ ] 1.1.6 Create `backend/app/` directory structure
  - [ ] 1.1.7 Create `backend/app/__init__.py`
  - [ ] 1.1.8 Create `backend/app/main.py`
  - [ ] 1.1.9 Create `backend/app/config.py`
  - [ ] 1.1.10 Create `backend/app/database.py`
  - [ ] 1.1.11 Create `backend/app/models/` directory
  - [ ] 1.1.12 Create `backend/app/models/__init__.py`
  - [ ] 1.1.13 Create `backend/app/models/database.py`
  - [ ] 1.1.14 Create `backend/app/models/schemas.py`
  - [ ] 1.1.15 Create `backend/app/agents/` directory with `__init__.py`
  - [ ] 1.1.16 Create `backend/app/orchestrator/` directory with `__init__.py`
  - [ ] 1.1.17 Create `backend/app/routers/` directory with `__init__.py`
  - [ ] 1.1.18 Create `backend/app/services/` directory with `__init__.py`
  - [ ] 1.1.19 Create `backend/tests/` directory
  - [ ] 1.1.20 Create `backend/.env.example`
  - [ ] 1.1.21 Create `backend/.env` (copy from example)
  - [ ] 1.1.22 Create `backend/.gitignore` for Python

- [ ] **1.2 Frontend Project Structure**
  - [ ] 1.2.1 Create `frontend/` directory
  - [ ] 1.2.2 Initialize Next.js 14: `npx create-next-app@latest frontend`
  - [ ] 1.2.3 Choose TypeScript, Tailwind CSS, App Router during setup
  - [ ] 1.2.4 Install dependencies: `cd frontend && npm install`
  - [ ] 1.2.5 Install additional packages: `npm install axios zustand @tanstack/react-query`
  - [ ] 1.2.6 Create `frontend/lib/` directory
  - [ ] 1.2.7 Create `frontend/hooks/` directory
  - [ ] 1.2.8 Create `frontend/components/ui/` directory
  - [ ] 1.2.9 Create `frontend/components/auth/` directory
  - [ ] 1.2.10 Create `frontend/components/generation/` directory
  - [ ] 1.2.11 Create `frontend/components/composition/` directory
  - [ ] 1.2.12 Create `frontend/.env.local.example`
  - [ ] 1.2.13 Create `frontend/.env.local` (copy from example)
  - [ ] 1.2.14 Update `frontend/.gitignore` to exclude `.env.local`

- [ ] **1.3 Environment Configuration**
  - [ ] 1.3.1 Add Replicate API key to `backend/.env`
  - [ ] 1.3.2 Add PostgreSQL DATABASE_URL to `backend/.env`
  - [ ] 1.3.3 Add AWS credentials to `backend/.env`
  - [ ] 1.3.4 Add S3 bucket name to `backend/.env`
  - [ ] 1.3.5 Generate JWT secret key: `openssl rand -hex 32`
  - [ ] 1.3.6 Add JWT_SECRET_KEY to `backend/.env`
  - [ ] 1.3.7 Set FRONTEND_URL in `backend/.env`
  - [ ] 1.3.8 Set ENV=development in `backend/.env`
  - [ ] 1.3.9 Add NEXT_PUBLIC_API_URL to `frontend/.env.local`
  - [ ] 1.3.10 Add NEXT_PUBLIC_WS_URL to `frontend/.env.local`
  - [ ] 1.3.11 Verify all required environment variables are set
  - [ ] 1.3.12 Test loading environment variables in both projects

---

### 2. Database Setup & Models (Hour 2-4)
**Estimated Time:** 2 hours | **Dependencies:** Task 1 completed

- [ ] **2.1 PostgreSQL Database Setup**
  - [ ] 2.1.1 Start PostgreSQL service
  - [ ] 2.1.2 Create database: `createdb ai_ad_video_db`
  - [ ] 2.1.3 Test connection: `psql ai_ad_video_db`
  - [ ] 2.1.4 Create database user (if needed)
  - [ ] 2.1.5 Grant privileges to user
  - [ ] 2.1.6 Exit psql and verify DATABASE_URL format
  - [ ] 2.1.7 Test connection from Python using SQLAlchemy

- [ ] **2.2 SQLAlchemy Models Implementation**
  - [ ] 2.2.1 Copy SessionStage enum to `models/database.py`
  - [ ] 2.2.2 Copy AssetType enum to `models/database.py`
  - [ ] 2.2.3 Implement `Base = declarative_base()`
  - [ ] 2.2.4 Implement `Session` model with all fields
  - [ ] 2.2.5 Add Session model indexes (user_id, stage, created_at)
  - [ ] 2.2.6 Implement `Asset` model with all fields
  - [ ] 2.2.7 Add Asset model indexes (session_id, asset_type)
  - [ ] 2.2.8 Implement `GenerationCost` model with all fields
  - [ ] 2.2.9 Add GenerationCost indexes (session_id, agent_name)
  - [ ] 2.2.10 Implement `User` model with all fields
  - [ ] 2.2.11 Add User model indexes (email)
  - [ ] 2.2.12 Verify all model relationships
  - [ ] 2.2.13 Test models with a simple script

- [ ] **2.3 Pydantic Schemas Implementation**
  - [ ] 2.3.1 Copy enums to `models/schemas.py`
  - [ ] 2.3.2 Implement `AgentInput` base schema
  - [ ] 2.3.3 Implement `AgentOutput` base schema
  - [ ] 2.3.4 Implement `LoginRequest` schema
  - [ ] 2.3.5 Implement `CreateSessionRequest` schema
  - [ ] 2.3.6 Implement `GenerateImagesRequest` schema with validation
  - [ ] 2.3.7 Implement `SaveApprovedImagesRequest` schema
  - [ ] 2.3.8 Implement `GenerateClipsRequest` schema
  - [ ] 2.3.9 Implement `SaveApprovedClipsRequest` schema
  - [ ] 2.3.10 Implement `TextOverlay` schema
  - [ ] 2.3.11 Implement `AudioConfig` schema
  - [ ] 2.3.12 Implement `ComposeFinalVideoRequest` schema
  - [ ] 2.3.13 Implement `LoginResponse` schema
  - [ ] 2.3.14 Implement `ImageAsset` schema
  - [ ] 2.3.15 Implement `VideoAsset` schema
  - [ ] 2.3.16 Implement `FinalVideo` schema
  - [ ] 2.3.17 Implement `SessionResponse` schema
  - [ ] 2.3.18 Implement `ProgressUpdate` schema
  - [ ] 2.3.19 Test schema validation with sample data

- [ ] **2.4 Database Connection Setup**
  - [ ] 2.4.1 Implement sync engine in `database.py`
  - [ ] 2.4.2 Implement async engine in `database.py`
  - [ ] 2.4.3 Configure connection pooling (pool_size=20, max_overflow=40)
  - [ ] 2.4.4 Implement SessionLocal factory
  - [ ] 2.4.5 Implement AsyncSessionLocal factory
  - [ ] 2.4.6 Implement `get_db()` dependency for FastAPI
  - [ ] 2.4.7 Implement `init_db()` function
  - [ ] 2.4.8 Test database connection with async session
  - [ ] 2.4.9 Verify connection pooling works

- [ ] **2.5 Alembic Migration Setup**
  - [ ] 2.5.1 Initialize Alembic: `alembic init alembic`
  - [ ] 2.5.2 Update `alembic.ini` with database URL
  - [ ] 2.5.3 Update `alembic/env.py` to import Base and models
  - [ ] 2.5.4 Configure target_metadata in `env.py`
  - [ ] 2.5.5 Create initial migration: `alembic revision --autogenerate -m "Initial tables"`
  - [ ] 2.5.6 Review generated migration file
  - [ ] 2.5.7 Run migration: `alembic upgrade head`
  - [ ] 2.5.8 Verify tables created in database: `psql ai_ad_video_db -c "\dt"`
  - [ ] 2.5.9 Verify table schemas: `\d sessions`, `\d assets`, etc.

- [ ] **2.6 Seed Demo User**
  - [ ] 2.6.1 Install bcrypt if not already: `pip install passlib[bcrypt]`
  - [ ] 2.6.2 Generate password hash for "demo123"
  - [ ] 2.6.3 Create SQL insert for demo user
  - [ ] 2.6.4 Insert demo user into database
  - [ ] 2.6.5 Verify user exists: `SELECT * FROM users WHERE email='demo@example.com';`
  - [ ] 2.6.6 Test password verification with bcrypt

---

### 3. FastAPI Application Setup (Hour 4-5)
**Estimated Time:** 1 hour | **Dependencies:** Task 2 completed

- [ ] **3.1 Configuration Module**
  - [ ] 3.1.1 Implement `Settings` class in `config.py`
  - [ ] 3.1.2 Add all API key fields with proper types
  - [ ] 3.1.3 Add all database fields
  - [ ] 3.1.4 Add all storage (AWS S3) fields
  - [ ] 3.1.5 Add JWT configuration fields
  - [ ] 3.1.6 Add CORS and server configuration
  - [ ] 3.1.7 Implement `get_settings()` with LRU cache
  - [ ] 3.1.8 Create global `settings` instance
  - [ ] 3.1.9 Test settings load correctly from .env
  - [ ] 3.1.10 Verify all required settings are present

- [ ] **3.2 Main Application Setup**
  - [ ] 3.2.1 Import all necessary FastAPI components in `main.py`
  - [ ] 3.2.2 Create FastAPI app instance with title and description
  - [ ] 3.2.3 Configure CORS middleware with correct origins
  - [ ] 3.2.4 Set allow_credentials=True for CORS
  - [ ] 3.2.5 Set allow_methods=["*"] for CORS
  - [ ] 3.2.6 Set allow_headers=["*"] for CORS
  - [ ] 3.2.7 Create placeholder router files (auth, sessions, generation, websocket)
  - [ ] 3.2.8 Include all routers with correct prefixes and tags
  - [ ] 3.2.9 Implement startup event handler
  - [ ] 3.2.10 Call `init_db()` in startup for development
  - [ ] 3.2.11 Implement health check endpoint: `GET /health`
  - [ ] 3.2.12 Add `if __name__ == "__main__"` block with uvicorn.run()

- [ ] **3.3 Test Server Startup**
  - [ ] 3.3.1 Start server: `uvicorn app.main:app --reload`
  - [ ] 3.3.2 Verify server starts without errors
  - [ ] 3.3.3 Check startup logs for database initialization
  - [ ] 3.3.4 Visit http://localhost:8000/docs (Swagger UI)
  - [ ] 3.3.5 Verify health endpoint: `curl http://localhost:8000/health`
  - [ ] 3.3.6 Check response: `{"status":"healthy","version":"1.0.0"}`
  - [ ] 3.3.7 Verify CORS headers in response
  - [ ] 3.3.8 Stop server and verify graceful shutdown

---

### 4. Authentication & Session Management (Hour 5-6)
**Estimated Time:** 1 hour | **Dependencies:** Task 3 completed

- [ ] **4.1 Authentication Router Implementation**
  - [ ] 4.1.1 Create `routers/auth.py` file
  - [ ] 4.1.2 Import necessary dependencies (FastAPI, SQLAlchemy, JWT, bcrypt)
  - [ ] 4.1.3 Create APIRouter instance
  - [ ] 4.1.4 Initialize password context with bcrypt
  - [ ] 4.1.5 Implement `create_access_token()` function
  - [ ] 4.1.6 Set token expiration from settings
  - [ ] 4.1.7 Encode JWT with proper algorithm
  - [ ] 4.1.8 Implement `POST /login` endpoint
  - [ ] 4.1.9 Add database session dependency
  - [ ] 4.1.10 Query user by email
  - [ ] 4.1.11 Handle user not found (401 error)
  - [ ] 4.1.12 Verify password with bcrypt
  - [ ] 4.1.13 Handle invalid password (401 error)
  - [ ] 4.1.14 Create access token on success
  - [ ] 4.1.15 Return LoginResponse with token
  - [ ] 4.1.16 Add proper error handling and logging

- [ ] **4.2 Session Router Implementation**
  - [ ] 4.2.1 Create `routers/sessions.py` file
  - [ ] 4.2.2 Import dependencies (FastAPI, SQLAlchemy, UUID, datetime)
  - [ ] 4.2.3 Create APIRouter instance
  - [ ] 4.2.4 Implement `POST /create` endpoint
  - [ ] 4.2.5 Generate UUID for session_id
  - [ ] 4.2.6 Create new Session database object
  - [ ] 4.2.7 Set initial stage to CREATED
  - [ ] 4.2.8 Add session to database
  - [ ] 4.2.9 Commit transaction
  - [ ] 4.2.10 Return session_id and metadata
  - [ ] 4.2.11 Implement `GET /{session_id}` endpoint
  - [ ] 4.2.12 Query session by ID
  - [ ] 4.2.13 Handle session not found (404 error)
  - [ ] 4.2.14 Build SessionResponse object
  - [ ] 4.2.15 Return session data
  - [ ] 4.2.16 Add error handling for database errors

- [ ] **4.3 Test Authentication Flow**
  - [ ] 4.3.1 Start backend server
  - [ ] 4.3.2 Test login with correct credentials via curl or Postman
  - [ ] 4.3.3 Verify successful response with token
  - [ ] 4.3.4 Test login with wrong password
  - [ ] 4.3.5 Verify 401 error response
  - [ ] 4.3.6 Test login with non-existent email
  - [ ] 4.3.7 Verify 401 error response
  - [ ] 4.3.8 Decode JWT token to verify payload
  - [ ] 4.3.9 Verify token expiration is set correctly

- [ ] **4.4 Test Session Management**
  - [ ] 4.4.1 Test create session endpoint
  - [ ] 4.4.2 Verify session_id is returned
  - [ ] 4.4.3 Verify session stage is "created"
  - [ ] 4.4.4 Test get session endpoint with valid session_id
  - [ ] 4.4.5 Verify all session fields are returned
  - [ ] 4.4.6 Test get session with invalid session_id
  - [ ] 4.4.7 Verify 404 error response
  - [ ] 4.4.8 Check database to confirm session is stored
  - [ ] 4.4.9 Verify timestamps are set correctly

---

### 5. WebSocket Infrastructure (Hour 6)
**Estimated Time:** 1 hour | **Dependencies:** Task 4 completed

- [ ] **5.1 WebSocket Manager Service**
  - [ ] 5.1.1 Create `services/websocket_manager.py` file
  - [ ] 5.1.2 Import WebSocket, Dict, json, datetime
  - [ ] 5.1.3 Create `WebSocketManager` class
  - [ ] 5.1.4 Initialize active_connections dictionary
  - [ ] 5.1.5 Implement `connect()` async method
  - [ ] 5.1.6 Accept WebSocket connection
  - [ ] 5.1.7 Store connection in dictionary
  - [ ] 5.1.8 Add connection logging
  - [ ] 5.1.9 Implement `disconnect()` method
  - [ ] 5.1.10 Remove connection from dictionary
  - [ ] 5.1.11 Add disconnection logging
  - [ ] 5.1.12 Implement `send_progress()` async method
  - [ ] 5.1.13 Check if session_id exists in connections
  - [ ] 5.1.14 Add timestamp to data if not present
  - [ ] 5.1.15 Send JSON data via websocket
  - [ ] 5.1.16 Handle send errors and auto-disconnect
  - [ ] 5.1.17 Add progress send logging
  - [ ] 5.1.18 Implement `broadcast()` method (optional)
  - [ ] 5.1.19 Create global ws_manager instance
  - [ ] 5.1.20 Export ws_manager for use in other modules

- [ ] **5.2 WebSocket Router Implementation**
  - [ ] 5.2.1 Create `routers/websocket.py` file
  - [ ] 5.2.2 Import APIRouter, WebSocket, WebSocketDisconnect
  - [ ] 5.2.3 Import ws_manager from services
  - [ ] 5.2.4 Create APIRouter instance
  - [ ] 5.2.5 Implement WebSocket endpoint: `@router.websocket("/{session_id}")`
  - [ ] 5.2.6 Accept WebSocket connection via ws_manager
  - [ ] 5.2.7 Create infinite loop for keeping connection alive
  - [ ] 5.2.8 Receive text messages from client
  - [ ] 5.2.9 Handle ping/pong messages (optional)
  - [ ] 5.2.10 Handle WebSocketDisconnect exception
  - [ ] 5.2.11 Call ws_manager.disconnect() on close
  - [ ] 5.2.12 Add error handling for unexpected errors
  - [ ] 5.2.13 Add logging for connection lifecycle

- [ ] **5.3 Test WebSocket Connection**
  - [ ] 5.3.1 Install wscat: `npm install -g wscat`
  - [ ] 5.3.2 Start backend server
  - [ ] 5.3.3 Create test session to get session_id
  - [ ] 5.3.4 Connect to WebSocket: `wscat -c ws://localhost:8000/ws/{session_id}`
  - [ ] 5.3.5 Verify "Connected" message in server logs
  - [ ] 5.3.6 Send ping message from wscat
  - [ ] 5.3.7 Verify message received in server
  - [ ] 5.3.8 Test sending progress update from Python (manual test script)
  - [ ] 5.3.9 Verify progress update received in wscat
  - [ ] 5.3.10 Close wscat connection
  - [ ] 5.3.11 Verify "Disconnected" message in server logs
  - [ ] 5.3.12 Test multiple concurrent connections
  - [ ] 5.3.13 Verify each connection is tracked separately

---

### 6. Testing & Verification (Final Hour 6)
**Estimated Time:** 30 minutes | **Dependencies:** All above tasks completed

- [ ] **6.1 Write Basic Unit Tests**
  - [ ] 6.1.1 Create `tests/test_database.py`
  - [ ] 6.1.2 Write test for database connection
  - [ ] 6.1.3 Write test for user query
  - [ ] 6.1.4 Create `tests/test_auth.py`
  - [ ] 6.1.5 Write test for successful login
  - [ ] 6.1.6 Write test for failed login
  - [ ] 6.1.7 Run tests: `pytest tests/ -v`
  - [ ] 6.1.8 Verify all tests pass
  - [ ] 6.1.9 Fix any failing tests
  - [ ] 6.1.10 Add test for session creation

- [ ] **6.2 Integration Testing**
  - [ ] 6.2.1 Test complete login → create session flow
  - [ ] 6.2.2 Verify session is stored in database
  - [ ] 6.2.3 Test WebSocket connection with real session
  - [ ] 6.2.4 Test sending progress update to connected client
  - [ ] 6.2.5 Verify database queries are optimized
  - [ ] 6.2.6 Check for N+1 query issues
  - [ ] 6.2.7 Test error handling for invalid inputs

- [ ] **6.3 Code Quality & Documentation**
  - [ ] 6.3.1 Run Black formatter: `black .`
  - [ ] 6.3.2 Run Ruff linter: `ruff check .`
  - [ ] 6.3.3 Fix any linting issues
  - [ ] 6.3.4 Add docstrings to key functions
  - [ ] 6.3.5 Add type hints where missing
  - [ ] 6.3.6 Review code for security issues
  - [ ] 6.3.7 Commit all changes to Git
  - [ ] 6.3.8 Push to GitHub repository

---

## Phase 1 Completion Criteria

✅ Backend FastAPI application running on http://localhost:8000
✅ Frontend Next.js scaffold running on http://localhost:3000
✅ PostgreSQL database created with all tables
✅ Database migrations working (Alembic)
✅ Demo user seeded in database
✅ Login endpoint functional with JWT tokens
✅ Session creation endpoint functional
✅ Session retrieval endpoint functional
✅ WebSocket endpoint accepting connections
✅ WebSocket manager sending progress updates
✅ All unit tests passing
✅ Code formatted and linted
✅ All changes committed to Git

---

## Troubleshooting Common Issues

### Database Connection Issues
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL format: `postgresql://user:password@localhost:5432/dbname`
- Test connection: `psql $DATABASE_URL`

### Import Errors
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `echo $PYTHONPATH`

### WebSocket Connection Failures
- Verify server is running on correct port
- Check firewall settings
- Test with wscat before frontend integration

### Alembic Migration Errors
- Drop all tables and recreate: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
- Delete alembic/versions/* and regenerate
- Check alembic.ini database URL matches .env

---

## Next Steps

**Proceed to:** [Phase_2_Tasks.md](Phase_2_Tasks.md)

**What's Next:**
- Implement Prompt Parser Agent (Llama 3.1)
- Implement Batch Image Generator Agent (Flux-Pro)
- Build Video Generation Orchestrator
- Create image generation API endpoints
- Test end-to-end image generation flow

---

## Notes & Observations

**Track your progress, issues, and solutions:**

```
[Your notes here]
```

---

**Last Updated:** November 14, 2025
