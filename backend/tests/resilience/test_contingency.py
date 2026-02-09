"""Tests for Contingency Analysis (Power Grid N-1/N-2 Planning)."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.resilience.contingency import (
    CascadeSimulation,
    CentralityScore,
    ContingencyAnalyzer,
    FatalPair,
    Vulnerability,
    VulnerabilityReport,
)


# ==================== Lightweight mock objects ====================


@dataclass
class MockFaculty:
    id: UUID
    name: str


@dataclass
class MockBlock:
    id: UUID
    date: date


@dataclass
class MockAssignment:
    person_id: UUID
    block_id: UUID


def _make_faculty(n=3):
    return [MockFaculty(id=uuid4(), name=f"Dr.{i}") for i in range(n)]


def _make_blocks(n=5):
    base = date(2026, 1, 5)
    return [MockBlock(id=uuid4(), date=base + timedelta(days=i)) for i in range(n)]


# ==================== Vulnerability dataclass ====================


class TestVulnerability:
    def test_required_fields(self):
        v = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            severity="critical",
            affected_blocks=3,
        )
        assert v.severity == "critical"
        assert v.affected_blocks == 3

    def test_defaults(self):
        v = Vulnerability(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            severity="low",
            affected_blocks=0,
        )
        assert v.affected_services == []
        assert v.is_unique_provider is False
        assert v.details == ""


# ==================== FatalPair dataclass ====================


class TestFatalPair:
    def test_all_fields(self):
        fp = FatalPair(
            faculty_1_id=uuid4(),
            faculty_1_name="Dr. A",
            faculty_2_id=uuid4(),
            faculty_2_name="Dr. B",
            uncoverable_blocks=5,
        )
        assert fp.uncoverable_blocks == 5
        assert fp.probability_estimate == "unknown"


# ==================== VulnerabilityReport dataclass ====================


class TestVulnerabilityReport:
    def test_defaults(self):
        report = VulnerabilityReport(
            analysis_date=date.today(),
            period_start=date.today(),
            period_end=date.today(),
        )
        assert report.n1_pass is True
        assert report.n2_pass is True
        assert report.n1_vulnerabilities == []
        assert report.n2_fatal_pairs == []
        assert report.phase_transition_risk == "low"


# ==================== CentralityScore dataclass ====================


class TestCentralityScore:
    def test_all_fields(self):
        cs = CentralityScore(
            faculty_id=uuid4(),
            faculty_name="Dr. Hub",
            score=0.85,
            services_covered=5,
            unique_coverage_slots=2,
            replacement_difficulty=0.7,
            workload_share=0.3,
        )
        assert cs.score == 0.85
        assert cs.betweenness == 0.0  # defaults
        assert cs.pagerank == 0.0


# ==================== CascadeSimulation dataclass ====================


class TestCascadeSimulation:
    def test_all_fields(self):
        cs = CascadeSimulation(
            initial_failures=[uuid4()],
            cascade_steps=[],
            total_failures=1,
            final_coverage=0.8,
            cascade_length=0,
            is_catastrophic=False,
        )
        assert cs.total_failures == 1
        assert not cs.is_catastrophic


# ==================== ContingencyAnalyzer.analyze_n1 ====================


class TestAnalyzeN1:
    def test_no_vulnerabilities(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(2)
        # Each block covered by 2 faculty
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[1].id),
            MockAssignment(person_id=faculty[2].id, block_id=blocks[1].id),
        ]
        reqs = {b.id: 1 for b in blocks}
        vulns = analyzer.analyze_n1(faculty, blocks, assignments, reqs)
        assert len(vulns) == 0

    def test_unique_provider_critical(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        blocks = _make_blocks(1)
        # Only faculty[0] covers block
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
        ]
        reqs = {blocks[0].id: 1}
        vulns = analyzer.analyze_n1(faculty, blocks, assignments, reqs)
        assert len(vulns) == 1
        assert vulns[0].severity == "critical"
        assert vulns[0].is_unique_provider is True

    def test_multiple_blocks_affected(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(1)
        blocks = _make_blocks(8)
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=b.id) for b in blocks
        ]
        reqs = {b.id: 1 for b in blocks}
        vulns = analyzer.analyze_n1(faculty, blocks, assignments, reqs)
        assert len(vulns) == 1
        assert vulns[0].severity == "critical"  # unique + >5 blocks
        assert vulns[0].affected_blocks == 8

    def test_high_severity_not_unique(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(6)
        # Faculty[0] covers all blocks, faculty[1] covers block[0] only
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=b.id) for b in blocks
        ]
        assignments.append(
            MockAssignment(person_id=faculty[1].id, block_id=blocks[0].id)
        )
        # Require 2 per block → only block[0] has enough without faculty[0]
        reqs = {b.id: 2 for b in blocks}
        vulns = analyzer.analyze_n1(faculty, blocks, assignments, reqs)
        # Faculty[0] loss affects blocks that only have 1 assignment
        assert len(vulns) >= 1

    def test_sorted_by_severity(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(3)
        # Faculty[0] is unique on block[0], Faculty[1] has backup on blocks[1,2]
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[1].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[2].id),
            MockAssignment(person_id=faculty[2].id, block_id=blocks[1].id),
        ]
        reqs = {b.id: 2 for b in blocks}
        vulns = analyzer.analyze_n1(faculty, blocks, assignments, reqs)
        if len(vulns) >= 2:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(vulns) - 1):
                assert (
                    severity_order[vulns[i].severity]
                    <= severity_order[vulns[i + 1].severity]
                )

    def test_no_assignments_no_vulns(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(2)
        vulns = analyzer.analyze_n1(faculty, blocks, [], {})
        assert vulns == []


# ==================== ContingencyAnalyzer.analyze_n2 ====================


class TestAnalyzeN2:
    def test_no_fatal_pairs(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(4)
        blocks = _make_blocks(2)
        # Heavy redundancy: all 4 cover both blocks
        assignments = [
            MockAssignment(person_id=f.id, block_id=b.id)
            for f in faculty
            for b in blocks
        ]
        reqs = {b.id: 1 for b in blocks}
        pairs = analyzer.analyze_n2(faculty, blocks, assignments, reqs)
        assert len(pairs) == 0

    def test_finds_fatal_pair(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        blocks = _make_blocks(1)
        # Only 2 faculty cover the block, each exactly once
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[0].id),
        ]
        reqs = {blocks[0].id: 2}
        pairs = analyzer.analyze_n2(
            faculty, blocks, assignments, reqs, critical_faculty_only=False
        )
        assert len(pairs) >= 1
        assert pairs[0].uncoverable_blocks >= 1

    def test_sorted_by_severity(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(3)
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[0].id, block_id=blocks[1].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[2].id),
            MockAssignment(person_id=faculty[2].id, block_id=blocks[2].id),
        ]
        reqs = {b.id: 2 for b in blocks}
        pairs = analyzer.analyze_n2(
            faculty, blocks, assignments, reqs, critical_faculty_only=False
        )
        if len(pairs) >= 2:
            for i in range(len(pairs) - 1):
                assert pairs[i].uncoverable_blocks >= pairs[i + 1].uncoverable_blocks


# ==================== calculate_centrality ====================


class TestCalculateCentrality:
    def test_basic_centrality(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(3)
        svc_id = uuid4()
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[0].id, block_id=blocks[1].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[2].id),
        ]
        services = {svc_id: [faculty[0].id, faculty[1].id]}
        scores = analyzer.calculate_centrality(faculty, assignments, services)
        assert len(scores) == 3
        assert all(isinstance(s, CentralityScore) for s in scores)
        # Sorted by score descending
        assert scores[0].score >= scores[-1].score

    def test_unique_provider_high_score(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        svc1, svc2 = uuid4(), uuid4()
        assignments = [MockAssignment(person_id=faculty[0].id, block_id=uuid4())]
        # Faculty[0] is sole provider for svc1
        services = {svc1: [faculty[0].id], svc2: [faculty[0].id, faculty[1].id]}
        scores = analyzer.calculate_centrality(faculty, assignments, services)
        top = scores[0]
        assert top.faculty_id == faculty[0].id
        assert top.unique_coverage_slots >= 1

    def test_no_services(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        assignments = []
        scores = analyzer.calculate_centrality(faculty, assignments, {})
        assert len(scores) == 2
        assert all(s.score == 0.0 for s in scores)

    def test_no_assignments(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        svc_id = uuid4()
        services = {svc_id: [faculty[0].id]}
        scores = analyzer.calculate_centrality(faculty, [], services)
        assert len(scores) == 2
        assert all(s.workload_share == 0.0 for s in scores)


# ==================== build_scheduling_graph ====================


class TestBuildSchedulingGraph:
    def test_builds_graph(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        blocks = _make_blocks(2)
        svc_id = uuid4()
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
        ]
        services = {svc_id: [faculty[0].id]}
        g = analyzer.build_scheduling_graph(faculty, blocks, assignments, services)
        assert g is not None
        # 2 faculty + 2 blocks + 1 service = 5 nodes
        assert g.number_of_nodes() == 5
        # 1 assignment edge + 1 credential edge = 2
        assert g.number_of_edges() == 2

    def test_empty_graph(self):
        analyzer = ContingencyAnalyzer()
        g = analyzer.build_scheduling_graph([], [], [], {})
        assert g is not None
        assert g.number_of_nodes() == 0


# ==================== calculate_centrality_networkx ====================


class TestCalculateCentralityNetworkx:
    def test_returns_scores_with_nx_metrics(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(3)
        svc_id = uuid4()
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
            MockAssignment(person_id=faculty[1].id, block_id=blocks[1].id),
            MockAssignment(person_id=faculty[2].id, block_id=blocks[2].id),
        ]
        services = {svc_id: [f.id for f in faculty]}
        scores = analyzer.calculate_centrality_networkx(
            faculty, blocks, assignments, services
        )
        assert len(scores) == 3
        # Should have NetworkX metrics populated
        for s in scores:
            # pagerank should be > 0 for connected nodes
            assert isinstance(s.pagerank, float)


# ==================== simulate_cascade_failure ====================


class TestSimulateCascadeFailure:
    def test_no_cascade(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(5)
        blocks = _make_blocks(5)
        # Light load: each faculty covers 1 block
        assignments = [
            MockAssignment(person_id=faculty[i].id, block_id=blocks[i].id)
            for i in range(5)
        ]
        result = analyzer.simulate_cascade_failure(
            faculty, blocks, assignments, [faculty[0].id]
        )
        assert isinstance(result, CascadeSimulation)
        assert result.total_failures >= 1

    def test_catastrophic_collapse(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(3)
        # Every faculty covers every block (high interdependence)
        assignments = [
            MockAssignment(person_id=f.id, block_id=b.id)
            for f in faculty
            for b in blocks
        ]
        # Removing 2 should leave 1 covering all 9 original assignments
        result = analyzer.simulate_cascade_failure(
            faculty,
            blocks,
            assignments,
            [faculty[0].id, faculty[1].id],
            overload_threshold=0.5,  # Very low threshold to trigger cascade
        )
        assert result.total_failures >= 2

    def test_empty_initial_failures(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        blocks = _make_blocks(2)
        assignments = [MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id)]
        result = analyzer.simulate_cascade_failure(faculty, blocks, assignments, [])
        assert result.total_failures == 0
        assert result.final_coverage == 1.0

    def test_no_assignments(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(3)
        result = analyzer.simulate_cascade_failure(faculty, [], [], [faculty[0].id])
        assert result.final_coverage == 0.0


# ==================== detect_phase_transition_risk ====================


class TestDetectPhaseTransitionRisk:
    def test_low_risk(self):
        analyzer = ContingencyAnalyzer()
        risk, indicators = analyzer.detect_phase_transition_risk([], 0.70)
        assert risk == "low"
        assert len(indicators) == 0

    def test_high_utilization(self):
        analyzer = ContingencyAnalyzer()
        risk, indicators = analyzer.detect_phase_transition_risk([], 0.96)
        assert risk in ("medium", "high", "critical")
        assert any("95%" in i for i in indicators)

    def test_high_change_frequency(self):
        analyzer = ContingencyAnalyzer()
        changes = [{"date": date.today()} for _ in range(25)]
        risk, indicators = analyzer.detect_phase_transition_risk(changes, 0.70)
        assert risk in ("medium", "high", "critical")
        assert any("change" in i.lower() for i in indicators)

    def test_critical_combined(self):
        analyzer = ContingencyAnalyzer()
        changes = [{"date": date.today()} for _ in range(25)]
        risk, indicators = analyzer.detect_phase_transition_risk(changes, 0.96)
        # High utilization + many changes = multiple indicators
        assert len(indicators) >= 2

    def test_moderate_utilization(self):
        analyzer = ContingencyAnalyzer()
        risk, indicators = analyzer.detect_phase_transition_risk([], 0.91)
        assert "90%" in indicators[0]

    def test_elevated_utilization(self):
        analyzer = ContingencyAnalyzer()
        risk, indicators = analyzer.detect_phase_transition_risk([], 0.87)
        assert "85%" in indicators[0]


# ==================== generate_report ====================


class TestGenerateReport:
    def test_clean_report(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(4)
        blocks = _make_blocks(2)
        # Full redundancy
        assignments = [
            MockAssignment(person_id=f.id, block_id=b.id)
            for f in faculty
            for b in blocks
        ]
        reqs = {b.id: 1 for b in blocks}
        report = analyzer.generate_report(faculty, blocks, assignments, reqs)
        assert isinstance(report, VulnerabilityReport)
        assert report.n1_pass is True
        assert report.phase_transition_risk == "low"

    def test_report_with_vulnerabilities(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        blocks = _make_blocks(1)
        assignments = [
            MockAssignment(person_id=faculty[0].id, block_id=blocks[0].id),
        ]
        reqs = {blocks[0].id: 1}
        report = analyzer.generate_report(faculty, blocks, assignments, reqs)
        assert report.n1_pass is False  # Faculty[0] is unique provider
        assert len(report.n1_vulnerabilities) >= 1
        assert len(report.recommended_actions) > 0

    def test_report_with_high_utilization(self):
        analyzer = ContingencyAnalyzer()
        faculty = _make_faculty(2)
        blocks = _make_blocks(1)
        assignments = [
            MockAssignment(person_id=f.id, block_id=blocks[0].id) for f in faculty
        ]
        reqs = {blocks[0].id: 1}
        report = analyzer.generate_report(
            faculty,
            blocks,
            assignments,
            reqs,
            current_utilization=0.96,
        )
        assert report.phase_transition_risk in ("medium", "high", "critical")

    def test_empty_blocks(self):
        analyzer = ContingencyAnalyzer()
        report = analyzer.generate_report([], [], [], {})
        assert report.period_start == date.today()
        assert report.period_end == date.today()
