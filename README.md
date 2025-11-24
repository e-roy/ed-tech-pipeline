# AI Video Generation Orchestrator

Central coordination service for an end-to-end AI video ad generation pipeline. Manages job lifecycle, coordinates microservices, tracks costs, and provides real-time progress updates.

**Competition**: Gauntlet AI Video Generation Challenge
**Category**: Ad Creative Pipeline (Category 2)
**MVP Deadline**: Sunday, Nov 17, 10:59 PM CT
**Final Deadline**: Saturday, Nov 23, 10:59 PM CT

---

## Features

- **Async Job Processing**: FastAPI with background tasks
- **4-Stage Pipeline**: Prompt parsing → Image gen → Video gen (parallel) → Composition
- **Real-Time Progress**: Granular progress updates (0-100%)
- **Cost Tracking**: Itemized breakdown per stage, sub-$2 target
- **Error Handling**: Retry logic with exponential backoff
- **Database Persistence**: PostgreSQL with SQLAlchemy (async)
- **Docker Ready**: Full Docker Compose setup

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for database)
- PostgreSQL 15+ (or use Docker)

### 1. Clone Repository

```bash
git clone https://github.com/Gauntlet-Pipeline/pipeline.git
cd pipeline
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your microservice URLs
# DATABASE_URL, PROMPT_PARSER_URL, IMAGE_GEN_URL, etc.
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4. Start Database

```bash
# Using Docker Compose
docker-compose up -d db

# Or install PostgreSQL locally
```

### 5. Run Application

```bash
# Development mode (auto-reload)
python app/main.py

# Or with uvicorn
uvicorn app.main:app --reload

# Application runs on http://localhost:8000
```

### 6. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Create job
curl -X POST http://localhost:8000/api/v1/generate-ad \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a 30 second luxury watch ad",
    "duration": 30,
    "aspect_ratio": "9:16"
  }'

# Get job status (replace JOB_ID)
curl http://localhost:8000/api/v1/jobs/{JOB_ID}
```

---

## Deployment

### EC2 Production Deployment

Deploy the latest backend code to the production EC2 instance:

```bash
# Deploy to EC2 (runs from your local machine)
./deploy_to_ec2.sh
```

This script will:
1. Pull latest code from GitHub to EC2
2. Update environment configuration
3. Install/update dependencies
4. Restart the backend service
5. Verify deployment health

**Production Backend**: https://api.classclipscohort3.com

**Manual deployment steps:**

```bash
# Get current EC2 IP (IP changes on restart - use ALB URL for API access)
# For SSH, get current IP from AWS Console or use: aws ec2 describe-instances --instance-ids i-051a27d0f69e98ca2 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
# SSH into EC2 (replace IP_ADDRESS with current IP)
ssh -i ~/Downloads/pipeline_orchestrator.pem ec2-user@IP_ADDRESS

# Pull latest code
cd /opt/pipeline
sudo git pull

# Restart service
sudo systemctl restart pipeline-backend

# Check status
sudo systemctl status pipeline-backend

# View logs
sudo journalctl -u pipeline-backend -f
```

### Docker Deployment (Local Development)

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f orchestrator

