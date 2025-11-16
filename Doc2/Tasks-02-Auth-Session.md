# Phase 02: Authentication & Session Management (Hours 2-4)

**Timeline:** Day 1, Hours 2-4
**Dependencies:** Phase 01 (Foundation & Setup)
**Completion:** 0% (0/18 tasks complete)

---

## Overview

Implement authentication with JWT tokens and session creation/management. Users will be able to log in with demo credentials and create video generation sessions.

---

## Tasks

### 1. Backend Authentication

#### 1.1 Create Authentication Utilities
- [ ] Create `backend/utils/auth.py`:
  ```python
  from datetime import datetime, timedelta
  from jose import JWTError, jwt
  from passlib.context import CryptContext
  import os

  SECRET_KEY = os.getenv("JWT_SECRET_KEY")
  ALGORITHM = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      return pwd_context.verify(plain_password, hashed_password)

  def create_access_token(data: dict) -> str:
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
      return encoded_jwt

  def decode_access_token(token: str) -> dict:
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          return payload
      except JWTError:
          return None
  ```

**Dependencies:** Phase 01 complete
**Testing:** Import and test: `from utils.auth import create_access_token, verify_password`

#### 1.2 Create Pydantic Models for Auth
- [ ] Create `backend/models/schemas.py`:
  ```python
  from pydantic import BaseModel, EmailStr

  class LoginRequest(BaseModel):
      email: EmailStr
      password: str

  class LoginResponse(BaseModel):
      access_token: str
      token_type: str
      user_id: int
      email: str
      name: str

  class SessionCreate(BaseModel):
      topic: str

  class SessionResponse(BaseModel):
      id: int
      user_id: int
      topic: str
      status: str
      created_at: str

      class Config:
          from_attributes = True
  ```

**Dependencies:** Task 1.1
**Testing:** Import: `from models.schemas import LoginRequest, LoginResponse`

#### 1.3 Create Login Endpoint
- [ ] Create `backend/routes/auth.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, User
  from models.schemas import LoginRequest, LoginResponse
  from utils.auth import verify_password, create_access_token

  router = APIRouter(prefix="/api/auth", tags=["authentication"])

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()

  @router.post("/login", response_model=LoginResponse)
  async def login(request: LoginRequest, db: DBSession = Depends(get_db)):
      user = db.query(User).filter(User.email == request.email).first()

      if not user or not verify_password(request.password, user.hashed_password):
          raise HTTPException(status_code=401, detail="Invalid credentials")

      access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

      return LoginResponse(
          access_token=access_token,
          token_type="bearer",
          user_id=user.id,
          email=user.email,
          name=user.name or ""
      )
  ```
- [ ] Register router in `backend/main.py`:
  ```python
  from routes.auth import router as auth_router
  app.include_router(auth_router)
  ```

**Dependencies:** Tasks 1.1, 1.2
**Testing:** POST to http://localhost:8000/api/auth/login with `{"email":"demo@example.com","password":"demo123"}`

#### 1.4 Test Login Endpoint
- [ ] Use curl or Postman:
  ```bash
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"demo@example.com","password":"demo123"}'
  ```
- [ ] Verify response contains `access_token`, `user_id`, `email`
- [ ] Copy token for next tests

**Dependencies:** Task 1.3
**Testing:** Should return 200 status with JWT token

---

### 2. Session Management Backend

