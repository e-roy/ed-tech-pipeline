# Phase 04: Narrative Builder (Agent 2) (Hours 6-12)

**Timeline:** Day 1, Hours 6-12
**Dependencies:** Phase 03 (Fact Extraction)
**Completion:** 0% (0/26 tasks complete)

---

## Overview

Implement Agent 2 (Narrative Builder) which transforms extracted facts into a 4-part educational script using Llama 3.1 70B. This includes backend agent implementation, API endpoints, WebSocket progress, and frontend script review UI.

---

## Tasks

### 1. Agent 2 Backend Implementation (Hours 6-8)

#### 1.1 Install AI Dependencies
- [ ] Add to `backend/requirements.txt`:
  ```
  replicate==0.22.0
  together==0.2.7
  ```
- [ ] Install: `pip install replicate together`
- [ ] Add to `.env`:
  ```
  LLAMA_API_KEY=your-together-ai-or-replicate-key
  LLAMA_MODEL=meta-llama/Llama-3.1-70B-Instruct-Turbo
  ```

**Dependencies:** Phase 03 complete
**Testing:** Import replicate: `import replicate`

#### 1.2 Create Agent Base Classes
- [ ] Create `backend/agents/base.py`:
  ```python
  from pydantic import BaseModel
  from typing import Any, Dict

  class AgentInput(BaseModel):
      session_id: int
      data: Dict[str, Any]
      metadata: Dict[str, Any] = {}

  class AgentOutput(BaseModel):
      success: bool
      data: Dict[str, Any]
      cost: float  # USD
      duration: float  # seconds
      error: str | None = None
  ```

**Dependencies:** Task 1.1
**Testing:** Import: `from agents.base import AgentInput, AgentOutput`

#### 1.3 Create Narrative Builder Agent Class
- [ ] Create `backend/agents/narrative_builder.py`:
  ```python
  import json
  import time
  import os
  from together import Together
  from .base import AgentInput, AgentOutput

  class NarrativeBuilderAgent:
      def __init__(self):
          self.client = Together(api_key=os.getenv("LLAMA_API_KEY"))
          self.model = os.getenv("LLAMA_MODEL", "meta-llama/Llama-3.1-70B-Instruct-Turbo")

      async def process(self, input: AgentInput) -> AgentOutput:
          start_time = time.time()

          try:
              # Extract input data
              topic = input.data.get("topic", "")
              facts = input.data.get("facts", [])
              target_duration = input.data.get("target_duration", 60)

              # Build system prompt
              system_prompt = self._build_system_prompt(target_duration)

              # Build user prompt
              user_prompt = self._build_user_prompt(topic, facts, target_duration)

              # Call LLM
              response = self.client.chat.completions.create(
                  model=self.model,
                  messages=[
                      {"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}
                  ],
                  temperature=0.7,
                  max_tokens=2000
              )

              # Parse response
              content = response.choices[0].message.content
              script_data = json.loads(content)

              # Calculate cost (Together AI: ~$0.88 per 1M tokens)
              input_tokens = response.usage.prompt_tokens
              output_tokens = response.usage.completion_tokens
              cost = (input_tokens * 0.88 / 1_000_000) + (output_tokens * 0.88 / 1_000_000)

              duration = time.time() - start_time

              return AgentOutput(
                  success=True,
                  data={"script": script_data},
                  cost=cost,
                  duration=duration
              )

          except Exception as e:
              return AgentOutput(
                  success=False,
                  data={},
                  cost=0.0,
                  duration=time.time() - start_time,
                  error=str(e)
              )

      def _build_system_prompt(self, target_duration: int) -> str:
          return f"""You are an expert middle school science educator specializing in creating engaging, accurate educational video scripts.

  Your task:
  1. Create a 4-part educational script (Hook → Concept → Process → Conclusion)
  2. Each part has specific timing and purpose
  3. Use age-appropriate language for grades 6-7 (reading level ~6.5)
  4. Include all provided facts and key concepts
  5. Provide visual guidance for each segment
  6. Ensure scientific accuracy

  Structure:
  - Hook (0-10s): Engage with question or surprising fact
  - Concept Introduction (10-25s): Introduce key vocabulary and ideas
  - Process Explanation (25-45s): Explain how/why it works with details
  - Conclusion (45-60s): Real-world connection and summary

  Rules:
  - Total duration must be {target_duration} seconds
  - Use conversational, enthusiastic tone
  - Define technical terms when first introduced
  - Include concrete examples
  - End with memorable takeaway
  - Output ONLY valid JSON, no additional text

  Required JSON structure:
  {{
      "total_duration": {target_duration},
      "reading_level": "6.5",
      "key_terms_count": <number>,
      "segments": [
          {{
              "id": "seg_001",
              "type": "hook",
              "start_time": 0,
              "duration": 10,
              "narration": "<script text>",
              "visual_guidance": "<description of what should be shown>",
              "key_concepts": ["<concept1>", "<concept2>"],
              "educational_purpose": "<why this segment matters>"
          }},
          {{
              "id": "seg_002",
              "type": "concept_introduction",
              "start_time": 10,
              "duration": 15,
              "narration": "<script text>",
              "visual_guidance": "<description>",
              "key_concepts": [],
              "educational_purpose": "<purpose>"
          }},
          {{
              "id": "seg_003",
              "type": "process_explanation",
              "start_time": 25,
              "duration": 20,
              "narration": "<script text>",
              "visual_guidance": "<description>",
              "key_concepts": [],
              "educational_purpose": "<purpose>"
          }},
          {{
              "id": "seg_004",
              "type": "conclusion",
              "start_time": 45,
              "duration": 15,
              "narration": "<script text>",
              "visual_guidance": "<description>",
              "key_concepts": [],
              "educational_purpose": "<purpose>"
          }}
      ]
  }}"""

      def _build_user_prompt(self, topic: str, facts: list, target_duration: int) -> str:
          facts_str = "\n".join([f"- {fact['concept']}: {fact['details']}" for fact in facts])

          return f"""Topic: {topic}

  Key Facts to Include:
  {facts_str}

  Target Duration: {target_duration} seconds
  Grade Level: 6-7

  Generate an engaging, scientifically accurate educational script in JSON format."""
  ```

