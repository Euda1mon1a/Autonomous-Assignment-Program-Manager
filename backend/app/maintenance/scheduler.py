"""Automated backup scheduling service."""
import json
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.maintenance.backup import BackupService


class BackupScheduler:
    """Service for scheduling and managing automated backups."""

    def __init__(self, db: Session, backup_dir: str = "backups"):
        """
        Initialize backup scheduler.

        Args:
            db: Database session
            backup_dir: Directory to store backups
        """
        self.db = db
        self.backup_service = BackupService(db, backup_dir)
        self.config_path = Path(backup_dir) / "scheduler_config.json"
        self.config = self._load_config()

    def schedule_daily_backup(
        self,
        backup_time: time,
        compress: bool = True,
        enabled: bool = True
    ) -> dict[str, Any]:
        """
        Configure daily automated backups.

        Args:
            backup_time: Time of day to run backup (e.g., time(2, 0) for 2 AM)
            compress: Whether to compress backups
            enabled: Whether the schedule is enabled

        Returns:
            Schedule configuration
        """
        schedule = {
            "type": "daily",
            "time": backup_time.isoformat(),
            "compress": compress,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
        }

        self.config["daily_backup"] = schedule
        self._save_config()

        return schedule

    def schedule_weekly_backup(
        self,
        day_of_week: int,
        backup_time: time,
        compress: bool = True,
        enabled: bool = True
    ) -> dict[str, Any]:
        """
        Configure weekly full backups.

        Args:
            day_of_week: Day of week (0=Monday, 6=Sunday)
            backup_time: Time of day to run backup
            compress: Whether to compress backups
            enabled: Whether the schedule is enabled

        Returns:
            Schedule configuration
        """
        if not 0 <= day_of_week <= 6:
            raise ValueError("day_of_week must be between 0 (Monday) and 6 (Sunday)")

        schedule = {
            "type": "weekly",
            "day_of_week": day_of_week,
            "time": backup_time.isoformat(),
            "compress": compress,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
        }

        self.config["weekly_backup"] = schedule
        self._save_config()

        return schedule

    def set_retention_policy(
        self,
        days: int | None = None,
        count: int | None = None
    ) -> dict[str, Any]:
        """
        Set backup retention policy.

        Args:
            days: Keep backups for this many days (None = no time limit)
            count: Keep this many most recent backups (None = no count limit)

        Returns:
            Retention policy configuration
        """
        policy = {
            "keep_days": days,
            "keep_count": count,
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.config["retention_policy"] = policy
        self._save_config()

        return policy

    def get_next_scheduled(self) -> dict[str, Any] | None:
        """
        Get the next scheduled backup time.

        Returns:
            Dictionary with next backup info or None if no schedules
        """
        now = datetime.utcnow()
        next_backups = []

        # Check daily backup
        if self.config.get("daily_backup", {}).get("enabled"):
            daily = self.config["daily_backup"]
            backup_time = time.fromisoformat(daily["time"])
            next_daily = datetime.combine(now.date(), backup_time)

            if next_daily <= now:
                next_daily += timedelta(days=1)

            next_backups.append({
                "type": "daily",
                "scheduled_time": next_daily.isoformat(),
                "schedule": daily
            })

        # Check weekly backup
        if self.config.get("weekly_backup", {}).get("enabled"):
            weekly = self.config["weekly_backup"]
            backup_time = time.fromisoformat(weekly["time"])
            target_day = weekly["day_of_week"]

            # Calculate next occurrence of target day
            days_ahead = target_day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_weekly = datetime.combine(
                now.date() + timedelta(days=days_ahead),
                backup_time
            )

            # If it's today but time has passed, schedule for next week
            if next_weekly <= now:
                next_weekly += timedelta(days=7)

            next_backups.append({
                "type": "weekly",
                "scheduled_time": next_weekly.isoformat(),
                "schedule": weekly
            })

        if not next_backups:
            return None

        # Return the soonest scheduled backup
        return min(next_backups, key=lambda x: x["scheduled_time"])

    def run_pending_backups(self) -> list[dict[str, Any]]:
        """
        Execute any backups that are due.

        Returns:
            List of backup results
        """
        now = datetime.utcnow()
        results = []

        # Check and run daily backup
        daily = self.config.get("daily_backup", {})
        if daily.get("enabled") and self._should_run_backup(daily, now):
            try:
                backup_result = self.backup_service.create_backup(
                    backup_type='full',
                    compress=daily.get("compress", True)
                )
                results.append({
                    "type": "daily",
                    "status": "success",
                    "backup": backup_result,
                    "timestamp": now.isoformat()
                })
                daily["last_run"] = now.isoformat()
            except Exception as e:
                results.append({
                    "type": "daily",
                    "status": "failed",
                    "error": str(e),
                    "timestamp": now.isoformat()
                })

        # Check and run weekly backup
        weekly = self.config.get("weekly_backup", {})
        if weekly.get("enabled") and self._should_run_backup(weekly, now):
            try:
                backup_result = self.backup_service.create_backup(
                    backup_type='full',
                    compress=weekly.get("compress", True)
                )
                results.append({
                    "type": "weekly",
                    "status": "success",
                    "backup": backup_result,
                    "timestamp": now.isoformat()
                })
                weekly["last_run"] = now.isoformat()
            except Exception as e:
                results.append({
                    "type": "weekly",
                    "status": "failed",
                    "error": str(e),
                    "timestamp": now.isoformat()
                })

        # Apply retention policy after backups
        if results:
            self._apply_retention_policy()
            self._save_config()

        return results

    def apply_retention_policy(self) -> dict[str, Any]:
        """
        Manually apply retention policy to delete old backups.

        Returns:
            Summary of deletions
        """
        return self._apply_retention_policy()

    def get_schedule_status(self) -> dict[str, Any]:
        """
        Get current scheduler status and configuration.

        Returns:
            Status dictionary
        """
        next_backup = self.get_next_scheduled()

        return {
            "daily_backup": self.config.get("daily_backup"),
            "weekly_backup": self.config.get("weekly_backup"),
            "retention_policy": self.config.get("retention_policy"),
            "next_scheduled": next_backup,
            "total_backups": len(self.backup_service.list_backups()),
        }

    def disable_schedule(self, schedule_type: str) -> bool:
        """
        Disable a scheduled backup.

        Args:
            schedule_type: Type of schedule ('daily' or 'weekly')

        Returns:
            True if disabled successfully
        """
        key = f"{schedule_type}_backup"
        if key in self.config:
            self.config[key]["enabled"] = False
            self._save_config()
            return True
        return False

    def enable_schedule(self, schedule_type: str) -> bool:
        """
        Enable a scheduled backup.

        Args:
            schedule_type: Type of schedule ('daily' or 'weekly')

        Returns:
            True if enabled successfully
        """
        key = f"{schedule_type}_backup"
        if key in self.config:
            self.config[key]["enabled"] = True
            self._save_config()
            return True
        return False

    # Private helper methods

    def _load_config(self) -> dict[str, Any]:
        """Load scheduler configuration from file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save scheduler configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _should_run_backup(self, schedule: dict[str, Any], now: datetime) -> bool:
        """Check if a backup should run based on schedule."""
        last_run_str = schedule.get("last_run")

        if not last_run_str:
            return True

        last_run = datetime.fromisoformat(last_run_str)
        backup_time = time.fromisoformat(schedule["time"])

        if schedule["type"] == "daily":
            # Run if last run was on a different day and current time >= scheduled time
            if last_run.date() < now.date() and now.time() >= backup_time:
                return True

        elif schedule["type"] == "weekly":
            # Run if it's the scheduled day, time is right, and hasn't run this week
            target_day = schedule.get("day_of_week")
            if (now.weekday() == target_day and
                now.time() >= backup_time and
                (now - last_run).days >= 7):
                return True

        return False

    def _apply_retention_policy(self) -> dict[str, Any]:
        """Apply retention policy to delete old backups."""
        policy = self.config.get("retention_policy", {})
        keep_days = policy.get("keep_days")
        keep_count = policy.get("keep_count")

        if not keep_days and not keep_count:
            return {"deleted": 0, "message": "No retention policy configured"}

        backups = self.backup_service.list_backups()
        deleted_count = 0

        # Apply time-based retention
        if keep_days:
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
            for backup in backups:
                backup_date = datetime.fromisoformat(backup["timestamp"])
                if backup_date < cutoff_date:
                    if self.backup_service.delete_backup(backup["backup_id"]):
                        deleted_count += 1

        # Apply count-based retention
        if keep_count:
            backups = self.backup_service.list_backups()  # Refresh after time-based deletion
            if len(backups) > keep_count:
                # Keep the most recent backups
                backups_to_delete = backups[keep_count:]
                for backup in backups_to_delete:
                    if self.backup_service.delete_backup(backup["backup_id"]):
                        deleted_count += 1

        return {
            "deleted": deleted_count,
            "message": f"Deleted {deleted_count} old backup(s)",
            "policy": policy
        }
