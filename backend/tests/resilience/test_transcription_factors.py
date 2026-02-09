"""Tests for Transcription Factor Scheduler (bio-inspired constraint regulation)."""

import math
from datetime import datetime
from uuid import uuid4

import pytest

from app.resilience.transcription_factors import (
    BindingLogic,
    BindingSite,
    ChromatinState,
    GRNState,
    LoopType,
    PromoterArchitecture,
    RegulatoryEdge,
    RegulatoryLoop,
    SignalEvent,
    SignalStrength,
    TFType,
    TranscriptionFactor,
    TranscriptionFactorScheduler,
)


# ==================== Enums ====================


class TestEnums:
    def test_tf_type_values(self):
        assert TFType.ACTIVATOR.value == "activator"
        assert TFType.REPRESSOR.value == "repressor"
        assert TFType.DUAL.value == "dual"
        assert TFType.PIONEER.value == "pioneer"
        assert TFType.MASTER.value == "master"
        assert len(TFType) == 5

    def test_binding_logic_values(self):
        assert BindingLogic.AND.value == "and"
        assert BindingLogic.OR.value == "or"
        assert BindingLogic.MAJORITY.value == "majority"
        assert BindingLogic.THRESHOLD.value == "threshold"
        assert BindingLogic.SEQUENTIAL.value == "sequential"
        assert len(BindingLogic) == 5

    def test_chromatin_state_values(self):
        assert ChromatinState.OPEN.value == "open"
        assert ChromatinState.POISED.value == "poised"
        assert ChromatinState.CLOSED.value == "closed"
        assert ChromatinState.SILENCED.value == "silenced"
        assert len(ChromatinState) == 4

    def test_signal_strength_values(self):
        assert SignalStrength.WEAK.value == "weak"
        assert SignalStrength.MODERATE.value == "moderate"
        assert SignalStrength.STRONG.value == "strong"
        assert SignalStrength.MAXIMAL.value == "maximal"
        assert len(SignalStrength) == 4

    def test_loop_type_values(self):
        assert LoopType.POSITIVE_FEEDBACK.value == "positive_feedback"
        assert LoopType.NEGATIVE_FEEDBACK.value == "negative_feedback"
        assert len(LoopType) == 5


# ==================== BindingSite ====================


class TestBindingSite:
    def test_default_affinity(self):
        bs = BindingSite(
            id=uuid4(),
            name="site1",
            tf_types_accepted=[TFType.ACTIVATOR],
        )
        assert bs.binding_affinity == 1.0
        assert bs.is_enhancer is False
        assert bs.is_silencer is False
        assert bs.distance_from_core == 0.0

    def test_get_effective_affinity_base(self):
        bs = BindingSite(
            id=uuid4(),
            name="site1",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=0.8,
        )
        # distance=0 -> distance_factor=1.0; base = 0.8 * 0.5 * 1.0 = 0.4
        result = bs.get_effective_affinity(0.5)
        assert abs(result - 0.4) < 0.01

    def test_enhancer_boosts(self):
        bs = BindingSite(
            id=uuid4(),
            name="enhancer",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=0.8,
            is_enhancer=True,
        )
        result = bs.get_effective_affinity(0.8)
        # base = 0.8 * 0.8 * 1.0 = 0.64; enhanced = 0.64 * 1.5 = 0.96
        assert result > 0.64

    def test_enhancer_capped_at_1(self):
        bs = BindingSite(
            id=uuid4(),
            name="strong_enhancer",
            tf_types_accepted=[TFType.ACTIVATOR],
            binding_affinity=1.0,
            is_enhancer=True,
        )
        result = bs.get_effective_affinity(1.0)
        assert result <= 1.0

    def test_silencer_reduces(self):
        bs = BindingSite(
            id=uuid4(),
            name="silencer",
            tf_types_accepted=[TFType.REPRESSOR],
            binding_affinity=0.8,
            is_silencer=True,
        )
        result = bs.get_effective_affinity(0.8)
        # base = 0.8 * 0.8 * 1.0 = 0.64; silenced = 0.64 * 0.5 = 0.32
        assert abs(result - 0.32) < 0.01

    def test_distance_reduces_affinity(self):
        bs_close = BindingSite(
            id=uuid4(),
            name="close",
            tf_types_accepted=[TFType.ACTIVATOR],
            distance_from_core=0.0,
        )
        bs_far = BindingSite(
            id=uuid4(),
            name="far",
            tf_types_accepted=[TFType.ACTIVATOR],
            distance_from_core=10.0,
        )
        close_result = bs_close.get_effective_affinity(1.0)
        far_result = bs_far.get_effective_affinity(1.0)
        assert far_result < close_result


