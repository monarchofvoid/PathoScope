from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class PathogenType(str, Enum):
    MDR_TB = "MDR_TB"
    CRE = "CRE"
    MRSA = "MRSA"
    VRE = "VRE"
    CANDIDA_AURIS = "Candida_Auris"
    OTHER = "Other"


class TestType(str, Enum):
    PCR = "PCR"
    CULTURE = "Culture"
    RAPID_MOLECULAR = "Rapid_Molecular"
    ANTIGEN = "Antigen"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class InfectionCaseBase(BaseModel):
    patient_identifier: str = Field(..., min_length=1, max_length=255)
    staff_identifier: Optional[str] = Field(None, max_length=255)
    pathogen_type: PathogenType
    test_type: TestType
    specimen_collection_date: datetime
    symptom_onset_date: Optional[datetime]
    tek_lookback_days: int = Field(default=14, ge=1, le=30)
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('symptom_onset_date')
    def validate_symptom_date(cls, v, values):
        if v and 'specimen_collection_date' in values:
            if v > values['specimen_collection_date']:
                raise ValueError('Symptom onset date cannot be after specimen collection date')
        return v

    @validator('tek_lookback_days')
    def validate_lookback_days(cls, v, values):
        if 'pathogen_type' in values:
            # Set default lookback days based on pathogen type
            pathogen_lookbacks = {
                PathogenType.MDR_TB: 21,
                PathogenType.CRE: 14,
                PathogenType.MRSA: 14,
                PathogenType.VRE: 14,
                PathogenType.CANDIDA_AURIS: 30,
                PathogenType.OTHER: 14
            }
            return pathogen_lookbacks.get(values['pathogen_type'], 14)
        return v


class InfectionCaseCreate(InfectionCaseBase):
    pass


class InfectionCaseUpdate(BaseModel):
    pathogen_type: Optional[PathogenType] = None
    test_type: Optional[TestType] = None
    specimen_collection_date: Optional[datetime] = None
    symptom_onset_date: Optional[datetime] = None
    tek_lookback_days: Optional[int] = Field(None, ge=1, le=30)
    notes: Optional[str] = Field(None, max_length=1000)


class InfectionCaseResponse(InfectionCaseBase):
    id: str
    case_number: str
    verification_status: VerificationStatus
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InfectionCaseVerification(BaseModel):
    verification_status: VerificationStatus
    notes: Optional[str] = Field(None, max_length=1000)


class TokenType(str, Enum):
    TEK_UPLOAD = "tek_upload"
    FOLLOW_UP = "follow_up"


class DeliveryMethod(str, Enum):
    HIS_SYSTEM = "his_system"
    SMS = "sms"
    EMAIL = "email"


class TokenCreate(BaseModel):
    infection_case_id: str
    token_type: TokenType = TokenType.TEK_UPLOAD
    delivery_method: DeliveryMethod
    delivery_address: str = Field(..., min_length=1, max_length=255)
    expires_hours: int = Field(default=72, ge=1, le=168)  # 1 hour to 7 days


class TokenResponse(BaseModel):
    id: str
    token_value: str
    token_type: TokenType
    delivery_method: DeliveryMethod
    delivery_address: str
    issued_at: datetime
    expires_at: datetime
    is_active: bool
    infection_case: InfectionCaseResponse

    class Config:
        from_attributes = True


class TokenStatusResponse(BaseModel):
    id: str
    is_active: bool
    used_at: Optional[datetime]
    used_by: Optional[str]
    tek_uploads: list[dict]

    class Config:
        from_attributes = True


class UploadStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TEKUploadResponse(BaseModel):
    id: str
    verification_token_id: str
    upload_status: UploadStatus
    tek_count: int
    uploaded_at: Optional[datetime]
    processed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    retention_expires_at: datetime

    class Config:
        from_attributes = True


class ComplianceStats(BaseModel):
    total_cases: int
    tokens_generated: int
    tek_uploads_completed: int
    tek_uploads_pending: int
    tek_uploads_failed: int
    compliance_rate: float
    average_upload_delay_hours: float


class CaseListParams(BaseModel):
    verification_status: Optional[VerificationStatus] = None
    pathogen_type: Optional[PathogenType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)
    search: Optional[str] = Field(None, max_length=100)