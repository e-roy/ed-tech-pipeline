# Person B Work - Quick Start Guide

## ⚡ 60-Second Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Add your Replicate API key to .env
echo "REPLICATE_API_KEY=your_key_here" >> .env

# 4. Test it works
python test_agents.py quick
```

**Expected output:**
```
✅ Quick test passed - agents initialized successfully!
```

---

## 🎯 What You Can Do Now

### Test Prompt Parser (FREE - costs $0.001)

```bash
python test_agents.py parser
```

**What it does:** Converts "pink tennis shoes" → 4 detailed prompts

---

### Test Image Generator (costs ~$0.012)

```bash
python test_agents.py generator
```

**What it does:** Generates 1-4 real images using Flux-Schnell

---

### Full Pipeline Test (costs ~$0.02)

```bash
python test_agents.py full
# Type 'yes' to confirm
```

**What it does:** Complete flow: prompt → parse → generate → display

---

## 📁 What Was Built

```
backend/app/agents/
├── base.py                      # Agent interfaces
├── prompt_parser.py             # Prompt Parser Agent
└── batch_image_generator.py    # Image Generator Agent

backend/
├── test_agents.py               # Testing suite
├── PERSON_B_README.md          # Full documentation
└── app/services/orchestrator.py # Integrated with agents
```

---

## 🔌 How to Use in Code

### Quick Example:

```python
from app.agents.prompt_parser import PromptParserAgent
from app.agents.batch_image_generator import BatchImageGeneratorAgent
from app.agents.base import AgentInput
import os

# Get API key
api_key = os.getenv("REPLICATE_API_KEY")

# Initialize agents
parser = PromptParserAgent(api_key)
generator = BatchImageGeneratorAgent(api_key)

# Parse prompt
prompt_input = AgentInput(
    session_id="test-123",
    data={
        "user_prompt": "red sneakers",
        "options": {"num_images": 4}
    }
)
prompt_result = await parser.process(prompt_input)

# Generate images
image_input = AgentInput(
    session_id="test-123",
    data={
        "image_prompts": prompt_result.data["image_prompts"],
        "model": "flux-schnell"
    }
)
image_result = await generator.process(image_input)

# Get results
for img in image_result.data["images"]:
    print(f"Image URL: {img['url']}")
```

---

## 💡 Common Use Cases

### Use Case 1: Test with Different Models

```python
# Fast & cheap (testing)
options = {"model": "flux-schnell"}  # $0.003/image

# High quality (production)
options = {"model": "flux-pro"}      # $0.05/image

# Balanced
options = {"model": "sdxl"}          # $0.01/image
```

### Use Case 2: Custom Number of Images

```python
options = {
    "num_images": 4,      # Generate 4 images
    "model": "flux-schnell"
}
```

### Use Case 3: Add Style Keywords

```python
options = {
    "num_images": 6,
    "style_keywords": ["professional", "studio", "vibrant"]
}
```

---

## 🐛 Troubleshooting

### Problem: "REPLICATE_API_KEY not set"

```bash
# Check if set
cat backend/.env | grep REPLICATE

# If missing, add it
echo "REPLICATE_API_KEY=r8_your_key_here" >> backend/.env
```

### Problem: "Import error"

```bash
# Make sure you're in backend directory
pwd
# Should show: .../pipeline/backend

# Make sure venv is activated
which python
# Should show: .../backend/venv/bin/python
```

### Problem: "Model not found"

Valid models are:
- `flux-schnell` ← Use this for testing
- `flux-dev`
- `flux-pro`
- `sdxl`

---

## 📊 Cost Reference

| Action | Cost | Time |
|--------|------|------|
| Prompt parsing | $0.001 | 2-5s |
| 1 image (flux-schnell) | $0.003 | 5-8s |
| 1 image (flux-pro) | $0.05 | 8-15s |
| Full test (4 images, schnell) | ~$0.02 | 30s |
| Full test (6 images, pro) | ~$0.30 | 90s |

---

## ✅ Verification Checklist

Before claiming "it works":

- [ ] `python test_agents.py quick` passes
- [ ] Can see "✅ agents initialized successfully"
- [ ] Environment variable `REPLICATE_API_KEY` is set
- [ ] Located in `backend/` directory
- [ ] Virtual environment activated

---

## 🚀 Next Steps

### For Backend Team (Person A):
Test orchestrator integration:
```bash
# Start server
uvicorn app.main:app --reload

# In another terminal, test endpoint
curl -X POST http://localhost:8000/api/generate-images \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "pink tennis shoes", "options": {"num_images": 4}}'
```

### For Frontend Team (Person D):
Connect to WebSocket for real-time updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/session-id')
ws.onmessage = (event) => {
  const update = JSON.parse(event.data)
  console.log(update.status, update.progress, update.details)
}
```

---

## 📚 Documentation

- **Quick Summary:** `PERSON_B_SUMMARY.md`
- **Full Details:** `backend/PERSON_B_README.md`
- **Team Breakdown:** `Docs/TEAM_WORK_BREAKDOWN.md`

---

## 💬 Need Help?

1. Check `backend/PERSON_B_README.md` for detailed docs
2. Run `python test_agents.py quick` to verify setup
3. Check Replicate dashboard: https://replicate.com/account
4. Review logs in console output

---

**⚡ That's it! You're ready to generate AI images.**

**Time to complete Person B setup:** ~5 minutes
**Time to test full pipeline:** ~2 minutes (+ API call time)
