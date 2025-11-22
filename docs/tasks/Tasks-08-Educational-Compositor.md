# Phase 08: Educational Compositor (Agent 5 - Self-Healing) (Hours 30-42)

**Timeline:** Day 2, Hours 30-42
**Dependencies:** Phase 07 (Audio Pipeline)
**Completion:** 0% (0/32 tasks complete)

---

## Overview

Implement Agent 5 (Educational Compositor) with self-healing logic. Reads Gemini validations, detects mismatches, makes LLM-powered decisions (substitute/generate/fallback), and composes final video with FFmpeg.

---

## Tasks

### 1. Self-Healing Logic (Hours 30-33)

#### 1.1 Create Ed Compositor Base Class
- [ ] Create `backend/agents/ed_compositor.py`:
  ```python
  from typing import List, Dict, Optional
  from .base import AgentInput, AgentOutput
  from models.database import SessionLocal, Asset, GeminiValidation
  import time

  class EducationalCompositor:
      def __init__(self):
          self.db = SessionLocal()

      async def process(self, input: AgentInput) -> AgentOutput:
          start_time = time.time()

          try:
              session_id = input.session_id

              # Step 1: Read Gemini validations
              validations = await self.read_validations(session_id)

              # Step 2: Detect mismatches
              mismatches = await self.detect_mismatches(validations)

              # Step 3: Make decisions for mismatches
              decisions = await self.make_healing_decisions(mismatches, session_id)

              # Step 4: Execute healing actions
              healed_visuals = await self.execute_healing_actions(decisions, session_id)

              # Step 5: Build final timeline
              timeline = await self.build_timeline(session_id, healed_visuals)

              # Step 6: Compose video with FFmpeg
              video_path = await self.compose_video(timeline, session_id)

              duration = time.time() - start_time

              return AgentOutput(
                  success=True,
                  data={
                      "video_path": video_path,
                      "timeline": timeline,
                      "healing_log": decisions
                  },
                  cost=0.0,  # FFmpeg is free
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

      async def read_validations(self, session_id: int) -> List[Dict]:
          """Read Gemini validations from database"""
          visuals = self.db.query(Asset).filter(
              Asset.session_id == session_id,
              Asset.asset_type == "visual"
          ).all()

          validations = []
          for visual in visuals:
              gemini_val = self.db.query(GeminiValidation).filter(
                  GeminiValidation.asset_id == visual.id
              ).first()

              if gemini_val:
                  validations.append({
                      "visual_id": visual.id,
                      "url": visual.url,
                      "segment_id": visual.metadata.get("segment_id"),
                      "all_criteria_pass": gemini_val.all_criteria_pass,
                      "scientific_accuracy": gemini_val.scientific_accuracy,
                      "label_quality": gemini_val.label_quality,
                      "age_appropriate": gemini_val.age_appropriate,
                      "visual_clarity": gemini_val.visual_clarity,
                      "notes": gemini_val.notes
                  })

          return validations

      async def detect_mismatches(self, validations: List[Dict]) -> List[Dict]:
          """Detect which visuals failed validation"""
          mismatches = [
              v for v in validations
              if not v["all_criteria_pass"]
          ]
          return mismatches

      async def make_healing_decisions(self, mismatches: List[Dict], session_id: int) -> List[Dict]:
          """Use LLM to decide healing action for each mismatch"""
          decisions = []

          for mismatch in mismatches:
              # Placeholder for LLM decision-making (will implement in task 1.3)
              decisions.append({
                  "visual_id": mismatch["visual_id"],
                  "segment_id": mismatch["segment_id"],
                  "action": "substitute",  # Options: substitute, regenerate, text_slide
                  "reason": mismatch["notes"]
              })

          return decisions

      async def execute_healing_actions(self, decisions: List[Dict], session_id: int) -> List[Dict]:
          """Execute healing actions (placeholder for now)"""
          # Will implement in tasks 1.4-1.6
          return []

      async def build_timeline(self, session_id: int, healed_visuals: List[Dict]) -> Dict:
          """Build final video timeline (placeholder)"""
          # Will implement in task 3.1
          return {}

      async def compose_video(self, timeline: Dict, session_id: int) -> str:
          """Compose video with FFmpeg (placeholder)"""
          # Will implement in task 3.2
          return ""

      def __del__(self):
          self.db.close()
  ```

