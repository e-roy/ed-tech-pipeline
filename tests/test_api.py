"""API endpoint tests"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-video-orchestrator"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "ai-video-orchestrator"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_generate_ad_valid_request(client: AsyncClient):
    """Test creating a video generation job with valid request"""
    request_data = {
        "prompt": "Create a 30 second ad for luxury watches",
        "duration": 30,
        "aspect_ratio": "9:16",
        "brand_guidelines": {
            "primary_color": "#D4AF37",
            "secondary_color": "#000000",
            "style": "luxury minimalist",
        },
    }

    response = await client.post("/api/v1/generate-ad", json=request_data)
    assert response.status_code == 201

    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_generate_ad_invalid_duration(client: AsyncClient):
    """Test validation error for invalid duration"""
    request_data = {
        "prompt": "Create a short ad",
        "duration": 5,  # Too short (min is 15)
        "aspect_ratio": "9:16",
    }

    response = await client.post("/api/v1/generate-ad", json=request_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_generate_ad_invalid_aspect_ratio(client: AsyncClient):
    """Test validation error for invalid aspect ratio"""
    request_data = {
        "prompt": "Create a video ad",
        "duration": 30,
        "aspect_ratio": "21:9",  # Invalid ratio
    }

    response = await client.post("/api/v1/generate-ad", json=request_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job_status_not_found(client: AsyncClient):
    """Test getting status for non-existent job"""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get(f"/api/v1/jobs/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_status_after_creation(client: AsyncClient):
    """Test getting status immediately after creating job"""
    # Create job
    request_data = {
        "prompt": "Create a test ad",
        "duration": 30,
        "aspect_ratio": "16:9",
    }

    create_response = await client.post("/api/v1/generate-ad", json=request_data)
    job_id = create_response.json()["job_id"]

    # Get status
    status_response = await client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200

    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "queued"
    assert data["progress"]["percentage"] == 0
    assert data["cost"]["total"] == 0.0