# Stop services
docker-compose down
```

Services:

- **orchestrator**: API service on port 8000
- **db**: PostgreSQL on port 5432

---

## Project Structure

```
pipeline/
├── app/
│   ├── api/
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Pydantic models
│   ├── core/
│   │   └── orchestrator.py    # Pipeline logic
│   ├── models/
│   │   └── job.py             # Database models
│   ├── services/
│   │   ├── base_client.py     # HTTP client base
│   │   ├── prompt_parser.py   # Prompt Parser client
│   │   ├── image_gen.py       # Image Gen client
│   │   ├── video_gen.py       # Video Gen client (parallel)
│   │   └── composition.py     # Composition client
│   ├── config.py              # Settings
│   ├── database.py            # DB connection
│   └── main.py                # FastAPI app
├── alembic/                   # Database migrations
├── tests/                     # Pytest tests
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Multi-container setup
├── prd.md                     # Product Requirements
├── ARCHITECTURE.md            # Architecture doc
└── README.md                  # This file
```

**Architecture Diagram**: [Workflowy Brainlift Diagram](https://workflowy.com/s/gauntlet-ai-video-ge/DU6xAqfBk5XyIBmS)

---

## API Documentation

### Endpoints

**Health Check**

```
GET /health
Response: 200 OK
{
  "status": "healthy",
  "service": "ai-video-orchestrator",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

**Generate Video Ad**

```
POST /api/v1/generate-ad
Request:
{
  "prompt": "Create a 30 second Instagram ad for luxury watches",
  "duration": 30,
  "aspect_ratio": "9:16",
  "brand_guidelines": {
    "primary_color": "#D4AF37",
    "secondary_color": "#000000",
    "style": "luxury minimalist"
  }
}

Response: 201 Created
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-11-14T10:30:00Z",
  "estimated_completion_time": "2025-11-14T10:35:00Z"
}
```

**Get Job Status**

```
GET /api/v1/jobs/{job_id}
Response: 200 OK
{
  "job_id": "550e8400-...",
  "status": "processing",
  "progress": {
    "current_stage": "video_generation",
    "stages_completed": ["prompt_parsing", "image_generation"],
    "percentage": 60
  },
  "cost": {
    "prompt_parsing": 0.05,
    "image_generation": 0.30,
    "video_generation": 1.20,
    "total": 1.55
  },
  "result": null,
  "error": null
}
```

For complete API spec, see [ARCHITECTURE.md](ARCHITECTURE.md).

**Architecture Diagram**: [Workflowy Brainlift Diagram](https://workflowy.com/s/gauntlet-ai-video-ge/DU6xAqfBk5XyIBmS)

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# View coverage report
open htmlcov/index.html
```

---

## Development

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

```bash
# Lint with ruff
ruff check app/

# Format code
ruff format app/
```

---

## Configuration

Environment variables (see `.env.example`):

| Variable                         | Description                  | Default                    |
| -------------------------------- | ---------------------------- | -------------------------- |
| `DATABASE_URL`                   | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `PROMPT_PARSER_URL`              | Prompt Parser service URL    | `http://localhost:8001`    |
| `IMAGE_GEN_URL`                  | Image Gen service URL        | `http://localhost:8002`    |
| `VIDEO_GEN_URL`                  | Video Gen service URL        | `http://localhost:8003`    |
| `COMPOSITION_URL`                | Composition service URL      | `http://localhost:8004`    |
| `MAX_COST_PER_VIDEO`             | Max cost before job fails    | `10.00`                    |
| `MAX_PARALLEL_VIDEO_GENERATIONS` | Concurrent video clips       | `4`                        |
| `LOG_LEVEL`                      | Logging level                | `INFO`                     |

---

## Pipeline Flow

```
1. POST /api/v1/generate-ad → Create job (status: queued)
2. Background task starts → Update to "processing"
3. Stage 1: Prompt Parser → 20% progress (+$0.05)
4. Stage 2: Image Generation → 35% progress (+$0.30)
5. Stage 3: Video Generation (parallel) → 85% progress (+$1.20)
6. Stage 4: Composition → 100% progress (+$0.10)
7. Mark complete → Return video URL
8. GET /api/v1/jobs/{id} → Poll for status
```

---

## Troubleshooting

**Database connection errors**:

- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running: `docker-compose up db`

**Microservice timeouts**:

- Verify service URLs are correct
- Check service health endpoints
- Increase timeout in `app/config.py`

**Migration errors**:

- Drop and recreate: `alembic downgrade base && alembic upgrade head`
- Or delete DB and restart: `docker-compose down -v && docker-compose up`

---

## Team Integration

### For Frontend Developers

1. Start orchestrator: `docker-compose up`
2. API available at `http://localhost:8000`
3. Use `/api/v1/generate-ad` to create jobs
4. Poll `/api/v1/jobs/{id}` for status (every 2-3 seconds)
5. Display progress percentage and cost in real-time

### For Microservice Developers

Your service must return this format:

```json
{
  "success": true,
  "result": {
    /* your data */
  },
  "cost": 1.25,
  "processing_time": 3.4
}
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed contracts.

---

## Roadmap

### MVP (48 hours) ✅

- [x] API endpoints (health, generate-ad, get-status)
- [x] Database models and migrations
- [x] Microservice clients with retry logic
- [ ] Orchestrator pipeline implementation
- [ ] Integration testing

### Final (8 days)

- [ ] Webhook notifications
- [ ] Metrics endpoint
- [ ] Caching for repeated prompts
- [ ] Performance optimization
- [ ] Comprehensive error handling

---

## License

MIT License - See LICENSE file for details

---

## Contact

**Technical Lead**: [Your Team]
**GitHub**: https://github.com/Gauntlet-Pipeline/pipeline
**Competition**: Gauntlet AI Video Generation Challenge

---

_Built with FastAPI, PostgreSQL, and ❤️_

---