**Dependencies:** Task 1.2
**Testing:** Instantiate: `agent = NarrativeBuilderAgent()`

#### 1.4 Test Narrative Builder Agent
- [ ] Create `backend/test_narrative_agent.py`:
  ```python
  import asyncio
  from agents.narrative_builder import NarrativeBuilderAgent
  from agents.base import AgentInput

  async def test_agent():
      agent = NarrativeBuilderAgent()

      input_data = AgentInput(
          session_id=1,
          data={
              "topic": "Photosynthesis",
              "facts": [
                  {"concept": "photosynthesis", "details": "Process where plants make food from sunlight"},
                  {"concept": "chlorophyll", "details": "Green pigment that captures light"},
                  {"concept": "glucose", "details": "Sugar produced as plant food"}
              ],
              "target_duration": 60
          }
      )

      result = await agent.process(input_data)
      print(f"Success: {result.success}")
      print(f"Cost: ${result.cost:.4f}")
      print(f"Duration: {result.duration:.2f}s")
      if result.success:
          print(f"Script segments: {len(result.data['script']['segments'])}")
      else:
          print(f"Error: {result.error}")

  if __name__ == "__main__":
      asyncio.run(test_agent())
  ```
- [ ] Run: `python test_narrative_agent.py`
- [ ] Verify 4 segments returned

**Dependencies:** Task 1.3
**Testing:** Should return script with 4 segments, cost ~$0.01

---

### 2. Script Generation API (Hours 8-10)

#### 2.1 Create WebSocket Manager
- [ ] Create `backend/utils/websocket_manager.py`:
  ```python
  from fastapi import WebSocket
  from typing import Dict, List
  import json

  class WebSocketManager:
      def __init__(self):
          self.active_connections: Dict[int, List[WebSocket]] = {}

      async def connect(self, session_id: int, websocket: WebSocket):
          await websocket.accept()
          if session_id not in self.active_connections:
              self.active_connections[session_id] = []
          self.active_connections[session_id].append(websocket)

      def disconnect(self, session_id: int, websocket: WebSocket):
          if session_id in self.active_connections:
              self.active_connections[session_id].remove(websocket)

      async def send_progress(self, session_id: int, message: dict):
          if session_id in self.active_connections:
              for connection in self.active_connections[session_id]:
                  try:
                      await connection.send_json(message)
                  except:
                      pass

  ws_manager = WebSocketManager()
  ```

**Dependencies:** Phase 01
**Testing:** Import: `from utils.websocket_manager import ws_manager`

