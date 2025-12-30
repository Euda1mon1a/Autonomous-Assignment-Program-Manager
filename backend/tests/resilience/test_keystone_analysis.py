"""
Tests for keystone species analysis.

Test scenarios:
1. Keystone identification - low abundance, high impact
2. Non-keystone identification - high abundance, proportional impact
3. Cascade simulation - multi-level propagation
4. Functional redundancy calculation
5. Succession planning recommendations
"""

import pytest
from datetime import datetime, date
from uuid import uuid4

from app.resilience.keystone_analysis import (
    KeystoneAnalyzer,
    KeystoneResource,
    CascadeAnalysis,
    SuccessionPlan,
    EntityType,
    KeystoneRiskLevel,
    SuccessionStatus,
)


class MockEntity:
    """Mock entity for testing."""

    def __init__(self, entity_id, name):
        self.id = entity_id
        self.name = name


class MockAssignment:
    """Mock assignment for testing."""

    def __init__(self, person_id, rotation_template_id):
        self.person_id = person_id
        self.rotation_template_id = rotation_template_id

    def get(self, key, default=None):
        """Dict-like get() for compatibility with keystone analysis code."""
        return getattr(self, key, default)


class TestKeystoneAnalyzer:
    """Test suite for KeystoneAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return KeystoneAnalyzer(keystone_threshold=0.6, use_networkx=True)

    @pytest.fixture
    def sample_ecosystem(self):
        """
        Create sample scheduling ecosystem.

        Scenario:
        - Faculty A: Neonatology specialist (low volume, critical)
        - Faculty B: General outpatient (high volume, replaceable)
        - Faculty C: Sports medicine (moderate volume, replaceable)
        - Resident 1, 2, 3: General residents
        - Services: Neonatology (A only), Outpatient (A, B, C), Sports (B, C)
        - Rotations: NICU (needs Neonate), Clinic (needs Outpatient)
        """
        faculty_a = MockEntity(uuid4(), "Dr. Smith (Neonate Specialist)")
        faculty_b = MockEntity(uuid4(), "Dr. Jones (General)")
        faculty_c = MockEntity(uuid4(), "Dr. Lee (Sports Med)")

        resident_1 = MockEntity(uuid4(), "Resident 1")
        resident_2 = MockEntity(uuid4(), "Resident 2")
        resident_3 = MockEntity(uuid4(), "Resident 3")

        faculty = [faculty_a, faculty_b, faculty_c]
        residents = [resident_1, resident_2, resident_3]

        # Services
        service_neonate = uuid4()
        service_outpatient = uuid4()
        service_sports = uuid4()

        services = {
            service_neonate: [faculty_a.id],  # Only A can do neonatology
            service_outpatient: [
                faculty_a.id,
                faculty_b.id,
                faculty_c.id,
            ],  # All can do outpatient
            service_sports: [faculty_b.id, faculty_c.id],  # B and C do sports
        }

        # Rotations
        rotation_nicu = uuid4()
        rotation_clinic = uuid4()
        rotation_sports = uuid4()

        rotations = {
            rotation_nicu: {
                "name": "NICU",
                "required_services": [service_neonate],
            },
            rotation_clinic: {
                "name": "General Clinic",
                "required_services": [service_outpatient],
            },
            rotation_sports: {
                "name": "Sports Clinic",
                "required_services": [service_sports],
            },
        }

        # Assignments
        # Faculty A: 10 NICU blocks (critical), 5 clinic blocks
        # Faculty B: 30 clinic blocks, 10 sports blocks
        # Faculty C: 25 clinic blocks, 15 sports blocks
        assignments = []

        # Faculty A assignments
        for _ in range(10):
            assignments.append(MockAssignment(faculty_a.id, rotation_nicu))
        for _ in range(5):
            assignments.append(MockAssignment(faculty_a.id, rotation_clinic))

        # Faculty B assignments
        for _ in range(30):
            assignments.append(MockAssignment(faculty_b.id, rotation_clinic))
        for _ in range(10):
            assignments.append(MockAssignment(faculty_b.id, rotation_sports))

        # Faculty C assignments
        for _ in range(25):
            assignments.append(MockAssignment(faculty_c.id, rotation_clinic))
        for _ in range(15):
            assignments.append(MockAssignment(faculty_c.id, rotation_sports))

        # Resident assignments (they work with faculty)
        for res in residents:
            for _ in range(5):
                assignments.append(MockAssignment(res.id, rotation_clinic))

        return {
            "faculty": faculty,
            "residents": residents,
            "assignments": assignments,
            "services": services,
            "rotations": rotations,
            "faculty_a": faculty_a,
            "faculty_b": faculty_b,
            "faculty_c": faculty_c,
            "service_neonate": service_neonate,
        }

    def test_build_dependency_graph(self, analyzer, sample_ecosystem):
        """Test dependency graph construction."""
        graph = analyzer.build_dependency_graph(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        assert graph is not None
        assert graph.number_of_nodes() > 0

        # Should have faculty, resident, service, and rotation nodes
        node_types = [graph.nodes[n].get("type") for n in graph.nodes()]
        assert EntityType.FACULTY.value in node_types
        assert EntityType.RESIDENT.value in node_types
        assert EntityType.SERVICE.value in node_types
        assert EntityType.ROTATION.value in node_types

    def test_compute_keystoneness_score(self, analyzer, sample_ecosystem):
        """Test keystoneness score calculation."""
        graph = analyzer.build_dependency_graph(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        faculty_a_id = str(sample_ecosystem["faculty_a"].id)
        faculty_b_id = str(sample_ecosystem["faculty_b"].id)

        # Faculty A should have high keystoneness (low abundance, high impact)
        keystoneness_a = analyzer.compute_keystoneness_score(faculty_a_id, graph)

        # Faculty B should have lower keystoneness (high abundance, moderate impact)
        keystoneness_b = analyzer.compute_keystoneness_score(faculty_b_id, graph)

        # A should be more keystone than B
        assert keystoneness_a > keystoneness_b

        # Both should be in valid range
        assert 0.0 <= keystoneness_a <= 1.0
        assert 0.0 <= keystoneness_b <= 1.0

    def test_compute_functional_redundancy(self, analyzer, sample_ecosystem):
        """Test functional redundancy calculation."""
        faculty_a_id = str(sample_ecosystem["faculty_a"].id)
        faculty_b_id = str(sample_ecosystem["faculty_b"].id)

        # Faculty A provides neonatology (no backup) + outpatient (high backup)
        # Should have low redundancy overall
        redundancy_a = analyzer.compute_functional_redundancy(
            faculty_a_id, sample_ecosystem["services"]
        )

        # Faculty B provides outpatient (high backup) + sports (moderate backup)
        # Should have higher redundancy
        redundancy_b = analyzer.compute_functional_redundancy(
            faculty_b_id, sample_ecosystem["services"]
        )

        # A should have lower redundancy than B
        assert redundancy_a < redundancy_b

        # Both should be in valid range
        assert 0.0 <= redundancy_a <= 1.0
        assert 0.0 <= redundancy_b <= 1.0

    def test_identify_keystone_resources(self, analyzer, sample_ecosystem):
        """Test keystone resource identification."""
        keystones = analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
            threshold=0.5,
        )

        # Should identify Faculty A as keystone
        keystone_ids = [k.entity_id for k in keystones]
        assert sample_ecosystem["faculty_a"].id in keystone_ids

        # Faculty A should have high keystoneness
        faculty_a_keystone = next(
            k for k in keystones if k.entity_id == sample_ecosystem["faculty_a"].id
        )
        assert faculty_a_keystone.keystoneness_score >= 0.5
        assert faculty_a_keystone.is_keystone

        # Should have low functional redundancy
        assert faculty_a_keystone.functional_redundancy < 0.5

        # Should have unique capabilities
        assert len(faculty_a_keystone.unique_capabilities) > 0

    def test_simulate_removal_cascade(self, analyzer, sample_ecosystem):
        """Test cascade simulation when keystone is removed."""
        cascade = analyzer.simulate_removal_cascade(
            sample_ecosystem["faculty_a"].id,
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        assert cascade is not None
        assert cascade.removed_entity_id == sample_ecosystem["faculty_a"].id

        # Should have cascade steps
        assert cascade.cascade_depth > 0
        assert len(cascade.cascade_steps) > 0

        # Should affect neonatology service
        affected_services = cascade.affected_entities.get(EntityType.SERVICE, [])
        assert sample_ecosystem["service_neonate"] in affected_services

        # Should have some coverage loss
        assert cascade.coverage_loss > 0.0

        # Should have recovery time estimate
        assert cascade.recovery_time_days > 0

    def test_simulate_removal_non_keystone(self, analyzer, sample_ecosystem):
        """Test cascade simulation for non-keystone (should be minimal)."""
        # Remove Faculty C (sports medicine, has backup)
        cascade = analyzer.simulate_removal_cascade(
            sample_ecosystem["faculty_c"].id,
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        # Should have minimal cascade
        # Services should still be covered by B
        assert cascade.cascade_depth <= 1

        # Coverage loss should be smaller than keystone removal
        # (Just the assignments, not the whole service)
        assert cascade.coverage_loss < 0.5

    def test_recommend_succession_plan(self, analyzer, sample_ecosystem):
        """Test succession plan generation."""
        # First identify keystones
        keystones = analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        # Get Faculty A's keystone
        faculty_a_keystone = next(
            (k for k in keystones if k.entity_id == sample_ecosystem["faculty_a"].id),
            None,
        )

        assert faculty_a_keystone is not None

        # Generate succession plan
        all_entities = sample_ecosystem["faculty"] + sample_ecosystem["residents"]
        plan = analyzer.recommend_succession_plan(
            faculty_a_keystone,
            all_entities,
            sample_ecosystem["services"],
        )

        assert plan is not None
        assert plan.keystone_entity_id == sample_ecosystem["faculty_a"].id

        # Should have backup candidates
        assert len(plan.backup_candidates) > 0

        # Should have training needs (neonatology skill)
        assert len(plan.cross_training_needed) > 0

        # Should have estimated hours
        assert plan.estimated_training_hours > 0

        # Should have appropriate priority
        assert plan.training_priority in ["low", "medium", "high", "urgent"]

        # Should have timeline
        assert "training_start" in plan.timeline
        assert "training_complete" in plan.timeline

    def test_keystone_vs_hub_difference(self, analyzer):
        """
        Test that keystone analysis differs from hub analysis.

        Keystone: Low abundance, high impact
        Hub: High connectivity, central position
        """
        # Create scenario where hub != keystone

        # Hub faculty (many connections, but replaceable)
        hub_faculty = MockEntity(uuid4(), "Dr. Hub")

        # Keystone faculty (few connections, but critical)
        keystone_faculty = MockEntity(uuid4(), "Dr. Keystone")

        # Other faculty
        backup_1 = MockEntity(uuid4(), "Dr. Backup1")
        backup_2 = MockEntity(uuid4(), "Dr. Backup2")

        faculty = [hub_faculty, keystone_faculty, backup_1, backup_2]
        residents = []

        # Services
        service_common_1 = uuid4()
        service_common_2 = uuid4()
        service_common_3 = uuid4()
        service_critical = uuid4()

        services = {
            # Hub can do many common services (high connectivity)
            service_common_1: [hub_faculty.id, backup_1.id, backup_2.id],
            service_common_2: [hub_faculty.id, backup_1.id, backup_2.id],
            service_common_3: [hub_faculty.id, backup_1.id, backup_2.id],
            # Keystone is sole provider of critical service (low connectivity, high impact)
            service_critical: [keystone_faculty.id],
        }

        rotations = {
            uuid4(): {"name": "Common1", "required_services": [service_common_1]},
            uuid4(): {"name": "Common2", "required_services": [service_common_2]},
            uuid4(): {"name": "Common3", "required_services": [service_common_3]},
            uuid4(): {"name": "Critical", "required_services": [service_critical]},
        }

        # Hub has many assignments
        assignments = []
        for _ in range(50):
            assignments.append(
                MockAssignment(hub_faculty.id, list(rotations.keys())[0])
            )

        # Keystone has few assignments
        for _ in range(5):
            assignments.append(
                MockAssignment(keystone_faculty.id, list(rotations.keys())[3])
            )

        # Identify keystones
        keystones = analyzer.identify_keystone_resources(
            faculty, residents, assignments, services, rotations, threshold=0.5
        )

        keystone_ids = [k.entity_id for k in keystones]

        # Keystone faculty should be identified (low abundance, high impact)
        assert keystone_faculty.id in keystone_ids

        # Hub might or might not be keystone (high abundance, replaceable)
        # If hub is keystone, should have lower score than true keystone
        keystone_keystone = next(
            (k for k in keystones if k.entity_id == keystone_faculty.id), None
        )
        hub_keystone = next(
            (k for k in keystones if k.entity_id == hub_faculty.id), None
        )

        if keystone_keystone and hub_keystone:
            # True keystone should have higher score
            assert keystone_keystone.keystoneness_score > hub_keystone.keystoneness_score

    def test_risk_level_assignment(self, analyzer, sample_ecosystem):
        """Test risk level assignment based on metrics."""
        keystones = analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        for keystone in keystones:
            # Risk level should be valid
            assert isinstance(keystone.risk_level, KeystoneRiskLevel)

            # High keystoneness + low redundancy = high risk
            if (
                keystone.keystoneness_score > 0.8
                and keystone.functional_redundancy < 0.2
            ):
                assert keystone.risk_level in [
                    KeystoneRiskLevel.CRITICAL,
                    KeystoneRiskLevel.CATASTROPHIC,
                ]

    def test_single_point_of_failure_detection(self, analyzer, sample_ecosystem):
        """Test single point of failure detection."""
        keystones = analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        faculty_a_keystone = next(
            k for k in keystones if k.entity_id == sample_ecosystem["faculty_a"].id
        )

        # Faculty A is sole neonatology provider
        assert faculty_a_keystone.is_single_point_of_failure

    def test_get_keystone_summary(self, analyzer, sample_ecosystem):
        """Test summary statistics generation."""
        analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        summary = analyzer.get_keystone_summary()

        assert "total_keystones" in summary
        assert "by_risk_level" in summary
        assert "single_points_of_failure" in summary
        assert "average_keystoneness" in summary
        assert "succession_plans" in summary

        # Should have identified at least one keystone
        assert summary["total_keystones"] > 0

    def test_get_top_keystones(self, analyzer, sample_ecosystem):
        """Test top keystones retrieval."""
        analyzer.identify_keystone_resources(
            sample_ecosystem["faculty"],
            sample_ecosystem["residents"],
            sample_ecosystem["assignments"],
            sample_ecosystem["services"],
            sample_ecosystem["rotations"],
        )

        top_keystones = analyzer.get_top_keystones(n=3)

        # Should return up to 3
        assert len(top_keystones) <= 3

        # Should be sorted by keystoneness score
        if len(top_keystones) > 1:
            for i in range(len(top_keystones) - 1):
                assert (
                    top_keystones[i].keystoneness_score
                    >= top_keystones[i + 1].keystoneness_score
                )

    def test_cascade_analysis_dataclass(self):
        """Test CascadeAnalysis dataclass."""
        cascade = CascadeAnalysis(
            removed_entity_id=uuid4(),
            removed_entity_name="Test Entity",
            removed_entity_type=EntityType.FACULTY,
            simulation_date=datetime.now(),
        )

        # Test add_cascade_step
        cascade.add_cascade_step(
            level=1,
            affected_entities=[uuid4(), uuid4()],
            affected_types={EntityType.SERVICE: 2},
            reason="Test reason",
        )

        assert len(cascade.cascade_steps) == 1
        assert cascade.cascade_depth == 1

        cascade.add_cascade_step(
            level=2,
            affected_entities=[uuid4()],
            affected_types={EntityType.ROTATION: 1},
            reason="Level 2",
        )

        assert len(cascade.cascade_steps) == 2
        assert cascade.cascade_depth == 2

    def test_succession_plan_dataclass(self):
        """Test SuccessionPlan dataclass."""
        plan = SuccessionPlan(
            id=uuid4(),
            keystone_entity_id=uuid4(),
            keystone_entity_name="Test Keystone",
            keystone_entity_type=EntityType.FACULTY,
            created_at=datetime.now(),
            backup_candidates=[(uuid4(), "Backup 1", 0.8)],
            cross_training_needed=["Skill 1", "Skill 2"],
            estimated_training_hours=80,
            training_priority="high",
            timeline={"training_start": date.today()},
            status=SuccessionStatus.PLANNED,
        )

        assert plan.status == SuccessionStatus.PLANNED
        assert len(plan.backup_candidates) == 1
        assert len(plan.cross_training_needed) == 2

    def test_keystone_resource_properties(self):
        """Test KeystoneResource computed properties."""
        # Keystone: high keystoneness, low redundancy, has cascade
        keystone = KeystoneResource(
            entity_id=uuid4(),
            entity_name="Test Keystone",
            entity_type=EntityType.FACULTY,
            calculated_at=datetime.now(),
            keystoneness_score=0.75,
            abundance=0.1,
            impact_if_removed=0.8,
            replacement_difficulty=0.9,
            direct_dependents=5,
            indirect_dependents=15,
            cascade_depth=3,
            bottleneck_score=0.7,
            functional_redundancy=0.05,  # Must be < 0.1 for is_single_point_of_failure
            unique_capabilities=["Skill A"],
            shared_capabilities=["Skill B"],
        )

        assert keystone.is_keystone
        assert keystone.is_single_point_of_failure

        # Non-keystone: low keystoneness or high redundancy
        non_keystone = KeystoneResource(
            entity_id=uuid4(),
            entity_name="Test Non-Keystone",
            entity_type=EntityType.FACULTY,
            calculated_at=datetime.now(),
            keystoneness_score=0.3,
            abundance=0.7,
            impact_if_removed=0.3,
            replacement_difficulty=0.2,
            direct_dependents=2,
            indirect_dependents=2,
            cascade_depth=0,
            bottleneck_score=0.2,
            functional_redundancy=0.8,
            unique_capabilities=[],
            shared_capabilities=["Skill A", "Skill B"],
        )

        assert not non_keystone.is_keystone
        assert not non_keystone.is_single_point_of_failure


class TestKeystoneAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_ecosystem(self):
        """Test with empty ecosystem."""
        analyzer = KeystoneAnalyzer()

        keystones = analyzer.identify_keystone_resources(
            faculty=[],
            residents=[],
            assignments=[],
            services={},
            rotations={},
        )

        assert len(keystones) == 0

    def test_no_networkx(self):
        """Test fallback behavior when NetworkX unavailable."""
        analyzer = KeystoneAnalyzer(use_networkx=False)

        # Should still work but with degraded functionality
        graph = analyzer.build_dependency_graph([], [], [], {}, {})
        assert graph is None

    def test_single_entity_ecosystem(self):
        """Test with single entity."""
        analyzer = KeystoneAnalyzer()

        faculty = [MockEntity(uuid4(), "Solo Faculty")]
        service = uuid4()

        services = {service: [faculty[0].id]}
        rotations = {uuid4(): {"name": "Solo Rotation", "required_services": [service]}}

        keystones = analyzer.identify_keystone_resources(
            faculty=faculty,
            residents=[],
            assignments=[],
            services=services,
            rotations=rotations,
        )

        # Solo entity is automatically a keystone (single point of failure)
        if len(keystones) > 0:
            assert keystones[0].is_single_point_of_failure
