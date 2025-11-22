# Phase 01: Foundation & Setup (Hours 0-2)

**Timeline:** Day 1, Hours 0-2
**Dependencies:** Phase 00 (Pre-Sprint Template Prep)
**Completion:** 0% (0/24 tasks complete)

---

## Overview

Set up the complete project foundation including backend (FastAPI), frontend (Next.js 14), database (PostgreSQL), and verify end-to-end connectivity. This is the critical foundation for all subsequent phases.

---

## Tasks

### 1. Backend Setup (FastAPI)

#### 1.1 Create Project Structure
- [ ] Create `/backend` directory
- [ ] Create directory structure:
  ```
  backend/
  ├── main.py
  ├── requirements.txt
  ├── .env
  ├── agents/
  ├── models/
  ├── routes/
  └── utils/
  ```
- [ ] Initialize git repository (if not already done)

**Dependencies:** Phase 00 complete
**Testing:** Run `ls -R backend/` to verify structure

#### 1.2 Install Python Dependencies
- [ ] Create `requirements.txt`:
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  sqlalchemy==2.0.23
  psycopg2-binary==2.9.9
  pydantic==2.5.0
  python-jose[cryptography]==3.3.0
  python-multipart==0.0.6
  websockets==12.0
  python-dotenv==1.0.0
  ```
- [ ] Create Python virtual environment: `python3 -m venv venv`
- [ ] Activate venv: `source venv/bin/activate` (or Windows equivalent)
- [ ] Install: `pip install -r requirements.txt`

**Dependencies:** Task 1.1
**Testing:** Run `pip list` and verify all packages installed

#### 1.3 Create FastAPI Application
- [ ] Create `backend/main.py`:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  import os
  from dotenv import load_dotenv

  load_dotenv()

  app = FastAPI(title="Educational Video Generator API")

  # CORS
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  @app.get("/")
  async def root():
      return {"message": "Educational Video Generator API", "status": "running"}

  @app.get("/health")
  async def health():
      return {"status": "healthy"}
  ```

**Dependencies:** Task 1.2
**Testing:** Run `uvicorn main:app --reload` and visit http://localhost:8000

#### 1.4 Set Up Environment Variables
- [ ] Create `backend/.env`:
  ```
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  JWT_SECRET_KEY=your-secret-key-here-change-in-production
  LLAMA_API_KEY=your-together-ai-key
  DALLE_API_KEY=your-openai-key
  GEMINI_API_KEY=your-google-ai-key
  ELEVENLABS_API_KEY=your-elevenlabs-key
  STORAGE_BUCKET_URL=your-cloudflare-r2-url
  ```
- [ ] Add `.env` to `.gitignore`

**Dependencies:** Task 1.3
**Testing:** Load with `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DATABASE_URL'))"`

---

### 2. Database Setup (PostgreSQL)

#### 2.1 Create Railway PostgreSQL Database
- [ ] Log in to Railway.app
- [ ] Create new project
- [ ] Add PostgreSQL plugin
- [ ] Note connection credentials (host, port, user, password, database)
- [ ] Update `DATABASE_URL` in `.env`

**Dependencies:** Task 1.4
**Testing:** Connect via psql: `psql $DATABASE_URL`

