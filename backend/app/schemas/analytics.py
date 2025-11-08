from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class AlertType(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class RiskAlertResponse(BaseModel):
    id: str
    alert_type: AlertType
    exposure_count: int
    location_identifier: str
    time_window_start: datetime
    time_window_end: datetime
    detection_algorithm: str
    confidence_score: float
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000)


class KPIMetrics(BaseModel):
    # Alert metrics
    total_alerts_24h: int = 0
    high_risk_alerts_24h: int = 0
    moderate_risk_alerts_24h: int = 0
    low_risk_alerts_24h: int = 0
    total_alerts_7d: int = 0
    total_alerts_30d: int = 0

    # Compliance metrics
    tek_upload_compliance_rate: float = 0.0
    average_upload_delay_hours: float = 0.0
    token_usage_rate: float = 0.0

    # Case metrics
    total_active_cases: int = 0
    new_cases_24h: int = 0
    new_cases_7d: int = 0
    new_cases_30d: int = 0

    # Pathogen distribution
    pathogen_distribution: Dict[str, int] = {}

    # Timestamp
    last_updated: datetime


class AnalyticsSnapshotResponse(BaseModel):
    id: str
    snapshot_date: date
    total_alerts_24h: int
    high_risk_alerts_24h: int
    moderate_risk_alerts_24h: int
    low_risk_alerts_24h: int
    tek_upload_compliance_rate: float
    total_active_cases: int
    new_cases_24h: int
    additional_metrics: Optional[Dict[str, Any]]
    calculated_at: datetime

    class Config:
        from_attributes = True


class SystemHealthResponse(BaseModel):
    id: str
    service_name: str
    status: ServiceStatus
    response_time_ms: Optional[int]
    last_check: datetime
    error_count: int
    uptime_percentage: float
    details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class TrendData(BaseModel):
    date: date
    value: float
    metadata: Optional[Dict[str, Any]] = None


class TrendResponse(BaseModel):
    metric_name: str
    metric_type: str  # count, percentage, time
    time_period: str  # 7d, 30d, 90d
    data: List[TrendData]


class ClusterData(BaseModel):
    cluster_id: str
    location_identifier: str
    alert_count: int
    risk_level: AlertType
    time_window_start: datetime
    time_window_end: datetime
    confidence_score: float


class ClusterAnalysisResponse(BaseModel):
    total_clusters: int
    high_risk_clusters: int
    moderate_risk_clusters: int
    low_risk_clusters: int
    clusters: List[ClusterData]
    analysis_period: str


class HeatmapData(BaseModel):
    location_identifier: str
    alert_count: int
    risk_level: AlertType
    timestamp: datetime
    confidence_score: float


class HeatmapResponse(BaseModel):
    data: List[HeatmapData]
    time_range_start: datetime
    time_range_end: datetime
    location_count: int
    total_alerts: int


class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class AnalyticsParams(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    pathogen_type: Optional[str] = None
    location: Optional[str] = None
    risk_level: Optional[AlertType] = None


class DashboardOverview(BaseModel):
    kpi_metrics: KPIMetrics
    recent_alerts: List[RiskAlertResponse]
    system_health: List[SystemHealthResponse]
    pending_cases: int
    recent_activity: List[Dict[str, Any]]


class ComplianceTrend(BaseModel):
    date: date
    compliance_rate: float
    total_cases: int
    successful_uploads: int


class PathogenStats(BaseModel):
    pathogen_type: str
    total_cases: int
    active_cases: int
    percentage: float
    trend: str  # increasing, decreasing, stable