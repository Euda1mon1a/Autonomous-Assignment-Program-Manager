"""
Integration example for SOC (Self-Organized Criticality) predictor.

This file demonstrates how to integrate the SOC predictor with the existing
resilience service for early warning of cascade failures.

USAGE:

1. In ResilienceService (/backend/app/resilience/service.py):

    from app.resilience.soc_predictor import SOCAvalanchePredictor

    class ResilienceService:
        def __init__(self, db: Session, config: ResilienceConfig):
            # ... existing initialization ...

            # NEW: Add SOC predictor
            self.soc_predictor = SOCAvalanchePredictor()

        async def check_health(
            self, faculty, blocks, assignments
        ) -> SystemHealthReport:
            # ... existing health checks ...

            # NEW: Add SOC early warning analysis
            soc_result = await self._check_soc_warning(assignments)

            health_report.soc_avalanche_risk = soc_result.avalanche_risk_score
            health_report.soc_warning_level = soc_result.warning_level.value
            health_report.soc_days_to_critical = soc_result.estimated_days_to_critical

            # Add warnings if critical
            if soc_result.is_critical:
                health_report.immediate_actions.extend(
                    soc_result.immediate_actions
                )
                health_report.watch_items.extend(soc_result.watch_items)

            if soc_result.warning_level in (WarningLevel.ORANGE, WarningLevel.RED):
                health_report.warnings.append(
                    f"SOC Warning: {soc_result.warning_level.value} - "
                    f"{soc_result.signals_triggered} signals triggered"
                )

            return health_report

        async def _check_soc_warning(self, assignments) -> CriticalSlowingDownResult:
            '''
            Check for SOC early warning signals.

            Extracts utilization history from assignments and runs SOC analysis.
            '''
            # Get daily utilization for last 60 days
            utilization_history = await self._get_utilization_history(days=60)

            # Run SOC analysis
            result = await self.soc_predictor.detect_critical_slowing_down(
                utilization_history=utilization_history,
                days_lookback=60
            )

            logger.info(
                f"SOC Analysis: {result.warning_level.value} - "
                f"Risk={result.avalanche_risk_score:.2f}"
            )

            return result

        async def _get_utilization_history(self, days: int) -> list[float]:
            '''
            Get historical utilization values.

            This should query your database for actual utilization metrics.
            '''
            # Placeholder - replace with actual DB query
            # Example query:
            # SELECT date, AVG(utilization) as avg_util
            # FROM daily_metrics
            # WHERE date >= NOW() - INTERVAL '{days} days'
            # ORDER BY date ASC

            # For now, return mock data
            return [0.75] * days


2. Add API endpoint (/backend/app/api/routes/resilience.py):

    from app.schemas.resilience import (
        CriticalSlowingDownRequest,
        CriticalSlowingDownResponse,
    )

    @router.post("/soc-risk", response_model=CriticalSlowingDownResponse)
    async def analyze_soc_risk(
        request: CriticalSlowingDownRequest,
        db: AsyncSession = Depends(get_db),
    ):
        '''
        Analyze Self-Organized Criticality early warning signals.

        Detects critical slowing down in scheduling system to provide
        2-4 week advance warning of cascade failures.
        '''
        predictor = SOCAvalanchePredictor()

        result = await predictor.detect_critical_slowing_down(
            utilization_history=request.utilization_history,
            coverage_history=request.coverage_history,
            days_lookback=request.days_lookback,
        )

        # Convert to response schema
        return CriticalSlowingDownResponse(
            id=result.id,
            calculated_at=result.calculated_at,
            days_analyzed=result.days_analyzed,
            data_quality=result.data_quality,
            is_critical=result.is_critical,
            warning_level=result.warning_level,
            confidence=result.confidence,
            relaxation_time_hours=result.relaxation_time_hours,
            relaxation_time_baseline=result.relaxation_time_baseline,
            relaxation_time_increasing=result.relaxation_time_increasing,
            variance_current=result.variance_current,
            variance_baseline=result.variance_baseline,
            variance_slope=result.variance_slope,
            variance_increasing=result.variance_increasing,
            autocorrelation_ac1=result.autocorrelation_ac1,
            autocorrelation_baseline=result.autocorrelation_baseline,
            autocorrelation_increasing=result.autocorrelation_increasing,
            signals_triggered=result.signals_triggered,
            estimated_days_to_critical=result.estimated_days_to_critical,
            avalanche_risk_score=result.avalanche_risk_score,
            recommendations=result.recommendations,
            immediate_actions=result.immediate_actions,
            watch_items=result.watch_items,
        )


3. Frontend integration (Next.js):

    // app/dashboard/soc-monitor/page.tsx

    'use client';

    import { useQuery } from '@tanstack/react-query';
    import { api } from '@/lib/api';

    export default function SOCMonitorPage() {
      const { data: socData, isLoading } = useQuery({
        queryKey: ['soc-risk'],
        queryFn: async () => {
          // Get utilization history from API
          const utilization = await api.get('/metrics/utilization-history?days=60');

          // Analyze SOC risk
          const response = await api.post('/resilience/soc-risk', {
            utilization_history: utilization.data,
            days_lookback: 60,
          });

          return response.data;
        },
        refetchInterval: 15 * 60 * 1000, // 15 minutes
      });

      if (isLoading) return <div>Loading SOC analysis...</div>;

      const warningColors = {
        green: 'bg-green-100 text-green-800',
        yellow: 'bg-yellow-100 text-yellow-800',
        orange: 'bg-orange-100 text-orange-800',
        red: 'bg-red-100 text-red-800',
      };

      return (
        <div className="space-y-6">
          <h1 className="text-2xl font-bold">SOC Early Warning Monitor</h1>

          {/* Warning Status */}
          <div className={`p-4 rounded-lg ${warningColors[socData.warning_level]}`}>
            <h2 className="text-xl font-semibold">
              Status: {socData.warning_level.toUpperCase()}
            </h2>
            <p>Confidence: {(socData.confidence * 100).toFixed(0)}%</p>
            {socData.estimated_days_to_critical && (
              <p className="font-bold mt-2">
                ⚠️ Estimated {socData.estimated_days_to_critical} days to critical
              </p>
            )}
          </div>

          {/* Early Warning Signals */}
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              title="Relaxation Time"
              current={socData.relaxation_time_hours}
              baseline={socData.relaxation_time_baseline}
              threshold={48}
              unit="hours"
              increasing={socData.relaxation_time_increasing}
            />
            <MetricCard
              title="Variance Slope"
              current={socData.variance_slope}
              baseline={0}
              threshold={0.1}
              increasing={socData.variance_increasing}
            />
            <MetricCard
              title="Autocorrelation (AC1)"
              current={socData.autocorrelation_ac1}
              baseline={socData.autocorrelation_baseline}
              threshold={0.7}
              increasing={socData.autocorrelation_increasing}
            />
          </div>

          {/* Recommendations */}
          {socData.recommendations.length > 0 && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">Recommendations</h3>
              <ul className="list-disc list-inside space-y-1">
                {socData.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Immediate Actions */}
          {socData.immediate_actions.length > 0 && (
            <div className="bg-red-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-2">⚡ Immediate Actions Required</h3>
              <ul className="list-disc list-inside space-y-1">
                {socData.immediate_actions.map((action, i) => (
                  <li key={i}>{action}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }


4. Celery periodic task (for automatic monitoring):

    # backend/app/resilience/tasks.py

    from app.core.celery_app import celery_app
    from app.resilience.soc_predictor import SOCAvalanchePredictor

    @celery_app.task(name="check_soc_warning")
    async def check_soc_warning_task():
        '''
        Periodic task to check SOC early warning signals.

        Runs every 6 hours to detect approaching cascade failures.
        '''
        predictor = SOCAvalanchePredictor()

        # Get utilization history from database
        utilization = await get_utilization_history(days=60)

        # Run SOC analysis
        result = await predictor.detect_critical_slowing_down(
            utilization_history=utilization,
            days_lookback=60
        )

        # Log warning
        logger.info(
            f"SOC Check: {result.warning_level.value} - "
            f"Risk={result.avalanche_risk_score:.2f}, "
            f"Signals={result.signals_triggered}"
        )

        # Send alert if critical
        if result.is_critical:
            await send_alert(
                severity="high",
                title=f"SOC Warning: {result.warning_level.value}",
                message=result.recommendations[0],
                actions=result.immediate_actions,
            )

        return {
            "warning_level": result.warning_level.value,
            "risk_score": result.avalanche_risk_score,
            "signals": result.signals_triggered,
        }

    # Add to beat schedule in celeryconfig.py:
    # beat_schedule = {
    #     'soc-warning-check': {
    #         'task': 'check_soc_warning',
    #         'schedule': crontab(hour='*/6'),  # Every 6 hours
    #     },
    # }


5. Database model for persistence (optional):

    # backend/app/models/soc_metrics.py

    from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean, ARRAY
    from app.db.base_class import Base
    import uuid

    class SOCMetrics(Base):
        '''Historical SOC analysis results.'''

        __tablename__ = "soc_metrics"

        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        calculated_at = Column(DateTime, nullable=False)
        days_analyzed = Column(Integer, nullable=False)
        data_quality = Column(String(20), nullable=False)

        # Warning status
        is_critical = Column(Boolean, nullable=False)
        warning_level = Column(String(20), nullable=False)
        confidence = Column(Float, nullable=False)

        # Signals
        relaxation_time_hours = Column(Float)
        variance_slope = Column(Float)
        autocorrelation_ac1 = Column(Float)
        signals_triggered = Column(Integer, nullable=False)

        # Risk
        estimated_days_to_critical = Column(Integer)
        avalanche_risk_score = Column(Float, nullable=False)

        # Insights
        recommendations = Column(ARRAY(String))
        immediate_actions = Column(ARRAY(String))


TESTING:

    # Quick test with synthetic data
    import asyncio
    import numpy as np
    from app.resilience.soc_predictor import SOCAvalanchePredictor

    async def test_soc():
        predictor = SOCAvalanchePredictor()

        # Healthy system
        stable = list(0.65 + np.random.normal(0, 0.02, 60))
        result = await predictor.detect_critical_slowing_down(stable)
        print(f"Stable: {result.warning_level.value} - Risk: {result.avalanche_risk_score:.2f}")

        # Approaching criticality
        unstable_base = [0.7] * 30
        unstable_recent = []
        for i in range(30):
            unstable_recent.append(0.7 + np.random.normal(0, 0.05 * (i/30)))
        unstable = unstable_base + unstable_recent

        result = await predictor.detect_critical_slowing_down(unstable)
        print(f"Unstable: {result.warning_level.value} - Risk: {result.avalanche_risk_score:.2f}")
        print(f"Signals: {result.signals_triggered}")
        print(f"Recommendations: {result.recommendations}")

    asyncio.run(test_soc())
"""
