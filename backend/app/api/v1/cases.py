from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
import uuid
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_user, generate_secure_token
from ...models.user import User, UserRole
from ...models.infection import InfectionCase, PathogenType, TestType, VerificationStatus
from ...schemas.infection import (
    InfectionCaseCreate, InfectionCaseResponse, InfectionCaseUpdate,
    InfectionCaseVerification, CaseListParams
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


def generate_case_number(db: Session) -> str:
    """Generate unique case number"""
    year = datetime.now().year
    month = datetime.now().month

    # Count cases this month
    case_count = db.query(InfectionCase).filter(
        and_(
            InfectionCase.created_at >= datetime(year, month, 1),
            InfectionCase.created_at < datetime(year + (month // 12), (month % 12) + 1, 1)
        )
    ).count()

    return f"CASE-{year}-{month:02d}-{case_count + 1:04d}"


@router.get("/", response_model=List[InfectionCaseResponse])
async def list_infection_cases(
    verification_status: Optional[VerificationStatus] = Query(None),
    pathogen_type: Optional[PathogenType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List infection cases with filtering and pagination"""
    query = db.query(InfectionCase)

    # Apply filters
    if verification_status:
        query = query.filter(InfectionCase.verification_status == verification_status)

    if pathogen_type:
        query = query.filter(InfectionCase.pathogen_type == pathogen_type)

    if date_from:
        query = query.filter(InfectionCase.specimen_collection_date >= date_from)

    if date_to:
        query = query.filter(InfectionCase.specimen_collection_date <= date_to)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                InfectionCase.case_number.ilike(search_term),
                InfectionCase.patient_identifier.ilike(search_term),
                InfectionCase.staff_identifier.ilike(search_term)
            )
        )

    # Apply role-based filtering
    if current_user.role == UserRole.VIEWER:
        # Viewers can only see verified cases
        query = query.filter(InfectionCase.verification_status == VerificationStatus.VERIFIED)

    # Order by creation date (newest first)
    query = query.order_by(desc(InfectionCase.created_at))

    # Apply pagination
    offset = (page - 1) * limit
    cases = query.offset(offset).limit(limit).all()

    return [InfectionCaseResponse.from_orm(case) for case in cases]


@router.post("/", response_model=InfectionCaseResponse)
async def create_infection_case(
    case_data: InfectionCaseCreate,
    current_user: User = Depends(require_role(UserRole.ICT_MEMBER)),
    db: Session = Depends(get_db)
):
    """Create new infection case"""
    # Generate case number
    case_number = generate_case_number(db)

    # Create new case
    new_case = InfectionCase(
        case_number=case_number,
        patient_identifier=case_data.patient_identifier,
        staff_identifier=case_data.staff_identifier,
        pathogen_type=case_data.pathogen_type,
        test_type=case_data.test_type,
        specimen_collection_date=case_data.specimen_collection_date,
        symptom_onset_date=case_data.symptom_onset_date,
        tek_lookback_days=case_data.tek_lookback_days,
        notes=case_data.notes,
        verification_status=VerificationStatus.PENDING
    )

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return InfectionCaseResponse.from_orm(new_case)


@router.get("/{case_id}", response_model=InfectionCaseResponse)
async def get_infection_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific infection case details"""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid case ID format"
        )

    case = db.query(InfectionCase).filter(InfectionCase.id == case_uuid).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection case not found"
        )

    # Apply role-based access
    if current_user.role == UserRole.VIEWER and case.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access unverified cases"
        )

    return InfectionCaseResponse.from_orm(case)


@router.put("/{case_id}", response_model=InfectionCaseResponse)
async def update_infection_case(
    case_id: str,
    case_data: InfectionCaseUpdate,
    current_user: User = Depends(require_role(UserRole.ICT_MEMBER)),
    db: Session = Depends(get_db)
):
    """Update infection case"""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid case ID format"
        )

    case = db.query(InfectionCase).filter(InfectionCase.id == case_uuid).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection case not found"
        )

    # Prevent updates to verified cases (only admins can do this)
    if case.verification_status == VerificationStatus.VERIFIED and current_user.role != UserRole.ICT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify verified cases"
        )

    # Update fields
    update_data = case_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    return InfectionCaseResponse.from_orm(case)


@router.post("/{case_id}/verify", response_model=InfectionCaseResponse)
async def verify_infection_case(
    case_id: str,
    verification_data: InfectionCaseVerification,
    current_user: User = Depends(require_role(UserRole.ICT_MEMBER)),
    db: Session = Depends(get_db)
):
    """Verify or reject infection case"""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid case ID format"
        )

    case = db.query(InfectionCase).filter(InfectionCase.id == case_uuid).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection case not found"
        )

    if case.verification_status != VerificationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case has already been verified or rejected"
        )

    # Update verification status
    case.verification_status = verification_data.verification_status
    case.verified_by = current_user.id
    case.verified_at = datetime.utcnow()

    if verification_data.notes:
        case.notes = verification_data.notes

    db.commit()
    db.refresh(case)

    return InfectionCaseResponse.from_orm(case)


@router.delete("/{case_id}")
async def delete_infection_case(
    case_id: str,
    current_user: User = Depends(require_role(UserRole.ICT_ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete infection case (admin only)"""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid case ID format"
        )

    case = db.query(InfectionCase).filter(InfectionCase.id == case_uuid).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection case not found"
        )

    # Soft delete by marking as inactive or actually delete
    # For this implementation, we'll actually delete
    db.delete(case)
    db.commit()

    return {"message": "Infection case deleted successfully"}


@router.get("/{case_id}/exists")
async def check_case_exists(
    case_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if case number exists"""
    case = db.query(InfectionCase).filter(InfectionCase.case_number == case_number).first()
    return {"exists": case is not None}