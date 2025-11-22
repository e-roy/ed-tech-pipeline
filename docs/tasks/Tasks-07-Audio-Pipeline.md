# Phase 07: Audio Pipeline (Agent 4) (Hours 24-30)

**Timeline:** Day 2, Hours 24-30
**Dependencies:** Phase 06 (Visual Review & Gemini)
**Completion:** 0% (0/20 tasks complete)

---

## Overview

Implement Agent 4 (Audio Pipeline) with ElevenLabs TTS, audio selection UI with 4 options (TTS voices, teacher upload, no audio, instrumental), and trigger composition pipeline.

---

## Tasks

### 1. Audio Pipeline Agent (Hours 24-26)

#### 1.1 Install ElevenLabs SDK
- [ ] Add to `backend/requirements.txt`:
  ```
  elevenlabs==0.2.26
  ```
- [ ] Install: `pip install elevenlabs`
- [ ] Add to `.env`:
  ```
  ELEVENLABS_API_KEY=your-elevenlabs-key
  ```

**Dependencies:** Phase 06 complete
**Testing:** Import: `from elevenlabs import generate, Voice`

#### 1.2 Create Audio Pipeline Agent
- [ ] Create `backend/agents/audio_pipeline.py`:
  ```python
  from elevenlabs import generate, save, voices
  import os
  import time
  from .base import AgentInput, AgentOutput

  class AudioPipelineAgent:
      def __init__(self):
          self.api_key = os.getenv("ELEVENLABS_API_KEY")

      async def process(self, input: AgentInput) -> AgentOutput:
          start_time = time.time()

          try:
              segments = input.data.get("segments", [])
              voice_id = input.data.get("voice_id", "EXAVITQu4vr4xnSDxMaL")  # Default: Bella
              total_cost = 0.0
              audio_files = []

              for i, segment in enumerate(segments):
                  narration = segment.get("narration", "")

                  # Generate TTS
                  audio = generate(
                      text=narration,
                      voice=voice_id,
                      model="eleven_multilingual_v2",
                      api_key=self.api_key
                  )

                  # Save audio file (temp location for now)
                  filename = f"audio_segment_{i}.mp3"
                  filepath = f"/tmp/{filename}"
                  save(audio, filepath)

                  # ElevenLabs pricing: ~$0.30 per 1000 characters
                  char_count = len(narration)
                  cost = (char_count / 1000) * 0.30

                  audio_files.append({
                      "segment_id": segment.get("id"),
                      "filepath": filepath,
                      "url": "",  # Will upload to storage later
                      "duration": 0.0,  # Will calculate after saving
                      "cost": cost
                  })

                  total_cost += cost

              duration = time.time() - start_time

              return AgentOutput(
                  success=True,
                  data={"audio_files": audio_files},
                  cost=total_cost,
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

      async def get_available_voices(self) -> list:
          """Fetch available voices from ElevenLabs"""
          try:
              voice_list = voices(api_key=self.api_key)
              return [
                  {
                      "voice_id": voice.voice_id,
                      "name": voice.name,
                      "category": voice.category if hasattr(voice, 'category') else "general"
                  }
                  for voice in voice_list
              ]
          except Exception as e:
              print(f"Error fetching voices: {e}")
              return []
  ```

**Dependencies:** Task 1.1
**Testing:** Instantiate: `agent = AudioPipelineAgent()`

#### 1.3 Test Audio Generation
- [ ] Create test script `backend/test_audio_pipeline.py`:
  ```python
  import asyncio
  from agents.audio_pipeline import AudioPipelineAgent
  from agents.base import AgentInput

  async def test_agent():
      agent = AudioPipelineAgent()

      input_data = AgentInput(
          session_id=1,
          data={
              "segments": [
                  {
                      "id": "seg_001",
                      "narration": "Have you ever wondered how plants make their own food?"
                  },
                  {
                      "id": "seg_002",
                      "narration": "Plants use a process called photosynthesis."
                  }
              ],
              "voice_id": "EXAVITQu4vr4xnSDxMaL"  # Bella voice
          }
      )

      result = await agent.process(input_data)

      print(f"Success: {result.success}")
      print(f"Total Cost: ${result.cost:.2f}")
      print(f"Duration: {result.duration:.2f}s")
      print(f"Audio Files: {len(result.data.get('audio_files', []))}")

      # Check if files were created
      for audio in result.data.get("audio_files", []):
          import os
          exists = os.path.exists(audio['filepath'])
          print(f"  {audio['filepath']}: {'EXISTS' if exists else 'NOT FOUND'}")

  if __name__ == "__main__":
      asyncio.run(test_agent())
  ```