#### 2.1 Create Session Endpoints
- [ ] Create `backend/routes/sessions.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends, Header
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session
  from models.schemas import SessionCreate, SessionResponse
  from utils.auth import decode_access_token
  from datetime import datetime

  router = APIRouter(prefix="/api/sessions", tags=["sessions"])

  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()

  def get_current_user_id(authorization: str = Header(None)):
      if not authorization or not authorization.startswith("Bearer "):
          raise HTTPException(status_code=401, detail="Missing or invalid token")

      token = authorization.replace("Bearer ", "")
      payload = decode_access_token(token)

      if not payload:
          raise HTTPException(status_code=401, detail="Invalid token")

      return int(payload.get("sub"))

  @router.post("/create", response_model=SessionResponse)
  async def create_session(
      request: SessionCreate,
      user_id: int = Depends(get_current_user_id),
      db: DBSession = Depends(get_db)
  ):
      new_session = Session(
          user_id=user_id,
          topic=request.topic,
          status="created"
      )
      db.add(new_session)
      db.commit()
      db.refresh(new_session)

      return SessionResponse(
          id=new_session.id,
          user_id=new_session.user_id,
          topic=new_session.topic,
          status=new_session.status,
          created_at=new_session.created_at.isoformat()
      )

  @router.get("/{session_id}", response_model=SessionResponse)
  async def get_session(
      session_id: int,
      user_id: int = Depends(get_current_user_id),
      db: DBSession = Depends(get_db)
  ):
      session = db.query(Session).filter(
          Session.id == session_id,
          Session.user_id == user_id
      ).first()

      if not session:
          raise HTTPException(status_code=404, detail="Session not found")

      return SessionResponse(
          id=session.id,
          user_id=session.user_id,
          topic=session.topic,
          status=session.status,
          created_at=session.created_at.isoformat()
      )
  ```
- [ ] Register router in `backend/main.py`:
  ```python
  from routes.sessions import router as sessions_router
  app.include_router(sessions_router)
  ```

**Dependencies:** Tasks 1.1, 1.2, 1.3
**Testing:** Import router successfully

#### 2.2 Test Create Session Endpoint
- [ ] Use curl with token from Task 1.4:
  ```bash
  curl -X POST http://localhost:8000/api/sessions/create \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN_HERE" \
    -d '{"topic":"Photosynthesis"}'
  ```
- [ ] Verify response contains `id`, `topic`, `status: "created"`
- [ ] Note session ID for next test

**Dependencies:** Tasks 1.4, 2.1
**Testing:** Should return 200 with session object

#### 2.3 Test Get Session Endpoint
- [ ] Use curl with token and session ID:
  ```bash
  curl http://localhost:8000/api/sessions/1 \
    -H "Authorization: Bearer YOUR_TOKEN_HERE"
  ```
- [ ] Verify same session data returned

**Dependencies:** Task 2.2
**Testing:** Should return 200 with session details

---

### 3. Frontend Login Page

#### 3.1 Create Login Page Component
- [ ] Create `frontend/app/(auth)/login/page.tsx`:
  ```typescript
  'use client';
  import { useState } from 'react';
  import { useRouter } from 'next/navigation';
  import apiClient from '@/lib/api';

  export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setError('');

      try {
        const response = await apiClient.post('/api/auth/login', { email, password });
        const { access_token, user_id, email: userEmail, name } = response.data;

        // Store token
        localStorage.setItem('auth_token', access_token);
        localStorage.setItem('user_id', user_id.toString());
        localStorage.setItem('user_email', userEmail);
        localStorage.setItem('user_name', name);

        // Redirect to dashboard
        router.push('/dashboard');
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Login failed');
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow">
          <h1 className="text-2xl font-bold mb-6">Login</h1>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border rounded px-3 py-2"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="mt-4 text-sm text-gray-600">
            <p>Demo credentials:</p>
            <p>Email: demo@example.com</p>
            <p>Password: demo123</p>
          </div>
        </div>
      </div>
    );
  }
  ```

**Dependencies:** Phase 01 Task 3.3
**Testing:** Visit http://localhost:3000/login

#### 3.2 Create Dashboard Placeholder
- [ ] Create `frontend/app/dashboard/page.tsx`:
  ```typescript
  'use client';
  import { useEffect, useState } from 'react';
  import { useRouter } from 'next/navigation';

  export default function DashboardPage() {
    const [user, setUser] = useState<any>(null);
    const router = useRouter();

    useEffect(() => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const userEmail = localStorage.getItem('user_email');
      const userName = localStorage.getItem('user_name');
      setUser({ email: userEmail, name: userName });
    }, [router]);

    if (!user) return <div>Loading...</div>;

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
        <p>Welcome, {user.name || user.email}!</p>
      </div>
    );
  }
  ```

