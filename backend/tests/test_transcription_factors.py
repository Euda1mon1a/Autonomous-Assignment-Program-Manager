"""
Tests for Transcription Factor Scheduler module.

Tests cover:
1. TranscriptionFactor creation and properties
2. TF induction and decay dynamics
3. Promoter architecture and binding logic
4. Gene regulatory network structure
5. Signal transduction and cascades
6. Chromatin state management
7. Regulatory loop detection
8. Constraint weight calculation
9. Integration with ResilienceService
"""

from uuid import uuid4

from app.resilience.service import (
    ResilienceConfig,
    ResilienceService,
)
from app.resilience.transcription_factors import (
    BindingLogic,
    BindingSite,
    ChromatinState,
    LoopType,
    PromoterArchitecture,
    SignalStrength,
    TFType,
    TranscriptionFactor,
    TranscriptionFactorScheduler,
)

# ============================================================================
# TranscriptionFactor Tests
# ============================================================================


class TestTranscriptionFactor:
    """Tests for TranscriptionFactor dataclass and behavior."""

    def test_create_activator_tf(self):
        """Test creating an activator transcription factor."""
        tf = TranscriptionFactor(
            id=uuid4(),
            name="TestActivator",
            description="Test activator TF",
            tf_type=TFType.ACTIVATOR,
            binding_affinity=0.8,
            basal_expression=0.1,
            activation_strength=1.5,
        )

        assert tf.name == "TestActivator"
        assert tf.tf_type == TFType.ACTIVATOR
        assert tf.binding_affinity == 0.8
        assert tf.expression_level == 0.1  # Defaults to basal
        assert not tf.is_active  # Below 0.2 threshold

    def test_create_repressor_tf(self):
        """Test creating a repressor transcription factor."""
        tf = TranscriptionFactor(
            id=uuid4(),
            name="TestRepressor",
            description="Test repressor TF",
            tf_type=TFType.REPRESSOR,
            binding_affinity=0.9,
            repression_strength=0.7,
        )

        assert tf.tf_type == TFType.REPRESSOR
        assert tf.repression_strength == 0.7

    def test_tf_induction(self):
        """Test TF induction response to signal."""
        tf = TranscriptionFactor(
            id=uuid4(),
            name="InducibleTF",
            description="Test",
            tf_type=TFType.ACTIVATOR,
            basal_expression=0.1,
            max_expression=1.0,
        )

        # Initially at basal
        assert tf.expression_level == 0.1
        assert tf.signal_strength_category == SignalStrength.WEAK

        # Induce with strong signal
        tf.induce(signal_strength=1.0)

        # Should be highly expressed
        assert tf.expression_level > 0.8
        assert tf.is_active
        assert tf.signal_strength_category == SignalStrength.MAXIMAL

    def test_tf_induction_sigmoid_response(self):
        """Test sigmoid response to varying signal strengths."""
        tf = TranscriptionFactor(
            id=uuid4(),
            name="SigmoidTF",
            description="Test",
            tf_type=TFType.ACTIVATOR,
            basal_expression=0.0,
            max_expression=1.0,
        )

        # Weak signal (0.2) should give low response
        tf.induce(signal_strength=0.2)
        weak_response = tf.expression_level

        # Reset
        tf.expression_level = 0.0

        # Strong signal (0.8) should give high response
        tf.induce(signal_strength=0.8)
        strong_response = tf.expression_level

        assert strong_response > weak_response * 2  # Nonlinear response

    def test_tf_decay(self):
        """Test TF expression decay over time."""
        tf = TranscriptionFactor(
            id=uuid4(),
            name="DecayingTF",
            description="Test",
            tf_type=TFType.ACTIVATOR,
            basal_expression=0.1,
            max_expression=1.0,
            half_life_hours=24.0,
        )

        # Induce to max
        tf.induce(signal_strength=1.0)
        initial_expression = tf.expression_level

        # Decay for 24 hours (one half-life)
        tf.decay(hours_elapsed=24.0)

        # Should be approximately halfway between max and basal
        # (exponential decay toward basal, not zero)
        assert tf.expression_level < initial_expression
        assert tf.expression_level > tf.basal_expression

    def test_tf_effective_strength(self):
        """Test effective regulatory strength calculation."""
        activator = TranscriptionFactor(
            id=uuid4(),
            name="Activator",
            description="Test",
            tf_type=TFType.ACTIVATOR,
            activation_strength=2.0,
            expression_level=0.5,
        )

        repressor = TranscriptionFactor(
            id=uuid4(),
            name="Repressor",
            description="Test",
            tf_type=TFType.REPRESSOR,
            repression_strength=0.8,
            expression_level=0.5,
        )

        # Activator: activation_strength * expression_level
        assert activator.get_effective_strength() == 1.0  # 2.0 * 0.5

        # Repressor: repression_strength * expression_level
        assert repressor.get_effective_strength() == 0.4  # 0.8 * 0.5


