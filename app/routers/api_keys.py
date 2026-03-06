"""API Key management routes.

This module provides API endpoints for managing API keys.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey


router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Name for the API key")


class ApiKeyResponse(BaseModel):
    """Response model for API key (without the actual key)."""
    id: str
    name: str
    key_preview: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Response model for creating an API key (includes the actual key once)."""
    id: str
    name: str
    key: str  # The actual API key - only returned once!
    key_preview: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    """Response model for listing API keys."""
    items: list[ApiKeyResponse]


def generate_api_key() -> str:
    """Generate a secure random API key."""
    # Generate 32 bytes of randomness, base64 encoded
    random_part = secrets.token_urlsafe(32)
    return f"dailynews_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


def create_key_preview(key: str) -> str:
    """Create a preview of the API key (first 4 + **** + last 4)."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


@router.post("", response_model=ApiKeyCreateResponse)
def create_api_key(
    request: ApiKeyCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new API key.

    The actual API key is only returned once in this response.
    Make sure to copy and save it securely - it cannot be retrieved later!
    """
    # Generate a new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_preview = create_key_preview(api_key)

    # Create database record
    db_key = ApiKey(
        name=request.name,
        key_hash=key_hash,
        key_preview=key_preview,
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)

    return ApiKeyCreateResponse(
        id=db_key.id,
        name=db_key.name,
        key=api_key,  # Only returned once!
        key_preview=db_key.key_preview,
        created_at=db_key.created_at,
        is_active=db_key.is_active,
    )


@router.get("", response_model=ApiKeyListResponse)
def list_api_keys(
    db: Session = Depends(get_db),
):
    """List all API keys (without the actual key values)."""
    keys = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return ApiKeyListResponse(items=keys)


@router.delete("/{key_id}", response_model=dict)
def delete_api_key(
    key_id: str,
    db: Session = Depends(get_db),
):
    """Delete an API key."""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(key)
    db.commit()

    return {"message": "API key deleted successfully"}


@router.post("/{key_id}/revoke", response_model=ApiKeyResponse)
def revoke_api_key(
    key_id: str,
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    db.commit()
    db.refresh(key)

    return key


def verify_api_key(db: Session, api_key: str) -> Optional[ApiKey]:
    """
    Verify an API key and update last_used_at.

    Args:
        db: Database session
        api_key: The API key to verify

    Returns:
        ApiKey object if valid and active, None otherwise
    """
    key_hash = hash_api_key(api_key)
    db_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()

    if db_key:
        # Update last used timestamp
        db_key.last_used_at = datetime.now(timezone.utc)
        db.commit()

    return db_key
