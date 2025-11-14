"""API Routes"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    GenerateAdRequest,
    GenerateAdResponse,
    JobStatusResponse,
    HealthResponse,
    ProgressResponse,
    CostBreakdown,
    VideoResult,
    ErrorDetails,
)
from app.config import settings
from app.database import get_db, engine
from app.models.job import Job

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        db_status = "connected"
        status = "healthy"
    except Exception:
        db_status = "disconnected"
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service=settings.service_name,
        version=settings.version,
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@router.post("/api/v1/generate-ad", response_model=GenerateAdResponse, status_code=201)
async def generate_ad(
    request: GenerateAdRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new video generation job"""
    # Create job in database
    job = Job(
        status="queued",
        prompt=request.prompt,
        duration=request.duration,
        aspect_ratio=request.aspect_ratio,
        brand_guidelines=request.brand_guidelines.model_dump() if request.brand_guidelines else None,
        stages_completed=[],
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # TODO: Add background task to process job
    # background_tasks.add_task(process_job, job.id)

    # Estimate completion time (5 minutes for 30-second ad)
    estimated_time = datetime.utcnow() + timedelta(minutes=5)

    return GenerateAdResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        estimated_completion_time=estimated_time,
    )


@router.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get job status and results"""
    # Query job from database
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build progress response
    all_stages = ["prompt_parsing", "image_generation", "video_generation", "composition"]
    completed_stages = job.stages_completed or []
    remaining_stages = [s for s in all_stages if s not in completed_stages]

    progress = ProgressResponse(
        current_stage=job.current_stage,
        stages_completed=completed_stages,
        stages_remaining=remaining_stages,
        percentage=job.progress_percentage,
    )

    # Build cost breakdown
    cost = CostBreakdown(
        prompt_parsing=job.cost_prompt_parsing,
        image_generation=job.cost_image_generation,
        video_generation=job.cost_video_generation,
        composition=job.cost_composition,
        total=job.cost_total,
    )

    # Build result if completed
    result_data = None
    if job.result:
        result_data = VideoResult(**job.result)

    # Build error if failed
    error_data = None
    if job.error:
        error_data = ErrorDetails(**job.error)

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=progress,
        cost=cost,
        result=result_data,
        error=error_data,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        failed_at=job.failed_at,
    )
