# Phase 05: Visual Pipeline (Agent 3) (Hours 12-18)

**Timeline:** Day 1, Hours 12-18
**Dependencies:** Phase 04 (Narrative Builder)
**Completion:** 0% (0/28 tasks complete)

---

## Overview

Implement Agent 3 (Visual Pipeline) which generates 8-12 visuals using templates (60%+) and DALL-E 3 (40%). Includes template matching, PSD customization, AI generation, and WebSocket progress tracking.

---

## Tasks

### 1. Template Library Integration (Hours 12-14)

#### 1.1 Create Template Matcher
- [ ] Create `backend/agents/template_matcher.py`:
  ```python
  from models.database import SessionLocal, Template
  from typing import List, Optional
  import re

  class TemplateMatcher:
      def __init__(self):
          self.db = SessionLocal()

      def match_template(self, visual_guidance: str, key_concepts: List[str]) -> Optional[dict]:
          """Find best matching template based on visual guidance and concepts"""

          # Load all templates
          templates = self.db.query(Template).all()

          # Simple keyword matching
          keywords_to_categories = {
              'solar system': 'astronomy',
              'planet': 'astronomy',
              'photosynthesis': 'biology',
              'chlorophyll': 'biology',
              'plant': 'biology',
              'cell': 'biology',
              'water cycle': 'earth_science',
              'evaporation': 'earth_science',
              'condensation': 'earth_science',
          }

          # Find category based on concepts
          matched_category = None
          for concept in key_concepts:
              concept_lower = concept.lower()
              for keyword, category in keywords_to_categories.items():
                  if keyword in concept_lower:
                      matched_category = category
                      break
              if matched_category:
                  break

          # Find templates in that category
          if matched_category:
              matching_templates = [t for t in templates if t.category == matched_category]
              if matching_templates:
                  # Return first match (can be enhanced with scoring)
                  template = matching_templates[0]
                  return {
                      'id': template.id,
                      'template_id': template.template_id,
                      'name': template.name,
                      'psd_url': template.psd_url,
                      'preview_url': template.preview_url,
                      'editable_layers': template.editable_layers
                      }

          return None

      def __del__(self):
          self.db.close()
  ```

**Dependencies:** Phase 00 (templates in database)
**Testing:** Test matching: `matcher.match_template("Show photosynthesis", ["photosynthesis"])`

#### 1.2 Install Image Processing Libraries
- [ ] Add to `backend/requirements.txt`:
  ```
  pillow==10.1.0
  requests==2.31.0
  ```
- [ ] Install: `pip install pillow requests`

**Dependencies:** None
**Testing:** Import: `from PIL import Image`

#### 1.3 Create PSD Layer Customizer
- [ ] Create `backend/agents/psd_customizer.py`:
  ```python
  from PIL import Image, ImageDraw, ImageFont
  import requests
  from io import BytesIO
  import os

  class PSDCustomizer:
      """
      Note: Full PSD editing requires psd-tools library
      For MVP, we'll use template PNGs and overlay text
      """

      def customize_template(
          self,
          template_url: str,
          customizations: dict
      ) -> bytes:
          """
          Download template PNG and add custom text overlays
          Args:
              template_url: URL to template image
              customizations: {"title": "New Title", "labels": ["Label1", "Label2"]}
          Returns:
              Image bytes
          """

          # Download template
          response = requests.get(template_url)
          img = Image.open(BytesIO(response.content))

          # Create drawing context
          draw = ImageDraw.Draw(img)

          # Load font (fallback to default if custom font not available)
          try:
              font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
              font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
          except:
              font_title = ImageFont.load_default()
              font_label = ImageFont.load_default()

          # Add title if provided
          if 'title' in customizations:
              title = customizations['title']
              # Center title at top
              bbox = draw.textbbox((0, 0), title, font=font_title)
              text_width = bbox[2] - bbox[0]
              x = (img.width - text_width) // 2
              y = 50
              # Draw with outline for visibility
              draw.text((x-2, y-2), title, font=font_title, fill='black')
              draw.text((x+2, y+2), title, font=font_title, fill='black')
              draw.text((x, y), title, font=font_title, fill='white')

          # Add labels if provided
          if 'labels' in customizations:
              labels = customizations['labels']
              y_offset = 200
              for label in labels:
                  draw.text((100, y_offset), label, font=font_label, fill='white', stroke_width=2, stroke_fill='black')
                  y_offset += 60

          # Convert to bytes
          buffer = BytesIO()
          img.save(buffer, format='PNG')
          return buffer.getvalue()
  ```