**Dependencies:** Task 3.1
**Testing:** After login, should redirect to /dashboard

#### 3.3 Test Login Flow
- [ ] Visit http://localhost:3000/login
- [ ] Enter demo credentials (demo@example.com / demo123)
- [ ] Click "Login"
- [ ] Verify redirect to /dashboard
- [ ] Check localStorage for `auth_token`, `user_id`, `user_email`

**Dependencies:** Tasks 3.1, 3.2
**Testing:** Should see dashboard with welcome message

---

### 4. Session Creation Frontend

#### 4.1 Create Session Creation Component
- [ ] Create `frontend/components/CreateSessionForm.tsx`:
  ```typescript
  'use client';
  import { useState } from 'react';
  import apiClient from '@/lib/api';

  interface CreateSessionFormProps {
    onSessionCreated: (sessionId: number) => void;
  }

  export default function CreateSessionForm({ onSessionCreated }: CreateSessionFormProps) {
    const [topic, setTopic] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setError('');

      try {
        const response = await apiClient.post('/api/sessions/create', { topic });
        const sessionId = response.data.id;
        onSessionCreated(sessionId);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create session');
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Create New Video</h2>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              What topic do you want to create a video about?
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Photosynthesis, Solar System, Water Cycle"
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Session'}
          </button>
        </form>
      </div>
    );
  }
  ```

**Dependencies:** Phase 01 Task 3.3
**Testing:** Import component successfully

#### 4.2 Add Session Creation to Dashboard
- [ ] Update `frontend/app/dashboard/page.tsx`:
  ```typescript
  'use client';
  import { useEffect, useState } from 'react';
  import { useRouter } from 'next/navigation';
  import CreateSessionForm from '@/components/CreateSessionForm';

  export default function DashboardPage() {
    const [user, setUser] = useState<any>(null);
    const router = useRouter();

    useEffect(() => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const userEmail = localStorage.getItem('user_email');
      const userName = localStorage.getItem('user_name');
      setUser({ email: userEmail, name: userName });
    }, [router]);

    const handleSessionCreated = (sessionId: number) => {
      console.log('Session created:', sessionId);
      // TODO: Navigate to fact extraction (Phase 03)
      alert(`Session ${sessionId} created! Next: Fact extraction`);
    };

    if (!user) return <div>Loading...</div>;

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
        <p className="mb-6">Welcome, {user.name || user.email}!</p>

        <CreateSessionForm onSessionCreated={handleSessionCreated} />
      </div>
    );
  }
  ```

**Dependencies:** Task 4.1
**Testing:** Component renders on dashboard

#### 4.3 Test Session Creation Flow
- [ ] Log in to dashboard
- [ ] Enter topic: "Photosynthesis"
- [ ] Click "Create Session"
- [ ] Verify alert shows session ID
- [ ] Check browser network tab - should see POST to /api/sessions/create
- [ ] Verify database: `psql $DATABASE_URL -c "SELECT * FROM sessions;"`

**Dependencies:** Tasks 4.1, 4.2
**Testing:** Should see new session record in database

---

## Phase Checklist

**Before moving to Phase 03, verify:**

- [ ] Login endpoint returns valid JWT token
- [ ] Session creation endpoint works with auth token
- [ ] Frontend login page works
- [ ] Frontend redirects to dashboard after login
- [ ] Session creation form submits successfully
- [ ] Session record created in database
- [ ] Auth token stored in localStorage
- [ ] Protected routes check for token

---

## Completion Status

**Total Tasks:** 18
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- JWT token expires in 24 hours - adjust if needed
- Demo credentials are hardcoded for MVP
- In production, implement proper password reset flow
- Consider adding refresh tokens for better security