**Dependencies:** Phase 07 complete
**Testing:** Instantiate: `compositor = EducationalCompositor()`

#### 1.2 Test Validation Reading
- [ ] Create test script `backend/test_validation_reading.py`:
  ```python
  import asyncio
  from agents.ed_compositor import EducationalCompositor

  async def test_read():
      compositor = EducationalCompositor()

      validations = await compositor.read_validations(session_id=1)

      print(f"Found {len(validations)} validations")
      for v in validations:
          print(f"Visual {v['visual_id']}: Pass={v['all_criteria_pass']}, Notes={v['notes']}")

      mismatches = await compositor.detect_mismatches(validations)
      print(f"\nFound {len(mismatches)} mismatches")

  if __name__ == "__main__":
      asyncio.run(test_read())
  ```
- [ ] Run test with session that has validations

**Dependencies:** Task 1.1
**Testing:** Should read validations from database

#### 1.3 Implement LLM Decision-Making
- [ ] Update `make_healing_decisions` method:
  ```python
  async def make_healing_decisions(self, mismatches: List[Dict], session_id: int) -> List[Dict]:
      """Use LLM to decide healing action for each mismatch"""
      from agents.narrative_builder import NarrativeBuilderAgent
      import json

      decisions = []
      llm_agent = NarrativeBuilderAgent()

      for mismatch in mismatches:
          # Build LLM prompt
          prompt = f"""You are an AI compositor for educational videos. A visual failed validation with these issues:

  Issues: {mismatch['notes']}

  Criteria Failed:
  - Scientific Accuracy: {'FAIL' if not mismatch['scientific_accuracy'] else 'PASS'}
  - Label Quality: {'FAIL' if not mismatch['label_quality'] else 'PASS'}
  - Age Appropriate: {'FAIL' if not mismatch['age_appropriate'] else 'PASS'}
  - Visual Clarity: {'FAIL' if not mismatch['visual_clarity'] else 'PASS'}

  Decide the best action:
  1. **substitute**: Use another existing visual from the same category
  2. **regenerate**: Generate a new visual with corrected prompt
  3. **text_slide**: Create text slide as fallback

  Respond with JSON only:
  {{
      "action": "substitute|regenerate|text_slide",
      "reason": "Brief explanation"
  }}"""

          # Call LLM (reusing Narrative Builder's LLM client)
          response = llm_agent.client.chat.completions.create(
              model=llm_agent.model,
              messages=[{"role": "user", "content": prompt}],
              temperature=0.7,
              max_tokens=200
          )

          # Parse response
          content = response.choices[0].message.content
          try:
              decision_data = json.loads(content)
          except:
              # Fallback to text slide if parsing fails
              decision_data = {"action": "text_slide", "reason": "Failed to parse decision"}

          decisions.append({
              "visual_id": mismatch["visual_id"],
              "segment_id": mismatch["segment_id"],
              "action": decision_data.get("action", "text_slide"),
              "reason": decision_data.get("reason", "No reason provided")
          })

      return decisions
  ```

**Dependencies:** Task 1.1, Phase 04
**Testing:** Should return decisions for mismatches

---

### 2. Emergency Visual Generation & Text Fallback (Hours 33-39)

#### 2.1 Implement Visual Substitution
- [ ] Add method to `EducationalCompositor`:
  ```python
  async def substitute_visual(self, segment_id: str, session_id: int) -> Optional[str]:
      """Find another visual from same category to substitute"""

      # Find all visuals for this session
      visuals = self.db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "visual"
      ).all()

      # Find visuals with passing validation
      for visual in visuals:
          gemini_val = self.db.query(GeminiValidation).filter(
              GeminiValidation.asset_id == visual.id
          ).first()

          if gemini_val and gemini_val.all_criteria_pass:
              # Found a good visual to substitute
              return visual.url

      return None
  ```

**Dependencies:** Task 1.1
**Testing:** Test with session having multiple visuals