**Dependencies:** Task 1.2
**Testing:** Test with template URL and customizations

#### 1.4 Test Template Customization
- [ ] Create test script `backend/test_template_customization.py`:
  ```python
  from agents.psd_customizer import PSDCustomizer
  from models.database import SessionLocal, Template

  def test_customization():
      db = SessionLocal()
      template = db.query(Template).first()

      if not template:
          print("No templates found in database")
          return

      customizer = PSDCustomizer()
      customized_image = customizer.customize_template(
          template.preview_url,
          {
              'title': 'Photosynthesis',
              'labels': ['Sunlight', 'CO₂ + H₂O', 'Glucose + O₂']
          }
      )

      # Save to file
      with open('test_customized.png', 'wb') as f:
          f.write(customized_image)

      print(f"Customized image saved to test_customized.png ({len(customized_image)} bytes)")
      db.close()

  if __name__ == "__main__":
      test_customization()
  ```
- [ ] Run test
- [ ] Verify output image has custom text

**Dependencies:** Task 1.3
**Testing:** Should create customized PNG file

---

### 2. DALL-E 3 Integration (Hours 14-16)

#### 2.1 Install OpenAI Library
- [ ] Add to `backend/requirements.txt`:
  ```
  openai==1.3.0
  ```
- [ ] Install: `pip install openai`
- [ ] Add to `.env`:
  ```
  DALLE_API_KEY=your-openai-api-key
  ```

**Dependencies:** None
**Testing:** Import: `from openai import OpenAI`

#### 2.2 Create DALL-E Generator
- [ ] Create `backend/agents/dalle_generator.py`:
  ```python
  from openai import OpenAI
  import os
  import time

  class DALLEGenerator:
      def __init__(self):
          self.client = OpenAI(api_key=os.getenv("DALLE_API_KEY"))

      async def generate_image(self, prompt: str, style: str = "educational") -> dict:
          """
          Generate image using DALL-E 3
          Returns: {"url": "...", "cost": 0.04, "duration": 5.2}
          """
          start_time = time.time()

          try:
              # Build enhanced prompt for educational content
              enhanced_prompt = self._enhance_prompt(prompt, style)

              # Call DALL-E 3
              response = self.client.images.generate(
                  model="dall-e-3",
                  prompt=enhanced_prompt,
                  size="1792x1024",  # Landscape for video
                  quality="standard",  # "standard" or "hd"
                  n=1
              )

              image_url = response.data[0].url

              # DALL-E 3 pricing: $0.040 per image (standard), $0.080 (HD)
              cost = 0.040

              duration = time.time() - start_time

              return {
                  "success": True,
                  "url": image_url,
                  "cost": cost,
                  "duration": duration,
                  "prompt_used": enhanced_prompt
              }

          except Exception as e:
              return {
                  "success": False,
                  "url": None,
                  "cost": 0.0,
                  "duration": time.time() - start_time,
                  "error": str(e)
              }

      def _enhance_prompt(self, base_prompt: str, style: str) -> str:
          """Add style guidelines to prompt for consistent educational visuals"""

          style_guides = {
              "educational": "Educational diagram style, clean and clear, bright colors, labeled components, appropriate for middle school students (grades 6-7), scientific accuracy, no text in image",
              "realistic": "Photorealistic style, high detail, natural lighting",
              "illustration": "Hand-drawn illustration style, colorful, engaging for students"
          }

          guide = style_guides.get(style, style_guides["educational"])

          return f"{base_prompt}. {guide}"
  ```

