"""Settings management routes.

This module provides API endpoints for managing system settings.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database import get_db
from app.models import SystemConfig
from app.services.scheduler import restart_scheduler


router = APIRouter(prefix="/api/settings", tags=["settings"])
logger = logging.getLogger(__name__)


class SettingsResponse(BaseModel):
    """Response model for system settings."""
    fetch_interval_minutes: int
    updated_at: Optional[str] = None


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""
    fetch_interval_minutes: int = Field(
        ...,
        ge=30,
        description="RSS fetch interval in minutes (minimum 30)",
    )

    @field_validator("fetch_interval_minutes")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if v < 30:
            raise ValueError("Fetch interval must be at least 30 minutes")
        return v


class RestartResponse(BaseModel):
    """Response model for restart operation."""
    success: bool
    message: str


# Configuration key for fetch interval
FETCH_INTERVAL_KEY = "fetch_interval_minutes"
DEFAULT_FETCH_INTERVAL_MINUTES = 30  # 30 minutes default


def get_fetch_interval(db: Session) -> int:
    """Get current fetch interval from database or default."""
    value = SystemConfig.get_value(db, FETCH_INTERVAL_KEY, "")
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    return DEFAULT_FETCH_INTERVAL_MINUTES


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get current system settings."""
    interval = get_fetch_interval(db)
    
    # Get last updated time
    config = db.query(SystemConfig).filter(SystemConfig.key == FETCH_INTERVAL_KEY).first()
    updated_at = config.updated_at.isoformat() if config and config.updated_at else None
    
    return SettingsResponse(
        fetch_interval_minutes=interval,
        updated_at=updated_at,
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    request: SettingsUpdate,
    db: Session = Depends(get_db),
):
    """
    Update system settings.
    
    Fetch interval must be at least 30 minutes.
    Changes take effect after restarting the scheduler.
    """
    # Validate minimum interval
    if request.fetch_interval_minutes < 30:
        raise HTTPException(
            status_code=400,
            detail="Fetch interval must be at least 30 minutes",
        )
    
    # Save to database
    config = SystemConfig.set_value(
        db,
        FETCH_INTERVAL_KEY,
        str(request.fetch_interval_minutes),
    )
    
    logger.info(f"Updated fetch interval to {request.fetch_interval_minutes} minutes")
    
    return SettingsResponse(
        fetch_interval_minutes=request.fetch_interval_minutes,
        updated_at=config.updated_at.isoformat() if config.updated_at else None,
    )


@router.post("/restart", response_model=RestartResponse)
def restart_scheduler_endpoint(db: Session = Depends(get_db)):
    """
    Restart the scheduler to apply new settings.
    
    This will stop the current scheduler and start a new one
    with the updated fetch interval.
    """
    try:
        # Get current interval
        interval_minutes = get_fetch_interval(db)
        interval_seconds = interval_minutes * 60
        
        # Restart scheduler
        restart_scheduler(interval_seconds)
        
        logger.info(f"Scheduler restarted with interval {interval_minutes} minutes")
        
        return RestartResponse(
            success=True,
            message=f"Scheduler restarted successfully with {interval_minutes} minute interval",
        )
    except Exception as e:
        logger.error(f"Failed to restart scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart scheduler: {str(e)}",
        )