# ============================================================================
# Binding Site Tests
# ============================================================================


class TestBindingSite:
    """Tests for BindingSite and binding affinity calculations."""

    def test_binding_site_creation(self):
        """Test binding site creation."""
        site = BindingSite(
            id=uuid4(),
            name="PromoterSite1",
            tf_types_accepted=[TFType.ACTIVATOR, TFType.MASTER],
            binding_affinity=0.9,
        )

        assert site.name == "PromoterSite1"
        assert TFType.ACTIVATOR in site.tf_types_accepted
        assert site.binding_affinity == 0.9

    def test_enhancer_site(self):
        """Test enhancer site boosts binding."""
        enhancer = BindingSite(
            id=uuid4(),
            name="EnhancerSite",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=0.8,
            is_enhancer=True,
        )

        effective = enhancer.get_effective_affinity(tf_affinity=0.8)

        # Enhancer should boost by 1.5x (capped at 1.0)
        assert effective > 0.8 * 0.8

    def test_silencer_site(self):
        """Test silencer site reduces binding."""
        silencer = BindingSite(
            id=uuid4(),
            name="SilencerSite",
            tf_types_accepted=[TFType.REPRESSOR],
            binding_affinity=0.8,
            is_silencer=True,
        )

        effective = silencer.get_effective_affinity(tf_affinity=0.8)

        # Silencer should reduce by 0.5x
        assert effective < 0.8 * 0.8

    def test_distance_effect(self):
        """Test distance from core reduces binding."""
        proximal = BindingSite(
            id=uuid4(),
            name="Proximal",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=1.0,
            distance_from_core=0.0,
        )

        distal = BindingSite(
            id=uuid4(),
            name="Distal",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=1.0,
            distance_from_core=10.0,
        )

        proximal_eff = proximal.get_effective_affinity(tf_affinity=1.0)
        distal_eff = distal.get_effective_affinity(tf_affinity=1.0)

        assert distal_eff < proximal_eff


# ============================================================================
# Promoter Architecture Tests
# ============================================================================


