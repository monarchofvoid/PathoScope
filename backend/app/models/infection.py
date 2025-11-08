from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..core.database import Base


class PathogenType(str, enum.Enum):
    MDR_TB = "MDR_TB"
    CRE = "CRE"
    MRSA = "MRSA"
    VRE = "VRE"
    CANDIDA_AURIS = "Candida_Auris"
    OTHER = "Other"


class TestType(str, enum.Enum):
    PCR = "PCR"
    CULTURE = "Culture"
    RAPID_MOLECULAR = "Rapid_Molecular"
    ANTIGEN = "Antigen"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class InfectionCase(Base):
    __tablename__ = "infection_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(20), unique=True, nullable=False, index=True)

    # Patient/Staff identifiers (encrypted in application layer)
    patient_identifier = Column(String(255), nullable=False)
    staff_identifier = Column(String(255), nullable=True)

    # Case details
    pathogen_type = Column(SQLEnum(PathogenType), nullable=False)
    test_type = Column(SQLEnum(TestType), nullable=False)
    specimen_collection_date = Column(DateTime(timezone=True), nullable=False)
    symptom_onset_date = Column(DateTime(timezone=True), nullable=True)

    # Verification
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # TEK configuration
    tek_lookback_days = Column(Integer, default=14, nullable=False)

    # Additional information
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    verifier = relationship("User", foreign_keys=[verified_by], back_populates="verified_cases")
    verification_tokens = relationship("VerificationToken", back_populates="infection_case")


class TokenType(str, enum.Enum):
    TEK_UPLOAD = "tek_upload"
    FOLLOW_UP = "follow_up"


class DeliveryMethod(str, enum.Enum):
    HIS_SYSTEM = "his_system"
    SMS = "sms"
    EMAIL = "email"


class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    infection_case_id = Column(UUID(as_uuid=True), ForeignKey("infection_cases.id"), nullable=False)
    token_value = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(SQLEnum(TokenType), nullable=False)

    # Timestamps
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    used_by = Column(String(255), nullable=True)
    delivery_method = Column(SQLEnum(DeliveryMethod), nullable=False)
    delivery_address = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    infection_case = relationship("InfectionCase", back_populates="verification_tokens")
    created_by_user = relationship("User", back_populates="created_tokens")
    tek_uploads = relationship("TEKUpload", back_populates="verification_token")


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TEKUpload(Base):
    __tablename__ = "tek_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_token_id = Column(UUID(as_uuid=True), ForeignKey("verification_tokens.id"), nullable=False)

    # Upload details
    upload_status = Column(SQLEnum(UploadStatus), default=UploadStatus.PENDING)
    tek_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Retention
    retention_expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    verification_token = relationship("VerificationToken", back_populates="tek_uploads")