**Dependencies:** Task 2.1
**Testing:** Instantiate: `generator = DALLEGenerator()`

#### 2.3 Test DALL-E Generation
- [ ] Create test script `backend/test_dalle.py`:
  ```python
  import asyncio
  from agents.dalle_generator import DALLEGenerator

  async def test_generation():
      generator = DALLEGenerator()

      result = await generator.generate_image(
          "Diagram showing photosynthesis process with sunlight, chloroplast, CO2, H2O, glucose, and oxygen",
          style="educational"
      )

      print(f"Success: {result['success']}")
      print(f"URL: {result['url']}")
      print(f"Cost: ${result['cost']}")
      print(f"Duration: {result['duration']:.2f}s")

  if __name__ == "__main__":
      asyncio.run(test_generation())
  ```
- [ ] Run test
- [ ] Verify image URL is returned

**Dependencies:** Task 2.2
**Testing:** Should return image URL, cost $0.04

---

### 3. Visual Pipeline Agent Implementation (Hours 16-18)

#### 3.1 Create Visual Pipeline Agent
- [ ] Create `backend/agents/visual_pipeline.py`:
  ```python
  import asyncio
  from typing import List
  from .base import AgentInput, AgentOutput
  from .template_matcher import TemplateMatcher
  from .psd_customizer import PSDCustomizer
  from .dalle_generator import DALLEGenerator
  import time

  class VisualPipelineAgent:
      def __init__(self):
          self.template_matcher = TemplateMatcher()
          self.psd_customizer = PSDCustomizer()
          self.dalle_generator = DALLEGenerator()

      async def process(self, input: AgentInput) -> AgentOutput:
          start_time = time.time()

          try:
              segments = input.data.get("segments", [])
              total_cost = 0.0
              visuals = []

              for i, segment in enumerate(segments):
                  visual_guidance = segment.get("visual_guidance", "")
                  key_concepts = segment.get("key_concepts", [])

                  # Try to match template first (60% target)
                  template_match = self.template_matcher.match_template(visual_guidance, key_concepts)

                  if template_match and (i % 3 != 2):  # Use template for 2 out of 3 visuals
                      # Customize template
                      customizations = {
                          "title": segment.get("key_concepts", [""])[0] if segment.get("key_concepts") else "",
                          "labels": segment.get("key_concepts", [])[:3]
                      }

                      customized_image_bytes = self.psd_customizer.customize_template(
                          template_match['preview_url'],
                          customizations
                      )

                      # TODO: Upload to storage (for now, use local path)
                      visual_url = f"template_customized_seg_{i}.png"

                      visuals.append({
                          "segment_id": segment.get("id"),
                          "type": "template",
                          "url": visual_url,
                          "template_id": template_match['template_id'],
                          "cost": 0.0,  # Templates are free
                          "source": "template"
                      })

                  else:
                      # Generate with DALL-E 3
                      result = await self.dalle_generator.generate_image(
                          visual_guidance,
                          style="educational"
                      )

                      if result['success']:
                          visuals.append({
                              "segment_id": segment.get("id"),
                              "type": "ai_generated",
                              "url": result['url'],
                              "cost": result['cost'],
                              "source": "dalle3",
                              "prompt": result['prompt_used']
                          })
                          total_cost += result['cost']
                      else:
                          # Fallback to template or skip
                          print(f"DALL-E generation failed for segment {i}: {result.get('error')}")

              duration = time.time() - start_time

              return AgentOutput(
                  success=True,
                  data={"visuals": visuals},
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
  ```

**Dependencies:** Tasks 1.1, 1.3, 2.2
**Testing:** Instantiate: `agent = VisualPipelineAgent()`

