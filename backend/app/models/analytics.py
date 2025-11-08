from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, Text, Float, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..core.database import Base


class AlertType(str, enum.Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ServiceStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    exposure_count = Column(Integer, nullable=False)
    location_identifier = Column(String(255), nullable=False)  # Anonymized location

    # Time window
    time_window_start = Column(DateTime(timezone=True), nullable=False)
    time_window_end = Column(DateTime(timezone=True), nullable=False)

    # Detection details
    detection_algorithm = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)

    # Acknowledgment
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)

    # Alert metrics (24h)
    total_alerts_24h = Column(Integer, default=0)
    high_risk_alerts_24h = Column(Integer, default=0)
    moderate_risk_alerts_24h = Column(Integer, default=0)
    low_risk_alerts_24h = Column(Integer, default=0)

    # Compliance metrics
    tek_upload_compliance_rate = Column(Float, default=0.0)
    total_active_cases = Column(Integer, default=0)
    new_cases_24h = Column(Integer, default=0)

    # Additional metrics (stored as JSON for flexibility)
    additional_metrics = Column(JSONB, nullable=True)

    # Timestamp
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Service details
    service_name = Column(String(100), nullable=False)
    status = Column(SQLEnum(ServiceStatus), nullable=False)

    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    last_check = Column(DateTime(timezone=True), server_default=func.now())
    error_count = Column(Integer, default=0)
    uptime_percentage = Column(Float, default=100.0)

    # Additional details
    details = Column(JSONB, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KPIData(Base):
    __tablename__ = "kpi_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # KPI identification
    kpi_name = Column(String(100), nullable=False)
    kpi_category = Column(String(50), nullable=False)  # alerts, compliance, cases, system

    # Value and metadata
    kpi_value = Column(Float, nullable=False)
    kpi_unit = Column(String(20), nullable=True)  # count, percentage, time, etc.

    # Time context
    time_period = Column(String(20), nullable=False)  # 24h, 7d, 30d
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Additional context
    metadata = Column(JSONB, nullable=True)