#### 2.2 Create Database Models
- [ ] Create `backend/models/database.py`:
  ```python
  from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, JSON
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.orm import sessionmaker
  from datetime import datetime
  import os

  DATABASE_URL = os.getenv("DATABASE_URL")
  engine = create_engine(DATABASE_URL)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  Base = declarative_base()

  class Session(Base):
      __tablename__ = "sessions"
      id = Column(Integer, primary_key=True, index=True)
      user_id = Column(Integer, nullable=False)
      topic = Column(String(200))
      status = Column(String(50), default="created")
      created_at = Column(DateTime, default=datetime.utcnow)
      updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  class Asset(Base):
      __tablename__ = "assets"
      id = Column(Integer, primary_key=True, index=True)
      session_id = Column(Integer, nullable=False)
      asset_type = Column(String(50))  # script, visual, audio, video
      url = Column(Text)
      metadata = Column(JSON)
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

**Dependencies:** Tasks 1.2, 2.1
**Testing:** Import in Python: `from models.database import Base, Session, Asset`

#### 2.3 Create Additional Tables
- [ ] Add to `backend/models/database.py`:
  ```python
  class Template(Base):
      __tablename__ = "templates"
      id = Column(Integer, primary_key=True, index=True)
      template_id = Column(String(50), unique=True, nullable=False)
      name = Column(String(100), nullable=False)
      category = Column(String(50))
      psd_url = Column(Text, nullable=False)
      preview_url = Column(Text, nullable=False)
      editable_layers = Column(JSON)
      metadata = Column(JSON)
      created_at = Column(DateTime, default=datetime.utcnow)

  class GeminiValidation(Base):
      __tablename__ = "gemini_validations"
      id = Column(Integer, primary_key=True, index=True)
      asset_id = Column(Integer, nullable=False)
      frame_number = Column(Integer)
      scientific_accuracy = Column(Boolean)
      label_quality = Column(Boolean)
      age_appropriate = Column(Boolean)
      visual_clarity = Column(Boolean)
      all_criteria_pass = Column(Boolean)
      notes = Column(Text)
      created_at = Column(DateTime, default=datetime.utcnow)

  class User(Base):
      __tablename__ = "users"
      id = Column(Integer, primary_key=True, index=True)
      email = Column(String(100), unique=True, nullable=False)
      hashed_password = Column(String(200), nullable=False)
      name = Column(String(100))
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

**Dependencies:** Task 2.2
**Testing:** Import all models: `from models.database import User, Template, GeminiValidation`

#### 2.4 Run Database Migrations
- [ ] Create `backend/create_tables.py`:
  ```python
  from models.database import Base, engine

  def create_tables():
      Base.metadata.create_all(bind=engine)
      print("All tables created successfully!")

  if __name__ == "__main__":
      create_tables()
  ```
- [ ] Run: `python create_tables.py`
- [ ] Verify tables created: `psql $DATABASE_URL -c "\dt"`

**Dependencies:** Task 2.3
**Testing:** Should see tables: users, sessions, assets, templates, gemini_validations

#### 2.5 Insert Demo User
- [ ] Create `backend/seed_demo_user.py`:
  ```python
  from models.database import SessionLocal, User
  from passlib.context import CryptContext

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def seed_demo_user():
      db = SessionLocal()
      existing = db.query(User).filter(User.email == "demo@example.com").first()
      if existing:
          print("Demo user already exists")
          return

      demo_user = User(
          email="demo@example.com",
          hashed_password=pwd_context.hash("demo123"),
          name="Demo User"
      )
      db.add(demo_user)
      db.commit()
      print("Demo user created: demo@example.com / demo123")
      db.close()

  if __name__ == "__main__":
      seed_demo_user()
  ```
- [ ] Install passlib: `pip install passlib[bcrypt]`
- [ ] Run: `python seed_demo_user.py`

**Dependencies:** Task 2.4
**Testing:** Query: `psql $DATABASE_URL -c "SELECT email FROM users;"`

#### 2.6 Insert Template Metadata
- [ ] Verify Phase 00 templates are in database
- [ ] If not, create `backend/seed_templates.py` to insert 10 template records
- [ ] Verify: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM templates;"`
  - Should return 10

**Dependencies:** Phase 00, Task 2.4
**Testing:** Query all templates: `SELECT template_id, name FROM templates;`

---

### 3. Frontend Setup (Next.js 14)

#### 3.1 Create Next.js Project
- [ ] Run: `npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir`
- [ ] Navigate to frontend: `cd frontend`
- [ ] Install additional dependencies:
  ```bash
  npm install axios
  npm install zustand
  npm install @radix-ui/react-dialog @radix-ui/react-progress
  ```

**Dependencies:** None (parallel to backend setup)
**Testing:** Run `npm run dev` and visit http://localhost:3000

#### 3.2 Create Project Structure
- [ ] Create directories:
  ```
  frontend/
  ├── app/
  │   ├── (auth)/
  │   │   └── login/
  │   └── dashboard/
  ├── components/
  │   ├── ui/
  │   └── shared/
  ├── lib/
  │   ├── api.ts
  │   └── store.ts
  └── public/
  ```

