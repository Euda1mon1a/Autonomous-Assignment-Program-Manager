"""
Unit tests for analytics service.

Tests analytics functionality including:
- Fairness metrics (Gini coefficient, workload distribution)
- Workload analysis (hours per person, weekend/holiday distribution)
- Trend calculation (weekly, monthly, year-over-year)
- Report generation (monthly, resident, compliance, workload)
- Coverage and compliance metrics
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.analytics.engine import AnalyticsEngine
from app.analytics.metrics import (
    calculate_acgme_compliance_rate,
    calculate_consecutive_duty_stats,
    calculate_coverage_rate,
    calculate_fairness_index,
    calculate_preference_satisfaction,
)
from app.analytics.reports import ReportGenerator
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun

# ============================================================================
# Fairness Metrics Tests
# ============================================================================


class TestFairnessMetrics:
    """Test suite for fairness metrics calculation."""

    def test_calculate_fairness_index_perfect_distribution(self):
        """Test fairness index with perfectly equal distribution."""
        # Create assignments with equal distribution (5 per person, 3 people)
        assignments = []
        for person_idx in range(3):
            for _ in range(5):
                assignments.append(
                    {"person_id": str(uuid4()) if person_idx == 0 else str(uuid4())}
                )

        # Use same person IDs for equal distribution
        person_ids = [str(uuid4()) for _ in range(3)]
        assignments = [{"person_id": person_ids[i % 3]} for i in range(15)]

        result = calculate_fairness_index(assignments)

        assert result["value"] >= 0.95  # Very high fairness
        assert result["status"] == "good"
        assert result["details"]["min_assignments"] == 5
        assert result["details"]["max_assignments"] == 5
        assert result["details"]["std_dev"] == 0  # Perfect equality

    def test_calculate_fairness_index_unequal_distribution(self):
        """Test fairness index with unequal distribution."""
        # Create assignments with unequal distribution
        person_a = str(uuid4())
        person_b = str(uuid4())
        person_c = str(uuid4())

        assignments = (
            [{"person_id": person_a}] * 10  # Person A gets 10
            + [{"person_id": person_b}] * 2  # Person B gets 2
            + [{"person_id": person_c}] * 2  # Person C gets 2
        )

        result = calculate_fairness_index(assignments)

        assert result["value"] < 0.9  # Low fairness due to inequality
        assert result["status"] in ["warning", "critical"]
        assert result["details"]["min_assignments"] == 2
        assert result["details"]["max_assignments"] == 10
        assert result["details"]["std_dev"] > 0

    def test_calculate_fairness_index_empty_assignments(self):
        """Test fairness index with no assignments."""
        result = calculate_fairness_index([])

        assert result["value"] == 1.0  # Perfect fairness (no assignments)
        assert result["status"] == "good"
        assert "no assignments" in result["description"].lower()

    def test_calculate_gini_coefficient_calculation(self):
        """Test that Gini coefficient is calculated correctly."""
        # Create known distribution
        person_ids = [str(uuid4()) for _ in range(4)]
        assignments = (
            [{"person_id": person_ids[0]}] * 1
            + [{"person_id": person_ids[1]}] * 2
            + [{"person_id": person_ids[2]}] * 3
            + [{"person_id": person_ids[3]}] * 4
        )

        result = calculate_fairness_index(assignments)

        # Should detect inequality
        assert 0.0 <= result["value"] <= 1.0
        assert result["value"] < 1.0  # Not perfect equality
        assert result["details"]["mean_assignments"] == 2.5


# ============================================================================
# Workload Analysis Tests
# ============================================================================


class TestWorkloadAnalysis:
    """Test suite for workload analysis."""

    def test_get_resident_workload_distribution(
        self, db: Session, sample_residents: list[Person], sample_blocks: list[Block]
    ):
        """Test workload distribution calculation across residents."""
        engine = AnalyticsEngine(db)

        # Create assignments with different workloads
        for i, resident in enumerate(sample_residents):
            # Give different amounts: PGY1 gets 3, PGY2 gets 5, PGY3 gets 7
            num_blocks = 3 + (i * 2)
            for j in range(num_blocks):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=sample_blocks[j].id,
                    person_id=resident.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = engine.get_resident_workload_distribution()

        assert result["statistics"]["total_residents"] == 3
        assert result["statistics"]["min_assignments"] == 3
        assert result["statistics"]["max_assignments"] == 7
        assert result["statistics"]["average_assignments"] == 5.0
        assert len(result["residents"]) == 3

    def test_workload_utilization_calculation(
        self, db: Session, sample_resident: Person, sample_blocks: list[Block]
    ):
        """Test that utilization percentage is calculated correctly."""
        engine = AnalyticsEngine(db)

        # Set target blocks
        sample_resident.target_clinical_blocks = 10
        db.commit()

        # Assign 8 blocks (80% utilization)
        for i in range(8):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = engine.get_resident_workload_distribution()

        # Find the resident's data
        resident_data = next(
            r for r in result["residents"] if r["person_id"] == str(sample_resident.id)
        )
        assert resident_data["assignments"] == 8
        assert resident_data["target"] == 10
        assert resident_data["utilization_percent"] == 80.0
        assert resident_data["variance"] == -2

    def test_consecutive_duty_stats_calculation(self):
        """Test consecutive duty statistics calculation."""
        person_id = str(uuid4())
        base_date = date.today()

        # Create assignments for 5 consecutive days, then 2 days off, then 3 consecutive days
        assignments = [
            {"person_id": person_id, "block_date": base_date + timedelta(days=i)}
            for i in range(5)
        ] + [
            {"person_id": person_id, "block_date": base_date + timedelta(days=7 + i)}
            for i in range(3)
        ]

        result = calculate_consecutive_duty_stats(person_id, assignments)

        assert result["person_id"] == person_id
        assert result["max_consecutive_days"] == 5
        assert result["total_duty_days"] == 8
        assert result["status"] == "good"  # 5 days is within ACGME limits (<=6)

    def test_consecutive_duty_stats_acgme_violation(self):
        """Test consecutive duty stats detects ACGME violations."""
        person_id = str(uuid4())
        base_date = date.today()

        # Create assignments for 10 consecutive days (violates ACGME)
        assignments = [
            {"person_id": person_id, "block_date": base_date + timedelta(days=i)}
            for i in range(10)
        ]

        result = calculate_consecutive_duty_stats(person_id, assignments)

        assert result["max_consecutive_days"] == 10
        assert result["status"] == "warning"  # 10 days exceeds 6-day limit
        assert result["average_rest_days"] == 0

    def test_weekend_holiday_distribution(
        self, db: Session, sample_residents: list[Person]
    ):
        """Test weekend and holiday workload distribution."""
        # Create blocks including weekends and holidays
        blocks = []
        start_date = date(2025, 1, 1)

        for i in range(14):  # 2 weeks
            current_date = start_date + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=(i == 0),  # Jan 1 is a holiday
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Assign weekends/holidays unevenly
        weekend_blocks = [b for b in blocks if b.is_weekend or b.is_holiday]
        for i, block in enumerate(weekend_blocks):
            # Give all weekend/holiday shifts to first resident
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Calculate distribution
        weekend_assignments = (
            db.query(Assignment)
            .join(Block)
            .filter(Block.is_weekend == True)  # noqa: E712
            .all()
        )

        # All weekend assignments should go to one person
        weekend_person_ids = {str(a.person_id) for a in weekend_assignments}
        assert len(weekend_person_ids) == 1
        assert str(sample_residents[0].id) in weekend_person_ids


# ============================================================================
# Coverage and Compliance Tests
# ============================================================================


class TestCoverageAndCompliance:
    """Test suite for coverage rate and ACGME compliance metrics."""

    def test_calculate_coverage_rate_full_coverage(self):
        """Test coverage rate with 100% coverage."""
        blocks = [{"id": str(uuid4())} for _ in range(10)]
        assignments = [{"block_id": b["id"]} for b in blocks]

        result = calculate_coverage_rate(blocks, assignments)

        assert result["value"] == 100.0
        assert result["status"] == "good"
        assert result["details"]["covered_blocks"] == 10
        assert result["details"]["uncovered_blocks"] == 0

    def test_calculate_coverage_rate_partial_coverage(self):
        """Test coverage rate with partial coverage."""
        blocks = [{"id": str(uuid4())} for _ in range(10)]
        # Only cover 8 out of 10 blocks
        assignments = [{"block_id": blocks[i]["id"]} for i in range(8)]

        result = calculate_coverage_rate(blocks, assignments)

        assert result["value"] == 80.0
        assert result["status"] == "warning"
        assert result["details"]["covered_blocks"] == 8
        assert result["details"]["uncovered_blocks"] == 2

    def test_calculate_coverage_rate_no_blocks(self):
        """Test coverage rate with no blocks."""
        result = calculate_coverage_rate([], [])

        assert result["value"] == 100.0
        assert result["status"] == "good"
        assert "no blocks" in result["description"].lower()

    def test_calculate_acgme_compliance_rate_perfect(self):
        """Test ACGME compliance with no violations."""
        result = calculate_acgme_compliance_rate(violations=0, total_checks=100)

        assert result["value"] == 100.0
        assert result["status"] == "good"
        assert result["details"]["violations"] == 0
        assert result["details"]["compliance_checks_passed"] == 100

    def test_calculate_acgme_compliance_rate_with_violations(self):
        """Test ACGME compliance with violations."""
        result = calculate_acgme_compliance_rate(violations=5, total_checks=100)

        assert result["value"] == 95.0
        assert result["status"] == "warning"  # Has violations but >90%
        assert result["details"]["violations"] == 5

    def test_calculate_acgme_compliance_rate_critical(self):
        """Test ACGME compliance in critical state."""
        result = calculate_acgme_compliance_rate(violations=15, total_checks=100)

        assert result["value"] == 85.0
        assert result["status"] == "critical"  # <90% compliance
        assert result["details"]["violations"] == 15


# ============================================================================
# Preference Satisfaction Tests
# ============================================================================


class TestPreferenceSatisfaction:
    """Test suite for preference satisfaction metrics."""

    def test_calculate_preference_satisfaction_perfect(self):
        """Test preference satisfaction with all preferences met."""
        person_a = str(uuid4())
        rotation_x = str(uuid4())
        rotation_y = str(uuid4())

        preferences = [{"person_id": person_a, "rotation_template_id": rotation_x}]

        assignments = [{"person_id": person_a, "rotation_template_id": rotation_x}]

        result = calculate_preference_satisfaction(assignments, preferences)

        assert result["value"] == 100.0
        assert result["status"] == "good"
        assert result["details"]["preferences_matched"] == 1

    def test_calculate_preference_satisfaction_partial(self):
        """Test preference satisfaction with some preferences not met."""
        person_a = str(uuid4())
        rotation_x = str(uuid4())
        rotation_y = str(uuid4())

        preferences = [
            {"person_id": person_a, "rotation_template_id": rotation_x},
            {"person_id": person_a, "rotation_template_id": rotation_y},
        ]

        assignments = [
            {"person_id": person_a, "rotation_template_id": rotation_x},
            {"person_id": person_a, "rotation_template_id": rotation_y},
            {
                "person_id": person_a,
                "rotation_template_id": str(uuid4()),
            },  # Not preferred
        ]

        result = calculate_preference_satisfaction(assignments, preferences)

        assert result["value"] == pytest.approx(66.67, abs=0.1)
        assert result["status"] in ["warning", "good"]

    def test_calculate_preference_satisfaction_no_preferences(self):
        """Test preference satisfaction with no stated preferences."""
        result = calculate_preference_satisfaction([], [])

        assert result["value"] == 100.0
        assert result["status"] == "good"
        assert "no preferences" in result["description"].lower()


# ============================================================================
# Trend Analysis Tests
# ============================================================================


class TestTrendAnalysis:
    """Test suite for trend calculation."""

    def test_get_trend_analysis_violations(self, db: Session):
        """Test trend analysis for violations over time."""
        engine = AnalyticsEngine(db)

        # Create schedule runs with different violation counts
        for i in range(5):
            run = ScheduleRun(
                id=uuid4(),
                start_date=date.today() - timedelta(days=30 * (4 - i)),
                end_date=date.today() - timedelta(days=30 * (4 - i) - 7),
                algorithm="cp_sat",
                status="success",
                acgme_violations=i * 2,  # Increasing violations
                total_blocks_assigned=14,
                runtime_seconds=5.0,
                created_at=datetime.utcnow(),
            )
            db.add(run)
        db.commit()

        result = engine.get_trend_analysis(metric="violations", period="monthly")

        assert result["metric"] == "violations"
        assert result["total_runs"] == 5
        assert len(result["data_points"]) == 5
        # Violations should increase over time
        assert result["data_points"][0]["value"] == 0
        assert result["data_points"][4]["value"] == 8

    def test_get_trend_analysis_coverage(self, db: Session):
        """Test trend analysis for coverage over time."""
        engine = AnalyticsEngine(db)

        # Create schedule runs with varying coverage
        for i in range(3):
            run = ScheduleRun(
                id=uuid4(),
                start_date=date.today() - timedelta(days=7 * (2 - i)),
                end_date=date.today() - timedelta(days=7 * (2 - i) - 7),
                algorithm="cp_sat",
                status="success",
                acgme_violations=0,
                total_blocks_assigned=14 * (i + 1) // 3,  # Varying coverage
                runtime_seconds=5.0,
                created_at=datetime.utcnow(),
            )
            db.add(run)
        db.commit()

        result = engine.get_trend_analysis(metric="coverage", period="weekly")

        assert result["metric"] == "coverage"
        assert result["total_runs"] == 3
        assert all("value" in dp for dp in result["data_points"])

    def test_get_trend_analysis_runtime(self, db: Session):
        """Test trend analysis for runtime performance."""
        engine = AnalyticsEngine(db)

        # Create schedule runs with increasing runtime
        for i in range(4):
            run = ScheduleRun(
                id=uuid4(),
                start_date=date.today() - timedelta(days=i),
                end_date=date.today() - timedelta(days=i) + timedelta(days=7),
                algorithm="cp_sat",
                status="success",
                acgme_violations=0,
                total_blocks_assigned=14,
                runtime_seconds=5.0 + (i * 2.0),  # Increasing runtime
                created_at=datetime.utcnow(),
            )
            db.add(run)
        db.commit()

        result = engine.get_trend_analysis(metric="runtime", period="daily")

        assert result["metric"] == "runtime"
        assert result["total_runs"] == 4
        # Runtime should increase
        assert result["data_points"][0]["value"] == 5.0
        assert result["data_points"][3]["value"] == 11.0


# ============================================================================
# Report Generation Tests
# ============================================================================


class TestReportGeneration:
    """Test suite for report generation."""

    def test_generate_monthly_report(
        self, db: Session, sample_residents: list[Person], sample_blocks: list[Block]
    ):
        """Test monthly report generation."""
        generator = ReportGenerator(db)

        # Create some assignments
        for i, resident in enumerate(sample_residents):
            for j in range(3):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=sample_blocks[j + i].id,
                    person_id=resident.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Generate report for current month
        today = date.today()
        report = generator.generate_monthly_report(year=today.year, month=today.month)

        assert report["report_type"] == "monthly"
        assert report["period"]["year"] == today.year
        assert report["period"]["month"] == today.month
        assert "summary" in report
        assert "metrics" in report
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)

    def test_generate_resident_report(
        self, db: Session, sample_resident: Person, sample_blocks: list[Block]
    ):
        """Test individual resident report generation."""
        generator = ReportGenerator(db)

        # Set target blocks
        sample_resident.target_clinical_blocks = 10
        db.commit()

        # Create assignments
        for i in range(5):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        report = generator.generate_resident_report(
            person_id=str(sample_resident.id), start_date=start_date, end_date=end_date
        )

        assert report["report_type"] == "resident"
        assert report["person"]["id"] == str(sample_resident.id)
        assert report["person"]["name"] == sample_resident.name
        assert report["summary"]["total_assignments"] == 5
        assert "duty_patterns" in report
        assert "recommendations" in report

    def test_generate_compliance_report(self, db: Session):
        """Test ACGME compliance report generation."""
        generator = ReportGenerator(db)

        # Create schedule runs with violations
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=3,
            acgme_override_count=1,
            total_blocks_assigned=14,
            runtime_seconds=5.0,
            created_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()

        report = generator.generate_compliance_report(
            start_date=start_date, end_date=end_date
        )

        assert report["report_type"] == "compliance"
        assert report["summary"]["total_violations"] == 3
        assert report["summary"]["acknowledged_overrides"] == 1
        assert report["summary"]["unacknowledged_violations"] == 2
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0

    def test_generate_workload_report(self, db: Session, sample_blocks: list[Block]):
        """Test workload distribution report generation."""
        generator = ReportGenerator(db)

        # Create residents with different workloads
        residents = []
        for i in range(3):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Test {i}",
                type="resident",
                pgy_level=i + 1,
                target_clinical_blocks=10,
            )
            db.add(resident)
            residents.append(resident)
        db.commit()

        # Assign different amounts
        for i, resident in enumerate(residents):
            num_assignments = 5 + (i * 3)  # 5, 8, 11
            for j in range(num_assignments):
                if j < len(sample_blocks):
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=sample_blocks[j].id,
                        person_id=resident.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        report = generator.generate_workload_report(
            start_date=start_date, end_date=end_date
        )

        assert report["report_type"] == "workload"
        assert report["summary"]["total_residents"] == 3
        assert "fairness_index" in report["summary"]
        assert "over_utilized_count" in report["summary"]
        assert "under_utilized_count" in report["summary"]
        assert len(report["details"]["workload_by_resident"]) == 3


# ============================================================================
# Schedule Comparison Tests
# ============================================================================


class TestScheduleComparison:
    """Test suite for schedule version comparison."""

    def test_compare_schedules_basic(self, db: Session):
        """Test comparing two schedule versions."""
        engine = AnalyticsEngine(db)

        # Create two schedule runs
        run1 = ScheduleRun(
            id=uuid4(),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            algorithm="greedy",
            status="success",
            acgme_violations=5,
            total_blocks_assigned=14,
            runtime_seconds=3.0,
            created_at=datetime.utcnow(),
        )

        run2 = ScheduleRun(
            id=uuid4(),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            acgme_violations=2,
            total_blocks_assigned=14,
            runtime_seconds=7.5,
            created_at=datetime.utcnow(),
        )

        db.add(run1)
        db.add(run2)
        db.commit()

        comparison = engine.compare_schedules(str(run1.id), str(run2.id))

        assert comparison["run_1"]["id"] == str(run1.id)
        assert comparison["run_2"]["id"] == str(run2.id)
        assert comparison["differences"]["violations_delta"] == -3  # Improvement
        assert comparison["differences"]["blocks_delta"] == 0  # Same
        assert comparison["differences"]["runtime_delta"] == 4.5  # Slower

    def test_compare_schedules_not_found(self, db: Session):
        """Test comparing schedules when one doesn't exist."""
        engine = AnalyticsEngine(db)

        fake_id1 = str(uuid4())
        fake_id2 = str(uuid4())

        comparison = engine.compare_schedules(fake_id1, fake_id2)

        assert "error" in comparison
        assert "not found" in comparison["error"].lower()