#### 2.2 Create Script Generation Endpoint
- [ ] Create `backend/routes/script.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session, Asset
  from models.schemas import SessionResponse
  from agents.narrative_builder import NarrativeBuilderAgent
  from agents.base import AgentInput
  from utils.websocket_manager import ws_manager
  from routes.sessions import get_current_user_id, get_db
  import json

  router = APIRouter(prefix="/api/script", tags=["script"])

  async def generate_script_task(session_id: int, facts: list):
      """Background task for script generation"""
      try:
          # Send progress: starting
          await ws_manager.send_progress(session_id, {
              "stage": "script_generation",
              "status": "in_progress",
              "message": "Generating educational script..."
          })

          # Create agent and process
          agent = NarrativeBuilderAgent()
          db = SessionLocal()

          session = db.query(Session).filter(Session.id == session_id).first()
          if not session:
              raise Exception("Session not found")

          input_data = AgentInput(
              session_id=session_id,
              data={
                  "topic": session.topic,
                  "facts": facts,
                  "target_duration": 60
              }
          )

          result = await agent.process(input_data)

          if not result.success:
              raise Exception(result.error)

          # Save script to database
          script_asset = Asset(
              session_id=session_id,
              asset_type="script",
              url="",
              metadata={
                  "script": result.data["script"],
                  "cost": result.cost,
                  "duration": result.duration
              }
          )
          db.add(script_asset)

          # Update session status
          session.status = "script_generated"
          db.commit()

          # Send progress: complete
          await ws_manager.send_progress(session_id, {
              "stage": "script_generation",
              "status": "complete",
              "message": "Script generated successfully!",
              "data": {
                  "script": result.data["script"],
                  "cost": result.cost
              }
          })

          db.close()

      except Exception as e:
          await ws_manager.send_progress(session_id, {
              "stage": "script_generation",
              "status": "error",
              "message": str(e)
          })

  @router.post("/generate/{session_id}")
  async def generate_script(
      session_id: int,
      facts: list,
      background_tasks: BackgroundTasks,
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

      # Start background task
      background_tasks.add_task(generate_script_task, session_id, facts)

      return {"message": "Script generation started", "session_id": session_id}
  ```
- [ ] Register router in `backend/main.py`:
  ```python
  from routes.script import router as script_router
  app.include_router(script_router)
  ```

**Dependencies:** Tasks 1.3, 2.1
**Testing:** Endpoint registered successfully

#### 2.3 Add WebSocket Endpoint
- [ ] Add to `backend/main.py`:
  ```python
  from fastapi import WebSocket, WebSocketDisconnect
  from utils.websocket_manager import ws_manager

  @app.websocket("/ws/{session_id}")
  async def websocket_endpoint(websocket: WebSocket, session_id: int):
      await ws_manager.connect(session_id, websocket)
      try:
          while True:
              # Keep connection alive
              data = await websocket.receive_text()
              # Echo back (for testing)
              await websocket.send_json({"type": "ping", "message": "connected"})
      except WebSocketDisconnect:
          ws_manager.disconnect(session_id, websocket)
  ```

**Dependencies:** Task 2.1
**Testing:** Test with WebSocket client

#### 2.4 Test Script Generation API
- [ ] Use curl to trigger script generation:
  ```bash
  curl -X POST http://localhost:8000/api/script/generate/1 \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '[{"concept":"photosynthesis","details":"Plants make food from sunlight"}]'
  ```
- [ ] Connect WebSocket and watch for progress messages
- [ ] Verify script is saved to database

**Dependencies:** Tasks 2.2, 2.3
**Testing:** Should return "Script generation started", WebSocket receives progress

---

### 3. Script Review Frontend (Hours 10-12)

#### 3.1 Create WebSocket Hook
- [ ] Create `frontend/lib/useWebSocket.ts`:
  ```typescript
  import { useEffect, useRef, useState } from 'react';

  export function useWebSocket(sessionId: number) {
    const [messages, setMessages] = useState<any[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
      ws.current = new WebSocket(`${wsUrl}/ws/${sessionId}`);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev, data]);
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
      };

      return () => {
        ws.current?.close();
      };
    }, [sessionId]);

    return { messages, isConnected };
  }
  ```

**Dependencies:** Phase 03 complete
**Testing:** Import in component

#### 3.2 Update Topic Input to Trigger Script Generation
- [ ] Update `frontend/app/session/[id]/topic-input/page.tsx`:
  ```typescript
  import apiClient from '@/lib/api';

  const handleContinue = async () => {
      try {
        // Trigger script generation
        await apiClient.post(`/api/script/generate/${sessionId}`, extractedFacts);

        // Navigate to script review
        router.push(`/session/${sessionId}/script-review`);
      } catch (error) {
        alert('Failed to start script generation');
      }
    };
  ```

**Dependencies:** Task 2.2
**Testing:** Click continue, verify API call