#### 2.2 Implement Emergency Generation
- [ ] Add method to `EducationalCompositor`:
  ```python
  async def emergency_generate_visual(self, segment: Dict, attempt: int = 1, max_attempts: int = 3) -> Optional[Dict]:
      """Emergency visual generation with retry loop"""
      from agents.visual_pipeline import VisualPipelineAgent
      from agents.gemini_validator import GeminiVisionValidator

      if attempt > max_attempts:
          return None

      # Generate visual
      visual_agent = VisualPipelineAgent()
      result = await visual_agent.dalle_generator.generate_image(
          segment.get("visual_guidance", ""),
          style="educational"
      )

      if not result['success']:
          # Retry
          return await self.emergency_generate_visual(segment, attempt + 1, max_attempts)

      # Validate generated visual
      validator = GeminiVisionValidator()
      validation = await validator.validate_image(
          result['url'],
          context={
              "narration": segment.get("narration", ""),
              "key_concepts": segment.get("key_concepts", []),
              "grade_level": "6-7"
          }
      )

      if validation['all_criteria_pass']:
          # Success!
          return {
              "url": result['url'],
              "cost": result['cost'],
              "attempts": attempt,
              "validation": validation
          }
      else:
          # Retry
          return await self.emergency_generate_visual(segment, attempt + 1, max_attempts)
  ```

**Dependencies:** Tasks 1.1, Phase 05, Phase 06
**Testing:** Test with failing visual

