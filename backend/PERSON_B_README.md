# Person B: Image Pipeline Implementation

**Developer:** Agent Developer 1 (Image Pipeline)
**Role:** Implement Prompt Parser and Batch Image Generator agents
**Status:** ✅ COMPLETE
**Hours Invested:** 4-6 hours

---

## 🎯 Deliverables

### ✅ Completed Tasks

1. **Agent Base Interface** (`app/agents/base.py`)
   - `AgentInput` - Standard input model for all agents
   - `AgentOutput` - Standard output model with cost/duration tracking
   - `Agent` Protocol - Interface that all agents implement

2. **Prompt Parser Agent** (`app/agents/prompt_parser.py`)
   - Transforms user prompts into structured image generation prompts
   - Uses Llama 3.1 70B via Replicate
   - Generates consistent prompts for multiple viewing angles
   - Provides visual consistency via seed control
   - Cost: ~$0.001 per parse

3. **Batch Image Generator Agent** (`app/agents/batch_image_generator.py`)
   - Generates multiple images in parallel
   - Supports Flux-Pro, Flux-Dev, Flux-Schnell, SDXL models
   - Handles failures gracefully (continues if some images fail)
   - Cost: $0.003-$0.05 per image depending on model

4. **Orchestrator Integration** (`app/services/orchestrator.py`)
   - Replaced stub `generate_images()` with real agent pipeline
   - Integrated Prompt Parser → Image Generator flow
   - Added cost tracking to database
   - Added WebSocket progress updates for each stage
   - Stores generated images in database

5. **Testing Suite** (`test_agents.py`)
   - Quick initialization test
   - Individual agent tests
   - Full pipeline integration test
   - Multiple test modes for different scenarios

---

## 📁 File Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py              # Agent package exports
│   │   ├── base.py                  # Base agent interfaces
│   │   ├── prompt_parser.py         # Prompt Parser Agent
│   │   └── batch_image_generator.py # Batch Image Generator Agent
│   │
│   └── services/
│       └── orchestrator.py          # Updated with agent integration
│
├── test_agents.py                   # Agent testing suite
├── test_replicate.py                # Replicate API connection test
└── PERSON_B_README.md               # This file
```

---

## 🔧 Setup & Configuration

### Prerequisites

```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Verify dependencies (already installed)
pip list | grep replicate
# Should show: replicate==0.22.0
```

### Environment Variables

Add to `backend/.env`:

```bash
REPLICATE_API_KEY=r8_your_api_key_here
```

Get your API key from: https://replicate.com/account/api-tokens

---

## 🧪 Testing

### Quick Test (Initialization Only)

```bash
cd backend
source venv/bin/activate
python test_agents.py quick
```

**Expected Output:**
```
✅ Initializing Prompt Parser Agent...
   Model: meta/meta-llama-3-70b-instruct

✅ Initializing Batch Image Generator Agent...
   Available models: ['flux-pro', 'flux-dev', 'flux-schnell', 'sdxl']

✅ Quick test passed - agents initialized successfully!
```

### Test Prompt Parser Only

```bash
python test_agents.py parser
```

**What it does:**
- Tests Prompt Parser with "pink tennis shoes"
- Calls Llama 3.1 70B via Replicate
- Generates 4 structured prompts for different angles
- Cost: ~$0.001

### Test Image Generator Only

```bash
python test_agents.py generator
```

**What it does:**
- Tests Batch Image Generator with sample prompts
- Uses Flux-Schnell (fastest/cheapest)
- Generates 1-4 test images
- Cost: ~$0.003-$0.012

### Full Pipeline Test (USES REAL API)

```bash
python test_agents.py full
```

**⚠️ WARNING:** This costs money!
- Runs complete pipeline: Prompt Parser → Image Generator
- Generates 4 real images via Replicate
- Estimated cost: $0.012-$0.20 depending on model

**What it tests:**
1. User prompt → Llama 3.1 → Structured prompts
2. Structured prompts → Flux-Schnell → Generated images
3. Cost tracking and error handling
4. Full integration flow

---

## 💡 Usage Examples

### Example 1: Using Prompt Parser

```python
from app.agents.prompt_parser import PromptParserAgent
from app.agents.base import AgentInput
import os

# Initialize agent
api_key = os.getenv("REPLICATE_API_KEY")
parser = PromptParserAgent(api_key)

# Create input
input_data = AgentInput(
    session_id="session-123",
    data={
        "user_prompt": "red sneakers with black stripes",
        "options": {
            "num_images": 6,
            "style_keywords": ["professional", "athletic"]
        }
    }
)

# Process
result = await parser.process(input_data)

if result.success:
    print(f"Generated {len(result.data['image_prompts'])} prompts")
    print(f"Consistency seed: {result.data['consistency_seed']}")
    print(f"Cost: ${result.cost:.4f}")
```

### Example 2: Using Batch Image Generator

```python
from app.agents.batch_image_generator import BatchImageGeneratorAgent
from app.agents.base import AgentInput

# Initialize agent
generator = BatchImageGeneratorAgent(api_key)

# Create input (using prompts from Prompt Parser)
input_data = AgentInput(
    session_id="session-123",
    data={
        "image_prompts": [
            {
                "prompt": "Professional product photography of red sneakers...",
                "negative_prompt": "blurry, distorted...",
                "view_type": "front",
                "seed": 789456,
                "guidance_scale": 7.5
            }
            # ... more prompts
        ],
        "model": "flux-schnell"  # or "flux-pro", "sdxl"
    }
)

# Process
result = await generator.process(input_data)

if result.success:
    for img in result.data['images']:
        print(f"Generated: {img['url']} ({img['view_type']})")
    print(f"Total cost: ${result.cost:.4f}")
```

### Example 3: Full Pipeline via Orchestrator

```python
from app.services.orchestrator import VideoGenerationOrchestrator
from app.database import get_db

# Initialize orchestrator (happens in main.py)
orchestrator = VideoGenerationOrchestrator(websocket_manager)

# Generate images
result = await orchestrator.generate_images(
    db=db,
    session_id="session-123",
    user_prompt="pink tennis shoes with white laces",
    options={
        "num_images": 6,
        "model": "flux-schnell"
    }
)

if result["status"] == "success":
    print(f"Generated {len(result['images'])} images")
    print(f"Total cost: ${result['total_cost']:.4f}")
    print(f"Category: {result['product_category']}")
```

---

## 🎨 Supported Models

### Image Generation Models

| Model | Speed | Quality | Cost/Image | Best For |
|-------|-------|---------|------------|----------|
| **flux-schnell** | ⚡⚡⚡ Very Fast | Good | $0.003 | Testing, iteration |
| **flux-dev** | ⚡⚡ Fast | Better | $0.025 | Development |
| **flux-pro** | ⚡ Slow | Excellent | $0.05 | Production, demos |
| **sdxl** | ⚡⚡ Fast | Good | $0.01 | Cost-effective production |

### LLM Model (Prompt Parser)

- **meta-llama-3-70b-instruct**: Nearly free (~$0.001 per call)

---

## 📊 Cost Tracking

All costs are automatically tracked in the `generation_costs` database table:

```sql
SELECT agent_name, model_name, cost_usd, duration_seconds
FROM generation_costs
WHERE session_id = 'session-123';
```

**Typical Session Costs:**

| Stage | Agent | Model | Cost | Duration |
|-------|-------|-------|------|----------|
| Prompt Parsing | prompt_parser | llama-3-70b | $0.001 | 2-5s |
| Image Gen (6 images) | image_generator | flux-schnell | $0.018 | 20-40s |
| Image Gen (6 images) | image_generator | flux-pro | $0.30 | 50-80s |

**Total per session:**
- Testing (flux-schnell): ~$0.02
- Production (flux-pro): ~$0.30

---

## 🔍 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**Issue: "REPLICATE_API_KEY not set"**
- Solution: Add API key to `backend/.env`
- Verify: `echo $REPLICATE_API_KEY` (after loading .env)

**Issue: "Model not found"**
- Solution: Check model name spelling
- Valid models: `flux-pro`, `flux-dev`, `flux-schnell`, `sdxl`

**Issue: "Rate limit exceeded"**
- Solution: Wait 1 minute, retry
- Or: Use slower model (flux-schnell → sdxl)

**Issue: "Some images failed to generate"**
- This is normal - agent continues with successful images
- Check `result.data['errors']` for details
- Usually caused by prompt safety filters

---

## 🚀 Integration with Orchestrator

The agents are integrated into the orchestrator's `generate_images()` method:

**Flow:**
1. API receives `POST /api/generate-images`
2. Orchestrator calls Prompt Parser Agent
3. Prompt Parser returns structured prompts + seed
4. Orchestrator calls Batch Image Generator Agent
5. Images generated in parallel via Replicate
6. Results stored in database (`assets` table)
7. Costs tracked in `generation_costs` table
8. WebSocket sends real-time progress updates

**WebSocket Progress Stages:**
- `prompt_parsing` (10%) - Analyzing prompt with AI
- `image_generation` (30%) - Generating N images with AI
- `images_ready` (100%) - All images ready for review

---

## 🎯 Next Steps (Hour 8-12)

### For Person A (Backend Lead):
- [ ] Test orchestrator integration with real API calls
- [ ] Verify database schema matches agent output
- [ ] Test WebSocket progress updates
- [ ] Deploy to staging with Replicate API key

### For Person D (Frontend):
- [ ] Display real-time progress from WebSocket
- [ ] Show generated images in UI
- [ ] Add image selection/approval UI
- [ ] Display cost information

### For Person E (DevOps):
- [ ] Add REPLICATE_API_KEY to Railway environment
- [ ] Monitor API usage and costs
- [ ] Set up error alerting for agent failures

---

## 📝 API Contract

### Input (to orchestrator)

```json
{
  "session_id": "uuid",
  "user_prompt": "pink tennis shoes with white laces",
  "options": {
    "num_images": 6,
    "model": "flux-schnell",
    "style_keywords": ["professional", "studio"]
  }
}
```

### Output (from orchestrator)

```json
{
  "status": "success",
  "session_id": "uuid",
  "images": [
    {
      "url": "https://replicate.delivery/pbxt/...",
      "view_type": "front",
      "seed": 789456,
      "cost": 0.003,
      "duration": 5.2,
      "model": "flux-schnell"
    }
  ],
  "total_cost": 0.019,
  "product_category": "athletic footwear",
  "style_keywords": ["athletic", "professional", "vibrant"]
}
```

---

## ✅ Checkpoint Verification

Before moving to next phase, verify:

- [ ] `python test_agents.py quick` passes
- [ ] Can import agents: `from app.agents import PromptParserAgent, BatchImageGeneratorAgent`
- [ ] Orchestrator has `self.prompt_parser` and `self.image_generator`
- [ ] Database has `generation_costs` table
- [ ] Replicate API key is set in environment

---

## 📚 References

- [Replicate API Docs](https://replicate.com/docs)
- [Flux Model on Replicate](https://replicate.com/black-forest-labs/flux-schnell)
- [Llama 3.1 70B on Replicate](https://replicate.com/meta/meta-llama-3-70b-instruct)
- [PRD Section 4.2-4.3](../Docs/MVP_PRD.md) - Agent specifications

---

**🎉 Person B work complete! Image pipeline ready for integration.**