#### 3.3 Create Script Review Page
- [ ] Create `frontend/app/session/[id]/script-review/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams, useRouter } from 'next/navigation';
  import { useWebSocket } from '@/lib/useWebSocket';

  interface Segment {
    id: string;
    type: string;
    start_time: number;
    duration: number;
    narration: string;
    visual_guidance: string;
    key_concepts: string[];
    educational_purpose: string;
  }

  export default function ScriptReviewPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = parseInt(params.id as string);

    const { messages, isConnected } = useWebSocket(sessionId);
    const [script, setScript] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [editableSegments, setEditableSegments] = useState<Segment[]>([]);

    useEffect(() => {
      // Listen for script generation completion
      const scriptMessage = messages.find(m => m.stage === 'script_generation' && m.status === 'complete');
      if (scriptMessage) {
        setScript(scriptMessage.data.script);
        setEditableSegments(scriptMessage.data.script.segments);
        setLoading(false);
      }
    }, [messages]);

    const handleApprove = () => {
      // Store approved script
      localStorage.setItem(`script_${sessionId}`, JSON.stringify(editableSegments));
      // Navigate to visual generation
      router.push(`/session/${sessionId}/visual-generation`);
    };

    const handleRegenerateSegment = (index: number) => {
      alert('Regeneration feature coming in Phase 04.2');
    };

    if (loading) {
      return (
        <div className="min-h-screen bg-gray-50 p-8">
          <h1 className="text-3xl font-bold mb-6">Generating Script...</h1>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
              <span>AI is writing your educational script...</span>
            </div>
            <div className="mt-4 text-sm text-gray-600">
              {messages.filter(m => m.stage === 'script_generation').map((msg, i) => (
                <div key={i}>{msg.message}</div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Review Script</h1>
        <p className="text-gray-600 mb-6">Session ID: {sessionId}</p>

        <div className="space-y-4">
          {editableSegments.map((segment, index) => (
            <div key={segment.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded text-sm font-medium">
                    Segment {index + 1}: {segment.type}
                  </span>
                  <span className="ml-3 text-sm text-gray-600">
                    {segment.start_time}s - {segment.start_time + segment.duration}s
                  </span>
                </div>
                <button
                  onClick={() => handleRegenerateSegment(index)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  Regenerate
                </button>
              </div>

              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Narration:
                </label>
                <textarea
                  value={segment.narration}
                  onChange={(e) => {
                    const updated = [...editableSegments];
                    updated[index].narration = e.target.value;
                    setEditableSegments(updated);
                  }}
                  className="w-full border rounded px-3 py-2 min-h-[80px]"
                />
              </div>

              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Visual Guidance:
                </label>
                <textarea
                  value={segment.visual_guidance}
                  onChange={(e) => {
                    const updated = [...editableSegments];
                    updated[index].visual_guidance = e.target.value;
                    setEditableSegments(updated);
                  }}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
              </div>

              <div className="flex gap-4 text-sm">
                <div>
                  <span className="font-medium">Key Concepts:</span>{' '}
                  {segment.key_concepts.join(', ')}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 flex gap-4">
          <button
            onClick={handleApprove}
            className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 text-lg font-medium"
          >
            Approve Script & Generate Visuals →
          </button>
        </div>
      </div>
    );
  }
  ```

**Dependencies:** Tasks 3.1, 3.2
**Testing:** Navigate to page after script generation

#### 3.4 Test Script Review Flow
- [ ] Complete fact extraction
- [ ] Trigger script generation
- [ ] Watch WebSocket messages in console
- [ ] Verify script displays with 4 segments
- [ ] Edit a segment's narration
- [ ] Click "Approve Script"
- [ ] Verify script saved to localStorage
- [ ] Verify navigation to next page

**Dependencies:** Task 3.3
**Testing:** End-to-end flow should work

---

## Phase Checklist

**Before moving to Phase 05, verify:**

- [ ] Llama 3.1 API credentials configured
- [ ] Narrative Builder Agent generates 4-segment script
- [ ] Script saved to database as Asset
- [ ] WebSocket connection works
- [ ] WebSocket sends progress updates
- [ ] Frontend displays loading state
- [ ] Frontend receives and displays script
- [ ] Script segments are editable
- [ ] Approved script saved to localStorage
- [ ] Navigation to visual generation works

---

## Completion Status

**Total Tasks:** 26
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Together AI costs ~$0.88 per 1M tokens (Llama 3.1 70B)
- Expected cost per script: $0.01-0.02
- Script generation typically takes 3-5 seconds
- Consider adding retry logic if LLM fails
- Add validation to ensure script has exactly 4 segments
- Consider caching common scripts to reduce costs
