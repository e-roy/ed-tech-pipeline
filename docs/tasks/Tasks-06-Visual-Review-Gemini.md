# Phase 06: Visual Review & Gemini Validation (Hours 18-24)

**Timeline:** Day 1, Hours 18-24
**Dependencies:** Phase 05 (Visual Pipeline)
**Completion:** 0% (0/20 tasks complete)

---

## Overview

Implement visual review UI with final approval warning, and integrate Gemini Vision API for frame-by-frame validation against 4 criteria (scientific accuracy, label quality, age-appropriateness, visual clarity).

---

## Tasks

### 1. Visual Review UI (Hours 18-20)

#### 1.1 Create Visual Review Page
- [ ] Create `frontend/app/session/[id]/visual-review/page.tsx`:
  ```typescript
  'use client';
  import { useState, useEffect } from 'react';
  import { useParams, useRouter } from 'next/navigation';

  interface Visual {
    segment_id: string;
    type: string;
    url: string;
    cost: number;
    source: string;
  }

  export default function VisualReviewPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = parseInt(params.id as string);

    const [visuals, setVisuals] = useState<Visual[]>([]);
    const [selectedVisuals, setSelectedVisuals] = useState<Set<number>>(new Set());
    const [showFinalWarning, setShowFinalWarning] = useState(false);

    useEffect(() => {
      const stored = localStorage.getItem(`visuals_${sessionId}`);
      if (stored) {
        const visualsData = JSON.parse(stored);
        setVisuals(visualsData);
        // Pre-select all visuals
        setSelectedVisuals(new Set(visualsData.map((_: any, i: number) => i)));
      }
    }, [sessionId]);

    const toggleVisual = (index: number) => {
      const newSelected = new Set(selectedVisuals);
      if (newSelected.has(index)) {
        newSelected.delete(index);
      } else {
        newSelected.add(index);
      }
      setSelectedVisuals(newSelected);
    };

    const calculateTotalCost = () => {
      return Array.from(selectedVisuals)
        .reduce((sum, index) => sum + visuals[index].cost, 0);
    };

    const handleApprove = () => {
      setShowFinalWarning(true);
    };

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <h1 className="text-3xl font-bold mb-6">Review & Approve Visuals</h1>

        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Final Approval Gate</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Once you approve these visuals, costs will be incurred for:</p>
                <ul className="list-disc ml-5 mt-1">
                  <li>Gemini Vision validation</li>
                  <li>Audio generation</li>
                  <li>Video composition</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Selected Visuals</h2>
              <p className="text-sm text-gray-600">{selectedVisuals.size} of {visuals.length} selected</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Estimated Cost</div>
              <div className="text-2xl font-bold">${calculateTotalCost().toFixed(2)}</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          {visuals.map((visual, index) => (
            <div
              key={index}
              className={`bg-white p-4 rounded-lg shadow cursor-pointer border-2 ${
                selectedVisuals.has(index) ? 'border-blue-500' : 'border-transparent'
              }`}
              onClick={() => toggleVisual(index)}
            >
              <div className="aspect-video bg-gray-100 rounded mb-3 relative">
                {visual.url && visual.url.startsWith('http') && (
                  <img src={visual.url} alt={`Visual ${index + 1}`} className="w-full h-full object-cover rounded" />
                )}
                {selectedVisuals.has(index) && (
                  <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-1">
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className={`px-2 py-1 rounded ${visual.type === 'template' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                  {visual.type === 'template' ? 'Template' : 'AI Generated'}
                </span>
                <span className="text-gray-600">${visual.cost.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={handleApprove}
          disabled={selectedVisuals.size === 0}
          className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 text-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Approve Visuals & Continue →
        </button>

        {showFinalWarning && (
          <FinalApprovalModal
            onConfirm={() => {
              // Store approved visuals
              const approved = Array.from(selectedVisuals).map(i => visuals[i]);
              localStorage.setItem(`approved_visuals_${sessionId}`, JSON.stringify(approved));
              router.push(`/session/${sessionId}/audio-selection`);
            }}
            onCancel={() => setShowFinalWarning(false)}
            estimatedCost={calculateTotalCost()}
          />
        )}
      </div>
    );
  }

  function FinalApprovalModal({ onConfirm, onCancel, estimatedCost }: any) {
    const [confirmed, setConfirmed] = useState(false);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h2 className="text-2xl font-bold mb-4 text-red-600">⚠️ Final Approval</h2>

          <div className="mb-6">
            <p className="mb-4">By clicking "Confirm", you authorize:</p>
            <ul className="list-disc ml-5 space-y-2 text-sm">
              <li>Gemini Vision validation (~$0.50)</li>
              <li>Audio generation (~$0.30)</li>
              <li>Video composition (~$0.20)</li>
            </ul>
            <div className="mt-4 p-3 bg-gray-100 rounded">
              <div className="flex justify-between font-semibold">
                <span>Total Estimated Cost:</span>
                <span>${(estimatedCost + 1.00).toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div className="mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="h-4 w-4"
              />
              <span className="text-sm">I understand costs will be incurred</span>
            </label>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 bg-gray-200 text-gray-800 px-6 py-2 rounded hover:bg-gray-300"
            >
              Go Back
            </button>
            <button
              onClick={onConfirm}
              disabled={!confirmed}
              className="flex-1 bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Confirm & Proceed
            </button>
          </div>
        </div>
      </div>
    );
  }
  ```

**Dependencies:** Phase 05 complete
**Testing:** Navigate to page, verify visuals display

#### 1.2 Test Visual Selection
- [ ] Navigate to visual review page
- [ ] Verify all visuals are pre-selected
- [ ] Click on a visual to deselect
- [ ] Verify cost updates
- [ ] Select visual again
- [ ] Verify selection state persists

**Dependencies:** Task 1.1
**Testing:** Selection logic should work correctly

---

### 2. Gemini Vision Integration (Hours 20-22)

#### 2.1 Install Google AI SDK
- [ ] Add to `backend/requirements.txt`:
  ```
  google-generativeai==0.3.1
  ```
- [ ] Install: `pip install google-generativeai`
- [ ] Add to `.env`:
  ```
  GEMINI_API_KEY=your-google-ai-key
  ```

**Dependencies:** None
**Testing:** Import: `import google.generativeai as genai`

#### 2.2 Create Gemini Vision Validator
- [ ] Create `backend/agents/gemini_validator.py`:
  ```python
  import google.generativeai as genai
  import os
  import time
  import requests
  from PIL import Image
  from io import BytesIO
  import json

  class GeminiVisionValidator:
      def __init__(self):
          genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
          self.model = genai.GenerativeModel('gemini-1.5-pro-vision')

      async def validate_image(self, image_url: str, context: dict) -> dict:
          """
          Validate image against 4 criteria
          Args:
              image_url: URL to image
              context: {"narration": "...", "key_concepts": [...], "grade_level": "6-7"}
          Returns:
              {
                  "scientific_accuracy": true/false,
                  "label_quality": true/false,
                  "age_appropriate": true/false,
                  "visual_clarity": true/false,
                  "all_criteria_pass": true/false,
                  "notes": "...",
                  "cost": 0.001,
                  "duration": 1.2
              }
          """
          start_time = time.time()

          try:
              # Download image
              response = requests.get(image_url)
              img = Image.open(BytesIO(response.content))

              # Build validation prompt
              prompt = self._build_validation_prompt(context)

              # Call Gemini Vision
              response = self.model.generate_content([prompt, img])

              # Parse response
              result_text = response.text

              # Try to extract JSON from response
              try:
                  # Look for JSON in response
                  start = result_text.find('{')
                  end = result_text.rfind('}') + 1
                  if start >= 0 and end > start:
                      result_json = json.loads(result_text[start:end])
                  else:
                      # Fallback: parse from text
                      result_json = self._parse_text_response(result_text)
              except:
                  result_json = self._parse_text_response(result_text)

              # Gemini Pro Vision pricing: ~$0.001 per image
              cost = 0.001

              duration = time.time() - start_time

              return {
                  "scientific_accuracy": result_json.get("scientific_accuracy", True),
                  "label_quality": result_json.get("label_quality", True),
                  "age_appropriate": result_json.get("age_appropriate", True),
                  "visual_clarity": result_json.get("visual_clarity", True),
                  "all_criteria_pass": result_json.get("all_criteria_pass", True),
                  "notes": result_json.get("notes", ""),
                  "cost": cost,
                  "duration": duration
              }

          except Exception as e:
              return {
                  "scientific_accuracy": False,
                  "label_quality": False,
                  "age_appropriate": False,
                  "visual_clarity": False,
                  "all_criteria_pass": False,
                  "notes": f"Error: {str(e)}",
                  "cost": 0.0,
                  "duration": time.time() - start_time
              }

      def _build_validation_prompt(self, context: dict) -> str:
          narration = context.get("narration", "")
          concepts = context.get("key_concepts", [])
          grade_level = context.get("grade_level", "6-7")

          return f"""Evaluate this educational image against 4 criteria for a middle school science video (grades {grade_level}).

  Context:
  - Narration: "{narration}"
  - Key Concepts: {', '.join(concepts)}

  Evaluate on these 4 criteria (respond with true/false for each):

  1. **Scientific Accuracy**: Are all scientific facts, diagrams, labels, and representations accurate? No errors or misconceptions?

  2. **Label Quality**: Are labels clear, readable, properly placed, and scientifically correct? No spelling errors?

  3. **Age Appropriate**: Is the visual complexity, vocabulary, and content appropriate for grades {grade_level}? Not too simple or too complex?

  4. **Visual Clarity**: Is the image clear, well-composed, with good contrast and focus on key elements? No clutter or confusion?

  Respond ONLY with valid JSON:
  {{
      "scientific_accuracy": true/false,
      "label_quality": true/false,
      "age_appropriate": true/false,
      "visual_clarity": true/false,
      "all_criteria_pass": true/false,
      "notes": "Brief explanation (one sentence per failed criterion)"
  }}"""

      def _parse_text_response(self, text: str) -> dict:
          """Fallback parser if JSON extraction fails"""
          return {
              "scientific_accuracy": "scientific_accuracy: true" in text.lower() or "scientifically accurate" in text.lower(),
              "label_quality": "label_quality: true" in text.lower() or "labels are clear" in text.lower(),
              "age_appropriate": "age_appropriate: true" in text.lower() or "age-appropriate" in text.lower(),
              "visual_clarity": "visual_clarity: true" in text.lower() or "visually clear" in text.lower(),
              "all_criteria_pass": "all_criteria_pass: true" in text.lower(),
              "notes": text[:200]
          }
  ```

**Dependencies:** Task 2.1
**Testing:** Instantiate: `validator = GeminiVisionValidator()`

#### 2.3 Test Gemini Validation
- [ ] Create test script `backend/test_gemini_validation.py`:
  ```python
  import asyncio
  from agents.gemini_validator import GeminiVisionValidator

  async def test_validation():
      validator = GeminiVisionValidator()

      # Test with a sample image URL (use DALL-E generated image from Phase 05)
      result = await validator.validate_image(
          "https://example.com/sample_image.png",  # Replace with actual URL
          context={
              "narration": "This diagram shows photosynthesis with chloroplasts capturing sunlight",
              "key_concepts": ["photosynthesis", "chloroplast", "sunlight"],
              "grade_level": "6-7"
          }
      )

      print(f"Scientific Accuracy: {result['scientific_accuracy']}")
      print(f"Label Quality: {result['label_quality']}")
      print(f"Age Appropriate: {result['age_appropriate']}")
      print(f"Visual Clarity: {result['visual_clarity']}")
      print(f"All Pass: {result['all_criteria_pass']}")
      print(f"Notes: {result['notes']}")
      print(f"Cost: ${result['cost']:.4f}")

  if __name__ == "__main__":
      asyncio.run(test_validation())
  ```
- [ ] Run test with actual image URL

**Dependencies:** Task 2.2
**Testing:** Should return validation results

---

### 3. Frame-by-Frame Validation (Hours 22-24)

#### 3.1 Create Batch Validation Function
- [ ] Add to `backend/agents/gemini_validator.py`:
  ```python
  async def validate_all_visuals(self, visuals: list, script_segments: list) -> dict:
      """
      Validate all visuals in batch
      Returns: {"validations": [...], "total_cost": 0.01, "duration": 12.3}
      """
      start_time = time.time()
      validations = []
      total_cost = 0.0

      for visual in visuals:
          # Find matching segment
          segment = next((s for s in script_segments if s['id'] == visual.get('segment_id')), None)

          if segment:
              context = {
                  "narration": segment.get("narration", ""),
                  "key_concepts": segment.get("key_concepts", []),
                  "grade_level": "6-7"
              }

              result = await self.validate_image(visual['url'], context)
              validations.append({
                  "visual_url": visual['url'],
                  "segment_id": visual.get('segment_id'),
                  **result
              })
              total_cost += result['cost']

      duration = time.time() - start_time

      return {
          "validations": validations,
          "total_cost": total_cost,
          "duration": duration,
          "pass_rate": sum(1 for v in validations if v['all_criteria_pass']) / len(validations) if validations else 0
      }
  ```

**Dependencies:** Task 2.2
**Testing:** Function added successfully

#### 3.2 Create Validation API Endpoint
- [ ] Create `backend/routes/validation.py`:
  ```python
  from fastapi import APIRouter, BackgroundTasks, Depends
  from sqlalchemy.orm import Session as DBSession
  from models.database import SessionLocal, Session, Asset, GeminiValidation
  from agents.gemini_validator import GeminiVisionValidator
  from utils.websocket_manager import ws_manager
  from routes.sessions import get_current_user_id, get_db

  router = APIRouter(prefix="/api/validation", tags=["validation"])

  async def validate_visuals_task(session_id: int):
      """Background task for Gemini validation"""
      try:
          await ws_manager.send_progress(session_id, {
              "stage": "validation",
              "status": "in_progress",
              "message": "Validating visuals with Gemini Vision..."
          })

          db = SessionLocal()
          validator = GeminiVisionValidator()

          # Get visuals and script
          visuals_assets = db.query(Asset).filter(
              Asset.session_id == session_id,
              Asset.asset_type == "visual"
          ).all()

          script_asset = db.query(Asset).filter(
              Asset.session_id == session_id,
              Asset.asset_type == "script"
          ).first()

          if not visuals_assets or not script_asset:
              raise Exception("Visuals or script not found")

          visuals = [
              {"url": v.url, "segment_id": v.metadata.get("segment_id")}
              for v in visuals_assets
          ]

          script_segments = script_asset.metadata.get("script", {}).get("segments", [])

          # Validate all
          result = await validator.validate_all_visuals(visuals, script_segments)

          # Save validations to database
          for i, validation in enumerate(result['validations']):
              gemini_val = GeminiValidation(
                  asset_id=visuals_assets[i].id,
                  frame_number=0,
                  scientific_accuracy=validation['scientific_accuracy'],
                  label_quality=validation['label_quality'],
                  age_appropriate=validation['age_appropriate'],
                  visual_clarity=validation['visual_clarity'],
                  all_criteria_pass=validation['all_criteria_pass'],
                  notes=validation['notes']
              )
              db.add(gemini_val)

          session = db.query(Session).filter(Session.id == session_id).first()
          session.status = "validated"
          db.commit()

          await ws_manager.send_progress(session_id, {
              "stage": "validation",
              "status": "complete",
              "message": "Validation complete!",
              "data": {
                  "pass_rate": result['pass_rate'],
                  "total_cost": result['total_cost']
              }
          })

          db.close()

      except Exception as e:
          await ws_manager.send_progress(session_id, {
              "stage": "validation",
              "status": "error",
              "message": str(e)
          })

  @router.post("/validate/{session_id}")
  async def validate_visuals(
      session_id: int,
      background_tasks: BackgroundTasks,
      user_id: int = Depends(get_current_user_id)
  ):
      background_tasks.add_task(validate_visuals_task, session_id)
      return {"message": "Validation started", "session_id": session_id}
  ```
- [ ] Register router in `backend/main.py`

**Dependencies:** Tasks 2.2, 3.1
**Testing:** Endpoint registered

#### 3.3 Trigger Validation After Visual Approval
- [ ] Update final approval modal in visual review page to trigger validation:
  ```typescript
  const onConfirm = async () => {
    // Store approved visuals
    const approved = Array.from(selectedVisuals).map(i => visuals[i]);
    localStorage.setItem(`approved_visuals_${sessionId}`, JSON.stringify(approved));

    // Trigger Gemini validation
    try {
      await apiClient.post(`/api/validation/validate/${sessionId}`);
    } catch (error) {
      console.error('Failed to start validation:', error);
    }

    // Navigate to audio selection
    router.push(`/session/${sessionId}/audio-selection`);
  };
  ```

**Dependencies:** Task 3.2
**Testing:** Approval triggers validation

---

## Phase Checklist

**Before moving to Phase 07, verify:**

- [ ] Visual review page displays all generated visuals
- [ ] Visual selection/deselection works
- [ ] Cost calculation updates dynamically
- [ ] Final approval modal displays with warning
- [ ] Checkbox confirmation required before proceeding
- [ ] Gemini Vision API credentials configured
- [ ] Single image validation works
- [ ] Batch validation processes all visuals
- [ ] Validation results saved to database
- [ ] WebSocket sends validation progress
- [ ] Pass rate calculated correctly
- [ ] Navigation to audio selection works

---

## Completion Status

**Total Tasks:** 20
**Completed:** 0
**Percentage:** 0%

**Status:** ⏳ Not Started

---

## Notes

- Gemini Pro Vision costs ~$0.001 per image
- Expected total validation cost: $0.008-0.012 (for 8-12 images)
- Validation typically takes 1-2 seconds per image
- Consider implementing parallel validation for speed
- Store validation results for quality metrics
- Failed validations should trigger regeneration in Phase 08