class TestPromoterArchitecture:
    """Tests for PromoterArchitecture and activation logic."""

    def test_promoter_creation(self):
        """Test promoter creation with defaults."""
        constraint_id = uuid4()
        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=constraint_id,
            constraint_name="TestConstraint",
            base_weight=1.0,
        )

        assert promoter.constraint_id == constraint_id
        assert promoter.chromatin_state == ChromatinState.OPEN

    def test_or_logic_activation(self):
        """Test OR logic - any activator can activate."""
        tf1_id = uuid4()
        tf2_id = uuid4()

        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=uuid4(),
            constraint_name="ORConstraint",
            base_weight=1.0,
            activator_logic=BindingLogic.OR,
            optional_activators=[tf1_id, tf2_id],
        )

        # Only TF1 bound
        bound_tfs = {tf1_id: 0.8}
        activation, _ = promoter.calculate_activation(bound_tfs)

        assert activation > 0.5  # Should activate

    def test_and_logic_activation(self):
        """Test AND logic - all required activators must bind."""
        tf1_id = uuid4()
        tf2_id = uuid4()

        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=uuid4(),
            constraint_name="ANDConstraint",
            base_weight=1.0,
            activator_logic=BindingLogic.AND,
            required_activators=[tf1_id, tf2_id],
        )

        # Only TF1 bound - should NOT activate
        bound_tfs = {tf1_id: 0.8}
        activation, explanation = promoter.calculate_activation(bound_tfs)

        assert activation == 0.0
        assert "missing required" in explanation.lower()

        # Both bound - should activate
        bound_tfs = {tf1_id: 0.8, tf2_id: 0.7}
        activation, _ = promoter.calculate_activation(bound_tfs)

        assert activation > 0.5

    def test_repressor_reduces_activation(self):
        """Test repressor reduces activation level."""
        activator_id = uuid4()
        repressor_id = uuid4()

        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=uuid4(),
            constraint_name="RegulatedConstraint",
            base_weight=1.0,
            optional_activators=[activator_id],
            repressors=[repressor_id],
        )

        # Only activator
        activation_no_repressor, _ = promoter.calculate_activation({activator_id: 0.8})

        # Activator + repressor
        activation_with_repressor, _ = promoter.calculate_activation(
            {
                activator_id: 0.8,
                repressor_id: 0.5,
            }
        )

        assert activation_with_repressor < activation_no_repressor

    def test_silenced_chromatin_blocks_activation(self):
        """Test silenced chromatin prevents activation."""
        tf_id = uuid4()

        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=uuid4(),
            constraint_name="SilencedConstraint",
            base_weight=1.0,
            optional_activators=[tf_id],
            chromatin_state=ChromatinState.SILENCED,
        )

        # Strong activator should still be blocked
        bound_tfs = {tf_id: 1.0}
        activation, explanation = promoter.calculate_activation(bound_tfs)

        assert activation == 0.0
        assert "silenced" in explanation.lower()

    def test_effective_weight_calculation(self):
        """Test conversion of activation to weight."""
        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=uuid4(),
            constraint_name="WeightedConstraint",
            base_weight=2.0,
            min_weight=0.5,
            max_weight=5.0,
        )

        # Half activation
        weight = promoter.get_effective_weight(activation_level=0.5)
        assert weight == 1.0  # 2.0 * 0.5

        # Full activation
        weight = promoter.get_effective_weight(activation_level=1.0)
        assert weight == 2.0

        # Check min/max bounds
        assert promoter.get_effective_weight(0.0) >= promoter.min_weight


# ============================================================================
# TranscriptionFactorScheduler Tests
# ============================================================================


