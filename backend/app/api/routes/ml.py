"""Machine Learning API routes.

Endpoints for ML model management and predictions:
- Train models
- Check model health
- Score schedules
- Predict conflicts
- Predict preferences
- Analyze workload
"""

from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.ml import (
    ConflictPredictionResponse,
    ModelHealthResponse,
    ModelStatusResponse,
    PredictConflictRequest,
    PredictPreferenceRequest,
    PreferencePredictionResponse,
    ScheduleScoreResponse,
    ScoreComponentResponse,
    ScoreScheduleRequest,
    SuggestionResponse,
    TrainingResultResponse,
    TrainModelsRequest,
    TrainModelsResponse,
    WorkloadAnalysisRequest,
    WorkloadAnalysisResponse,
)

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=ModelHealthResponse)
async def get_model_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Check health status of ML models.

    Requires admin privileges.
    """
    models_dir = Path(settings.ML_MODELS_DIR)
    model_configs = [
        ("preference", models_dir / "preference_predictor" / "model.pkl"),
        ("conflict", models_dir / "conflict_predictor" / "model.pkl"),
        ("workload", models_dir / "workload_optimizer" / "workload_model.pkl"),
    ]

    models = []
    recommendations = []

    for name, path in model_configs:
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days

            models.append(
                ModelStatusResponse(
                    name=name,
                    available=True,
                    last_trained=mtime,
                    age_days=age_days,
                )
            )

            if age_days > settings.ML_TRAINING_FREQUENCY_DAYS * 2:
                recommendations.append(
                    f"{name} model is {age_days} days old. Consider retraining."
                )
        else:
            models.append(
                ModelStatusResponse(
                    name=name,
                    available=False,
                    last_trained=None,
                    age_days=None,
                )
            )
            recommendations.append(f"{name} model not found. Run training.")

    available_count = sum(1 for m in models if m.available)

    return ModelHealthResponse(
        ml_enabled=settings.ML_ENABLED,
        models_available=f"{available_count}/{len(models)}",
        models=models,
        recommendations=recommendations,
    )


@router.post("/train", response_model=TrainModelsResponse)
async def train_models(
    request: TrainModelsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Train ML models on historical data.

    This is a synchronous training for small datasets.
    For large datasets, use the async task endpoint.

    Requires admin privileges.
    """
    if not settings.ML_ENABLED and not request.force_retrain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ML is disabled. Set ML_ENABLED=true or use force_retrain=true.",
        )

    try:
        from app.ml import (
            ConflictPredictor,
            PreferencePredictor,
            TrainingDataPipeline,
            WorkloadOptimizer,
        )

        model_types = request.model_types or ["preference", "conflict", "workload"]
        lookback = request.lookback_days or settings.ML_TRAINING_LOOKBACK_DAYS
        min_samples = settings.ML_MIN_TRAINING_SAMPLES

        pipeline = TrainingDataPipeline(db)
        results = {}
        models_dir = Path(settings.ML_MODELS_DIR)
        models_dir.mkdir(parents=True, exist_ok=True)

        # Train each requested model
        for model_type in model_types:
            try:
                if model_type == "preference":
                    X, y = await pipeline.extract_preference_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                    if len(X) >= min_samples:
                        predictor = PreferencePredictor()
                        metrics = predictor.train(X, y)
                        model_path = models_dir / "preference_predictor"
                        predictor.save(model_path)
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="trained",
                            samples=len(X),
                            metrics=metrics,
                            path=str(model_path),
                        )
                    else:
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="skipped",
                            error=f"Insufficient samples ({len(X)} < {min_samples})",
                        )

                elif model_type == "conflict":
                    X, y = await pipeline.extract_conflict_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                    if len(X) >= min_samples:
                        predictor = ConflictPredictor()
                        metrics = predictor.train(X, y)
                        model_path = models_dir / "conflict_predictor"
                        predictor.save(model_path)
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="trained",
                            samples=len(X),
                            metrics=metrics,
                            path=str(model_path),
                        )
                    else:
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="skipped",
                            error=f"Insufficient samples ({len(X)} < {min_samples})",
                        )

                elif model_type == "workload":
                    X, y = await pipeline.extract_workload_training_data(
                        start_date=date.today() - timedelta(days=lookback),
                        end_date=date.today(),
                    )
                    if len(X) >= min_samples // 2:
                        optimizer = WorkloadOptimizer()
                        metrics = optimizer.train(X, y)
                        model_path = models_dir / "workload_optimizer"
                        optimizer.save(model_path)
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="trained",
                            samples=len(X),
                            metrics=metrics,
                            path=str(model_path),
                        )
                    else:
                        results[model_type] = TrainingResultResponse(
                            model_name=model_type,
                            status="skipped",
                            error=f"Insufficient samples ({len(X)} < {min_samples // 2})",
                        )

            except Exception as e:
                results[model_type] = TrainingResultResponse(
                    model_name=model_type,
                    status="failed",
                    error=str(e),
                )

        trained_count = sum(1 for r in results.values() if r.status == "trained")

        return TrainModelsResponse(
            timestamp=datetime.utcnow(),
            lookback_days=lookback,
            models_trained=trained_count,
            results=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}",
        )