**Dependencies:** Task 3.1
**Testing:** Run `tree -L 2 app/` to verify structure

#### 3.3 Set Up API Client Utility
- [ ] Create `frontend/lib/api.ts`:
  ```typescript
  import axios from 'axios';

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add auth token interceptor
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  export default apiClient;
  ```

**Dependencies:** Task 3.1
**Testing:** Import in any component: `import apiClient from '@/lib/api'`

#### 3.4 Create Environment Variables
- [ ] Create `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_WS_URL=ws://localhost:8000
  ```
- [ ] Add `.env.local` to `.gitignore`

**Dependencies:** Task 3.3
**Testing:** Access in component: `console.log(process.env.NEXT_PUBLIC_API_URL)`

---

### 4. End-to-End Connection Test

#### 4.1 Test Backend Health Endpoint
- [ ] Start backend: `cd backend && uvicorn main:app --reload`
- [ ] Open browser to http://localhost:8000
- [ ] Verify JSON response: `{"message": "Educational Video Generator API", "status": "running"}`
- [ ] Test /health: http://localhost:8000/health

**Dependencies:** Tasks 1.3, 1.4
**Testing:** `curl http://localhost:8000/health` should return `{"status":"healthy"}`

#### 4.2 Test Database Connection from Backend
- [ ] Create `backend/test_db.py`:
  ```python
  from models.database import SessionLocal, User

  def test_connection():
      db = SessionLocal()
      users = db.query(User).all()
      print(f"Database connection successful! Found {len(users)} user(s)")
      db.close()

  if __name__ == "__main__":
      test_connection()
  ```
- [ ] Run: `python test_db.py`
- [ ] Should print: "Database connection successful! Found 1 user(s)"

**Dependencies:** Tasks 2.4, 2.5
**Testing:** No errors should occur

#### 4.3 Test Frontend to Backend Connection
- [ ] Start backend: `uvicorn main:app --reload` (if not running)
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Create `frontend/app/page.tsx`:
  ```typescript
  'use client';
  import { useEffect, useState } from 'react';
  import apiClient from '@/lib/api';

  export default function Home() {
    const [status, setStatus] = useState('Checking...');

    useEffect(() => {
      apiClient.get('/health')
        .then(res => setStatus(res.data.status))
        .catch(err => setStatus('Error: ' + err.message));
    }, []);

    return (
      <main className="p-8">
        <h1 className="text-2xl font-bold">API Status: {status}</h1>
      </main>
    );
  }
  ```
- [ ] Visit http://localhost:3000
- [ ] Should display: "API Status: healthy"

**Dependencies:** Tasks 3.1, 3.3, 4.1
**Testing:** Check browser console for no CORS errors

#### 4.4 Test WebSocket Connection (Basic)
- [ ] Add WebSocket route to `backend/main.py`:
  ```python
  from fastapi import WebSocket

  @app.websocket("/ws")
  async def websocket_endpoint(websocket: WebSocket):
      await websocket.accept()
      await websocket.send_json({"message": "WebSocket connected"})
      await websocket.close()
  ```
- [ ] Create test script `frontend/lib/test-ws.ts`:
  ```typescript
  const ws = new WebSocket('ws://localhost:8000/ws');
  ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
  };
  ```
- [ ] Test in browser console

**Dependencies:** Tasks 1.3, 4.1
**Testing:** Console should log: "Received: {message: 'WebSocket connected'}"

---

## Phase Checklist

**Before moving to Phase 02, verify:**

- [ ] Backend FastAPI server running on port 8000
- [ ] Frontend Next.js server running on port 3000
- [ ] Database connection successful
- [ ] All 5 tables created (users, sessions, assets, templates, gemini_validations)
- [ ] Demo user exists in database
- [ ] 10 templates exist in database
- [ ] Frontend can call backend /health endpoint
- [ ] No CORS errors in browser console
- [ ] WebSocket connection test successful

---

## Completion Status

**Total Tasks:** 24
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- If Railway database connection fails, check firewall/network settings
- CORS errors are common - verify middleware is configured correctly
- Keep both backend and frontend running simultaneously for testing
- Use separate terminal windows for backend/frontend servers