class TestTranscriptionFactorScheduler:
    """Tests for the main TF Scheduler service."""

    def test_default_tfs_created(self):
        """Test default TFs are created on initialization."""
        tfs = TranscriptionFactorScheduler()

        # Should have default TFs
        assert len(tfs.transcription_factors) > 0

        # Check specific defaults exist
        patient_safety = tfs.get_tf_by_name("PatientSafety_MR")
        assert patient_safety is not None
        assert patient_safety.tf_type == TFType.MASTER
        assert patient_safety.basal_expression == 1.0  # Always on

        military_tf = tfs.get_tf_by_name("MilitaryEmergency_TF")
        assert military_tf is not None
        assert military_tf.tf_type == TFType.ACTIVATOR

    def test_create_custom_tf(self):
        """Test creating custom transcription factor."""
        tfs = TranscriptionFactorScheduler()

        custom_tf = tfs.create_tf(
            name="CustomTF",
            tf_type=TFType.DUAL,
            description="A custom TF for testing",
            binding_affinity=0.75,
            activation_conditions={"event_types": ["test_event"]},
        )

        assert custom_tf.name == "CustomTF"
        assert "CustomTF" in tfs._tf_by_name
        assert tfs.get_tf_by_name("CustomTF") == custom_tf

    def test_link_tf_to_constraint(self):
        """Test linking TF to regulate a constraint."""
        tfs = TranscriptionFactorScheduler()

        constraint_id = uuid4()

        # Create TF and link to constraint
        tf = tfs.create_tf("RegulatorTF", TFType.ACTIVATOR, "Test regulator")
        tfs.create_promoter(constraint_id, "TestConstraint", base_weight=1.0)
        tfs.link_tf_to_constraint(tf.id, constraint_id, as_activator=True)

        # Check linkage
        promoter = tfs.promoters[constraint_id]
        assert tf.id in promoter.optional_activators
        assert constraint_id in tf.target_constraint_ids
        assert len(tfs.edges) > 0

    def test_signal_processing(self):
        """Test signal event processing induces appropriate TFs."""
        tfs = TranscriptionFactorScheduler()

        # Military TF should respond to deployment
        military_tf = tfs.get_tf_by_name("MilitaryEmergency_TF")
        initial_expression = military_tf.expression_level

        # Process deployment signal
        signal = tfs.create_signal(
            event_type="deployment",
            description="Faculty deployed",
            signal_strength=1.0,
        )

        assert signal.propagated
        assert military_tf.id in signal.target_tf_ids
        assert military_tf.expression_level > initial_expression

    def test_constraint_weight_calculation(self):
        """Test constraint weight calculation based on TF state."""
        tfs = TranscriptionFactorScheduler()

        constraint_id = uuid4()

        # Create activator and link
        tf = tfs.create_tf(
            "WeightModifier",
            TFType.ACTIVATOR,
            activation_strength=2.0,
            basal_expression=0.0,
        )
        tfs.create_promoter(constraint_id, "WeightedConstraint", base_weight=1.0)
        tfs.link_tf_to_constraint(tf.id, constraint_id, as_activator=True)

        # Initially TF not active - weight should be low
        weights_before = tfs.get_constraint_weights([constraint_id])
        weight_before, _ = weights_before[constraint_id]

        # Induce TF
        tfs.induce_tf(tf.id, signal_strength=1.0)

        # Now weight should be higher
        weights_after = tfs.get_constraint_weights([constraint_id])
        weight_after, _ = weights_after[constraint_id]

        assert weight_after > weight_before

    def test_chromatin_state_management(self):
        """Test chromatin state changes affect constraint weights."""
        tfs = TranscriptionFactorScheduler()

        constraint_id = uuid4()

        # Setup constraint with active regulation
        tf = tfs.create_tf("ActiveTF", TFType.ACTIVATOR)
        tfs.create_promoter(constraint_id, "StatefulConstraint", base_weight=1.0)
        tfs.link_tf_to_constraint(tf.id, constraint_id)
        tfs.induce_tf(tf.id, 1.0)

        # Get weight while OPEN
        weights_open = tfs.get_constraint_weights([constraint_id])
        weight_open, _ = weights_open[constraint_id]

        # Silence the constraint
        tfs.set_chromatin_state(constraint_id, ChromatinState.SILENCED)

        # Weight should be 0 when silenced
        weights_silenced = tfs.get_constraint_weights([constraint_id])
        weight_silenced, explanation = weights_silenced[constraint_id]

        assert weight_silenced < weight_open
        assert "silenced" in explanation.lower()

    def test_tf_cascade(self):
        """Test TF-to-TF cascade propagation."""
        tfs = TranscriptionFactorScheduler()

        # Create two TFs where TF1 induces TF2
        tf1 = tfs.create_tf("UpstreamTF", TFType.ACTIVATOR, basal_expression=0.0)
        tf2 = tfs.create_tf("DownstreamTF", TFType.ACTIVATOR, basal_expression=0.0)

        tfs.link_tf_to_tf(tf1.id, tf2.id, as_activator=True)

        # Induce TF1
        tfs.induce_tf(tf1.id, signal_strength=1.0)

        # TF2 should also be induced via cascade
        assert tf2.expression_level > tf2.basal_expression

    def test_decay_all_tfs(self):
        """Test decay applied to all TFs."""
        tfs = TranscriptionFactorScheduler()

        # Induce a TF
        military_tf = tfs.get_tf_by_name("MilitaryEmergency_TF")
        tfs.induce_tf(military_tf.id, signal_strength=1.0)

        high_expression = military_tf.expression_level

        # Apply decay
        tfs.decay_all_tfs(hours_elapsed=48.0)

        # Should have decayed
        assert military_tf.expression_level < high_expression

    def test_get_status(self):
        """Test status report generation."""
        tfs = TranscriptionFactorScheduler()

        status = tfs.get_status()

        assert "total_tfs" in status
        assert "active_tfs" in status
        assert "regulatory_edges" in status
        assert status["total_tfs"] > 0

    def test_tf_expression_report(self):
        """Test TF expression report."""
        tfs = TranscriptionFactorScheduler()

        # Induce one TF
        military_tf = tfs.get_tf_by_name("MilitaryEmergency_TF")
        tfs.induce_tf(military_tf.id, 1.0)

        report = tfs.get_tf_expression_report()

        assert len(report) > 0
        assert all("name" in entry for entry in report)
        assert all("expression" in entry for entry in report)

        # Highest expressed should be first
        assert report[0]["expression"] >= report[-1]["expression"]