- [ ] Run test
- [ ] Verify MP3 files created in `/tmp/`
- [ ] Listen to generated audio

**Dependencies:** Task 1.2
**Testing:** Should create MP3 files with TTS audio

---

### 2. Audio Selection UI (Hours 26-28)

#### 2.1 Create Voices API Endpoint
- [ ] Create `backend/routes/audio.py`:
  ```python
  from fastapi import APIRouter, Depends
  from agents.audio_pipeline import AudioPipelineAgent

  router = APIRouter(prefix="/api/audio", tags=["audio"])

  @router.get("/voices")
  async def get_voices():
      agent = AudioPipelineAgent()
      voices = await agent.get_available_voices()
      return {"voices": voices}
  ```
- [ ] Register router in `backend/main.py`

**Dependencies:** Task 1.2
**Testing:** GET http://localhost:8000/api/audio/voices

#### 2.2 Create Audio Selection Page
- [ ] Create `frontend/app/session/[id]/audio-selection/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams, useRouter } from 'next/navigation';
  import apiClient from '@/lib/api';

  interface Voice {
    voice_id: string;
    name: string;
    category: string;
  }

  export default function AudioSelectionPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = parseInt(params.id as string);

    const [audioOption, setAudioOption] = useState<'tts' | 'upload' | 'none' | 'instrumental'>('tts');
    const [voices, setVoices] = useState<Voice[]>([]);
    const [selectedVoice, setSelectedVoice] = useState<string>('');
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      // Fetch available voices
      apiClient.get('/api/audio/voices')
        .then(res => {
          setVoices(res.data.voices);
          if (res.data.voices.length > 0) {
            setSelectedVoice(res.data.voices[0].voice_id);
          }
        })
        .catch(err => console.error('Failed to fetch voices:', err));
    }, []);

    const handleConfirm = async () => {
      setLoading(true);

      const script = JSON.parse(localStorage.getItem(`script_${sessionId}`) || '[]');

      const audioConfig = {
        option: audioOption,
        voice_id: audioOption === 'tts' ? selectedVoice : null,
        segments: script
      };

      try {
        // Trigger audio generation and composition
        await apiClient.post(`/api/composition/start/${sessionId}`, audioConfig);

        // Navigate to composition progress page
        router.push(`/session/${sessionId}/composition`);
      } catch (error) {
        console.error('Failed to start composition:', error);
        alert('Failed to start composition');
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Select Audio Option</h1>

        <div className="space-y-4 mb-8">
          {/* Option 1: TTS */}
          <div
            onClick={() => setAudioOption('tts')}
            className={`bg-white p-6 rounded-lg shadow cursor-pointer border-2 ${
              audioOption === 'tts' ? 'border-blue-500' : 'border-transparent'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="radio"
                checked={audioOption === 'tts'}
                onChange={() => setAudioOption('tts')}
                className="mt-1"
              />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">AI Voice (Text-to-Speech)</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Generate narration using AI voices from ElevenLabs
                </p>

                {audioOption === 'tts' && (
                  <div>
                    <label className="block text-sm font-medium mb-2">Select Voice:</label>
                    <select
                      value={selectedVoice}
                      onChange={(e) => setSelectedVoice(e.target.value)}
                      className="border rounded px-3 py-2 w-full max-w-md"
                    >
                      {voices.map(voice => (
                        <option key={voice.voice_id} value={voice.voice_id}>
                          {voice.name} ({voice.category})
                        </option>
                      ))}
                    </select>
                    <div className="mt-2 text-sm text-gray-600">
                      Cost: ~$0.30
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Option 2: Upload Teacher Audio */}
          <div
            onClick={() => setAudioOption('upload')}
            className={`bg-white p-6 rounded-lg shadow cursor-pointer border-2 ${
              audioOption === 'upload' ? 'border-blue-500' : 'border-transparent'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="radio"
                checked={audioOption === 'upload'}
                onChange={() => setAudioOption('upload')}
                className="mt-1"
              />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">Upload Your Recording</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Record and upload your own narration
                </p>

                {audioOption === 'upload' && (
                  <div>
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                      className="block"
                    />
                    <div className="mt-2 text-sm text-gray-600">
                      Cost: $0.00 (free)
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Option 3: No Audio */}
          <div
            onClick={() => setAudioOption('none')}
            className={`bg-white p-6 rounded-lg shadow cursor-pointer border-2 ${
              audioOption === 'none' ? 'border-blue-500' : 'border-transparent'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="radio"
                checked={audioOption === 'none'}
                onChange={() => setAudioOption('none')}
                className="mt-1"
              />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">No Audio</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Generate silent video (visuals only)
                </p>
                <div className="text-sm text-gray-600">
                  Cost: $0.00 (free)
                </div>
              </div>
            </div>
          </div>

          {/* Option 4: Instrumental Background */}
          <div
            onClick={() => setAudioOption('instrumental')}
            className={`bg-white p-6 rounded-lg shadow cursor-pointer border-2 ${
              audioOption === 'instrumental' ? 'border-blue-500' : 'border-transparent'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="radio"
                checked={audioOption === 'instrumental'}
                onChange={() => setAudioOption('instrumental')}
                className="mt-1"
              />
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">Instrumental Music Only</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Add background music without narration
                </p>
                <div className="text-sm text-gray-600">
                  Cost: $0.00 (free, using royalty-free music)
                </div>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={handleConfirm}
          disabled={loading || (audioOption === 'upload' && !uploadedFile)}
          className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 text-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Processing...' : 'Confirm & Start Composition →'}
        </button>
      </div>
    );
  }
  ```

**Dependencies:** Task 2.1
**Testing:** Navigate to page, verify 4 audio options display

#### 2.3 Test Audio Selection Flow
- [ ] Navigate to audio selection page
- [ ] Verify voices load in dropdown
- [ ] Select different audio options
- [ ] Verify cost displays for each option
- [ ] Select TTS option with specific voice
- [ ] Click "Confirm"
- [ ] Verify navigation to composition page

**Dependencies:** Task 2.2
**Testing:** All audio options should work

---

### 3. Trigger Composition Pipeline (Hours 28-30)

#### 3.1 Create Composition Start Endpoint
- [ ] Create `backend/routes/composition.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session, Asset
  from agents.audio_pipeline import AudioPipelineAgent
  from agents.base import AgentInput
  from utils.websocket_manager import ws_manager
  from routes.sessions import get_current_user_id, get_db

  router = APIRouter(prefix="/api/composition", tags=["composition"])

  async def composition_pipeline_task(session_id: int, audio_config: dict):
      """Background task for complete composition pipeline"""
      try:
          db = SessionLocal()

          # Step 1: Audio Generation (if TTS selected)
          if audio_config.get('option') == 'tts':
              await ws_manager.send_progress(session_id, {
                  "stage": "audio_generation",
                  "status": "in_progress",
                  "message": "Generating audio narration..."
              })

              agent = AudioPipelineAgent()
              audio_input = AgentInput(
                  session_id=session_id,
                  data={
                      "segments": audio_config.get("segments", []),
                      "voice_id": audio_config.get("voice_id")
                  }
              )

              result = await agent.process(audio_input)

              if not result.success:
                  raise Exception(result.error)

              # Save audio assets
              for audio_file in result.data["audio_files"]:
                  audio_asset = Asset(
                      session_id=session_id,
                      asset_type="audio",
                      url=audio_file["url"],
                      metadata={
                          "segment_id": audio_file["segment_id"],
                          "filepath": audio_file["filepath"],
                          "cost": audio_file["cost"]
                      }
                  )
                  db.add(audio_asset)

              db.commit()

              await ws_manager.send_progress(session_id, {
                  "stage": "audio_generation",
                  "status": "complete",
                  "message": "Audio generated!",
                  "data": {"cost": result.cost}
              })

          # Step 2: Will trigger Ed Compositor in Phase 08
          await ws_manager.send_progress(session_id, {
              "stage": "composition_ready",
              "status": "complete",
              "message": "Ready for composition (Phase 08)"
          })

          session = db.query(Session).filter(Session.id == session_id).first()
          session.status = "audio_complete"
          db.commit()

          db.close()

      except Exception as e:
          await ws_manager.send_progress(session_id, {
              "stage": "audio_generation",
              "status": "error",
              "message": str(e)
          })

  @router.post("/start/{session_id}")
  async def start_composition(
      session_id: int,
      audio_config: dict,
      background_tasks: BackgroundTasks,
      user_id: int = Depends(get_current_user_id),
      db: DBSession = Depends(get_db)
  ):
      session = db.query(Session).filter(
          Session.id == session_id,
          Session.user_id == user_id
      ).first()

      if not session:
          raise HTTPException(status_code=404, detail="Session not found")

      background_tasks.add_task(composition_pipeline_task, session_id, audio_config)

      return {"message": "Composition pipeline started", "session_id": session_id}
  ```
- [ ] Register router in `backend/main.py`

**Dependencies:** Task 1.2
**Testing:** Endpoint registered successfully

#### 3.2 Create Composition Progress Page
- [ ] Create `frontend/app/session/[id]/composition/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams } from 'next/navigation';
  import { useWebSocket } from '@/lib/useWebSocket';

  export default function CompositionPage() {
    const params = useParams();
    const sessionId = parseInt(params.id as string);
    const { messages } = useWebSocket(sessionId);

    const [currentStage, setCurrentStage] = useState('audio_generation');
    const [progress, setProgress] = useState<any[]>([]);

    useEffect(() => {
      // Track all progress messages
      setProgress(messages);

      // Determine current stage
      const latestStage = messages[messages.length - 1];
      if (latestStage) {
        setCurrentStage(latestStage.stage);
      }
    }, [messages]);

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Composing Your Video</h1>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
            <span className="text-lg">Processing...</span>
          </div>

          <div className="space-y-2">
            {progress.map((msg, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  msg.status === 'complete' ? 'bg-green-500' :
                  msg.status === 'error' ? 'bg-red-500' :
                  'bg-blue-500'
                }`}></div>
                <div className="flex-1">
                  <div className="font-medium">{msg.stage}</div>
                  <div className="text-sm text-gray-600">{msg.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="text-sm text-gray-600">
          This process may take several minutes. You can safely leave this page.
        </div>
      </div>
    );
  }
  ```

**Dependencies:** Phase 03
**Testing:** Navigate to page, verify progress display

#### 3.3 Test End-to-End Audio Pipeline
- [ ] Complete visual approval
- [ ] Navigate to audio selection
- [ ] Select TTS option
- [ ] Choose voice
- [ ] Click "Confirm"
- [ ] Verify WebSocket messages for audio generation
- [ ] Check database for audio Asset records
- [ ] Verify session status updated to "audio_complete"

**Dependencies:** Tasks 3.1, 3.2
**Testing:** Complete flow should work

---

## Phase Checklist

**Before moving to Phase 08, verify:**

- [ ] ElevenLabs API credentials configured
- [ ] Audio Pipeline Agent generates TTS audio
- [ ] Audio files saved to temporary location
- [ ] Voices API returns available voices
- [ ] Audio selection page displays 4 options
- [ ] TTS voice selection works
- [ ] Audio option costs display correctly
- [ ] Composition pipeline triggered after audio selection
- [ ] WebSocket sends audio generation progress
- [ ] Audio assets saved to database
- [ ] Session status updated to "audio_complete"

---

## Completion Status

**Total Tasks:** 20
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- ElevenLabs pricing: ~$0.30 per 1000 characters
- Expected audio cost for 60s video: $0.20-0.30
- Consider implementing audio preview before generation
- Add support for teacher audio upload in future iteration
- Instrumental music can use royalty-free libraries
- Audio files should be uploaded to cloud storage