# ==================== TranscriptionFactor ====================


class TestTranscriptionFactor:
    def _make_tf(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "name": "TestTF",
            "description": "Test",
            "tf_type": TFType.ACTIVATOR,
            "expression_level": 0.5,
            "basal_expression": 0.1,
        }
        defaults.update(kwargs)
        return TranscriptionFactor(**defaults)

    def test_induce_increases_expression(self):
        tf = self._make_tf(expression_level=0.1, basal_expression=0.1)
        old = tf.expression_level
        tf.induce(1.0)
        assert tf.expression_level > old

    def test_induce_respects_max(self):
        tf = self._make_tf(max_expression=0.8, expression_level=0.1)
        tf.induce(1.0)
        assert tf.expression_level <= 0.8

    def test_decay_toward_basal(self):
        tf = self._make_tf(
            expression_level=1.0, basal_expression=0.1, half_life_hours=1.0
        )
        tf.decay(10.0)
        # After 10 half-lives, should be very close to basal
        assert abs(tf.expression_level - 0.1) < 0.01

    def test_decay_zero_hours(self):
        tf = self._make_tf(expression_level=0.8)
        tf.decay(0)
        assert tf.expression_level == 0.8

    def test_decay_negative_hours(self):
        tf = self._make_tf(expression_level=0.8)
        tf.decay(-5)
        assert tf.expression_level == 0.8

    def test_get_effective_strength_activator(self):
        tf = self._make_tf(
            tf_type=TFType.ACTIVATOR,
            activation_strength=2.0,
            expression_level=0.5,
        )
        assert abs(tf.get_effective_strength() - 1.0) < 0.01

    def test_get_effective_strength_repressor(self):
        tf = self._make_tf(
            tf_type=TFType.REPRESSOR,
            repression_strength=0.5,
            expression_level=0.6,
        )
        assert abs(tf.get_effective_strength() - 0.3) < 0.01

    def test_get_effective_strength_dual(self):
        tf = self._make_tf(tf_type=TFType.DUAL, expression_level=0.7)
        assert abs(tf.get_effective_strength() - 0.7) < 0.01

    def test_is_active_above_threshold(self):
        tf = self._make_tf(expression_level=0.5)
        assert tf.is_active is True

    def test_is_active_below_threshold(self):
        tf = self._make_tf(expression_level=0.1)
        assert tf.is_active is False

    def test_signal_strength_weak(self):
        tf = self._make_tf(expression_level=0.1)
        assert tf.signal_strength_category == SignalStrength.WEAK

    def test_signal_strength_moderate(self):
        tf = self._make_tf(expression_level=0.4)
        assert tf.signal_strength_category == SignalStrength.MODERATE

    def test_signal_strength_strong(self):
        tf = self._make_tf(expression_level=0.7)
        assert tf.signal_strength_category == SignalStrength.STRONG

    def test_signal_strength_maximal(self):
        tf = self._make_tf(expression_level=0.9)
        assert tf.signal_strength_category == SignalStrength.MAXIMAL


# ==================== PromoterArchitecture ====================