@router.post("/train/async")
async def train_models_async(
    request: TrainModelsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """
    Trigger async ML model training via Celery.

    Returns a task ID that can be used to check training status.

    Requires admin privileges.
    """
    try:
        from app.tasks.ml_tasks import train_ml_models

        task = train_ml_models.delay(
            model_types=request.model_types,
            lookback_days=request.lookback_days,
            force_retrain=request.force_retrain,
        )

        return {
            "status": "training_started",
            "task_id": task.id,
            "message": "Training task submitted. Check status via /jobs/{task_id}.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training task: {str(e)}",
        )


@router.post("/score", response_model=ScheduleScoreResponse)
async def score_schedule(
    request: ScoreScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Score a schedule using ML models.

    Returns overall quality score, component scores, and improvement suggestions.
    """
    if not settings.ML_ENABLED:
        # Return default score when ML is disabled
        return ScheduleScoreResponse(
            overall_score=0.75,
            grade="B",
            components=[
                ScoreComponentResponse(
                    name="preference",
                    score=0.75,
                    weight=settings.ML_PREFERENCE_WEIGHT,
                    details={"note": "ML disabled, using default"},
                ),
                ScoreComponentResponse(
                    name="workload",
                    score=0.75,
                    weight=settings.ML_WORKLOAD_WEIGHT,
                    details={"note": "ML disabled, using default"},
                ),
                ScoreComponentResponse(
                    name="conflict",
                    score=0.75,
                    weight=settings.ML_CONFLICT_WEIGHT,
                    details={"note": "ML disabled, using default"},
                ),
            ],
            metadata={"ml_enabled": False},
        )

    try:
        from app.ml import ScheduleScorer

        models_dir = Path(settings.ML_MODELS_DIR)

        scorer = ScheduleScorer(
            preference_model_path=(
                models_dir / "preference_predictor"
                if (models_dir / "preference_predictor").exists()
                else None
            ),
            conflict_model_path=(
                models_dir / "conflict_predictor"
                if (models_dir / "conflict_predictor").exists()
                else None
            ),
            workload_model_path=(
                models_dir / "workload_optimizer"
                if (models_dir / "workload_optimizer").exists()
                else None
            ),
            db=db,
        )

        # Get schedule data
        schedule_data = request.schedule_data
        if not schedule_data and request.schedule_id:
            # Load schedule from database
            # This would need to be implemented based on your schedule storage
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="schedule_id lookup not yet implemented. Please provide schedule_data.",
            )

        if not schedule_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either schedule_id or schedule_data is required.",
            )

        result = scorer.score_schedule(schedule_data)
        suggestions = []
        if request.include_suggestions:
            raw_suggestions = scorer.suggest_improvements(schedule_data)
            suggestions = [
                SuggestionResponse(
                    type=s.get("type", "general"),
                    priority=s.get("priority", "medium"),
                    description=s.get("description", ""),
                    impact=s.get("impact", 0.1),
                    affected_items=s.get("affected_items", []),
                )
                for s in raw_suggestions
            ]

        # Convert result to response
        return ScheduleScoreResponse(
            overall_score=result.get("overall_score", 0.75),
            grade=result.get("grade", "B"),
            components=[
                ScoreComponentResponse(
                    name=comp_name,
                    score=comp_data.get("score", 0.75),
                    weight=comp_data.get("weight", 0.33),
                    details=comp_data.get("details", {}),
                )
                for comp_name, comp_data in result.get("components", {}).items()
            ],
            suggestions=suggestions,
            metadata={"ml_enabled": True},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring failed: {str(e)}",
        )


@router.post("/predict/conflict", response_model=ConflictPredictionResponse)
async def predict_conflict(
    request: PredictConflictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Predict conflict probability for a proposed assignment.
    """
    if not settings.ML_ENABLED:
        return ConflictPredictionResponse(
            conflict_probability=0.2,
            risk_level="LOW",
            risk_factors=["ML disabled, using default prediction"],
            recommendation="Proceed with caution.",
        )

    try:
        from app.ml import ConflictPredictor

        models_dir = Path(settings.ML_MODELS_DIR)
        model_path = models_dir / "conflict_predictor"

        if not model_path.exists():
            return ConflictPredictionResponse(
                conflict_probability=0.3,
                risk_level="MEDIUM",
                risk_factors=["Model not trained"],
                recommendation="Train model for accurate predictions.",
            )

        predictor = ConflictPredictor()
        predictor.load(model_path)

        prob = predictor.predict_conflict_probability(
            person_data={"id": request.person_id},
            assignment_data={
                "block_id": request.block_id,
                "rotation_id": request.rotation_id,
            },
            existing_assignments=request.existing_assignments,
            context={},
        )

        # Determine risk level
        if prob >= 0.8:
            risk_level = "CRITICAL"
            recommendation = "High conflict risk. Consider alternative assignment."
        elif prob >= 0.6:
            risk_level = "HIGH"
            recommendation = (
                "Elevated conflict risk. Review carefully before proceeding."
            )
        elif prob >= 0.4:
            risk_level = "MEDIUM"
            recommendation = "Moderate conflict risk. Monitor after assignment."
        elif prob >= 0.2:
            risk_level = "LOW"
            recommendation = "Low conflict risk. Proceed normally."
        else:
            risk_level = "MINIMAL"
            recommendation = "Minimal conflict risk."

        return ConflictPredictionResponse(
            conflict_probability=prob,
            risk_level=risk_level,
            risk_factors=[],  # Would come from explain_conflict_risk
            recommendation=recommendation,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/predict/preference", response_model=PreferencePredictionResponse)
async def predict_preference(
    request: PredictPreferenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Predict preference score for a proposed assignment.
    """
    if not settings.ML_ENABLED:
        return PreferencePredictionResponse(
            preference_score=0.6,
            interpretation="ML disabled, using default prediction",
            contributing_factors=[],
        )

    try:
        from app.ml import PreferencePredictor

        models_dir = Path(settings.ML_MODELS_DIR)
        model_path = models_dir / "preference_predictor"

        if not model_path.exists():
            return PreferencePredictionResponse(
                preference_score=0.5,
                interpretation="Model not trained",
                contributing_factors=[],
            )

        predictor = PreferencePredictor()
        predictor.load(model_path)

        score = predictor.predict(
            person_data={"id": request.person_id},
            rotation_data={"id": request.rotation_id},
            block_data={"id": request.block_id},
        )

        # Interpret score
        if score >= 0.8:
            interpretation = "Highly preferred assignment"
        elif score >= 0.6:
            interpretation = "Preferred assignment"
        elif score >= 0.4:
            interpretation = "Acceptable assignment"
        elif score >= 0.2:
            interpretation = "Less preferred assignment"
        else:
            interpretation = "Avoid if possible"

        return PreferencePredictionResponse(
            preference_score=score,
            interpretation=interpretation,
            contributing_factors=[],  # Would come from explain_prediction
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/analyze/workload", response_model=WorkloadAnalysisResponse)
async def analyze_workload(
    request: WorkloadAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Analyze workload distribution across personnel.
    """
    if not settings.ML_ENABLED:
        return WorkloadAnalysisResponse(
            total_people=0,
            overloaded_count=0,
            underutilized_count=0,
            fairness_score=0.75,
            gini_coefficient=0.2,
            people=[],
            rebalancing_suggestions=[
                SuggestionResponse(
                    type="info",
                    priority="low",
                    description="ML disabled. Enable ML for detailed workload analysis.",
                    impact=0.0,
                )
            ],
        )

    try:
        from app.ml import WorkloadOptimizer

        models_dir = Path(settings.ML_MODELS_DIR)
        model_path = models_dir / "workload_optimizer"

        if not model_path.exists():
            return WorkloadAnalysisResponse(
                total_people=0,
                overloaded_count=0,
                underutilized_count=0,
                fairness_score=0.5,
                gini_coefficient=0.5,
                people=[],
                rebalancing_suggestions=[
                    SuggestionResponse(
                        type="warning",
                        priority="high",
                        description="Workload model not trained. Run training first.",
                        impact=0.0,
                    )
                ],
            )

        optimizer = WorkloadOptimizer()
        optimizer.load(model_path)

        # This would need actual data from the database
        # For now, return placeholder response
        return WorkloadAnalysisResponse(
            total_people=0,
            overloaded_count=0,
            underutilized_count=0,
            fairness_score=0.75,
            gini_coefficient=0.2,
            people=[],
            rebalancing_suggestions=[
                SuggestionResponse(
                    type="info",
                    priority="low",
                    description="Full workload analysis requires schedule data.",
                    impact=0.0,
                )
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )
