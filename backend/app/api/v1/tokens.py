from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.security import (
    get_current_user, generate_verification_token, hash_token,
    verify_token_hash
)
from ...core.config import settings
from ...models.user import User, UserRole
from ...models.infection import (
    InfectionCase, VerificationToken, TokenType, DeliveryMethod,
    TEKUpload, UploadStatus, VerificationStatus
)
from ...schemas.infection import (
    TokenCreate, TokenResponse, TokenStatusResponse, TEKUploadResponse
)

router = APIRouter()


def require_role(required_role: UserRole):
    """Dependency to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ICT_MEMBER: 2,
            UserRole.ICT_ADMIN: 3
        }

        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


@router.get("/", response_model=List[TokenResponse])
async def list_verification_tokens(
    infection_case_id: Optional[str] = Query(None),
    token_type: Optional[TokenType] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List verification tokens with filtering"""
    query = db.query(VerificationToken)

    # Apply filters
    if infection_case_id:
        try:
            case_uuid = uuid.UUID(infection_case_id)
            query = query.filter(VerificationToken.infection_case_id == case_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid infection case ID format"
            )

    if token_type:
        query = query.filter(VerificationToken.token_type == token_type)

    if is_active is not None:
        query = query.filter(VerificationToken.is_active == is_active)

    # Order by creation date (newest first)
    query = query.order_by(desc(VerificationToken.issued_at))

    # Apply pagination
    offset = (page - 1) * limit
    tokens = query.offset(offset).limit(limit).all()

    return [TokenResponse.from_orm(token) for token in tokens]


@router.post("/", response_model=TokenResponse)
async def create_verification_token(
    token_data: TokenCreate,
    current_user: User = Depends(require_role(UserRole.ICT_MEMBER)),
    db: Session = Depends(get_db)
):
    """Create new verification token"""
    # Validate infection case
    try:
        case_uuid = uuid.UUID(token_data.infection_case_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid infection case ID format"
        )

    infection_case = db.query(InfectionCase).filter(
        InfectionCase.id == case_uuid
    ).first()

    if not infection_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection case not found"
        )

    # Only allow tokens for verified cases
    if infection_case.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only generate tokens for verified infection cases"
        )

    # Generate secure token
    token_value = generate_verification_token()
    expires_at = datetime.utcnow() + timedelta(hours=token_data.expires_hours)

    # Create token record
    new_token = VerificationToken(
        infection_case_id=case_uuid,
        token_value=token_value,
        token_type=token_data.token_type,
        delivery_method=token_data.delivery_method,
        delivery_address=token_data.delivery_address,
        expires_at=expires_at,
        created_by=current_user.id
    )

    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    # TODO: Implement actual delivery based on method
    # For now, we'll just return the token for manual delivery

    return TokenResponse.from_orm(new_token)


@router.get("/{token_id}", response_model=TokenResponse)
async def get_verification_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific verification token details"""
    try:
        token_uuid = uuid.UUID(token_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token ID format"
        )

    token = db.query(VerificationToken).filter(
        VerificationToken.id == token_uuid
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification token not found"
        )

    return TokenResponse.from_orm(token)


@router.post("/{token_id}/revoke")
async def revoke_verification_token(
    token_id: str,
    current_user: User = Depends(require_role(UserRole.ICT_MEMBER)),
    db: Session = Depends(get_db)
):
    """Revoke verification token"""
    try:
        token_uuid = uuid.UUID(token_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token ID format"
        )

    token = db.query(VerificationToken).filter(
        VerificationToken.id == token_uuid
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification token not found"
        )

    if not token.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is already inactive"
        )

    token.is_active = False
    db.commit()

    return {"message": "Verification token revoked successfully"}


@router.get("/{token_id}/status", response_model=TokenStatusResponse)
async def get_token_status(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get verification token status and upload information"""
    try:
        token_uuid = uuid.UUID(token_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid token ID format"
        )

    token = db.query(VerificationToken).filter(
        VerificationToken.id == token_uuid
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification token not found"
        )

    # Get related TEK uploads
    uploads = db.query(TEKUpload).filter(
        TEKUpload.verification_token_id == token_uuid
    ).all()

    upload_data = [
        {
            "id": str(upload.id),
            "status": upload.upload_status,
            "tek_count": upload.tek_count,
            "uploaded_at": upload.uploaded_at,
            "error_message": upload.error_message
        }
        for upload in uploads
    ]

    return TokenStatusResponse(
        id=str(token.id),
        is_active=token.is_active,
        used_at=token.used_at,
        used_by=token.used_by,
        tek_uploads=upload_data
    )


@router.post("/validate/{token_value}")
async def validate_verification_token(
    token_value: str,
    db: Session = Depends(get_db)
):
    """Validate verification token (public endpoint for mobile app)"""
    token = db.query(VerificationToken).filter(
        and_(
            VerificationToken.token_value == token_value,
            VerificationToken.is_active == True,
            VerificationToken.expires_at > datetime.utcnow()
        )
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )

    return {
        "valid": True,
        "token_type": token.token_type,
        "infection_case_id": str(token.infection_case_id),
        "expires_at": token.expires_at
    }


@router.post("/use/{token_value}")
async def use_verification_token(
    token_value: str,
    used_by: str,
    db: Session = Depends(get_db)
):
    """Mark verification token as used (public endpoint for mobile app)"""
    token = db.query(VerificationToken).filter(
        and_(
            VerificationToken.token_value == token_value,
            VerificationToken.is_active == True,
            VerificationToken.expires_at > datetime.utcnow()
        )
    ).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )

    if token.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used"
        )

    # Mark token as used
    token.used_at = datetime.utcnow()
    token.used_by = used_by
    token.is_active = False  # Single-use token

    # Create TEK upload record
    tek_upload = TEKUpload(
        verification_token_id=token.id,
        upload_status=UploadStatus.PENDING,
        retention_expires_at=datetime.utcnow() + timedelta(days=settings.TEK_RETENTION_DAYS)
    )

    db.add(tek_upload)
    db.commit()

    return {
        "message": "Token used successfully",
        "upload_id": str(tek_upload.id),
        "retention_expires_at": tek_upload.retention_expires_at
    }