# ============================================================================
# Regulatory Loop Detection Tests
# ============================================================================


class TestRegulatoryLoopDetection:
    """Tests for detecting regulatory network motifs."""

    def test_detect_feedback_loop(self):
        """Test detection of feedback loops."""
        tfs = TranscriptionFactorScheduler()

        # Create two TFs that regulate each other
        tf1 = tfs.create_tf("FeedbackTF1", TFType.ACTIVATOR)
        tf2 = tfs.create_tf("FeedbackTF2", TFType.ACTIVATOR)

        tfs.link_tf_to_tf(tf1.id, tf2.id, as_activator=True)
        tfs.link_tf_to_tf(tf2.id, tf1.id, as_activator=True)

        loops = tfs.detect_loops()

        # Should detect the feedback loop
        assert len(loops) > 0

        # Should be classified as positive feedback (both activators)
        positive_loops = [l for l in loops if l.loop_type == LoopType.POSITIVE_FEEDBACK]
        assert len(positive_loops) > 0

    def test_detect_negative_feedback(self):
        """Test detection of negative feedback loops."""
        tfs = TranscriptionFactorScheduler()

        # Create activator -> repressor -> activator
        tf1 = tfs.create_tf("NegFB_Activator", TFType.ACTIVATOR)
        tf2 = tfs.create_tf("NegFB_Repressor", TFType.REPRESSOR)

        tfs.link_tf_to_tf(tf1.id, tf2.id, as_activator=True)
        tfs.link_tf_to_tf(tf2.id, tf1.id, as_activator=False)

        loops = tfs.detect_loops()

        # Should find negative feedback
        negative_loops = [l for l in loops if l.loop_type == LoopType.NEGATIVE_FEEDBACK]
        assert len(negative_loops) > 0


# ============================================================================
# ResilienceService Integration Tests
# ============================================================================


class TestResilienceServiceIntegration:
    """Tests for TF scheduler integration with ResilienceService."""

    def test_tf_scheduler_enabled_by_default(self):
        """Test TF scheduler is enabled by default."""
        service = ResilienceService()

        assert service.tf_scheduler is not None
        assert service.config.enable_transcription_factors is True

    def test_tf_scheduler_can_be_disabled(self):
        """Test TF scheduler can be disabled."""
        config = ResilienceConfig(enable_transcription_factors=False)
        service = ResilienceService(config=config)

        assert service.tf_scheduler is None

    def test_create_tf_via_service(self):
        """Test creating TF through service interface."""
        service = ResilienceService()

        tf = service.create_transcription_factor(
            name="ServiceCreatedTF",
            tf_type=TFType.ACTIVATOR,
            description="Created via service",
        )

        assert tf is not None
        assert tf.name == "ServiceCreatedTF"

    def test_link_tf_to_constraint_via_service(self):
        """Test linking TF to constraint through service."""
        service = ResilienceService()

        constraint_id = uuid4()

        # Create TF
        service.create_transcription_factor(
            name="ServiceLinkedTF",
            tf_type=TFType.ACTIVATOR,
        )

        # Link to constraint
        service.link_tf_to_constraint(
            tf_name="ServiceLinkedTF",
            constraint_id=constraint_id,
            constraint_name="ServiceConstraint",
            as_activator=True,
        )

        # Verify linkage
        assert constraint_id in service.tf_scheduler.promoters

    def test_process_signal_via_service(self):
        """Test signal processing through service."""
        service = ResilienceService()

        signal = service.process_regulatory_signal(
            event_type="deployment",
            description="Test deployment",
            signal_strength=0.9,
        )

        assert signal is not None
        assert signal.event_type == "deployment"
        assert len(signal.target_tf_ids) > 0  # Should induce military TF

    def test_get_regulated_weights(self):
        """Test getting regulated constraint weights."""
        service = ResilienceService()

        constraint_id = uuid4()

        # Setup regulation
        service.create_transcription_factor(
            name="WeightTF",
            tf_type=TFType.ACTIVATOR,
            basal_expression=0.5,  # Already somewhat expressed
        )
        service.link_tf_to_constraint("WeightTF", constraint_id, "TestWeight")

        weights = service.get_regulated_constraint_weights([constraint_id])

        assert constraint_id in weights
        weight, explanation = weights[constraint_id]
        assert isinstance(weight, float)

    def test_silence_constraints_for_crisis(self):
        """Test silencing constraints during crisis."""
        service = ResilienceService()

        constraint_ids = [uuid4(), uuid4(), uuid4()]

        # Create promoters
        for cid in constraint_ids:
            service.link_tf_to_constraint(
                tf_name="PatientSafety_MR",
                constraint_id=cid,
                constraint_name=f"Constraint_{cid}",
            )

        # Silence for crisis
        service.silence_constraints_for_crisis(constraint_ids)

        # All should be silenced
        for cid in constraint_ids:
            promoter = service.tf_scheduler.promoters[cid]
            assert promoter.chromatin_state == ChromatinState.SILENCED

    def test_restore_silenced_constraints(self):
        """Test restoring silenced constraints."""
        service = ResilienceService()

        constraint_id = uuid4()
        service.link_tf_to_constraint("PatientSafety_MR", constraint_id, "Test")

        # Silence then restore
        service.silence_constraints_for_crisis([constraint_id])
        service.restore_silenced_constraints([constraint_id])

        promoter = service.tf_scheduler.promoters[constraint_id]
        assert promoter.chromatin_state == ChromatinState.OPEN

    def test_get_tier4_status(self):
        """Test getting Tier 4 status report."""
        service = ResilienceService()

        status = service.get_tier4_status()

        assert status["enabled"] is True
        assert "total_tfs" in status
        assert "active_tfs" in status
        assert "tier4_status" in status

    def test_get_tier4_status_when_disabled(self):
        """Test Tier 4 status when TF scheduler disabled."""
        config = ResilienceConfig(enable_transcription_factors=False)
        service = ResilienceService(config=config)

        status = service.get_tier4_status()

        assert status["enabled"] is False
        assert status["tier4_status"] == "disabled"

    def test_detect_regulatory_loops_via_service(self):
        """Test loop detection through service."""
        service = ResilienceService()

        # Create feedback loop
        tf1 = service.create_transcription_factor("LoopTF1", TFType.ACTIVATOR)
        tf2 = service.create_transcription_factor("LoopTF2", TFType.ACTIVATOR)

        service.tf_scheduler.link_tf_to_tf(tf1.id, tf2.id)
        service.tf_scheduler.link_tf_to_tf(tf2.id, tf1.id)

        loops = service.detect_regulatory_loops()

        assert len(loops) > 0

    def test_get_tf_expression_report_via_service(self):
        """Test expression report through service."""
        service = ResilienceService()

        report = service.get_tf_expression_report()

        assert isinstance(report, list)
        assert len(report) > 0

    def test_grn_state_snapshot(self):
        """Test GRN state snapshot."""
        service = ResilienceService()

        state = service.get_grn_state()

        assert state is not None
        assert hasattr(state, "tf_expressions")
        assert hasattr(state, "constraint_weights")
        assert hasattr(state, "network_entropy")