class TestPromoterArchitecture:
    def _make_promoter(self, **kwargs):
        defaults = {
            "id": uuid4(),
            "constraint_id": uuid4(),
            "constraint_name": "TestConstraint",
        }
        defaults.update(kwargs)
        return PromoterArchitecture(**defaults)

    def test_defaults(self):
        p = self._make_promoter()
        assert p.activator_logic == BindingLogic.OR
        assert p.chromatin_state == ChromatinState.OPEN
        assert p.base_weight == 1.0
        assert p.binding_sites == []

    def test_silenced_returns_zero(self):
        p = self._make_promoter(chromatin_state=ChromatinState.SILENCED)
        activation, explanation = p.calculate_activation({})
        assert activation == 0.0
        assert "Silenced" in explanation

    def test_closed_without_pioneer_returns_zero(self):
        p = self._make_promoter(chromatin_state=ChromatinState.CLOSED)
        activation, explanation = p.calculate_activation({})
        assert activation == 0.0
        assert "Closed" in explanation

    def test_or_logic_takes_max(self):
        tf1, tf2 = uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.OR)
        p.optional_activators = [tf1, tf2]
        activation, _ = p.calculate_activation({tf1: 0.3, tf2: 0.7})
        assert abs(activation - 0.7) < 0.01

    def test_and_logic_requires_all(self):
        tf1, tf2 = uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.AND)
        p.required_activators = [tf1, tf2]
        # Only tf1 present
        activation, explanation = p.calculate_activation({tf1: 0.5})
        assert activation == 0.0
        assert "missing" in explanation.lower()

    def test_and_logic_both_present(self):
        tf1, tf2 = uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.AND)
        p.required_activators = [tf1, tf2]
        activation, _ = p.calculate_activation({tf1: 0.5, tf2: 0.8})
        assert activation > 0.0
        assert activation == 0.5  # min of signals

    def test_majority_logic(self):
        tf1, tf2, tf3 = uuid4(), uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.MAJORITY)
        p.required_activators = [tf1, tf2, tf3]
        # 2 of 3 active (above 0.3) -> majority
        activation, _ = p.calculate_activation({tf1: 0.5, tf2: 0.6, tf3: 0.1})
        assert activation > 0.0

    def test_majority_logic_fails(self):
        tf1, tf2, tf3 = uuid4(), uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.MAJORITY)
        p.required_activators = [tf1, tf2, tf3]
        # Only 1 of 3 active
        activation, explanation = p.calculate_activation({tf1: 0.5, tf2: 0.1, tf3: 0.1})
        assert activation == 0.0
        assert "insufficient" in explanation.lower()

    def test_threshold_logic(self):
        tf1, tf2 = uuid4(), uuid4()
        p = self._make_promoter(
            activator_logic=BindingLogic.THRESHOLD,
            activation_threshold=0.8,
        )
        p.optional_activators = [tf1, tf2]
        # Sum = 0.5 + 0.5 = 1.0 >= 0.8
        activation, _ = p.calculate_activation({tf1: 0.5, tf2: 0.5})
        assert activation > 0.0

    def test_threshold_logic_fails(self):
        tf1, tf2 = uuid4(), uuid4()
        p = self._make_promoter(
            activator_logic=BindingLogic.THRESHOLD,
            activation_threshold=1.5,
        )
        p.optional_activators = [tf1, tf2]
        # Sum = 0.3 + 0.4 = 0.7 < 1.5
        activation, explanation = p.calculate_activation({tf1: 0.3, tf2: 0.4})
        assert activation == 0.0
        assert "THRESHOLD" in explanation

    def test_repressors_reduce_activation(self):
        tf_act, tf_rep = uuid4(), uuid4()
        p = self._make_promoter(activator_logic=BindingLogic.OR)
        p.optional_activators = [tf_act]
        p.repressors = [tf_rep]
        activation, _ = p.calculate_activation({tf_act: 0.8, tf_rep: 0.5})
        # activation = max(0, 0.8 - 0.5) = 0.3
        assert abs(activation - 0.3) < 0.01

    def test_get_effective_weight(self):
        p = self._make_promoter(base_weight=2.0, min_weight=0.0, max_weight=10.0)
        assert abs(p.get_effective_weight(0.5) - 1.0) < 0.01

    def test_get_effective_weight_clamped(self):
        p = self._make_promoter(base_weight=5.0, max_weight=3.0)
        assert p.get_effective_weight(1.0) == 3.0

    def test_get_effective_weight_min(self):
        p = self._make_promoter(base_weight=2.0, min_weight=0.5)
        assert p.get_effective_weight(0.0) == 0.5


# ==================== RegulatoryEdge ====================


class TestRegulatoryEdge:
    def test_defaults(self):
        e = RegulatoryEdge(
            id=uuid4(),
            source_tf_id=uuid4(),
            target_id=uuid4(),
            target_type="constraint",
            edge_type=TFType.ACTIVATOR,
        )
        assert e.strength == 1.0
        assert e.delay_hours == 0.0
        assert e.conditions == {}
        assert e.is_active is True


