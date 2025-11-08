from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User, UserRole, AuditLog
from ...models.infection import (
    InfectionCase, VerificationToken, TEKUpload, VerificationStatus,
    UploadStatus
)
from ...models.analytics import RiskAlert, SystemHealth, AlertType, ServiceStatus
from ...schemas.analytics import (
    DashboardOverview, HeatmapData, HeatmapResponse,
    AuditLogResponse, SystemHealthResponse
)

router = APIRouter()


def get_date_range(days: int) -> tuple[datetime, datetime]:
    """Get date range for last N days"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview data"""
    # Time ranges
    now_24h_ago, now = get_date_range(1)

    # Get recent alerts
    recent_alerts = db.query(RiskAlert).filter(
        RiskAlert.created_at >= now_24h_ago
    ).order_by(desc(RiskAlert.created_at)).limit(10).all()

    # Get system health
    system_health = db.query(SystemHealth).filter(
        SystemHealth.last_check >= now_24h_ago
    ).order_by(desc(SystemHealth.last_check)).all()

    # Count pending cases
    pending_cases = db.query(InfectionCase).filter(
        InfectionCase.verification_status == VerificationStatus.PENDING
    ).count()

    # Get KPI metrics (reuse from analytics)
    from .analytics import get_kpi_metrics
    kpi_metrics = await get_kpi_metrics(current_user, db)

    # Get recent activity from audit logs
    recent_activity = db.query(AuditLog).filter(
        AuditLog.timestamp >= now_24h_ago
    ).order_by(desc(AuditLog.timestamp)).limit(20).all()

    activity_data = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "action": log.action,
            "resource_type": log.resource_type,
            "timestamp": log.timestamp,
            "details": log.details
        }
        for log in recent_activity
    ]

    return DashboardOverview(
        kpi_metrics=kpi_metrics,
        recent_alerts=[
            {
                "id": str(alert.id),
                "alert_type": alert.alert_type.value,
                "exposure_count": alert.exposure_count,
                "location_identifier": alert.location_identifier,
                "created_at": alert.created_at,
                "confidence_score": alert.confidence_score,
                "acknowledged_at": alert.acknowledged_at
            }
            for alert in recent_alerts
        ],
        system_health=[
            SystemHealthResponse.from_orm(health) for health in system_health
        ],
        pending_cases=pending_cases,
        recent_activity=activity_data
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap_data(
    hours_back: int = Query(24, description="Hours of data to include"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get heatmap data for spatial visualization"""
    start_time = datetime.utcnow() - timedelta(hours=hours_back)

    # Get risk alerts within time range
    alerts = db.query(RiskAlert).filter(
        RiskAlert.created_at >= start_time
    ).order_by(RiskAlert.created_at).all()

    heatmap_data = []
    locations = set()

    for alert in alerts:
        locations.add(alert.location_identifier)
        heatmap_data.append(HeatmapData(
            location_identifier=alert.location_identifier,
            alert_count=1,  # Each alert counts as 1 for heatmap intensity
            risk_level=alert.alert_type,
            timestamp=alert.created_at,
            confidence_score=alert.confidence_score
        ))

    return HeatmapResponse(
        data=heatmap_data,
        time_range_start=start_time,
        time_range_end=datetime.utcnow(),
        location_count=len(locations),
        total_alerts=len(alerts)
    )


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    # Get recent system health data
    health_data = db.query(SystemHealth).order_by(
        desc(SystemHealth.last_check)
    ).limit(50).all()

    return [SystemHealthResponse.from_orm(health) for health in health_data]


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    # Join with user to get user names
    query = query.join(User, AuditLog.user_id == User.id)

    # Order by timestamp (newest first)
    query = query.order_by(desc(AuditLog.timestamp))

    # Apply pagination
    offset = (page - 1) * limit
    logs = query.offset(offset).limit(limit).all()

    return [
        AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            user_name=log.user.full_name if log.user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp
        )
        for log in logs
    ]


@router.get("/alerts")
async def get_dashboard_alerts(
    hours_back: int = Query(24, description="Hours of data to include"),
    acknowledged: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get risk alerts for dashboard"""
    start_time = datetime.utcnow() - timedelta(hours=hours_back)

    query = db.query(RiskAlert).filter(
        RiskAlert.created_at >= start_time
    )

    if acknowledged is not None:
        if acknowledged:
            query = query.filter(RiskAlert.acknowledged_at.isnot(None))
        else:
            query = query.filter(RiskAlert.acknowledged_at.is_(None))

    if alert_type:
        try:
            alert_enum = AlertType(alert_type)
            query = query.filter(RiskAlert.alert_type == alert_enum)
        except ValueError:
            pass

    alerts = query.order_by(desc(RiskAlert.created_at)).all()

    return [
        {
            "id": str(alert.id),
            "alert_type": alert.alert_type.value,
            "exposure_count": alert.exposure_count,
            "location_identifier": alert.location_identifier,
            "time_window_start": alert.time_window_start,
            "time_window_end": alert.time_window_end,
            "detection_algorithm": alert.detection_algorithm,
            "confidence_score": alert.confidence_score,
            "acknowledged_by": str(alert.acknowledged_by) if alert.acknowledged_by else None,
            "acknowledged_at": alert.acknowledged_at,
            "notes": alert.notes,
            "created_at": alert.created_at
        }
        for alert in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge a risk alert"""
    try:
        import uuid
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID format"
        )

    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_uuid).first()
    if not alert:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    if alert.acknowledged_at:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert has already been acknowledged"
        )

    # Acknowledge the alert
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    if notes:
        alert.notes = notes

    db.commit()

    return {"message": "Alert acknowledged successfully"}


@router.get("/stats/summary")
async def get_dashboard_stats_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for dashboard"""
    # Time ranges
    now_24h_ago, now = get_date_range(1)
    now_7d_ago, _ = get_date_range(7)

    # Alert stats
    total_alerts_24h = db.query(RiskAlert).filter(
        RiskAlert.created_at >= now_24h_ago
    ).count()

    unacknowledged_alerts = db.query(RiskAlert).filter(
        and_(
            RiskAlert.created_at >= now_24h_ago,
            RiskAlert.acknowledged_at.is_(None)
        )
    ).count()

    # Case stats
    pending_cases = db.query(InfectionCase).filter(
        InfectionCase.verification_status == VerificationStatus.PENDING
    ).count()

    new_cases_24h = db.query(InfectionCase).filter(
        InfectionCase.created_at >= now_24h_ago
    ).count()

    # TEK stats
    tokens_issued_24h = db.query(VerificationToken).filter(
        VerificationToken.issued_at >= now_24h_ago
    ).count()

    tek_uploads_24h = db.query(TEKUpload).filter(
        and_(
            TEKUpload.uploaded_at >= now_24h_ago,
            TEKUpload.upload_status == UploadStatus.COMPLETED
        )
    ).count()

    # System health
    healthy_services = db.query(SystemHealth).filter(
        and_(
            SystemHealth.last_check >= now_1h_ago,
            SystemHealth.status == ServiceStatus.HEALTHY
        )
    ).count()

    total_services = db.query(SystemHealth).filter(
        SystemHealth.last_check >= now_1h_ago
    ).count()

    return {
        "alerts": {
            "total_24h": total_alerts_24h,
            "unacknowledged": unacknowledged_alerts
        },
        "cases": {
            "pending": pending_cases,
            "new_24h": new_cases_24h
        },
        "tek": {
            "tokens_issued_24h": tokens_issued_24h,
            "uploads_completed_24h": tek_uploads_24h
        },
        "system": {
            "healthy_services": healthy_services,
            "total_services": total_services
        }
    }