#### 3.2 Test Visual Pipeline Agent
- [ ] Create test script `backend/test_visual_pipeline.py`:
  ```python
  import asyncio
  from agents.visual_pipeline import VisualPipelineAgent
  from agents.base import AgentInput

  async def test_agent():
      agent = VisualPipelineAgent()

      input_data = AgentInput(
          session_id=1,
          data={
              "segments": [
                  {
                      "id": "seg_001",
                      "visual_guidance": "Animated question mark with plant growing",
                      "key_concepts": ["photosynthesis"]
                  },
                  {
                      "id": "seg_002",
                      "visual_guidance": "Diagram of leaf cross-section with chloroplast",
                      "key_concepts": ["chloroplast", "chlorophyll"]
                  },
                  {
                      "id": "seg_003",
                      "visual_guidance": "Animated diagram showing CO2 + H2O → Glucose + O2",
                      "key_concepts": ["carbon dioxide", "water", "glucose", "oxygen"]
                  },
                  {
                      "id": "seg_004",
                      "visual_guidance": "Real-world scene with child near tree",
                      "key_concepts": ["oxygen", "plants"]
                  }
              ]
          }
      )

      result = await agent.process(input_data)

      print(f"Success: {result.success}")
      print(f"Total Cost: ${result.cost:.2f}")
      print(f"Duration: {result.duration:.2f}s")
      print(f"Visuals Generated: {len(result.data.get('visuals', []))}")

      for i, visual in enumerate(result.data.get("visuals", [])):
          print(f"\nVisual {i+1}:")
          print(f"  Type: {visual['type']}")
          print(f"  Source: {visual['source']}")
          print(f"  Cost: ${visual['cost']}")

  if __name__ == "__main__":
      asyncio.run(test_agent())
  ```
- [ ] Run test
- [ ] Verify mix of templates and AI-generated images

**Dependencies:** Task 3.1
**Testing:** Should generate 4 visuals (mix of templates and DALL-E)

#### 3.3 Create Visual Generation API Endpoint
- [ ] Create `backend/routes/visuals.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session, Asset
  from agents.visual_pipeline import VisualPipelineAgent
  from agents.base import AgentInput
  from utils.websocket_manager import ws_manager
  from routes.sessions import get_current_user_id, get_db
  import json

  router = APIRouter(prefix="/api/visuals", tags=["visuals"])

  async def generate_visuals_task(session_id: int, segments: list):
      """Background task for visual generation"""
      try:
          await ws_manager.send_progress(session_id, {
              "stage": "visual_generation",
              "status": "in_progress",
              "message": "Generating visuals...",
              "progress": 0
          })

          agent = VisualPipelineAgent()
          db = SessionLocal()

          input_data = AgentInput(
              session_id=session_id,
              data={"segments": segments}
          )

          result = await agent.process(input_data)

          if not result.success:
              raise Exception(result.error)

          # Save each visual as Asset
          for visual in result.data["visuals"]:
              visual_asset = Asset(
                  session_id=session_id,
                  asset_type="visual",
                  url=visual["url"],
                  metadata={
                      "segment_id": visual["segment_id"],
                      "type": visual["type"],
                      "source": visual["source"],
                      "cost": visual["cost"]
                  }
              )
              db.add(visual_asset)

          # Update session
          session = db.query(Session).filter(Session.id == session_id).first()
          session.status = "visuals_generated"
          db.commit()

          await ws_manager.send_progress(session_id, {
              "stage": "visual_generation",
              "status": "complete",
              "message": "All visuals generated!",
              "data": {
                  "visuals": result.data["visuals"],
                  "total_cost": result.cost
              }
          })

          db.close()

      except Exception as e:
          await ws_manager.send_progress(session_id, {
              "stage": "visual_generation",
              "status": "error",
              "message": str(e)
          })

  @router.post("/generate/{session_id}")
  async def generate_visuals(
      session_id: int,
      segments: list,
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

      background_tasks.add_task(generate_visuals_task, session_id, segments)

      return {"message": "Visual generation started", "session_id": session_id}
  ```
- [ ] Register router in `backend/main.py`

**Dependencies:** Task 3.1
**Testing:** Endpoint registered successfully