#### 2.3 Implement Text Slide Generator
- [ ] Install FFmpeg (if not already installed):
  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu
  apt-get install ffmpeg
  ```
- [ ] Add to `backend/requirements.txt`:
  ```
  ffmpeg-python==0.2.0
  ```
- [ ] Create `backend/agents/text_slide_generator.py`:
  ```python
  import ffmpeg
  import os
  from typing import List

  class TextSlideGenerator:
      def __init__(self):
          self.output_dir = "/tmp/text_slides"
          os.makedirs(self.output_dir, exist_ok=True)

      def generate_slide(self, text: str, duration: int = 5, filename: str = None) -> str:
          """
          Generate text slide using FFmpeg
          Args:
              text: Text to display
              duration: Duration in seconds
              filename: Output filename (default: auto-generated)
          Returns:
              Path to generated slide
          """
          if not filename:
              filename = f"text_slide_{int(time.time())}.mp4"

          output_path = os.path.join(self.output_dir, filename)

          # Extract key points (simple approach: split into lines)
          lines = self.format_text(text)

          # Create text slide with FFmpeg
          (
              ffmpeg
              .input('color=c=white:s=1920x1080:d=' + str(duration), f='lavfi')
              .drawtext(
                  text=lines,
                  fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                  fontsize=48,
                  fontcolor='black',
                  x='(w-text_w)/2',
                  y='(h-text_h)/2'
              )
              .output(output_path, vcodec='libx264', pix_fmt='yuv420p')
              .overwrite_output()
              .run(quiet=True)
          )

          return output_path

      def format_text(self, text: str, max_chars_per_line: int = 40) -> str:
          """Format text for slide (wrap lines)"""
          words = text.split()
          lines = []
          current_line = []

          for word in words:
              if len(' '.join(current_line + [word])) <= max_chars_per_line:
                  current_line.append(word)
              else:
                  lines.append(' '.join(current_line))
                  current_line = [word]

          if current_line:
              lines.append(' '.join(current_line))

          return '\\n'.join(lines[:5])  # Limit to 5 lines
  ```

**Dependencies:** Task 2.2
**Testing:** Generate sample text slide

#### 2.4 Test Text Slide Generation
- [ ] Create test script `backend/test_text_slide.py`:
  ```python
  from agents.text_slide_generator import TextSlideGenerator

  def test_slide():
      generator = TextSlideGenerator()

      slide_path = generator.generate_slide(
          text="Photosynthesis is the process by which plants convert sunlight into energy",
          duration=5
      )

      print(f"Text slide created: {slide_path}")
      print(f"File exists: {os.path.exists(slide_path)}")

      # Play with ffplay
      # os.system(f"ffplay {slide_path}")

  if __name__ == "__main__":
      test_slide()
  ```
- [ ] Run test
- [ ] Verify MP4 file created

**Dependencies:** Task 2.3
**Testing:** Should create text slide video

#### 2.5 Implement Execute Healing Actions
- [ ] Update `execute_healing_actions` method:
  ```python
  async def execute_healing_actions(self, decisions: List[Dict], session_id: int) -> List[Dict]:
      """Execute healing actions based on decisions"""
      from agents.text_slide_generator import TextSlideGenerator

      healed_visuals = []

      # Get script for context
      script_asset = self.db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "script"
      ).first()

      script_segments = script_asset.metadata.get("script", {}).get("segments", [])

      for decision in decisions:
          segment = next((s for s in script_segments if s['id'] == decision['segment_id']), None)

          if decision['action'] == 'substitute':
              new_url = await self.substitute_visual(decision['segment_id'], session_id)
              if new_url:
                  healed_visuals.append({
                      "segment_id": decision['segment_id'],
                      "url": new_url,
                      "source": "substituted",
                      "original_visual_id": decision['visual_id']
                  })
              else:
                  # Fallback to text slide
                  decision['action'] = 'text_slide'

          if decision['action'] == 'regenerate':
              result = await self.emergency_generate_visual(segment)
              if result:
                  healed_visuals.append({
                      "segment_id": decision['segment_id'],
                      "url": result['url'],
                      "source": "emergency_generated",
                      "attempts": result['attempts'],
                      "cost": result['cost']
                  })
              else:
                  # Fallback to text slide
                  decision['action'] = 'text_slide'

          if decision['action'] == 'text_slide':
              generator = TextSlideGenerator()
              slide_path = generator.generate_slide(
                  text=segment.get("narration", ""),
                  duration=segment.get("duration", 5)
              )
              healed_visuals.append({
                  "segment_id": decision['segment_id'],
                  "url": slide_path,
                  "source": "text_slide",
                  "local_path": slide_path
              })

      return healed_visuals
  ```

**Dependencies:** Tasks 2.1, 2.2, 2.3
**Testing:** Test with various decision types

---

### 3. FFmpeg Composition (Hours 39-42)

#### 3.1 Implement Build Timeline
- [ ] Update `build_timeline` method:
  ```python
  async def build_timeline(self, session_id: int, healed_visuals: List[Dict]) -> Dict:
      """Build final video timeline with all assets"""

      # Get all visuals (original + healed)
      visuals = self.db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "visual"
      ).all()

      # Get audio
      audio_assets = self.db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "audio"
      ).all()

      # Get script for timing
      script_asset = self.db.query(Asset).filter(
          Asset.session_id == session_id,
          Asset.asset_type == "script"
      ).first()

      script_segments = script_asset.metadata.get("script", {}).get("segments", [])

      timeline = {
          "segments": [],
          "total_duration": 0
      }

      for segment in script_segments:
          segment_id = segment['id']

          # Find visual (healed or original)
          healed_visual = next((h for h in healed_visuals if h['segment_id'] == segment_id), None)

          if healed_visual:
              visual_url = healed_visual['url']
          else:
              # Use original visual
              original_visual = next((v for v in visuals if v.metadata.get('segment_id') == segment_id), None)
              visual_url = original_visual.url if original_visual else None

          # Find audio
          audio_file = next((a for a in audio_assets if a.metadata.get('segment_id') == segment_id), None)
          audio_path = audio_file.metadata.get('filepath') if audio_file else None

          timeline["segments"].append({
              "segment_id": segment_id,
              "start_time": segment['start_time'],
              "duration": segment['duration'],
              "visual_url": visual_url,
              "audio_path": audio_path,
              "narration": segment['narration']
          })

          timeline["total_duration"] += segment['duration']

      return timeline
  ```

**Dependencies:** Tasks 1.1, 2.5
**Testing:** Build timeline for session

#### 3.2 Implement FFmpeg Composition
- [ ] Install `ffmpeg-python`:
  ```bash
  pip install ffmpeg-python
  ```
- [ ] Update `compose_video` method:
  ```python
  import ffmpeg
  import requests
  from io import BytesIO

  async def compose_video(self, timeline: Dict, session_id: int) -> str:
      """Compose final video with FFmpeg"""
      import tempfile

      # Download all visuals to temp directory
      temp_dir = tempfile.mkdtemp()
      video_clips = []

      for i, segment in enumerate(timeline['segments']):
          # Download visual
          visual_url = segment['visual_url']

          if visual_url.startswith('http'):
              response = requests.get(visual_url)
              visual_path = f"{temp_dir}/visual_{i}.png"
              with open(visual_path, 'wb') as f:
                  f.write(response.content)
          else:
              visual_path = visual_url  # Local path

          # Create video clip from image (with duration)
          clip_path = f"{temp_dir}/clip_{i}.mp4"
          (
              ffmpeg
              .input(visual_path, loop=1, t=segment['duration'])
              .output(clip_path, vcodec='libx264', pix_fmt='yuv420p')
              .overwrite_output()
              .run(quiet=True)
          )

          video_clips.append(clip_path)

      # Concatenate video clips
      concat_file = f"{temp_dir}/concat.txt"
      with open(concat_file, 'w') as f:
          for clip in video_clips:
              f.write(f"file '{clip}'\\n")

      temp_video = f"{temp_dir}/video_no_audio.mp4"
      os.system(f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {temp_video}")

      # Add audio if exists
      audio_files = [s['audio_path'] for s in timeline['segments'] if s.get('audio_path')]

      if audio_files:
          # Concatenate audio
          audio_concat = f"{temp_dir}/audio_concat.txt"
          with open(audio_concat, 'w') as f:
              for audio in audio_files:
                  f.write(f"file '{audio}'\\n")

          temp_audio = f"{temp_dir}/audio_combined.mp3"
          os.system(f"ffmpeg -f concat -safe 0 -i {audio_concat} -c copy {temp_audio}")

          # Merge video + audio
          final_path = f"{temp_dir}/final_video_{session_id}.mp4"
          (
              ffmpeg
              .input(temp_video)
              .input(temp_audio)
              .output(final_path, vcodec='copy', acodec='aac')
              .overwrite_output()
              .run(quiet=True)
          )
      else:
          final_path = temp_video

      return final_path
  ```

**Dependencies:** Task 3.1
**Testing:** Compose video from timeline

#### 3.3 Test End-to-End Composition
- [ ] Create test that runs full composition:
  ```python
  import asyncio
  from agents.ed_compositor import EducationalCompositor
  from agents.base import AgentInput

  async def test_composition():
      compositor = EducationalCompositor()

      input_data = AgentInput(
          session_id=1,
          data={}
      )

      result = await compositor.process(input_data)

      print(f"Success: {result.success}")
      print(f"Video Path: {result.data.get('video_path')}")
      print(f"Duration: {result.duration:.2f}s")

      if result.success:
          video_path = result.data['video_path']
          print(f"Video exists: {os.path.exists(video_path)}")
          # Play: os.system(f"ffplay {video_path}")

  if __name__ == "__main__":
      asyncio.run(test_composition())
  ```
- [ ] Run with session that has all assets
- [ ] Verify video file created
- [ ] Play video to check quality

**Dependencies:** Tasks 3.1, 3.2
**Testing:** Should create final MP4 video

---

## Phase Checklist

**Before moving to Phase 09, verify:**

- [ ] Ed Compositor reads Gemini validations from database
- [ ] Mismatch detection identifies failed visuals
- [ ] LLM makes healing decisions
- [ ] Visual substitution works
- [ ] Emergency visual generation works with retry
- [ ] Text slide generator creates fallback slides
- [ ] Healing actions execute correctly
- [ ] Timeline builds with all segments
- [ ] FFmpeg composes video clips
- [ ] Audio overlays correctly
- [ ] Final video file created
- [ ] Video plays without errors

---

## Completion Status

**Total Tasks:** 32
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

##Notes

- FFmpeg composition is CPU-intensive
- Consider running composition in background worker
- Add progress tracking for long compositions
- Store composition log for debugging
- Text slides are reliable fallback option
- Emergency generation can be expensive (up to $0.12 for 3 attempts)
- Consider adding transitions between clips for polish
