"""
Celery Tasks for ML Model Training and Scoring.

Provides automated background tasks for:
- Training ML models on historical data
- Scoring schedules using trained models
- Periodic model retraining
- Model health checks
"""

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.db.session import SessionLocal

    return SessionLocal()


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    return loop.run_until_complete(coro)


@shared_task(
    bind=True,
    name="app.tasks.ml_tasks.train_ml_models",
    max_retries=2,
    default_retry_delay=300,
)
def train_ml_models(
    self,
    model_types: list[str] | None = None,
    lookback_days: int | None = None,
    force_retrain: bool = False,
) -> dict[str, Any]:
    """
    Train ML models on historical scheduling data.

    Args:
        model_types: List of models to train ('preference', 'conflict', 'workload')
                    If None, trains all models.
        lookback_days: Number of days of historical data to use.
                      Defaults to ML_TRAINING_LOOKBACK_DAYS setting.
        force_retrain: Force retraining even if models exist.

    Returns:
        Dict with training results for each model.

    Raises:
        Retries on failure up to max_retries.
    """
    logger.info("Starting ML model training")

    if not settings.ML_ENABLED and not force_retrain:
        logger.info("ML is disabled. Skipping training.")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "skipped",
            "reason": "ML_ENABLED is False",
        }

    db = get_db_session()
    try:
        from app.ml import (
            ConflictPredictor,
            PreferencePredictor,
            TrainingDataPipeline,
            WorkloadOptimizer,
        )

        # Determine which models to train
        if model_types is None:
            model_types = ["preference", "conflict", "workload"]

        lookback = lookback_days or settings.ML_TRAINING_LOOKBACK_DAYS
        min_samples = settings.ML_MIN_TRAINING_SAMPLES

        pipeline = TrainingDataPipeline(db)
        results = {}
        models_dir = Path(settings.ML_MODELS_DIR)
        models_dir.mkdir(parents=True, exist_ok=True)

        # Train preference predictor
        if "preference" in model_types:
            logger.info("Training preference predictor...")
            try:
                X, y = _run_async(
                    pipeline.extract_preference_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                )

                if len(X) >= min_samples:
                    predictor = PreferencePredictor()
                    metrics = predictor.train(X, y)
                    model_path = models_dir / "preference_predictor"
                    predictor.save(model_path)
                    results["preference"] = {
                        "status": "trained",
                        "samples": len(X),
                        "metrics": metrics,
                        "path": str(model_path),
                    }
                else:
                    results["preference"] = {
                        "status": "skipped",
                        "reason": f"Insufficient samples ({len(X)} < {min_samples})",
                    }
            except Exception as e:
                logger.error(f"Preference model training failed: {e}")
                results["preference"] = {"status": "failed", "error": str(e)}

        # Train conflict predictor
        if "conflict" in model_types:
            logger.info("Training conflict predictor...")
            try:
                X, y = _run_async(
                    pipeline.extract_conflict_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                )

                if len(X) >= min_samples:
                    predictor = ConflictPredictor()
                    metrics = predictor.train(X, y)
                    model_path = models_dir / "conflict_predictor"
                    predictor.save(model_path)
                    results["conflict"] = {
                        "status": "trained",
                        "samples": len(X),
                        "metrics": metrics,
                        "path": str(model_path),
                    }
                else:
                    results["conflict"] = {
                        "status": "skipped",
                        "reason": f"Insufficient samples ({len(X)} < {min_samples})",
                    }
            except Exception as e:
                logger.error(f"Conflict model training failed: {e}")
                results["conflict"] = {"status": "failed", "error": str(e)}

        # Train workload optimizer
        if "workload" in model_types:
            logger.info("Training workload optimizer...")
            try:
                X, y = _run_async(
                    pipeline.extract_workload_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                )

                if len(X) >= min_samples // 2:  # Workload needs fewer samples
                    optimizer = WorkloadOptimizer()
                    metrics = optimizer.train(X, y)
                    model_path = models_dir / "workload_optimizer"
                    optimizer.save(model_path)
                    results["workload"] = {
                        "status": "trained",
                        "samples": len(X),
                        "metrics": metrics,
                        "path": str(model_path),
                    }
                else:
                    results["workload"] = {
                        "status": "skipped",
                        "reason": f"Insufficient samples ({len(X)} < {min_samples // 2})",
                    }
            except Exception as e:
                logger.error(f"Workload model training failed: {e}")
                results["workload"] = {"status": "failed", "error": str(e)}

        trained_count = sum(1 for r in results.values() if r.get("status") == "trained")
        logger.info(
            f"ML training complete: {trained_count}/{len(model_types)} models trained"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "lookback_days": lookback,
            "models_trained": trained_count,
            "results": results,
            "task_status": "completed",
        }

    except Exception as e:
        logger.error(f"ML training failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.ml_tasks.score_schedule",
    max_retries=2,
    default_retry_delay=60,
)
def score_schedule(
    self,
    schedule_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Score a schedule using ML models.

    Args:
        schedule_data: Schedule data to score (assignments, blocks, etc.)

    Returns:
        Dict with scoring results including overall score, grade,
        component scores, and improvement suggestions.

    Raises:
        Retries on failure up to max_retries.
    """
    logger.info("Starting schedule scoring")

    if not settings.ML_ENABLED:
        logger.info("ML is disabled. Returning default score.")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "skipped",
            "reason": "ML_ENABLED is False",
            "default_score": 0.75,
        }

    db = get_db_session()
    try:
        from app.ml import ScheduleScorer

        models_dir = Path(settings.ML_MODELS_DIR)

        scorer = ScheduleScorer(
            preference_model_path=models_dir / "preference_predictor"
            if (models_dir / "preference_predictor").exists()
            else None,
            conflict_model_path=models_dir / "conflict_predictor"
            if (models_dir / "conflict_predictor").exists()
            else None,
            workload_model_path=models_dir / "workload_optimizer"
            if (models_dir / "workload_optimizer").exists()
            else None,
            db=db,
        )

        result = scorer.score_schedule(schedule_data)
        suggestions = scorer.suggest_improvements(schedule_data)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "score": result,
            "suggestions": suggestions,
            "task_status": "completed",
        }

    except Exception as e:
        logger.error(f"Schedule scoring failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.ml_tasks.check_model_health",
    max_retries=1,
    default_retry_delay=60,
)
def check_model_health(self) -> dict[str, Any]:
    """
    Check health of ML models.

    Returns:
        Dict with model health status including:
        - availability: Whether each model exists
        - last_trained: Training timestamps
        - recommendations: Suggested actions
    """
    logger.info("Checking ML model health")

    models_dir = Path(settings.ML_MODELS_DIR)
    model_paths = {
        "preference": models_dir / "preference_predictor",
        "conflict": models_dir / "conflict_predictor",
        "workload": models_dir / "workload_optimizer",
    }

    health = {}
    recommendations = []

    for name, path in model_paths.items():
        model_file = path / "model.pkl"
        if model_file.exists():
            mtime = datetime.fromtimestamp(model_file.stat().st_mtime)
            age_days = (datetime.now() - mtime).days

            health[name] = {
                "available": True,
                "last_trained": mtime.isoformat(),
                "age_days": age_days,
            }

            if age_days > settings.ML_TRAINING_FREQUENCY_DAYS * 2:
                recommendations.append(
                    f"{name} model is {age_days} days old. Consider retraining."
                )
        else:
            health[name] = {
                "available": False,
                "last_trained": None,
                "age_days": None,
            }
            recommendations.append(f"{name} model not found. Run training task.")

    available_count = sum(1 for h in health.values() if h["available"])

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ml_enabled": settings.ML_ENABLED,
        "models_available": f"{available_count}/{len(health)}",
        "health": health,
        "recommendations": recommendations,
        "task_status": "completed",
    }


@shared_task(
    bind=True,
    name="app.tasks.ml_tasks.periodic_retrain",
    max_retries=2,
    default_retry_delay=600,
)
def periodic_retrain(self) -> dict[str, Any]:
    """
    Periodic retraining task for ML models.

    Checks if models need retraining based on age and ML_TRAINING_FREQUENCY_DAYS
    setting. Only retrains models that are older than the threshold.

    This task should be scheduled via Celery Beat.

    Returns:
        Dict with retraining results.
    """
    if not settings.ML_AUTO_TRAINING_ENABLED:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "skipped",
            "reason": "ML_AUTO_TRAINING_ENABLED is False",
        }

    logger.info("Running periodic ML model retrain check")

    models_dir = Path(settings.ML_MODELS_DIR)
    threshold_days = settings.ML_TRAINING_FREQUENCY_DAYS
    models_to_retrain = []

    model_paths = {
        "preference": models_dir / "preference_predictor" / "model.pkl",
        "conflict": models_dir / "conflict_predictor" / "model.pkl",
        "workload": models_dir / "workload_optimizer" / "workload_model.pkl",
    }

    for name, path in model_paths.items():
        if not path.exists():
            models_to_retrain.append(name)
        else:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days
            if age_days >= threshold_days:
                models_to_retrain.append(name)
                logger.info(f"{name} model is {age_days} days old, scheduling retrain")

    if models_to_retrain:
        # Trigger training task for stale models
        train_ml_models.delay(model_types=models_to_retrain)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "models_scheduled": models_to_retrain,
            "task_status": "training_scheduled",
        }
    else:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "models_scheduled": [],
            "task_status": "no_retrain_needed",
        }