# ============================================================================
# Analytics Engine Integration Tests
# ============================================================================


class TestAnalyticsEngineIntegration:
    """Test suite for AnalyticsEngine comprehensive analysis."""

    def test_analyze_schedule_comprehensive(
        self, db: Session, sample_residents: list[Person], sample_blocks: list[Block]
    ):
        """Test comprehensive schedule analysis."""
        engine = AnalyticsEngine(db)

        # Create schedule run
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=1,
            acgme_override_count=0,
            total_blocks_assigned=14,
            runtime_seconds=5.0,
            created_at=datetime.utcnow(),
        )
        db.add(run)

        # Create assignments
        for i, resident in enumerate(sample_residents):
            for j in range(3):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=sample_blocks[i * 3 + j].id,
                    person_id=resident.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = engine.analyze_schedule(start_date, end_date)

        assert "period" in result
        assert result["period"]["start_date"] == start_date.isoformat()
        assert result["period"]["end_date"] == end_date.isoformat()
        assert "summary" in result
        assert "metrics" in result
        assert "fairness" in result["metrics"]
        assert "coverage" in result["metrics"]
        assert "compliance" in result["metrics"]
        assert "workload" in result
        assert "violations" in result

    def test_get_rotation_coverage_stats(
        self, db: Session, sample_resident: Person, sample_blocks: list[Block]
    ):
        """Test rotation coverage statistics."""
        engine = AnalyticsEngine(db)

        # Create rotation templates
        rotation_a = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            rotation_type="clinic",
            abbreviation="CA",
        )
        rotation_b = RotationTemplate(
            id=uuid4(),
            name="Procedures B",
            rotation_type="procedures",
            abbreviation="PB",
        )
        db.add(rotation_a)
        db.add(rotation_b)
        db.commit()

        # Create assignments
        for i in range(5):
            rotation = rotation_a if i < 3 else rotation_b
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=sample_resident.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = engine.get_rotation_coverage_stats()

        assert "rotations" in result
        assert "by_rotation_type" in result
        assert result["total_rotations"] == 2
        assert "clinic" in result["by_rotation_type"]
        assert "procedures" in result["by_rotation_type"]


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestAnalyticsEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_fairness_index_single_person(self):
        """Test fairness index with only one person."""
        person_id = str(uuid4())
        assignments = [{"person_id": person_id}] * 10

        result = calculate_fairness_index(assignments)

        assert result["value"] == 1.0  # Perfect fairness (only one person)
        assert result["status"] == "good"
        assert result["details"]["std_dev"] == 0

    def test_consecutive_duty_stats_no_assignments(self):
        """Test consecutive duty stats with no assignments."""
        person_id = str(uuid4())

        result = calculate_consecutive_duty_stats(person_id, [])

        assert result["person_id"] == person_id
        assert result["max_consecutive_days"] == 0
        assert result["total_duty_days"] == 0
        assert result["status"] == "good"

    def test_generate_resident_report_person_not_found(self, db: Session):
        """Test resident report for non-existent person."""
        generator = ReportGenerator(db)

        fake_id = str(uuid4())
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        report = generator.generate_resident_report(fake_id, start_date, end_date)

        assert "error" in report
        assert "not found" in report["error"].lower()

    def test_workload_distribution_no_residents(self, db: Session):
        """Test workload distribution with no residents."""
        engine = AnalyticsEngine(db)

        result = engine.get_resident_workload_distribution()

        assert result["statistics"]["total_residents"] == 0
        assert result["statistics"]["average_assignments"] == 0
        assert len(result["residents"]) == 0

    def test_coverage_rate_multiple_assignments_per_block(self):
        """Test coverage rate when blocks have multiple assignments."""
        blocks = [{"id": str(uuid4())} for _ in range(5)]
        # Multiple assignments for same block
        assignments = (
            [{"block_id": blocks[0]["id"]}] * 3
            + [{"block_id": blocks[1]["id"]}] * 2
            + [{"block_id": blocks[2]["id"]}]
        )

        result = calculate_coverage_rate(blocks, assignments)

        # Should count unique covered blocks (3 out of 5)
        assert result["value"] == 60.0
        assert result["details"]["covered_blocks"] == 3
