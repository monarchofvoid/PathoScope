from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User, UserRole
from ...models.infection import (
    InfectionCase, VerificationToken, TEKUpload, VerificationStatus,
    UploadStatus, PathogenType
)
from ...models.analytics import (
    RiskAlert, AnalyticsSnapshot, SystemHealth, AlertType
)
from ...schemas.analytics import (
    KPIMetrics, AnalyticsSnapshotResponse, TrendResponse,
    ClusterAnalysisResponse, ComplianceStats, AnalyticsParams
)

router = APIRouter()


def get_date_range(days: int) -> tuple[datetime, datetime]:
    """Get date range for last N days"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


@router.get("/kpi", response_model=KPIMetrics)
async def get_kpi_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current KPI metrics"""
    # Time ranges
    now_24h_ago, now = get_date_range(1)
    now_7d_ago, _ = get_date_range(7)
    now_30d_ago, _ = get_date_range(30)

    # Alert metrics
    total_alerts_24h = db.query(RiskAlert).filter(
        RiskAlert.created_at >= now_24h_ago
    ).count()

    alert_distribution_24h = db.query(
        RiskAlert.alert_type,
        func.count(RiskAlert.id).label('count')
    ).filter(
        RiskAlert.created_at >= now_24h_ago
    ).group_by(RiskAlert.alert_type).all()

    high_risk_alerts_24h = 0
    moderate_risk_alerts_24h = 0
    low_risk_alerts_24h = 0

    for alert_type, count in alert_distribution_24h:
        if alert_type == AlertType.HIGH:
            high_risk_alerts_24h = count
        elif alert_type == AlertType.MODERATE:
            moderate_risk_alerts_24h = count
        elif alert_type == AlertType.LOW:
            low_risk_alerts_24h = count

    total_alerts_7d = db.query(RiskAlert).filter(
        RiskAlert.created_at >= now_7d_ago
    ).count()

    total_alerts_30d = db.query(RiskAlert).filter(
        RiskAlert.created_at >= now_30d_ago
    ).count()

    # Case metrics
    total_active_cases = db.query(InfectionCase).filter(
        InfectionCase.verification_status == VerificationStatus.VERIFIED
    ).count()

    new_cases_24h = db.query(InfectionCase).filter(
        InfectionCase.created_at >= now_24h_ago
    ).count()

    new_cases_7d = db.query(InfectionCase).filter(
        InfectionCase.created_at >= now_7d_ago
    ).count()

    new_cases_30d = db.query(InfectionCase).filter(
        InfectionCase.created_at >= now_30d_ago
    ).count()

    # Compliance metrics
    total_tokens = db.query(VerificationToken).filter(
        VerificationToken.token_type == 'tek_upload'
    ).count()

    completed_uploads = db.query(TEKUpload).filter(
        TEKUpload.upload_status == UploadStatus.COMPLETED
    ).count()

    tek_upload_compliance_rate = (completed_uploads / total_tokens * 100) if total_tokens > 0 else 0.0

    # Calculate average upload delay
    uploads_with_delay = db.query(TEKUpload, VerificationToken).join(
        VerificationToken, TEKUpload.verification_token_id == VerificationToken.id
    ).filter(
        and_(
            TEKUpload.uploaded_at.isnot(None),
            TEKUpload.upload_status == UploadStatus.COMPLETED
        )
    ).all()

    total_delay_hours = 0
    upload_count = len(uploads_with_delay)

    for upload, token in uploads_with_delay:
        delay = upload.uploaded_at - token.issued_at
        total_delay_hours += delay.total_seconds() / 3600

    average_upload_delay_hours = total_delay_hours / upload_count if upload_count > 0 else 0.0

    # Token usage rate
    used_tokens = db.query(VerificationToken).filter(
        and_(
            VerificationToken.used_at.isnot(None),
            VerificationToken.token_type == 'tek_upload'
        )
    ).count()

    token_usage_rate = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0.0

    # Pathogen distribution
    pathogen_distribution = db.query(
        InfectionCase.pathogen_type,
        func.count(InfectionCase.id).label('count')
    ).filter(
        InfectionCase.verification_status == VerificationStatus.VERIFIED
    ).group_by(InfectionCase.pathogen_type).all()

    pathogen_dist_dict = {
        pathogen_type.value: count for pathogen_type, count in pathogen_distribution
    }

    return KPIMetrics(
        total_alerts_24h=total_alerts_24h,
        high_risk_alerts_24h=high_risk_alerts_24h,
        moderate_risk_alerts_24h=moderate_risk_alerts_24h,
        low_risk_alerts_24h=low_risk_alerts_24h,
        total_alerts_7d=total_alerts_7d,
        total_alerts_30d=total_alerts_30d,
        tek_upload_compliance_rate=round(tek_upload_compliance_rate, 2),
        average_upload_delay_hours=round(average_upload_delay_hours, 2),
        token_usage_rate=round(token_usage_rate, 2),
        total_active_cases=total_active_cases,
        new_cases_24h=new_cases_24h,
        new_cases_7d=new_cases_7d,
        new_cases_30d=new_cases_30d,
        pathogen_distribution=pathogen_dist_dict,
        last_updated=datetime.utcnow()
    )


@router.get("/compliance", response_model=ComplianceStats)
async def get_compliance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get TEK upload compliance statistics"""
    # Total verified cases
    total_cases = db.query(InfectionCase).filter(
        InfectionCase.verification_status == VerificationStatus.VERIFIED
    ).count()

    # Tokens generated
    tokens_generated = db.query(VerificationToken).filter(
        VerificationToken.token_type == 'tek_upload'
    ).count()

    # TEK upload statuses
    completed_uploads = db.query(TEKUpload).filter(
        TEKUpload.upload_status == UploadStatus.COMPLETED
    ).count()

    pending_uploads = db.query(TEKUpload).filter(
        TEKUpload.upload_status == UploadStatus.PENDING
    ).count()

    failed_uploads = db.query(TEKUpload).filter(
        TEKUpload.upload_status == UploadStatus.FAILED
    ).count()

    # Compliance rate calculation
    compliance_rate = (completed_uploads / tokens_generated * 100) if tokens_generated > 0 else 0.0

    # Average upload delay
    uploads_with_delay = db.query(TEKUpload, VerificationToken).join(
        VerificationToken, TEKUpload.verification_token_id == VerificationToken.id
    ).filter(
        and_(
            TEKUpload.uploaded_at.isnot(None),
            TEKUpload.upload_status == UploadStatus.COMPLETED
        )
    ).all()

    total_delay_hours = 0
    upload_count = len(uploads_with_delay)

    for upload, token in uploads_with_delay:
        delay = upload.uploaded_at - token.issued_at
        total_delay_hours += delay.total_seconds() / 3600

    average_upload_delay_hours = total_delay_hours / upload_count if upload_count > 0 else 0.0

    return ComplianceStats(
        total_cases=total_cases,
        tokens_generated=tokens_generated,
        tek_uploads_completed=completed_uploads,
        tek_uploads_pending=pending_uploads,
        tek_uploads_failed=failed_uploads,
        compliance_rate=round(compliance_rate, 2),
        average_upload_delay_hours=round(average_upload_delay_hours, 2)
    )


@router.get("/trends")
async def get_trend_data(
    metric: str = Query(..., description="Metric name: alerts, cases, uploads"),
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trend data for charts"""
    # Parse period
    period_days = int(period.replace('d', ''))
    start_date, end_date = get_date_range(period_days)

    data = []

    if metric == "alerts":
        # Daily alert counts
        daily_alerts = db.query(
            func.date(RiskAlert.created_at).label('date'),
            func.count(RiskAlert.id).label('count')
        ).filter(
            RiskAlert.created_at >= start_date
        ).group_by(
            func.date(RiskAlert.created_at)
        ).order_by('date').all()

        for day_date, count in daily_alerts:
            data.append({
                "date": day_date.isoformat(),
                "value": float(count)
            })

    elif metric == "cases":
        # Daily new cases
        daily_cases = db.query(
            func.date(InfectionCase.created_at).label('date'),
            func.count(InfectionCase.id).label('count')
        ).filter(
            InfectionCase.created_at >= start_date
        ).group_by(
            func.date(InfectionCase.created_at)
        ).order_by('date').all()

        for day_date, count in daily_cases:
            data.append({
                "date": day_date.isoformat(),
                "value": float(count)
            })

    elif metric == "uploads":
        # Daily TEK uploads
        daily_uploads = db.query(
            func.date(TEKUpload.uploaded_at).label('date'),
            func.count(TEKUpload.id).label('count')
        ).filter(
            and_(
                TEKUpload.uploaded_at >= start_date,
                TEKUpload.upload_status == UploadStatus.COMPLETED
            )
        ).group_by(
            func.date(TEKUpload.uploaded_at)
        ).order_by('date').all()

        for day_date, count in daily_uploads:
            data.append({
                "date": day_date.isoformat(),
                "value": float(count)
            })

    return TrendResponse(
        metric_name=metric,
        metric_type="count",
        time_period=period,
        data=data
    )


