"""
Session routes - retrieve session data and cost information.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.database import Session as SessionModel, Asset, GenerationCost, User
from app.routes.auth import get_current_user

router = APIRouter()


# Response models
class AssetInfo(BaseModel):
    id: int
    type: str
    url: str
    approved: bool
    order_index: Optional[int]
    created_at: str


class SessionResponse(BaseModel):
    id: str
    status: str
    prompt: Optional[str]
    video_prompt: Optional[str]
    final_video_url: Optional[str]
    created_at: str
    completed_at: Optional[str]
    assets: List[AssetInfo]


class CostBreakdown(BaseModel):
    service: str
    cost: float
    tokens_used: Optional[int]
    details: Optional[dict]


class CostsResponse(BaseModel):
    session_id: str
    total_cost: float
    breakdown: List[CostBreakdown]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific session.

    Returns session metadata, status, and all associated assets.
    """
    # Query session
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all assets for this session
    assets = db.query(Asset).filter(Asset.session_id == session_id).all()

    # Format assets
    asset_list = [
        AssetInfo(
            id=asset.id,
            type=asset.type,
            url=asset.url,
            approved=asset.approved,
            order_index=asset.order_index,
            created_at=asset.created_at.isoformat() if asset.created_at else None
        )
        for asset in assets
    ]

    return SessionResponse(
        id=session.id,
        status=session.status,
        prompt=session.prompt,
        video_prompt=session.video_prompt,
        final_video_url=session.final_video_url,
        created_at=session.created_at.isoformat() if session.created_at else None,
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        assets=asset_list
    )


@router.get("/{session_id}/costs", response_model=CostsResponse)
async def get_session_costs(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cost breakdown for a specific session.

    Returns total cost and breakdown by service (Replicate, OpenAI, S3, etc.).
    """
    # Verify session exists and belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all costs for this session
    costs = db.query(GenerationCost).filter(
        GenerationCost.session_id == session_id
    ).all()

    # Calculate total
    total = db.query(func.sum(GenerationCost.cost)).filter(
        GenerationCost.session_id == session_id
    ).scalar() or 0.0

    # Format breakdown
    breakdown = [
        CostBreakdown(
            service=cost.service,
            cost=cost.cost,
            tokens_used=cost.tokens_used,
            details=cost.details
        )
        for cost in costs
    ]

    return CostsResponse(
        session_id=session_id,
        total_cost=total,
        breakdown=breakdown
    )


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """
    List all sessions for the current user.

    Supports pagination via limit and offset parameters.
    """
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(
        SessionModel.created_at.desc()
    ).offset(offset).limit(limit).all()

    result = []
    for session in sessions:
        # Get assets for each session
        assets = db.query(Asset).filter(Asset.session_id == session.id).all()
        asset_list = [
            AssetInfo(
                id=asset.id,
                type=asset.type,
                url=asset.url,
                approved=asset.approved,
                order_index=asset.order_index,
                created_at=asset.created_at.isoformat() if asset.created_at else None
            )
            for asset in assets
        ]

        result.append(SessionResponse(
            id=session.id,
            status=session.status,
            prompt=session.prompt,
            video_prompt=session.video_prompt,
            final_video_url=session.final_video_url,
            created_at=session.created_at.isoformat() if session.created_at else None,
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            assets=asset_list
        ))

    return result
