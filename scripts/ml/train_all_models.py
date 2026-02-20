#!/usr/bin/env python3
"""Train all ML models using historical assignment data.

Uses sync SQLAlchemy session (simpler, no greenlet issues).

Usage:
    cd ~/workspace/aapm
    backend/.venv/bin/python scripts/ml/train_all_models.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("train_all")


def main():
    from dotenv import load_dotenv
    env_path = Path.home() / ".aapm-env"
    if env_path.exists():
        load_dotenv(env_path)

    models_dir = Path(os.getenv(
        "ML_MODELS_DIR",
        str(Path(__file__).resolve().parents[2] / "models"),
    ))
    models_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Models directory: {models_dir}")

    # Use sync SQLAlchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    db_url = os.getenv("DATABASE_URL", "postgresql://scheduler@localhost:5432/residency_scheduler")
    # Ensure it's a sync URL (not asyncpg)
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")

    engine = create_engine(db_url, echo=False)

    with Session(engine) as db:
        # Quick count check
        result = db.execute(text("SELECT COUNT(*) FROM assignments"))
        count = result.scalar()
        logger.info(f"Found {count} assignments in database")

        if count < 50:
            logger.error("Not enough assignments to train. Need at least 50.")
            return

        # The TrainingDataPipeline uses async methods but supports sync sessions
        # via the _execute wrapper. We'll call the methods using asyncio.run().
        from app.ml.training.data_pipeline import TrainingDataPipeline
        pipeline = TrainingDataPipeline(db)

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=730)

        # ═══════════════════════════════════════════
        # 1. PREFERENCE PREDICTOR
        # ═══════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("Training PreferencePredictor...")
        try:
            X_pref, y_pref = asyncio.run(pipeline.extract_preference_training_data(
                start_date=start_date,
                end_date=end_date,
                min_samples=50,
            ))
            logger.info(f"  Extracted {len(X_pref)} samples, {X_pref.shape[1]} features")
            logger.info(f"  Label distribution: mean={y_pref.mean():.3f}, std={y_pref.std():.3f}")

            from app.ml.models.preference_predictor import PreferencePredictor
            pref_model = PreferencePredictor()
            pref_metrics = pref_model.train(X_pref, y_pref)
            pref_path = models_dir / "preference_predictor"
            pref_path.mkdir(parents=True, exist_ok=True)
            pref_model.save(pref_path)
            logger.info(f"  Metrics: {pref_metrics}")
        except Exception as e:
            logger.error(f"  FAILED: {e}", exc_info=True)

        # ═══════════════════════════════════════════
        # 2. CONFLICT PREDICTOR
        # ═══════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("Training ConflictPredictor...")
        try:
            X_conf, y_conf = asyncio.run(pipeline.extract_conflict_training_data(
                start_date=start_date,
                end_date=end_date,
                min_samples=50,
            ))
            logger.info(f"  Extracted {len(X_conf)} samples, {X_conf.shape[1]} features")
            logger.info(f"  Positive rate: {y_conf.mean():.3f}")

            from app.ml.models.conflict_predictor import ConflictPredictor
            conf_model = ConflictPredictor()
            conf_metrics = conf_model.train(X_conf, y_conf)
            conf_path = models_dir / "conflict_predictor"
            conf_path.mkdir(parents=True, exist_ok=True)
            conf_model.save(conf_path)
            logger.info(f"  Metrics: {conf_metrics}")
        except Exception as e:
            logger.error(f"  FAILED: {e}", exc_info=True)

        # ═══════════════════════════════════════════
        # 3. WORKLOAD OPTIMIZER
        # ═══════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("Training WorkloadOptimizer...")
        try:
            X_work, y_work = asyncio.run(pipeline.extract_workload_training_data(
                start_date=start_date,
                end_date=end_date,
                min_samples=50,
            ))
            logger.info(f"  Extracted {len(X_work)} samples, {X_work.shape[1]} features")
            logger.info(f"  Label distribution: mean={y_work.mean():.3f}, std={y_work.std():.3f}")

            from app.ml.models.workload_optimizer import WorkloadOptimizer
            work_model = WorkloadOptimizer()
            work_metrics = work_model.train(X_work, y_work)
            work_path = models_dir / "workload_optimizer"
            work_path.mkdir(parents=True, exist_ok=True)
            work_model.save(work_path)
            logger.info(f"  Metrics: {work_metrics}")
        except Exception as e:
            logger.error(f"  FAILED: {e}", exc_info=True)

        # ═══════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("Training complete. Model artifacts:")
        for subdir in ["preference_predictor", "conflict_predictor", "workload_optimizer"]:
            p = models_dir / subdir
            if p.exists():
                files = list(p.glob("*.pkl"))
                if files:
                    total_kb = sum(f.stat().st_size for f in files) / 1024
                    logger.info(f"  {subdir}/: {len(files)} files ({total_kb:.1f} KB)")
                else:
                    logger.warning(f"  {subdir}/: directory exists but no .pkl files")
            else:
                logger.warning(f"  {subdir}/: MISSING")

    engine.dispose()


if __name__ == "__main__":
    main()