@router.get("/clusters")
async def get_cluster_analysis(
    location: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cluster analysis data"""
    # Time window for cluster analysis (last 7 days)
    start_date, end_date = get_date_range(7)

    query = db.query(RiskAlert).filter(
        RiskAlert.created_at >= start_date
    )

    if location:
        query = query.filter(RiskAlert.location_identifier.ilike(f"%{location}%"))

    if risk_level:
        try:
            alert_type = AlertType(risk_level)
            query = query.filter(RiskAlert.alert_type == alert_type)
        except ValueError:
            pass

    alerts = query.order_by(desc(RiskAlert.created_at)).all()

    # Group by location to identify clusters
    location_clusters = {}
    for alert in alerts:
        location = alert.location_identifier
        if location not in location_clusters:
            location_clusters[location] = []
        location_clusters[location].append(alert)

    # Analyze clusters
    clusters = []
    total_clusters = 0
    high_risk_clusters = 0
    moderate_risk_clusters = 0
    low_risk_clusters = 0

    for location, location_alerts in location_clusters.items():
        if len(location_alerts) > 1:  # Only consider locations with multiple alerts as clusters
            cluster_id = f"cluster-{location.replace(' ', '-').lower()}"
            alert_count = len(location_alerts)

            # Determine risk level based on alert distribution
            high_count = sum(1 for alert in location_alerts if alert.alert_type == AlertType.HIGH)
            if high_count > 0:
                cluster_risk_level = AlertType.HIGH
                high_risk_clusters += 1
            elif any(alert.alert_type == AlertType.MODERATE for alert in location_alerts):
                cluster_risk_level = AlertType.MODERATE
                moderate_risk_clusters += 1
            else:
                cluster_risk_level = AlertType.LOW
                low_risk_clusters += 1

            # Calculate time window
            earliest_time = min(alert.created_at for alert in location_alerts)
            latest_time = max(alert.created_at for alert in location_alerts)

            # Average confidence score
            avg_confidence = sum(alert.confidence_score for alert in location_alerts) / len(location_alerts)

            clusters.append({
                "cluster_id": cluster_id,
                "location_identifier": location,
                "alert_count": alert_count,
                "risk_level": cluster_risk_level.value,
                "time_window_start": earliest_time,
                "time_window_end": latest_time,
                "confidence_score": round(avg_confidence, 2)
            })
            total_clusters += 1

    return ClusterAnalysisResponse(
        total_clusters=total_clusters,
        high_risk_clusters=high_risk_clusters,
        moderate_risk_clusters=moderate_risk_clusters,
        low_risk_clusters=low_risk_clusters,
        clusters=clusters,
        analysis_period="7d"
    )


@router.get("/snapshots")
async def get_analytics_snapshots(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics snapshots for historical data"""
    query = db.query(AnalyticsSnapshot)

    if date_from:
        query = query.filter(AnalyticsSnapshot.snapshot_date >= date_from)

    if date_to:
        query = query.filter(AnalyticsSnapshot.snapshot_date <= date_to)

    snapshots = query.order_by(desc(AnalyticsSnapshot.snapshot_date)).limit(30).all()

    return [AnalyticsSnapshotResponse.from_orm(snapshot) for snapshot in snapshots]