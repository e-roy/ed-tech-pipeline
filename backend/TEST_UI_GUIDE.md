# Test UI Quick Start Guide

## Overview

The Test UI (`test_ui.html`) is a **standalone testing interface** for the educational video pipeline. It's a single HTML file that lets you test the complete workflow without running the Next.js frontend.

## Quick Start

### Step 1: Start the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open the Test UI

```bash
open test_ui.html
```

That's it! The Test UI connects to `http://localhost:8000` automatically.

## You Only Need

✅ Backend running  
❌ Frontend Next.js app NOT required

## Complete Workflow

1. **Create Script** - Fill in hook, concept, process, conclusion
2. **Finalize Script** - Generates images + audio in parallel
3. **Compose Video** - Creates final video with AI-generated clips

## Cost Per Video

- Images (4): $0.00 (Flux Schnell - free)
- Audio (4 parts): $0.008 (OpenAI TTS)
- Video clips (4): ~$0.60 (Minimax Gen-4 Turbo)
- **Total: ~$0.61 per video**

## See Full Documentation

For detailed instructions, troubleshooting, and advanced usage, see the inline documentation in `test_ui.html`.
