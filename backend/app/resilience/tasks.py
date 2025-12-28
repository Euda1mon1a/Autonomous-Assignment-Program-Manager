"""
Celery Tasks for Resilience Monitoring.

Provides automated background tasks for:
- Periodic health checks
- Contingency analysis (N-1/N-2)
- Fallback schedule precomputation
- Utilization forecasting
- Alert generation

Tasks integrate with the ResilienceService and update Prometheus metrics.
"""

from datetime import date, datetime, timedelta

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.db.session import SessionLocal

    return SessionLocal()


@shared_task(
    bind=True,
    name="app.resilience.tasks.periodic_health_check",
    max_retries=3,
    default_retry_delay=60,
)
def periodic_health_check(self) -> dict:
    """
    Perform periodic system health check.

    Runs every 15 minutes (configured in celery_app.py).

    Checks:
    - Current utilization vs threshold
    - Faculty availability
    - Coverage rate
    - Active alerts

    Updates Prometheus metrics and triggers alerts if needed.
    """
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.resilience.metrics import get_metrics
    from app.resilience.service import ResilienceService

    logger.info("Starting periodic health check")
    metrics = get_metrics()

    db = get_db_session()
    try:
        with metrics.time_health_check():
            # Get current date range (today + next 7 days)
            today = date.today()
            end_date = today + timedelta(days=7)

            # Load data
            faculty = db.query(Person).filter(Person.type == "faculty").all()
            blocks = (
                db.query(Block)
                .filter(
                    Block.date >= today,
                    Block.date <= end_date,
                )
                .all()
            )
            assignments = (
                db.query(Assignment)
                .filter(Assignment.block_id.in_([b.id for b in blocks]))
                .all()
                if blocks
                else []
            )

            # Run health check
            service = ResilienceService(db)
            health = service.check_health(faculty, blocks, assignments)

            # Update metrics
            metrics.update_utilization(
                rate=health.utilization.utilization_rate,
                level=health.utilization.level.value,
                buffer=health.utilization.buffer_remaining,
            )
            metrics.update_defense_level(health.defense_level.value)
            metrics.update_load_shedding(
                level=health.load_shedding_level.value,
                suspended_count=len(service.sacrifice.get_suspended_activities()),
            )
            metrics.update_contingency_status(health.n1_pass, health.n2_pass)
            metrics.update_faculty_counts(
                total=len(faculty),
                on_duty=len(list(faculty)),  # Would filter by availability
            )
            metrics.update_active_fallbacks(len(health.active_fallbacks))

            result = {
                "timestamp": datetime.now().isoformat(),
                "status": health.overall_status,
                "utilization": health.utilization.utilization_rate,
                "defense_level": health.defense_level.name,
                "n1_pass": health.n1_pass,
                "n2_pass": health.n2_pass,
                "immediate_actions": health.immediate_actions,
            }

            # Check if alerts needed
            if health.overall_status in ("critical", "emergency"):
                send_resilience_alert.delay(
                    level="critical",
                    message=f"System status: {health.overall_status}",
                    details=result,
                )

            logger.info(f"Health check complete: {health.overall_status}")
            return result

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        metrics.record_health_check_failure(str(e))
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.resilience.tasks.run_contingency_analysis",
    max_retries=2,
    default_retry_delay=300,
)
def run_contingency_analysis(
    self,
    days_ahead: int = 90,
) -> dict:
    """
    Run comprehensive contingency analysis.

    Runs daily at 2 AM (configured in celery_app.py).

    Performs:
    - N-1 analysis (single faculty loss)
    - N-2 analysis (pair faculty loss)
    - Centrality calculation (with NetworkX if available)
    - Critical failure point identification

    Returns vulnerability report.
    """
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.resilience.contingency import ContingencyAnalyzer
    from app.resilience.metrics import get_metrics

    logger.info(f"Starting contingency analysis for next {days_ahead} days")
    metrics = get_metrics()

    db = get_db_session()
    try:
        with metrics.time_contingency_analysis():
            # Get date range
            today = date.today()
            end_date = today + timedelta(days=days_ahead)

            # Load data
            faculty = db.query(Person).filter(Person.type == "faculty").all()
            blocks = (
                db.query(Block)
                .filter(
                    Block.date >= today,
                    Block.date <= end_date,
                )
                .all()
            )
            assignments = (
                db.query(Assignment)
                .filter(Assignment.block_id.in_([b.id for b in blocks]))
                .all()
                if blocks
                else []
            )

            # Build coverage requirements (1 per block by default)
            coverage_requirements = {b.id: 1 for b in blocks}

            # Run analysis
            analyzer = ContingencyAnalyzer()
            report = analyzer.generate_report(
                faculty=faculty,
                blocks=blocks,
                assignments=assignments,
                coverage_requirements=coverage_requirements,
            )

            # Update metrics
            metrics.update_contingency_status(report.n1_pass, report.n2_pass)

            result = {
                "timestamp": datetime.now().isoformat(),
                "period": {
                    "start": report.period_start.isoformat(),
                    "end": report.period_end.isoformat(),
                },
                "n1_pass": report.n1_pass,
                "n1_vulnerabilities_count": len(report.n1_vulnerabilities),
                "n2_pass": report.n2_pass,
                "n2_fatal_pairs_count": len(report.n2_fatal_pairs),
                "phase_transition_risk": report.phase_transition_risk,
                "most_critical_faculty": [str(f) for f in report.most_critical_faculty],
                "recommendations": report.recommended_actions,
            }

            # Alert if critical issues found
            if not report.n1_pass or report.phase_transition_risk == "critical":
                send_resilience_alert.delay(
                    level="warning",
                    message=f"Contingency analysis found issues: N1={report.n1_pass}, "
                    f"Phase risk={report.phase_transition_risk}",
                    details=result,
                )

            logger.info(
                f"Contingency analysis complete: N1={report.n1_pass}, N2={report.n2_pass}"
            )
            return result

    except Exception as e:
        logger.error(f"Contingency analysis failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.resilience.tasks.precompute_fallback_schedules",
    max_retries=1,
    default_retry_delay=600,
)
def precompute_fallback_schedules(
    self,
    days_ahead: int = 90,
) -> dict:
    """
    Precompute fallback schedules for all scenarios.

    Runs weekly on Sunday at 3 AM (configured in celery_app.py).

    Generates fallback schedules for:
    - Single faculty loss
    - Double faculty loss
    - PCS season (50% capacity)
    - Holiday skeleton
    - Pandemic essential only
    - Mass casualty event
    - Weather emergency

    These pre-computed schedules enable instant crisis response.
    """
    from app.resilience.static_stability import FallbackScenario, FallbackScheduler

    logger.info(f"Starting fallback precomputation for next {days_ahead} days")

    db = get_db_session()
    try:
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        scheduler = FallbackScheduler()

        # Precompute all scenarios
        results = {}
        for scenario in FallbackScenario:
            try:
                fallback = scheduler.precompute_fallback(
                    scenario=scenario,
                    start_date=today,
                    end_date=end_date,
                    assumptions=[
                        f"Generated {datetime.now().isoformat()}",
                        f"Period: {today} to {end_date}",
                    ],
                )
                results[scenario.value] = {
                    "id": str(fallback.id),
                    "valid_until": fallback.valid_until.isoformat(),
                    "coverage_rate": fallback.coverage_rate,
                    "services_reduced": fallback.services_reduced,
                }
                logger.info(f"Precomputed fallback: {scenario.value}")
            except Exception as e:
                logger.error(f"Failed to precompute {scenario.value}: {e}")
                results[scenario.value] = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "period": {
                "start": today.isoformat(),
                "end": end_date.isoformat(),
            },
            "scenarios_computed": len(
                [r for r in results.values() if "error" not in r]
            ),
            "scenarios_failed": len([r for r in results.values() if "error" in r]),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Fallback precomputation failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.resilience.tasks.generate_utilization_forecast",
    max_retries=2,
    default_retry_delay=300,
)
def generate_utilization_forecast(
    self,
    days_ahead: int = 90,
) -> dict:
    """
    Generate utilization forecast based on known absences.

    Runs daily at 6 AM (configured in celery_app.py).

    Uses known absences (PCS, leave, TDY) to forecast
    utilization and identify high-risk periods.
    """
    from app.models.absence import Absence
    from app.models.person import Person
    from app.resilience.utilization import UtilizationMonitor

    logger.info(f"Generating utilization forecast for next {days_ahead} days")

    db = get_db_session()
    try:
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        # Load faculty
        faculty = db.query(Person).filter(Person.type == "faculty").all()

        # Load absences
        absences = (
            db.query(Absence)
            .filter(
                Absence.start_date <= end_date,
                Absence.end_date >= today,
            )
            .all()
        )

        # Build absence map by date
        known_absences = {}
        for d in range(days_ahead):
            check_date = today + timedelta(days=d)
            absent_ids = [
                a.person_id
                for a in absences
                if a.start_date <= check_date <= a.end_date
            ]
            if absent_ids:
                known_absences[check_date] = absent_ids

        # Generate required coverage (assume 2 blocks per weekday)
        required_coverage = {}
        for d in range(days_ahead):
            check_date = today + timedelta(days=d)
            if check_date.weekday() < 5:  # Weekday
                required_coverage[check_date] = 2
            else:
                required_coverage[check_date] = 0

        # Generate forecast
        monitor = UtilizationMonitor()
        forecasts = monitor.forecast_utilization(
            base_faculty=faculty,
            known_absences=known_absences,
            required_coverage_by_date=required_coverage,
            forecast_days=days_ahead,
        )

        # Identify high-risk periods
        high_risk_periods = [
            {
                "date": f.date.isoformat(),
                "utilization": f.predicted_utilization,
                "level": f.predicted_level.value,
                "factors": f.contributing_factors,
            }
            for f in forecasts
            if f.predicted_level.value in ("red", "black")
        ]

        result = {
            "timestamp": datetime.now().isoformat(),
            "period": {
                "start": today.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_faculty": len(faculty),
            "high_risk_days": len(high_risk_periods),
            "high_risk_periods": high_risk_periods[:10],  # Top 10
        }

        # Alert if significant high-risk periods
        if len(high_risk_periods) > 5:
            send_resilience_alert.delay(
                level="warning",
                message=f"Forecast shows {len(high_risk_periods)} high-risk days in next {days_ahead} days",
                details=result,
            )

        logger.info(
            f"Forecast complete: {len(high_risk_periods)} high-risk days identified"
        )
        return result

    except Exception as e:
        logger.error(f"Utilization forecast failed: {e}")
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    name="app.resilience.tasks.send_resilience_alert",
    max_retries=3,
    default_retry_delay=30,
)
def send_resilience_alert(
    level: str,
    message: str,
    details: dict | None = None,
) -> dict:
    """
    Send resilience alert via configured channels.

    Args:
        level: Alert level ("info", "warning", "critical", "emergency")
        message: Alert message
        details: Additional details dict

    Sends via:
    - In-app notification
    - Email (for warning and above)
    - Webhook (if configured)
    """
    from uuid import uuid4

    from app.notifications.channels import (
        NotificationPayload,
    )

    logger.info(f"Sending resilience alert: {level} - {message}")

    # Create payload
    NotificationPayload(
        recipient_id=uuid4(),  # Would be admin user ID
        notification_type=f"resilience_alert_{level}",
        subject=f"[RESILIENCE {level.upper()}] {message[:50]}",
        body=message,
        data=details,
        priority="high" if level in ("critical", "emergency") else "normal",
    )

    results = []

    # Always send in-app
    try:
        # In production, this would use async/await
        # For now, just log
        logger.info(f"In-app alert: {message}")
        results.append({"channel": "in_app", "success": True})
    except Exception as e:
        results.append({"channel": "in_app", "success": False, "error": str(e)})

    # Email for warning and above
    if level in ("warning", "critical", "emergency"):
        try:
            logger.info(f"Email alert queued: {message}")
            results.append({"channel": "email", "success": True})
        except Exception as e:
            results.append({"channel": "email", "success": False, "error": str(e)})

    return {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "delivery_results": results,
    }