# ==================== RegulatoryLoop ====================


class TestRegulatoryLoop:
    def test_construction(self):
        loop = RegulatoryLoop(
            id=uuid4(),
            loop_type=LoopType.POSITIVE_FEEDBACK,
            description="Test loop",
            tf_ids=[uuid4(), uuid4()],
            constraint_ids=[],
            edges=[],
        )
        assert loop.stability == "unknown"
        assert loop.period_hours is None


# ==================== SignalEvent ====================


class TestSignalEvent:
    def test_construction(self):
        s = SignalEvent(
            id=uuid4(),
            event_type="deployment",
            description="Unit deployment",
            timestamp=datetime.now(),
            target_tf_ids=[],
        )
        assert s.signal_strength == 1.0
        assert s.propagated is False
        assert s.cascade_depth == 0


# ==================== GRNState ====================


class TestGRNState:
    def test_construction(self):
        state = GRNState(
            timestamp=datetime.now(),
            tf_expressions={uuid4(): 0.5},
            constraint_weights={uuid4(): 1.0},
            active_loops=[],
            total_activation=0.5,
            total_repression=0.0,
            network_entropy=0.1,
        )
        assert state.total_activation == 0.5


# ==================== TranscriptionFactorScheduler ====================


class TestTFSchedulerInit:
    def test_has_default_tfs(self):
        tfs = TranscriptionFactorScheduler()
        assert len(tfs.transcription_factors) >= 8  # Default TFs

    def test_default_tf_names(self):
        tfs = TranscriptionFactorScheduler()
        names = set(tfs._tf_by_name.keys())
        assert "PatientSafety_MR" in names
        assert "ACGMECompliance_MR" in names
        assert "MilitaryEmergency_TF" in names
        assert "CrisisMode_TF" in names

    def test_patient_safety_always_active(self):
        tfs = TranscriptionFactorScheduler()
        ps = tfs.get_tf_by_name("PatientSafety_MR")
        assert ps is not None
        assert ps.is_active is True  # basal_expression=1.0 > 0.2


class TestCreateTF:
    def test_creates_and_stores(self):
        tfs = TranscriptionFactorScheduler()
        initial_count = len(tfs.transcription_factors)
        tf = tfs.create_tf("Custom_TF", TFType.ACTIVATOR, "Custom test")
        assert len(tfs.transcription_factors) == initial_count + 1
        assert tfs.get_tf_by_name("Custom_TF") is not None

    def test_expression_starts_at_basal(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Test", TFType.ACTIVATOR, basal_expression=0.3)
        assert tf.expression_level == 0.3


class TestGetTFByName:
    def test_found(self):
        tfs = TranscriptionFactorScheduler()
        assert tfs.get_tf_by_name("PatientSafety_MR") is not None

    def test_not_found(self):
        tfs = TranscriptionFactorScheduler()
        assert tfs.get_tf_by_name("NonExistent") is None


class TestInduceTF:
    def test_induces(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Inducible", TFType.ACTIVATOR, basal_expression=0.0)
        old = tf.expression_level
        tfs.induce_tf(tf.id, 1.0)
        assert tf.expression_level > old

    def test_induce_nonexistent_no_error(self):
        tfs = TranscriptionFactorScheduler()
        tfs.induce_tf(uuid4(), 1.0)  # Should not raise


class TestCascadePropagation:
    def test_cascade(self):
        tfs = TranscriptionFactorScheduler()
        tf1 = tfs.create_tf("Source", TFType.ACTIVATOR, basal_expression=0.0)
        tf2 = tfs.create_tf("Target", TFType.ACTIVATOR, basal_expression=0.0)
        tf1.target_tf_ids.append(tf2.id)
        tfs.induce_tf(tf1.id, 1.0)
        assert tf2.expression_level > 0.0


class TestDecayAllTFs:
    def test_decays(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Decayer", TFType.ACTIVATOR, basal_expression=0.0)
        tf.induce(1.0)
        high = tf.expression_level
        tfs.decay_all_tfs(hours_elapsed=100)
        assert tf.expression_level < high


class TestCreatePromoter:
    def test_creates(self):
        tfs = TranscriptionFactorScheduler()
        cid = uuid4()
        p = tfs.create_promoter(cid, "TestConstraint")
        assert cid in tfs.promoters
        assert p.constraint_name == "TestConstraint"


class TestLinkTFToConstraint:
    def test_link_activator(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Linker", TFType.ACTIVATOR)
        cid = uuid4()
        tfs.link_tf_to_constraint(tf.id, cid, as_activator=True)
        assert cid in tf.target_constraint_ids
        assert cid in tfs.promoters

    def test_link_repressor(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Repressor", TFType.REPRESSOR)
        cid = uuid4()
        tfs.link_tf_to_constraint(tf.id, cid, as_activator=False)
        promoter = tfs.promoters[cid]
        assert tf.id in promoter.repressors

    def test_link_required_activator(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Required", TFType.ACTIVATOR)
        cid = uuid4()
        tfs.link_tf_to_constraint(tf.id, cid, as_activator=True, required=True)
        promoter = tfs.promoters[cid]
        assert tf.id in promoter.required_activators

    def test_link_nonexistent_tf(self):
        tfs = TranscriptionFactorScheduler()
        tfs.link_tf_to_constraint(uuid4(), uuid4())  # Should not raise


class TestLinkTFToTF:
    def test_creates_edge(self):
        tfs = TranscriptionFactorScheduler()
        tf1 = tfs.create_tf("Source", TFType.ACTIVATOR)
        tf2 = tfs.create_tf("Target", TFType.ACTIVATOR)
        tfs.link_tf_to_tf(tf1.id, tf2.id)
        assert tf2.id in tf1.target_tf_ids
        assert len(tfs.edges) > 0

    def test_link_nonexistent_no_error(self):
        tfs = TranscriptionFactorScheduler()
        tfs.link_tf_to_tf(uuid4(), uuid4())  # Should not raise


class TestProcessSignal:
    def test_signal_induces_matching_tfs(self):
        tfs = TranscriptionFactorScheduler()
        mil_tf = tfs.get_tf_by_name("MilitaryEmergency_TF")
        old = mil_tf.expression_level
        tfs.create_signal("deployment", "Test deployment", signal_strength=1.0)
        assert mil_tf.expression_level > old

    def test_signal_recorded(self):
        tfs = TranscriptionFactorScheduler()
        tfs.create_signal("test_event", "Test")
        assert len(tfs.signal_history) == 1
        assert tfs.signal_history[0].propagated is True

    def test_custom_handler(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("CustomTarget", TFType.ACTIVATOR, basal_expression=0.0)

        def handler(signal):
            return [tf.id]

        tfs.register_signal_handler("custom", handler)
        tfs.create_signal("custom", "Custom event")
        assert tf.expression_level > 0.0

    def test_crisis_induces_crisis_tf(self):
        tfs = TranscriptionFactorScheduler()
        crisis_tf = tfs.get_tf_by_name("CrisisMode_TF")
        old = crisis_tf.expression_level
        tfs.create_signal("crisis", "Test crisis")
        assert crisis_tf.expression_level > old


class TestGetConstraintWeights:
    def test_no_promoters_returns_empty(self):
        tfs = TranscriptionFactorScheduler()
        weights = tfs.get_constraint_weights()
        assert weights == {}

    def test_with_linked_constraint(self):
        tfs = TranscriptionFactorScheduler()
        tf = tfs.create_tf("Active", TFType.ACTIVATOR, basal_expression=0.5)
        cid = uuid4()
        tfs.link_tf_to_constraint(tf.id, cid, as_activator=True)
        weights = tfs.get_constraint_weights()
        assert cid in weights
        weight, explanation = weights[cid]
        assert weight >= 0.0

    def test_get_weight_for_single(self):
        tfs = TranscriptionFactorScheduler()
        cid = uuid4()
        weight, explanation = tfs.get_weight_for_constraint(cid)
        assert weight == 1.0  # No regulatory data
        assert "No regulatory data" in explanation


class TestChromatinStateManagement:
    def test_set_state(self):
        tfs = TranscriptionFactorScheduler()
        cid = uuid4()
        tfs.create_promoter(cid, "Test")
        tfs.set_chromatin_state(cid, ChromatinState.SILENCED)
        assert tfs.promoters[cid].chromatin_state == ChromatinState.SILENCED

    def test_silence_constraints(self):
        tfs = TranscriptionFactorScheduler()
        cid1, cid2 = uuid4(), uuid4()
        tfs.create_promoter(cid1, "C1")
        tfs.create_promoter(cid2, "C2")
        tfs.silence_constraints([cid1, cid2])
        assert tfs.promoters[cid1].chromatin_state == ChromatinState.SILENCED
        assert tfs.promoters[cid2].chromatin_state == ChromatinState.SILENCED

    def test_open_constraints(self):
        tfs = TranscriptionFactorScheduler()
        cid = uuid4()
        tfs.create_promoter(cid, "C1")
        tfs.silence_constraints([cid])
        tfs.open_constraints([cid])
        assert tfs.promoters[cid].chromatin_state == ChromatinState.OPEN


class TestDetectLoops:
    def test_no_loops_initially(self):
        tfs = TranscriptionFactorScheduler()
        loops = tfs.detect_loops()
        # Default TFs have no TF-to-TF links
        assert len(loops) == 0

    def test_feedback_loop(self):
        tfs = TranscriptionFactorScheduler()
        tf1 = tfs.create_tf("A", TFType.ACTIVATOR)
        tf2 = tfs.create_tf("B", TFType.ACTIVATOR)
        tfs.link_tf_to_tf(tf1.id, tf2.id, as_activator=True)
        tfs.link_tf_to_tf(tf2.id, tf1.id, as_activator=True)
        loops = tfs.detect_loops()
        # Should detect positive feedback (both activators)
        assert any(l.loop_type == LoopType.POSITIVE_FEEDBACK for l in loops)

    def test_negative_feedback_loop(self):
        tfs = TranscriptionFactorScheduler()
        tf1 = tfs.create_tf("A", TFType.ACTIVATOR)
        tf2 = tfs.create_tf("B", TFType.REPRESSOR)
        tfs.link_tf_to_tf(tf1.id, tf2.id, as_activator=True)
        tfs.link_tf_to_tf(tf2.id, tf1.id, as_activator=False)
        loops = tfs.detect_loops()
        assert any(l.loop_type == LoopType.NEGATIVE_FEEDBACK for l in loops)


class TestSnapshotState:
    def test_snapshot(self):
        tfs = TranscriptionFactorScheduler()
        state = tfs.snapshot_state()
        assert isinstance(state, GRNState)
        assert len(state.tf_expressions) == len(tfs.transcription_factors)

    def test_history_stored(self):
        tfs = TranscriptionFactorScheduler()
        tfs.snapshot_state()
        tfs.snapshot_state()
        assert len(tfs.state_history) == 2

    def test_history_pruned(self):
        tfs = TranscriptionFactorScheduler()
        # Take many snapshots
        for _ in range(1010):
            tfs.snapshot_state()
        # Pruned from 1010 to ~500 (may vary slightly due to test calls)
        assert len(tfs.state_history) < 600


class TestGetStatus:
    def test_status_keys(self):
        tfs = TranscriptionFactorScheduler()
        status = tfs.get_status()
        assert "total_tfs" in status
        assert "active_tfs" in status
        assert "master_regulators_active" in status
        assert "regulatory_edges" in status
        assert "network_entropy" in status
        assert "active_tf_names" in status

    def test_master_regulators_counted(self):
        tfs = TranscriptionFactorScheduler()
        status = tfs.get_status()
        # PatientSafety_MR and ACGMECompliance_MR are both MASTER and active
        assert status["master_regulators_active"] >= 2


class TestGetTFExpressionReport:
    def test_returns_list(self):
        tfs = TranscriptionFactorScheduler()
        report = tfs.get_tf_expression_report()
        assert isinstance(report, list)
        assert len(report) == len(tfs.transcription_factors)

    def test_report_fields(self):
        tfs = TranscriptionFactorScheduler()
        report = tfs.get_tf_expression_report()
        entry = report[0]
        assert "name" in entry
        assert "type" in entry
        assert "expression" in entry
        assert "is_active" in entry
        assert "targets" in entry

    def test_sorted_by_expression(self):
        tfs = TranscriptionFactorScheduler()
        report = tfs.get_tf_expression_report()
        for i in range(len(report) - 1):
            assert report[i]["expression"] >= report[i + 1]["expression"]
