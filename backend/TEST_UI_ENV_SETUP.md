# Test UI Environment Variables Setup

## Minimum Required (Basic Test UI)

To just **create scripts** and test the UI interface, you only need:

```env
# Database (required for saving scripts)
DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
```

## Full Functionality

To use **all features** of the test UI, you need:

### Required for Script Creation
```env
DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
```

### Required for Audio Generation
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Required for Image Generation
```env
REPLICATE_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Optional (for S3 uploads - files work locally without this)
```env
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-2
```

### Optional (has defaults, only change if needed)
```env
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:3000
DEBUG=True
```

## Complete .env Example

Create a `.env` file in the `backend/` directory:

```env
# Database (REQUIRED for script creation)
DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline

# OpenAI (REQUIRED for audio generation)
OPENAI_API_KEY=sk-your-openai-key-here

# Replicate (REQUIRED for image generation)
REPLICATE_API_KEY=r8_your-replicate-key-here

# AWS S3 (OPTIONAL - files work locally without this)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=pipeline-backend-assets
AWS_REGION=us-east-2

# JWT (OPTIONAL - has default)
JWT_SECRET_KEY=dev-secret-key-change-in-production

# Frontend (OPTIONAL - has default)
FRONTEND_URL=http://localhost:3000
DEBUG=True
```

## What Works Without Each Key

| Feature | What You Need |
|---------|---------------|
| ✅ Create Scripts | `DATABASE_URL` only |
| ❌ Generate Audio | `OPENAI_API_KEY` required |
| ❌ Generate Images | `REPLICATE_API_KEY` required |
| ❌ Compose Videos | FFmpeg installed (separate from .env) |
| ⚠️ S3 Uploads | AWS credentials (optional - files work locally) |

## Test UI Endpoints Used

1. **`POST /api/test/save-script`** - Only needs database
2. **`POST /api/generate-audio`** - Needs `OPENAI_API_KEY`
3. **`POST /api/generate-images`** - Needs `REPLICATE_API_KEY`
4. **`POST /api/compose-video`** - Needs FFmpeg (not in .env)

## Quick Start

1. **Minimum setup** (just to see the UI work):
   ```env
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
   ```

2. **For audio generation**:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **For image generation**:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
   REPLICATE_API_KEY=r8_your-key-here
   ```

4. **For everything**:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/gauntlet_pipeline
   OPENAI_API_KEY=sk-your-key-here
   REPLICATE_API_KEY=r8_your-key-here
   ```

## Notes

- The server will start without API keys, but those features won't work
- You'll see warnings like "OPENAI_API_KEY not set" - this is normal
- Audio/image generation will fail gracefully with error messages
- S3 uploads are optional - files are returned directly to the browser if S3 isn't configured