#### 3.4 Create Visual Generation Page (Frontend)
- [ ] Create `frontend/app/session/[id]/visual-generation/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams, useRouter } from 'next/navigation';
  import { useWebSocket } from '@/lib/useWebSocket';
  import apiClient from '@/lib/api';

  export default function VisualGenerationPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = parseInt(params.id as string);

    const { messages } = useWebSocket(sessionId);
    const [visuals, setVisuals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [totalCost, setTotalCost] = useState(0);

    useEffect(() => {
      // Trigger visual generation on mount
      const script = JSON.parse(localStorage.getItem(`script_${sessionId}`) || '[]');

      if (script.length > 0) {
        apiClient.post(`/api/visuals/generate/${sessionId}`, script)
          .catch(err => console.error('Failed to start visual generation:', err));
      }
    }, [sessionId]);

    useEffect(() => {
      // Listen for visual generation completion
      const visualMessage = messages.find(m => m.stage === 'visual_generation' && m.status === 'complete');
      if (visualMessage) {
        setVisuals(visualMessage.data.visuals);
        setTotalCost(visualMessage.data.total_cost);
        setLoading(false);
      }
    }, [messages]);

    const handleContinue = () => {
      localStorage.setItem(`visuals_${sessionId}`, JSON.stringify(visuals));
      router.push(`/session/${sessionId}/visual-review`);
    };

    if (loading) {
      return (
        <div className="min-h-screen bg-gray-50 p-8">
          <h1 className="text-3xl font-bold mb-6">Generating Visuals...</h1>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
              <span>Creating educational visuals...</span>
            </div>
            <div className="space-y-2 text-sm text-gray-600">
              {messages.filter(m => m.stage === 'visual_generation').map((msg, i) => (
                <div key={i}>{msg.message}</div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Visuals Generated!</h1>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Generation Summary</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-600">Total Visuals</div>
              <div className="text-2xl font-bold">{visuals.length}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Templates Used</div>
              <div className="text-2xl font-bold">
                {visuals.filter(v => v.type === 'template').length}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Total Cost</div>
              <div className="text-2xl font-bold">${totalCost.toFixed(2)}</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          {visuals.map((visual, index) => (
            <div key={index} className="bg-white p-4 rounded-lg shadow">
              <div className="aspect-video bg-gray-100 rounded mb-3">
                {visual.url && visual.url.startsWith('http') && (
                  <img src={visual.url} alt={`Visual ${index + 1}`} className="w-full h-full object-cover rounded" />
                )}
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className={`px-2 py-1 rounded ${visual.type === 'template' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                  {visual.type === 'template' ? 'Template' : 'AI Generated'}
                </span>
                <span className="text-gray-600">
                  ${visual.cost.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={handleContinue}
          className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 text-lg font-medium"
        >
          Continue to Visual Review →
        </button>
      </div>
    );
  }
  ```

**Dependencies:** Tasks 3.3, Phase 03
**Testing:** Navigate to page after script approval

---

## Phase Checklist

**Before moving to Phase 06, verify:**

- [ ] Template matcher finds appropriate templates
- [ ] PSD customizer adds text to templates
- [ ] DALL-E 3 generates educational images
- [ ] Visual Pipeline Agent generates mix of templates and AI images
- [ ] At least 60% of visuals use templates
- [ ] Visuals saved to database as Assets
- [ ] WebSocket sends progress updates during generation
- [ ] Frontend displays visual generation progress
- [ ] Generated visuals display in grid
- [ ] Cost breakdown shows template vs AI costs
- [ ] Navigation to visual review works

---

## Completion Status

**Total Tasks:** 28
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Template usage target: 60%+ to minimize costs
- DALL-E 3 costs $0.04 per image (standard quality)
- Consider implementing image upload to cloud storage (currently local)
- Add retry logic for failed DALL-E generations
- Template customization can be enhanced with full PSD editing (psd-tools library)
- Parallel visual generation can speed up the process