# ============================================================================
# Scenario Tests
# ============================================================================


class TestScenarios:
    """Test realistic usage scenarios."""

    def test_deployment_scenario(self):
        """Test emergency coverage during military deployment."""
        service = ResilienceService()

        # Setup emergency coverage constraint
        emergency_constraint_id = uuid4()
        service.link_tf_to_constraint(
            tf_name="MilitaryEmergency_TF",
            constraint_id=emergency_constraint_id,
            constraint_name="EmergencyCoverage",
            base_weight=0.5,  # Low weight normally
        )

        # Get weight before deployment
        weights_before = service.get_regulated_constraint_weights(
            [emergency_constraint_id]
        )
        weight_before, _ = weights_before[emergency_constraint_id]

        # Process deployment signal
        service.process_regulatory_signal(
            event_type="deployment",
            description="Faculty member deployed",
            signal_strength=1.0,
        )

        # Get weight after deployment
        weights_after = service.get_regulated_constraint_weights(
            [emergency_constraint_id]
        )
        weight_after, _ = weights_after[emergency_constraint_id]

        # Emergency constraint should be more important now
        assert weight_after > weight_before

    def test_crisis_mode_scenario(self):
        """Test crisis mode silences non-essential constraints."""
        service = ResilienceService()

        # Setup constraints
        essential_id = uuid4()
        optional_id = uuid4()

        # Essential constraint - linked to master regulator
        service.link_tf_to_constraint(
            tf_name="PatientSafety_MR",
            constraint_id=essential_id,
            constraint_name="PatientSafety",
        )

        # Optional constraint - linked to crisis mode repressor
        service.link_tf_to_constraint(
            tf_name="CrisisMode_TF",
            constraint_id=optional_id,
            constraint_name="OptionalEducation",
            as_activator=False,  # Represses this constraint
        )

        # Activate crisis mode
        service.process_regulatory_signal(
            event_type="crisis",
            description="Mass casualty event",
            signal_strength=1.0,
        )

        # Essential should remain active (master regulator always on)
        essential_weights = service.get_regulated_constraint_weights([essential_id])
        essential_weight, _ = essential_weights.get(essential_id, (1.0, ""))

        # Crisis mode TF should repress optional
        crisis_tf = service.tf_scheduler.get_tf_by_name("CrisisMode_TF")
        assert crisis_tf.is_active

    def test_combinatorial_regulation(self):
        """Test constraint requiring multiple TFs (AND logic)."""
        service = ResilienceService()

        # Create two TFs that must both be active
        tf1 = service.create_transcription_factor(
            "RequiredTF1",
            TFType.ACTIVATOR,
            basal_expression=0.0,
        )
        tf2 = service.create_transcription_factor(
            "RequiredTF2",
            TFType.ACTIVATOR,
            basal_expression=0.0,
        )

        constraint_id = uuid4()

        # Create promoter with AND logic
        service.tf_scheduler.create_promoter(
            constraint_id=constraint_id,
            constraint_name="ANDGatedConstraint",
            base_weight=2.0,
            activator_logic=BindingLogic.AND,
        )

        # Link both as required
        service.tf_scheduler.link_tf_to_constraint(
            tf1.id, constraint_id, as_activator=True, required=True
        )
        service.tf_scheduler.link_tf_to_constraint(
            tf2.id, constraint_id, as_activator=True, required=True
        )

        # Only TF1 active - should not activate constraint
        service.tf_scheduler.induce_tf(tf1.id, 1.0)
        weights1 = service.get_regulated_constraint_weights([constraint_id])
        weight1, _ = weights1[constraint_id]

        # Both active - should activate
        service.tf_scheduler.induce_tf(tf2.id, 1.0)
        weights2 = service.get_regulated_constraint_weights([constraint_id])
        weight2, _ = weights2[constraint_id]

        assert weight2 > weight1