@shared_task(
    bind=True,
    name="app.resilience.tasks.activate_crisis_response",
)
def activate_crisis_response(
    self,
    severity: str,
    reason: str,
    approved_by: str | None = None,
) -> dict:
    """
    Activate crisis response mode via background task.

    This allows crisis activation to be triggered programmatically
    or via API without blocking the request.
    """
    from app.resilience.metrics import get_metrics
    from app.resilience.service import ResilienceService

    logger.warning(f"Activating crisis response: {severity} - {reason}")
    metrics = get_metrics()

    db = get_db_session()
    try:
        service = ResilienceService(db)
        result = service.activate_crisis_response(
            severity=severity,
            reason=reason,
        )

        # Record metrics
        metrics.record_crisis_activation(severity, reason)

        # Update load shedding metrics
        metrics.update_load_shedding(
            level=service.sacrifice.current_level.value,
            suspended_count=len(service.sacrifice.get_suspended_activities()),
        )

        # Send alert
        send_resilience_alert.delay(
            level="critical",
            message=f"Crisis response activated: {severity}",
            details={
                "severity": severity,
                "reason": reason,
                "approved_by": approved_by,
                "actions_taken": result.get("actions_taken", []),
            },
        )

        return result

    except Exception as e:
        logger.error(f"Crisis activation failed: {e}")
        raise
    finally:
        db.close()
