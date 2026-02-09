"""Tests for Hub Vulnerability Analysis (network theory pattern)."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from app.resilience.hub_analysis import (
    CrossTrainingPriority,
    CrossTrainingRecommendation,
    FacultyCentrality,
    HubAnalyzer,
    HubDistributionReport,
    HubProfile,
    HubProtectionPlan,
    HubProtectionStatus,
    HubRiskLevel,
)


# ==================== Enums ====================


class TestHubRiskLevel:
    def test_values(self):
        assert HubRiskLevel.LOW == "low"
        assert HubRiskLevel.CATASTROPHIC == "catastrophic"


class TestHubProtectionStatus:
    def test_values(self):
        assert HubProtectionStatus.UNPROTECTED == "unprotected"
        assert HubProtectionStatus.REDUNDANT == "redundant"


class TestCrossTrainingPriority:
    def test_values(self):
        assert CrossTrainingPriority.LOW == "low"
        assert CrossTrainingPriority.URGENT == "urgent"


# ==================== FacultyCentrality ====================


class TestFacultyCentrality:
    def _make_centrality(self, **kwargs):
        defaults = {
            "faculty_id": uuid4(),
            "faculty_name": "Dr. Test",
            "calculated_at": datetime.now(),
            "degree_centrality": 0.0,
            "betweenness_centrality": 0.0,
            "eigenvector_centrality": 0.0,
            "pagerank": 0.0,
            "services_covered": 0,
            "unique_services": 0,
            "total_assignments": 0,
            "replacement_difficulty": 0.0,
        }
        defaults.update(kwargs)
        return FacultyCentrality(**defaults)

    def test_defaults(self):
        fc = self._make_centrality()
        assert fc.composite_score == 0.0

    def test_calculate_composite_default_weights(self):
        fc = self._make_centrality(
            degree_centrality=0.5,
            betweenness_centrality=0.8,
            eigenvector_centrality=0.3,
            pagerank=0.4,
            replacement_difficulty=0.6,
        )
        score = fc.calculate_composite()
        # 0.5*0.2 + 0.8*0.3 + 0.3*0.2 + 0.4*0.15 + 0.6*0.15
        expected = 0.1 + 0.24 + 0.06 + 0.06 + 0.09
        assert abs(score - expected) < 0.001
        assert fc.composite_score == score

    def test_calculate_composite_custom_weights(self):
        fc = self._make_centrality(
            degree_centrality=1.0,
            betweenness_centrality=0.0,
            eigenvector_centrality=0.0,
            pagerank=0.0,
            replacement_difficulty=0.0,
        )
        score = fc.calculate_composite({"degree": 1.0})
        assert abs(score - 1.0) < 0.001

    def test_risk_level_catastrophic(self):
        fc = self._make_centrality(composite_score=0.9)
        assert fc.risk_level == HubRiskLevel.CATASTROPHIC

    def test_risk_level_catastrophic_unique_services(self):
        fc = self._make_centrality(unique_services=3)
        assert fc.risk_level == HubRiskLevel.CATASTROPHIC

    def test_risk_level_critical(self):
        fc = self._make_centrality(composite_score=0.65)
        assert fc.risk_level == HubRiskLevel.CRITICAL

    def test_risk_level_critical_unique_services(self):
        fc = self._make_centrality(composite_score=0.1, unique_services=2)
        assert fc.risk_level == HubRiskLevel.CRITICAL

    def test_risk_level_high(self):
        fc = self._make_centrality(composite_score=0.45)
        assert fc.risk_level == HubRiskLevel.HIGH

    def test_risk_level_high_unique_services(self):
        fc = self._make_centrality(composite_score=0.1, unique_services=1)
        assert fc.risk_level == HubRiskLevel.HIGH

    def test_risk_level_moderate(self):
        fc = self._make_centrality(composite_score=0.25)
        assert fc.risk_level == HubRiskLevel.MODERATE

    def test_risk_level_low(self):
        fc = self._make_centrality(composite_score=0.1)
        assert fc.risk_level == HubRiskLevel.LOW

    def test_is_hub_high_composite(self):
        fc = self._make_centrality(composite_score=0.5)
        assert fc.is_hub is True

    def test_is_hub_unique_services(self):
        fc = self._make_centrality(composite_score=0.1, unique_services=1)
        assert fc.is_hub is True

    def test_not_hub(self):
        fc = self._make_centrality(composite_score=0.1, unique_services=0)
        assert fc.is_hub is False


# ==================== HubAnalyzer ====================


@dataclass
class MockFaculty:
    id: UUID
    name: str


@dataclass
class MockAssignment:
    faculty_id: UUID
    block_id: UUID


class TestHubAnalyzerInit:
    def test_defaults(self):
        ha = HubAnalyzer()
        assert ha.hub_threshold == 0.4
        assert ha.critical_hub_threshold == 0.6
        assert ha.centrality_cache == {}

    def test_custom(self):
        ha = HubAnalyzer(hub_threshold=0.3, critical_hub_threshold=0.5)
        assert ha.hub_threshold == 0.3


class TestCalculateCentralityBasic:
    def _make_scenario(self):
        f1_id, f2_id, f3_id = uuid4(), uuid4(), uuid4()
        faculty = [
            MockFaculty(id=f1_id, name="Dr. A"),
            MockFaculty(id=f2_id, name="Dr. B"),
            MockFaculty(id=f3_id, name="Dr. C"),
        ]
        s1, s2, s3 = uuid4(), uuid4(), uuid4()
        services = {
            s1: [f1_id],  # Only f1 can cover s1 (SPOF)
            s2: [f1_id, f2_id],
            s3: [f1_id, f2_id, f3_id],
        }
        assignments = [
            {"faculty_id": f1_id, "block_id": uuid4()},
            {"faculty_id": f1_id, "block_id": uuid4()},
            {"faculty_id": f2_id, "block_id": uuid4()},
        ]
        return faculty, assignments, services, f1_id

    def test_basic_centrality(self):
        ha = HubAnalyzer(use_networkx=False)
        faculty, assignments, services, f1_id = self._make_scenario()
        results = ha.calculate_centrality(faculty, assignments, services)
        assert len(results) == 3
        # f1 covers all services and is the only one for s1 → highest score
        assert results[0].faculty_id == f1_id

    def test_unique_services_detected(self):
        ha = HubAnalyzer(use_networkx=False)
        faculty, assignments, services, f1_id = self._make_scenario()
        results = ha.calculate_centrality(faculty, assignments, services)
        f1_result = next(r for r in results if r.faculty_id == f1_id)
        assert f1_result.unique_services == 1
        assert f1_result.services_covered == 3

    def test_results_cached(self):
        ha = HubAnalyzer(use_networkx=False)
        faculty, assignments, services, _ = self._make_scenario()
        ha.calculate_centrality(faculty, assignments, services)
        assert len(ha.centrality_cache) == 3

    def test_sorted_by_composite_desc(self):
        ha = HubAnalyzer(use_networkx=False)
        faculty, assignments, services, _ = self._make_scenario()
        results = ha.calculate_centrality(faculty, assignments, services)
        scores = [r.composite_score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestCalculateCentralityNetworkx:
    def test_networkx_centrality(self):
        ha = HubAnalyzer(use_networkx=True)
        f1_id, f2_id = uuid4(), uuid4()
        faculty = [
            MockFaculty(id=f1_id, name="Dr. A"),
            MockFaculty(id=f2_id, name="Dr. B"),
        ]
        s1 = uuid4()
        services = {s1: [f1_id, f2_id]}
        assignments = [{"faculty_id": f1_id, "block_id": uuid4()}]
        results = ha.calculate_centrality(faculty, assignments, services)
        assert len(results) == 2


class TestIdentifyHubs:
    def test_identifies_hubs(self):
        ha = HubAnalyzer(use_networkx=False)
        f1_id, f2_id = uuid4(), uuid4()
        faculty = [
            MockFaculty(id=f1_id, name="Dr. Hub"),
            MockFaculty(id=f2_id, name="Dr. Normal"),
        ]
        s1, s2 = uuid4(), uuid4()
        services = {
            s1: [f1_id],  # SPOF
            s2: [f1_id, f2_id],
        }
        results = ha.calculate_centrality(faculty, [], services)
        hubs = ha.identify_hubs(results)
        assert any(h.faculty_id == f1_id for h in hubs)

    def test_no_hubs(self):
        ha = HubAnalyzer()
        fc = FacultyCentrality(
            faculty_id=uuid4(),
            faculty_name="Nobody",
            calculated_at=datetime.now(),
            composite_score=0.1,
        )
        ha.centrality_cache[fc.faculty_id] = fc
        hubs = ha.identify_hubs()
        assert len(hubs) == 0


class TestCreateHubProfile:
    def test_creates_profile(self):
        ha = HubAnalyzer()
        fid = uuid4()
        s1, s2 = uuid4(), uuid4()
        services = {
            s1: [fid],  # unique
            s2: [fid, uuid4()],
        }
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.7,
            unique_services=1,
            betweenness_centrality=0.6,
            replacement_difficulty=0.8,
        )
        ha.centrality_cache[fid] = fc

        profile = ha.create_hub_profile(fid, services, {s1: "ICU", s2: "Clinic"})
        assert profile is not None
        assert "ICU" in profile.unique_skills
        assert len(profile.risk_factors) > 0
        assert len(profile.mitigation_actions) > 0

    def test_no_centrality_returns_none(self):
        ha = HubAnalyzer()
        assert ha.create_hub_profile(uuid4(), {}) is None


class TestGenerateCrossTrainingRecommendations:
    def test_single_provider_high_priority(self):
        ha = HubAnalyzer()
        f1 = uuid4()
        s1 = uuid4()
        services = {s1: [f1]}
        recs = ha.generate_cross_training_recommendations(
            services, {s1: "ICU"}, [f1, uuid4()]
        )
        assert len(recs) == 1
        assert recs[0].priority == CrossTrainingPriority.HIGH

    def test_no_provider_urgent(self):
        ha = HubAnalyzer()
        s1 = uuid4()
        services = {s1: []}
        recs = ha.generate_cross_training_recommendations(
            services, {s1: "OR"}, [uuid4()]
        )
        assert recs[0].priority == CrossTrainingPriority.URGENT

    def test_dual_provider_medium(self):
        ha = HubAnalyzer()
        f1, f2 = uuid4(), uuid4()
        s1 = uuid4()
        services = {s1: [f1, f2]}
        recs = ha.generate_cross_training_recommendations(
            services, {s1: "Clinic"}, [f1, f2, uuid4()]
        )
        assert recs[0].priority == CrossTrainingPriority.MEDIUM

    def test_well_covered_no_recommendations(self):
        ha = HubAnalyzer()
        s1 = uuid4()
        services = {s1: [uuid4() for _ in range(5)]}
        recs = ha.generate_cross_training_recommendations(services)
        assert len(recs) == 0

    def test_sorted_by_priority(self):
        ha = HubAnalyzer()
        f1, f2 = uuid4(), uuid4()
        s_none, s_single, s_dual = uuid4(), uuid4(), uuid4()
        services = {
            s_none: [],
            s_single: [f1],
            s_dual: [f1, f2],
        }
        recs = ha.generate_cross_training_recommendations(
            services, all_faculty=[f1, f2, uuid4()]
        )
        assert recs[0].priority == CrossTrainingPriority.URGENT
        assert recs[1].priority == CrossTrainingPriority.HIGH


class TestCreateProtectionPlan:
    def test_creates_plan(self):
        ha = HubAnalyzer()
        fid = uuid4()
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.7,
            unique_services=2,
        )
        ha.centrality_cache[fid] = fc

        plan = ha.create_protection_plan(
            fid,
            date(2026, 6, 1),
            date(2026, 8, 31),
            reason="PCS season",
        )
        assert plan is not None
        assert plan.hub_faculty_id == fid
        assert plan.status == "planned"
        assert fid in ha.protection_plans

    def test_not_hub_returns_none(self):
        ha = HubAnalyzer()
        fid = uuid4()
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Nobody",
            calculated_at=datetime.now(),
            composite_score=0.1,
        )
        ha.centrality_cache[fid] = fc
        assert (
            ha.create_protection_plan(fid, date(2026, 1, 1), date(2026, 1, 31), "test")
            is None
        )

    def test_high_reduction_sets_critical_only(self):
        ha = HubAnalyzer()
        fid = uuid4()
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.8,
            unique_services=3,
        )
        ha.centrality_cache[fid] = fc
        plan = ha.create_protection_plan(
            fid, date(2026, 1, 1), date(2026, 1, 31), "test", workload_reduction=0.7
        )
        assert plan.critical_only is True


class TestActivateDeactivateProtectionPlan:
    def test_activate(self):
        ha = HubAnalyzer()
        fid = uuid4()
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.8,
            unique_services=3,
        )
        ha.centrality_cache[fid] = fc
        plan = ha.create_protection_plan(
            fid, date(2026, 1, 1), date(2026, 1, 31), "test"
        )
        ha.activate_protection_plan(plan.id)
        assert ha.protection_plans[fid].status == "active"

    def test_deactivate(self):
        ha = HubAnalyzer()
        fid = uuid4()
        fc = FacultyCentrality(
            faculty_id=fid,
            faculty_name="Dr. Hub",
            calculated_at=datetime.now(),
            composite_score=0.8,
            unique_services=3,
        )
        ha.centrality_cache[fid] = fc
        plan = ha.create_protection_plan(
            fid, date(2026, 1, 1), date(2026, 1, 31), "test"
        )
        ha.activate_protection_plan(plan.id)
        ha.deactivate_protection_plan(plan.id)
        assert ha.protection_plans[fid].status == "completed"


class TestGetDistributionReport:
    def test_generates_report(self):
        ha = HubAnalyzer(use_networkx=False)
        f1_id, f2_id, f3_id = uuid4(), uuid4(), uuid4()
        faculty = [
            MockFaculty(id=f1_id, name="Dr. A"),
            MockFaculty(id=f2_id, name="Dr. B"),
            MockFaculty(id=f3_id, name="Dr. C"),
        ]
        s1, s2 = uuid4(), uuid4()
        services = {
            s1: [f1_id],  # single provider
            s2: [f1_id, f2_id, f3_id],  # well covered
        }
        ha.calculate_centrality(faculty, [], services)
        report = ha.get_distribution_report(services, {s1: "ICU", s2: "Clinic"})
        assert isinstance(report, HubDistributionReport)
        assert report.total_faculty == 3
        assert "ICU" in report.services_with_single_provider
        assert "Clinic" in report.well_covered_services
        assert len(report.recommendations) > 0


class TestGetHubStatus:
    def test_initial_status(self):
        ha = HubAnalyzer()
        status = ha.get_hub_status()
        assert status["total_faculty_analyzed"] == 0
        assert status["total_hubs"] == 0
        assert status["last_analysis"] is None


class TestGetTopHubs:
    def test_returns_top_n(self):
        ha = HubAnalyzer()
        for i in range(5):
            fid = uuid4()
            fc = FacultyCentrality(
                faculty_id=fid,
                faculty_name=f"Dr. {i}",
                calculated_at=datetime.now(),
                composite_score=i * 0.2,
            )
            ha.centrality_cache[fid] = fc
        top = ha.get_top_hubs(n=3)
        assert len(top) == 3
        assert top[0].composite_score >= top[1].composite_score
