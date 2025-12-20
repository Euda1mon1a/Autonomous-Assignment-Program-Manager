# Neural Computation Concepts for Scheduling Systems: Research Report

> **Research Date:** 2025-12-20
> **Purpose:** Explore neuroscience and neural computation principles for preference learning, assignment optimization, and adaptive scheduling
> **Context:** Complement existing transcription factor networks (gene regulation) and stigmergy (swarm intelligence) with neural computation metaphors

---

## Executive Summary

This report examines seven exotic neuroscience concepts and their applications to scheduling optimization:

1. **Hebbian Learning** - Associative preference strengthening
2. **Lateral Inhibition** - Winner-take-all assignment competition
3. **Neural Plasticity** - Adaptive weight adjustment and continual learning
4. **Sparse Coding** - Efficient schedule representation
5. **Attractor Networks** - Stable schedule states and convergence
6. **Predictive Coding** - Prediction error minimization
7. **Neuromodulation** - Global context signals for adaptive processing

Each concept offers unique advantages for learning faculty preferences, optimizing assignments, and adapting to changing conditions while balancing stability (retain learned patterns) and plasticity (adapt to new information).

---

## Table of Contents

1. [Hebbian Learning](#1-hebbian-learning)
2. [Lateral Inhibition](#2-lateral-inhibition)
3. [Neural Plasticity](#3-neural-plasticity)
4. [Sparse Coding](#4-sparse-coding)
5. [Attractor Networks](#5-attractor-networks)
6. [Predictive Coding](#6-predictive-coding)
7. [Neuromodulation](#7-neuromodulation)
8. [Integration Strategy](#8-integration-strategy)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [References](#10-references)

---

## 1. Hebbian Learning

### Core Neuroscience Principle

**"Neurons that fire together, wire together"** - Donald Hebb (1949)

When a presynaptic neuron repeatedly stimulates a postsynaptic neuron, the connection (synapse) between them strengthens. This is the brain's fundamental mechanism for associative learning and pattern recognition.

**Mathematical Formulation:**
```
Δw_ij = η * x_i * x_j
```
Where:
- `w_ij` = connection weight from neuron i to neuron j
- `η` = learning rate
- `x_i` = activity of presynaptic neuron i
- `x_j` = activity of postsynaptic neuron j

**Biological Context:**
- Synaptic strength increases when neurons fire synchronously
- Mechanism for learning temporal and spatial correlations
- Underlies associative memory formation
- No central supervisor required - purely local learning rule

### Application to Scheduling

**Preference Learning:**
When faculty member F is repeatedly assigned to slot S and provides positive signals (accepts assignment, high satisfaction), strengthen the association between F and S.

**Assignment Optimization:**
Learn which faculty-slot pairs "work well together" by tracking co-occurrence and satisfaction. Strong associations guide future assignments.

**Adaptation:**
Continuously update associations based on recent experience. Positive outcomes strengthen connections; negative outcomes weaken them.

### Implementation Ideas

#### Architecture: Faculty-Slot Hebbian Network

```python
class HebbianPreferenceNetwork:
    """
    Learn faculty-slot associations through Hebbian strengthening.

    Network Structure:
    - Nodes: Faculty members and time slots
    - Edges: Association weights (preference strength)
    - Updates: Hebbian rule applied after each assignment
    """

    def __init__(self, learning_rate: float = 0.01):
        self.weights = {}  # (faculty_id, slot_id) -> weight
        self.learning_rate = learning_rate
        self.decay_rate = 0.001  # Prevent unbounded growth

    def strengthen_association(
        self,
        faculty_id: UUID,
        slot_id: UUID,
        faculty_satisfaction: float = 1.0,  # 0-1 scale
        slot_quality: float = 1.0  # How well faculty performed
    ):
        """
        Hebbian update: strengthen when both neurons fire.

        Args:
            faculty_id: Faculty who was assigned
            slot_id: Slot they were assigned to
            faculty_satisfaction: How satisfied faculty was (0-1)
            slot_quality: How well assignment worked out (0-1)
        """
        key = (faculty_id, slot_id)
        current_weight = self.weights.get(key, 0.0)

        # Classic Hebbian: Δw = η * x_i * x_j
        delta = self.learning_rate * faculty_satisfaction * slot_quality

        # Update with decay to prevent saturation
        new_weight = current_weight + delta - (self.decay_rate * current_weight)
        self.weights[key] = max(0.0, min(1.0, new_weight))

    def get_preference_score(self, faculty_id: UUID, slot_id: UUID) -> float:
        """Get learned association strength."""
        return self.weights.get((faculty_id, slot_id), 0.5)  # Default: neutral

    def recommend_assignments(
        self,
        available_faculty: list[UUID],
        available_slots: list[UUID]
    ) -> list[tuple[UUID, UUID, float]]:
        """
        Recommend assignments based on Hebbian weights.

        Returns:
            List of (faculty_id, slot_id, preference_score) sorted by strength
        """
        recommendations = []
        for faculty_id in available_faculty:
            for slot_id in available_slots:
                score = self.get_preference_score(faculty_id, slot_id)
                recommendations.append((faculty_id, slot_id, score))

        return sorted(recommendations, key=lambda x: -x[2])
```

#### Advanced: Contrastive Hebbian Learning (CHL)

**Concept:** Learn by comparing two states:
- **Clamped state:** Actual assignment that occurred
- **Free state:** What network would predict without constraints

```python
def contrastive_hebbian_update(
    self,
    faculty_id: UUID,
    assigned_slot: UUID,
    predicted_slot: UUID,
    outcome_quality: float
):
    """
    CHL: Δw = (x_clamped - x_free) * outcome

    Strengthens correct predictions, weakens incorrect ones.
    """
    # Strengthen actual assignment if outcome was good
    if outcome_quality > 0.5:
        self.strengthen_association(faculty_id, assigned_slot, outcome_quality)

    # Weaken what was predicted if it was wrong and outcome was bad
    if assigned_slot != predicted_slot and outcome_quality < 0.5:
        self.weaken_association(faculty_id, predicted_slot, 1 - outcome_quality)
```

### Balancing Stability and Plasticity

**Challenge:** Strong Hebbian learning can lead to runaway excitation (weights grow unbounded) or premature convergence (network gets stuck in local optimum).

**Solutions:**

1. **Weight Decay (Oja's Rule):**
   ```python
   Δw = η * x_i * x_j - decay_rate * w * x_j^2
   ```
   Prevents weights from growing unbounded while maintaining learned patterns.

2. **Weight Normalization:**
   ```python
   # Keep sum of all weights for a faculty constant
   total = sum(self.weights[(faculty_id, s)] for s in all_slots)
   for slot in all_slots:
       self.weights[(faculty_id, slot)] /= total
   ```
   Ensures learning new preferences doesn't destroy all existing knowledge.

3. **Temporal Windowing:**
   ```python
   # Only update based on recent assignments (last N weeks)
   if assignment.date > datetime.now() - timedelta(weeks=12):
       self.strengthen_association(...)
   ```
   Allows adaptation to changing preferences while maintaining stable long-term patterns.

4. **BCM (Bienenstock-Cooper-Munro) Rule:**
   ```python
   # Sliding threshold: strengthen if post-synaptic activity exceeds threshold
   threshold = exponential_average(faculty_satisfaction)
   if faculty_satisfaction > threshold:
       strengthen()
   else:
       weaken()
   ```
   Prevents saturation by adjusting learning threshold based on recent history.

---

## 2. Lateral Inhibition

### Core Neuroscience Principle

**Neighboring neurons suppress each other's activity** - creates "winner-take-all" dynamics where the most activated neuron inhibits its neighbors, sharpening responses and enhancing contrast.

**Biological Examples:**
- **Visual system:** Edge detection - center-surround receptive fields enhance boundaries
- **Motor control:** One muscle group activates while antagonists are inhibited
- **Decision-making:** Competing options inhibit each other until one "wins"

**Mathematical Model:**
```
activation_i = input_i - Σ(w_ij * activation_j) for j ≠ i
```
Where stronger neighbors suppress weaker ones.

### Application to Scheduling

**Assignment Competition:**
When multiple faculty want the same desirable slot, lateral inhibition creates competitive dynamics where the best-fit faculty "wins" and others are suppressed.

**Conflict Resolution:**
Mutually exclusive assignments inhibit each other. If faculty A is assigned to Monday AM, they cannot also be assigned to Monday AM clinic - the chosen assignment inhibits competing options.

**Load Balancing:**
High-assignment faculty inhibit themselves from being assigned more, creating pressure to distribute work evenly.

### Implementation Ideas

#### Architecture: Winner-Take-All Assignment Selection

```python
class LateralInhibitionScheduler:
    """
    Assignment selection using lateral inhibition dynamics.

    Competing assignments inhibit each other until the system
    converges to a stable, non-conflicting schedule.
    """

    def __init__(self, inhibition_strength: float = 0.5):
        self.inhibition_strength = inhibition_strength
        self.activations = {}  # (faculty, slot) -> activation level

    def initialize_activations(
        self,
        faculty_preferences: dict[tuple[UUID, UUID], float],
        constraints: dict[tuple[UUID, UUID], float]
    ):
        """
        Initialize activation levels based on preferences and constraints.

        Args:
            faculty_preferences: (faculty_id, slot_id) -> preference score
            constraints: (faculty_id, slot_id) -> constraint satisfaction
        """
        for (faculty_id, slot_id), pref in faculty_preferences.items():
            constraint_score = constraints.get((faculty_id, slot_id), 1.0)
            initial_activation = pref * constraint_score
            self.activations[(faculty_id, slot_id)] = initial_activation

    def apply_lateral_inhibition(self):
        """
        Apply lateral inhibition: strong assignments suppress weak ones.

        Inhibition Rules:
        1. Same faculty, different slots: compete for faculty time
        2. Different faculty, same slot: compete for slot access
        3. Conflicting ACGME constraints: mutual inhibition
        """
        new_activations = {}

        for (faculty_id, slot_id), activation in self.activations.items():
            # Start with current activation
            inhibited_activation = activation

            # Inhibition from competing assignments for same faculty
            for (other_faculty, other_slot), other_activation in self.activations.items():
                if other_faculty == faculty_id and other_slot != slot_id:
                    # Competing for same faculty's time
                    inhibition = self.inhibition_strength * other_activation
                    inhibited_activation -= inhibition

            # Inhibition from competing assignments for same slot
            for (other_faculty, other_slot), other_activation in self.activations.items():
                if other_slot == slot_id and other_faculty != faculty_id:
                    # Competing for same slot
                    inhibition = self.inhibition_strength * other_activation
                    inhibited_activation -= inhibition

            # Apply ReLU: activation can't go negative
            new_activations[(faculty_id, slot_id)] = max(0.0, inhibited_activation)

        self.activations = new_activations

    def converge_to_winner_take_all(self, max_iterations: int = 100) -> dict:
        """
        Iterate lateral inhibition until convergence.

        Returns:
            Dict of (faculty_id, slot_id) -> final_activation
        """
        for iteration in range(max_iterations):
            old_activations = dict(self.activations)
            self.apply_lateral_inhibition()

            # Check convergence: activations stop changing
            max_change = max(
                abs(self.activations.get(k, 0) - old_activations.get(k, 0))
                for k in set(self.activations.keys()) | set(old_activations.keys())
            )

            if max_change < 0.01:
                logger.info(f"Converged after {iteration} iterations")
                break

        return self.activations

    def select_winners(self, threshold: float = 0.5) -> list[tuple[UUID, UUID]]:
        """
        Select assignments that survived inhibition.

        Args:
            threshold: Minimum activation to be selected

        Returns:
            List of (faculty_id, slot_id) assignments
        """
        return [
            (faculty_id, slot_id)
            for (faculty_id, slot_id), activation in self.activations.items()
            if activation >= threshold
        ]
```

#### Advanced: K-Winner-Take-All (K-WTA)

Instead of single winner, select top K activations:

```python
def k_winner_take_all(self, k: int = 5) -> list[tuple[UUID, UUID, float]]:
    """
    Select K strongest assignments per slot.

    Useful when you need backup assignments or want to
    consider multiple options before final selection.
    """
    assignments_by_slot = {}
    for (faculty_id, slot_id), activation in self.activations.items():
        if slot_id not in assignments_by_slot:
            assignments_by_slot[slot_id] = []
        assignments_by_slot[slot_id].append((faculty_id, activation))

    winners = []
    for slot_id, candidates in assignments_by_slot.items():
        # Sort by activation, take top K
        top_k = sorted(candidates, key=lambda x: -x[1])[:k]
        for faculty_id, activation in top_k:
            winners.append((faculty_id, slot_id, activation))

    return winners
```

### Balancing Stability and Plasticity

**Challenge:** Too much inhibition creates brittle solutions where small changes cause cascading failures. Too little inhibition creates ambiguous, conflicting assignments.

**Solutions:**

1. **Adaptive Inhibition Strength:**
   ```python
   # Increase inhibition when many conflicts, decrease when stable
   conflict_rate = count_conflicts() / total_assignments
   self.inhibition_strength = 0.3 + (0.4 * conflict_rate)
   ```

2. **Soft WTA (Softmax):**
   ```python
   # Instead of hard winner-take-all, use softmax for probabilistic selection
   def softmax_selection(self, temperature: float = 1.0):
       """Lower temperature = sharper winner-take-all"""
       exp_activations = {
           k: math.exp(v / temperature)
           for k, v in self.activations.items()
       }
       # Normalize to probabilities
       total = sum(exp_activations.values())
       return {k: v/total for k, v in exp_activations.items()}
   ```

3. **Homeostatic Inhibition:**
   ```python
   # Adjust inhibition to maintain target sparsity (e.g., 20% of assignments active)
   target_sparsity = 0.2
   current_sparsity = count_active() / total_possible_assignments

   if current_sparsity > target_sparsity:
       self.inhibition_strength *= 1.1  # More inhibition
   else:
       self.inhibition_strength *= 0.9  # Less inhibition
   ```

---

## 3. Neural Plasticity

### Core Neuroscience Principle

**The brain continuously adapts its structure and function in response to experience** through mechanisms like:
- **Synaptic plasticity:** Connection strength changes (Hebbian, LTP/LTD)
- **Structural plasticity:** New synapses form, old ones prune
- **Homeostatic plasticity:** Overall excitability adjusts to maintain stability
- **Metaplasticity:** The ability to learn changes over time

**Key Insight:** Plasticity is not uniform - critical circuits are more stable, less critical circuits are more plastic.

### Application to Scheduling

**Preference Adaptation:**
Faculty preferences evolve over time (new research interests, family situations, career stage). The system must adapt without forgetting stable core preferences.

**Constraint Evolution:**
ACGME rules change, new services are added, faculty retire. The scheduling system must flexibly incorporate new constraints.

**Continual Learning:**
Learn from every schedule generated without catastrophic forgetting of previously successful patterns.

### Implementation Ideas

#### Architecture: Plasticity-Driven Learning Framework (PDLF)

```python
class AdaptivePreferenceNetwork:
    """
    Neural network with adaptive plasticity for continual preference learning.

    Inspired by PDLF (2025): Learn not just weights, but plasticity rules themselves.
    """

    def __init__(self):
        self.weights = {}  # (faculty, slot) -> preference weight
        self.plasticity = {}  # (faculty, slot) -> learning rate
        self.importance = {}  # (faculty, slot) -> how critical this weight is

    def compute_plasticity(
        self,
        faculty_id: UUID,
        slot_id: UUID,
        recent_variance: float,
        satisfaction_history: list[float]
    ) -> float:
        """
        Adaptive plasticity: high variance = high plasticity (still learning),
        low variance = low plasticity (stable preference).

        This is Synaptic Cooperation Plasticity (SCP) from PDLF.
        """
        # High variance in recent satisfaction -> preference still uncertain
        if recent_variance > 0.2:
            return 0.5  # High plasticity

        # Consistent satisfaction -> stable preference
        if all(s > 0.7 for s in satisfaction_history[-5:]):
            return 0.05  # Low plasticity (don't mess with what works)

        # Consistently low satisfaction -> need to relearn
        if all(s < 0.3 for s in satisfaction_history[-5:]):
            return 0.4  # High plasticity (explore alternatives)

        return 0.2  # Default moderate plasticity

    def elastic_weight_consolidation(
        self,
        faculty_id: UUID,
        slot_id: UUID,
        new_signal: float,
        task_importance: float = 1.0
    ):
        """
        Elastic Weight Consolidation (EWC): protect important weights.

        Based on neuroscience: critical memories are protected from disruption.

        Args:
            faculty_id: Faculty member
            slot_id: Time slot
            new_signal: New preference signal (0-1)
            task_importance: How important this assignment was (0-1)
        """
        key = (faculty_id, slot_id)

        # Get current values
        current_weight = self.weights.get(key, 0.5)
        importance = self.importance.get(key, 0.0)
        plasticity = self.plasticity.get(key, 0.2)

        # Update importance based on task criticality
        # Important assignments (e.g., critical clinical coverage) get high importance
        self.importance[key] = importance + (task_importance * 0.1)

        # Compute update with elastic constraint
        # High importance = resist change (elastic pull-back)
        elastic_constraint = importance * (new_signal - current_weight)
        learning_term = plasticity * (new_signal - current_weight)

        # Balance new learning with protecting important knowledge
        delta = learning_term - (0.5 * elastic_constraint)

        self.weights[key] = current_weight + delta

    def metaplasticity_adjustment(self, faculty_id: UUID):
        """
        Metaplasticity: adjust plasticity based on learning history.

        Faculty who consistently have stable preferences get lower global plasticity.
        Faculty with volatile preferences get higher global plasticity.
        """
        # Get all weights for this faculty
        faculty_weights = {
            k: v for k, v in self.weights.items()
            if k[0] == faculty_id
        }

        if not faculty_weights:
            return

        # Compute weight variance (how diverse are preferences)
        weight_values = list(faculty_weights.values())
        mean_weight = sum(weight_values) / len(weight_values)
        variance = sum((w - mean_weight)**2 for w in weight_values) / len(weight_values)

        # High variance = diverse preferences = need more plasticity
        # Low variance = consistent preferences = need less plasticity
        global_plasticity_adjustment = min(0.5, variance)

        # Update all plasticity values for this faculty
        for (fid, slot_id) in faculty_weights.keys():
            current_plasticity = self.plasticity.get((fid, slot_id), 0.2)
            self.plasticity[(fid, slot_id)] = (
                0.7 * current_plasticity + 0.3 * global_plasticity_adjustment
            )
```

#### Advanced: Continual Learning with Synaptic Scaling

```python
class ContinualLearningScheduler:
    """
    Prevent catastrophic forgetting when learning new scheduling patterns.

    Based on Adaptive Synaptic Scaling (AS-SNN, 2025).
    """

    def __init__(self):
        self.weights = {}
        self.historical_patterns = []  # Store old successful schedules
        self.memory_buffer = []  # Experience replay buffer

    def learn_new_schedule(
        self,
        new_assignments: list[Assignment],
        satisfaction_scores: dict[UUID, float]
    ):
        """
        Learn from new schedule without forgetting old patterns.

        Uses three mechanisms:
        1. Experience replay: rehearse old patterns
        2. Synaptic scaling: normalize weights to prevent drift
        3. Memory consolidation: protect critical patterns
        """
        # Add new experience to buffer
        self.memory_buffer.append({
            'assignments': new_assignments,
            'satisfaction': satisfaction_scores,
            'timestamp': datetime.now()
        })

        # Limit buffer size (keep last 100 schedules)
        if len(self.memory_buffer) > 100:
            self.memory_buffer = self.memory_buffer[-100:]

        # 1. Learn from new schedule
        for assignment in new_assignments:
            faculty_id = assignment.person_id
            slot_id = assignment.block_id
            satisfaction = satisfaction_scores.get(faculty_id, 0.5)

            self._update_weight(faculty_id, slot_id, satisfaction)

        # 2. Experience replay: rehearse random samples from memory
        import random
        replay_samples = random.sample(
            self.memory_buffer,
            min(10, len(self.memory_buffer))
        )

        for sample in replay_samples:
            for assignment in sample['assignments']:
                faculty_id = assignment.person_id
                slot_id = assignment.block_id
                satisfaction = sample['satisfaction'].get(faculty_id, 0.5)

                # Smaller update for replayed experiences
                self._update_weight(faculty_id, slot_id, satisfaction, lr=0.01)

        # 3. Synaptic scaling: maintain stable weight distribution
        self._apply_synaptic_scaling()

    def _apply_synaptic_scaling(self):
        """
        Homeostatic synaptic scaling: adjust all weights proportionally
        to maintain target mean activation.

        Prevents weight drift over continual learning.
        """
        if not self.weights:
            return

        # Target mean weight
        target_mean = 0.5

        # Current mean
        current_mean = sum(self.weights.values()) / len(self.weights)

        # Scaling factor
        scale = target_mean / current_mean if current_mean > 0 else 1.0

        # Apply scaling to all weights
        self.weights = {k: v * scale for k, v in self.weights.items()}
```

### Balancing Stability and Plasticity

**The Stability-Plasticity Dilemma:** How to learn new information without disrupting old knowledge?

**Solutions from Neuroscience (2025 research):**

1. **Elastic Weight Consolidation (EWC):**
   - Protect weights important for past tasks
   - Allow less important weights to change freely
   - Implemented above in `elastic_weight_consolidation()`

2. **Progressive Neural Networks:**
   ```python
   class ProgressiveScheduler:
       """Add new capacity for new patterns instead of overwriting."""

       def __init__(self):
           self.networks = []  # List of specialist networks

       def learn_new_pattern(self, pattern_type: str):
           # Create new network for new pattern
           new_network = HebbianPreferenceNetwork()
           # Connect to previous networks (lateral connections)
           for old_network in self.networks:
               new_network.add_lateral_connections(old_network)
           self.networks.append(new_network)
   ```

3. **Synaptic Intelligence:**
   ```python
   def compute_parameter_importance(self, weight_history: list[float]) -> float:
       """
       Compute how important a weight is based on its gradient trajectory.

       Weights that changed a lot during learning are important.
       """
       if len(weight_history) < 2:
           return 0.0

       # Sum of squared gradient magnitudes
       importance = sum(
           (weight_history[i+1] - weight_history[i])**2
           for i in range(len(weight_history)-1)
       )
       return importance
   ```

4. **Memory-Augmented Transformers:**
   - Store exemplar schedules in external memory
   - Retrieve similar past solutions when solving new problems
   - Blend old solutions with new constraints

---

## 4. Sparse Coding

### Core Neuroscience Principle

**The brain represents information using sparse, efficient codes** where only a small fraction of neurons are active at any time.

**Biological Examples:**
- **Visual cortex:** Only ~5% of neurons active for any image
- **Hippocampus:** Place cells - sparse activation for specific locations
- **Olfactory system:** Sparse combinatorial codes for odors

**Key Advantages:**
- **Energy efficiency:** Fewer active neurons = less metabolic cost
- **Noise robustness:** Distributed sparse codes resist corruption
- **Interference reduction:** Sparse patterns don't overlap much
- **Generalization:** Learned sparse features transfer to new inputs

**Mathematical Formulation:**
```
minimize: ||x - D*a||^2 + λ||a||_1

Where:
- x = input (schedule requirements)
- D = dictionary (basis schedules)
- a = sparse coefficients (active assignment patterns)
- λ = sparsity penalty
```

### Application to Scheduling

**Schedule Representation:**
Instead of representing a schedule as a dense assignment of all faculty to all slots, use sparse representation where only critical assignments are explicitly specified, and the rest are defaults.

**Constraint Compression:**
Represent complex ACGME constraints as sparse linear combinations of simple basis constraints.

**Pattern Detection:**
Discover sparse recurring scheduling patterns (templates) that can be reused.

### Implementation Ideas

#### Architecture: Sparse Schedule Encoder

```python
class SparseScheduleEncoder:
    """
    Represent schedules using sparse coding.

    Discovers a small set of "basis schedules" (dictionary)
    that can be linearly combined to represent any schedule.
    """

    def __init__(self, n_basis_schedules: int = 20, sparsity: float = 0.1):
        self.n_basis = n_basis_schedules
        self.sparsity = sparsity
        self.dictionary = {}  # basis_id -> BaseSch schedule pattern
        self.learned = False

    def learn_dictionary(
        self,
        historical_schedules: list[dict],
        max_iterations: int = 100
    ):
        """
        Learn sparse dictionary from historical schedules.

        Uses K-SVD algorithm (sparse coding variant of PCA).

        Args:
            historical_schedules: List of past schedule assignments
            max_iterations: Number of learning iterations
        """
        from sklearn.decomposition import DictionaryLearning

        # Convert schedules to matrix (rows = schedules, cols = (faculty, slot) pairs)
        schedule_matrix = self._schedules_to_matrix(historical_schedules)

        # Learn sparse dictionary
        dict_learner = DictionaryLearning(
            n_components=self.n_basis,
            alpha=self.sparsity,
            max_iter=max_iterations,
            fit_algorithm='lars',
            transform_algorithm='lasso_lars'
        )

        # Fit to historical data
        dict_learner.fit(schedule_matrix)

        # Store learned dictionary
        self.dictionary = dict_learner.components_
        self.learned = True

        logger.info(f"Learned {self.n_basis} basis schedules")

    def encode_schedule(
        self,
        schedule: dict,
        return_reconstruction: bool = False
    ) -> tuple[np.ndarray, float]:
        """
        Encode schedule as sparse coefficients over learned dictionary.

        Args:
            schedule: Current schedule assignments
            return_reconstruction: Whether to return reconstructed schedule

        Returns:
            (sparse_coefficients, reconstruction_error)
        """
        if not self.learned:
            raise ValueError("Dictionary not learned yet")

        # Convert to vector
        schedule_vector = self._schedule_to_vector(schedule)

        # Sparse coding: find sparse α such that schedule ≈ D*α
        from sklearn.linear_model import Lasso

        lasso = Lasso(alpha=self.sparsity, max_iter=1000)
        # Fit to reconstruct schedule_vector using dictionary
        # (This is a bit unconventional sklearn usage, but illustrates the concept)

        # In practice, you'd use:
        coefficients = lasso.fit(self.dictionary.T, schedule_vector).coef_

        # Compute reconstruction
        reconstruction = self.dictionary.T @ coefficients
        error = np.linalg.norm(schedule_vector - reconstruction)

        # Count active (non-zero) coefficients
        active_count = np.count_nonzero(coefficients)
        sparsity_achieved = active_count / len(coefficients)

        logger.debug(
            f"Encoded schedule with {active_count}/{len(coefficients)} "
            f"active basis patterns (sparsity: {sparsity_achieved:.1%})"
        )

        if return_reconstruction:
            return coefficients, error, reconstruction

        return coefficients, error

    def decode_schedule(self, coefficients: np.ndarray) -> dict:
        """
        Decode sparse coefficients back to full schedule.

        Args:
            coefficients: Sparse coefficients over basis schedules

        Returns:
            Reconstructed schedule assignments
        """
        # Reconstruct: schedule = D * α
        schedule_vector = self.dictionary.T @ coefficients
        return self._vector_to_schedule(schedule_vector)

    def compress_schedule(
        self,
        schedule: dict,
        compression_ratio: float = 0.9
    ) -> tuple[dict, float]:
        """
        Compress schedule by keeping only most important assignments.

        Uses sparse coding to identify which assignments are "typical"
        (well-represented by basis) vs. "exceptional" (require explicit storage).

        Args:
            schedule: Full schedule
            compression_ratio: Fraction to compress (0.9 = 90% compression)

        Returns:
            (compressed_schedule, information_preserved)
        """
        # Encode schedule
        coefficients, error = self.encode_schedule(schedule)

        # Reconstruct using only top-k coefficients
        k = int(len(coefficients) * (1 - compression_ratio))

        # Zero out all but top-k largest (absolute value) coefficients
        top_k_indices = np.argsort(np.abs(coefficients))[-k:]
        compressed_coeffs = np.zeros_like(coefficients)
        compressed_coeffs[top_k_indices] = coefficients[top_k_indices]

        # Decode compressed schedule
        compressed_schedule = self.decode_schedule(compressed_coeffs)

        # Measure information preserved
        original_vector = self._schedule_to_vector(schedule)
        compressed_vector = self._schedule_to_vector(compressed_schedule)

        similarity = np.dot(original_vector, compressed_vector)
        similarity /= (np.linalg.norm(original_vector) * np.linalg.norm(compressed_vector))

        logger.info(
            f"Compressed schedule to {k}/{len(coefficients)} coefficients "
            f"(preserved {similarity:.1%} of information)"
        )

        return compressed_schedule, similarity
```

#### Advanced: Compressed Sensing for Partial Schedule Recovery

```python
class CompressedSensingScheduler:
    """
    Use compressed sensing to recover full schedule from partial information.

    Application: When some assignments are unknown (e.g., faculty on leave),
    use sparse structure to infer likely assignments.
    """

    def recover_missing_assignments(
        self,
        partial_schedule: dict,  # Known assignments
        missing_slots: list[tuple[UUID, UUID]],  # (faculty, slot) pairs unknown
        sparsity: int = 10  # Expected number of non-default assignments
    ) -> dict:
        """
        Compressed sensing recovery: solve for missing assignments.

        Based on theory: if schedule is sparse, can recover from partial observations.

        Uses L1-minimization (Basis Pursuit):
            minimize ||α||_1 subject to D*α = observed_schedule

        Args:
            partial_schedule: Known (faculty, slot) assignments
            missing_slots: Which assignments are unknown
            sparsity: Expected number of exceptional assignments

        Returns:
            Completed schedule (original + inferred)
        """
        from scipy.optimize import linprog

        # This is a simplified illustration - full implementation would use
        # specialized compressed sensing libraries like CVX or Pyomo

        # Create measurement matrix for observed assignments
        observed_vector = self._schedule_to_vector(partial_schedule)

        # Use L1-minimization to find sparsest schedule consistent with observations
        # In practice, use LASSO or Orthogonal Matching Pursuit (OMP)

        from sklearn.linear_model import OrthogonalMatchingPursuit

        omp = OrthogonalMatchingPursuit(n_nonzero_coefs=sparsity)
        omp.fit(self.dictionary.T, observed_vector)

        # Reconstruct full schedule
        inferred_coefficients = omp.coef_
        full_schedule_vector = self.dictionary.T @ inferred_coefficients

        full_schedule = self._vector_to_schedule(full_schedule_vector)

        return full_schedule
```

### Balancing Stability and Plasticity

**Challenge:** Too much sparsity can lose important information. Too little sparsity defeats the purpose of compression.

**Solutions:**

1. **Adaptive Sparsity:**
   ```python
   def adaptive_sparsity_level(self, schedule_complexity: float) -> float:
       """
       Adjust sparsity based on schedule complexity.

       Simple schedules: high sparsity (few active basis patterns)
       Complex schedules: low sparsity (many active patterns)
       """
       if schedule_complexity < 0.3:
           return 0.05  # 5% of basis patterns active
       elif schedule_complexity < 0.7:
           return 0.15
       else:
           return 0.30  # Complex schedule, more patterns needed
   ```

2. **Hierarchical Sparse Coding:**
   ```python
   class HierarchicalSparseScheduler:
       """
       Multiple levels of sparsity:
       - Level 1: Coarse patterns (month-level templates)
       - Level 2: Medium patterns (week-level variations)
       - Level 3: Fine patterns (day-level exceptions)
       """
       def __init__(self):
           self.coarse_dictionary = {}  # Monthly patterns
           self.medium_dictionary = {}  # Weekly patterns
           self.fine_dictionary = {}    # Daily exceptions
   ```

3. **Sparse + Dense Hybrid:**
   ```python
   def hybrid_representation(self, schedule):
       """
       Sparse code for exceptional assignments.
       Dense code for routine baseline assignments.

       Total representation = baseline + sparse_corrections
       """
       baseline = self.get_default_schedule_template()

       # Find differences from baseline
       exceptions = []
       for faculty, slot in schedule:
           if schedule[(faculty, slot)] != baseline.get((faculty, slot)):
               exceptions.append((faculty, slot, schedule[(faculty, slot)]))

       # Store as: (baseline_template_id, sparse_exception_list)
       return {
           'template': baseline.template_id,
           'exceptions': exceptions  # Sparse list of deviations
       }
   ```

---

## 5. Attractor Networks

### Core Neuroscience Principle

**Recurrent neural networks with stable states (attractors) that the network converges to** from any nearby starting point.

**Key Concepts:**
- **Energy landscape:** Network has potential energy function that decreases over time
- **Attractor basins:** Regions of state space that converge to same stable state
- **Content-addressable memory:** Partial cue retrieves full stored pattern
- **Pattern completion:** Noisy/incomplete input converges to clean stored memory

**Hopfield Network:**
Classic model where:
- Stable states are stored patterns (e.g., successful schedules)
- Network energy: `E = -½ ΣΣ w_ij * s_i * s_j`
- Updates reduce energy until reaching local minimum (attractor)

**Modern Extensions (2025):**
- **Dense Associative Memories:** Exponential storage capacity
- **Continuous attractors:** Stable manifolds instead of discrete points
- **Hierarchical attractors:** Multi-level stability (coarse + fine patterns)

### Application to Scheduling

**Schedule Templates as Attractors:**
Successful historical schedules become stable attractors. New scheduling problems converge to nearest successful template.

**Partial Schedule Completion:**
Given partial constraints (e.g., "Dr. Smith wants Monday AM clinic"), network fills in rest of schedule by converging to compatible attractor.

**Resilience to Perturbations:**
Small changes (one faculty on leave) don't completely disrupt schedule - network finds nearby stable configuration.

### Implementation Ideas

#### Architecture: Hopfield Scheduler Network

```python
class HopfieldSchedulerNetwork:
    """
    Attractor network for schedule generation and retrieval.

    Stores successful historical schedules as stable attractors.
    Given partial schedule, converges to nearest complete schedule.
    """

    def __init__(self, n_faculty: int, n_slots: int):
        self.n_faculty = n_faculty
        self.n_slots = n_slots
        self.n_neurons = n_faculty * n_slots

        # Weight matrix (symmetric)
        self.weights = np.zeros((self.n_neurons, self.n_neurons))

        # Stored patterns (successful schedules)
        self.stored_patterns = []

    def store_pattern(self, schedule: np.ndarray):
        """
        Store a successful schedule as an attractor.

        Uses Hebbian learning: w_ij = Σ (pattern_i * pattern_j)

        Args:
            schedule: Binary matrix (n_faculty × n_slots)
                     1 = faculty assigned to slot, 0 = not assigned
        """
        # Flatten to vector
        pattern = schedule.flatten()
        pattern = 2*pattern - 1  # Convert 0/1 to -1/+1

        # Outer product: Hebbian storage rule
        self.weights += np.outer(pattern, pattern)

        # Zero diagonal (no self-connections)
        np.fill_diagonal(self.weights, 0)

        self.stored_patterns.append(schedule)

        logger.info(f"Stored pattern {len(self.stored_patterns)}")

    def compute_energy(self, state: np.ndarray) -> float:
        """
        Compute Hopfield energy of current state.

        E = -½ Σ_ij w_ij * s_i * s_j

        Lower energy = more stable
        """
        state_vec = state.flatten()
        state_vec = 2*state_vec - 1  # Convert to -1/+1

        energy = -0.5 * state_vec @ self.weights @ state_vec
        return energy

    def update_async(self, state: np.ndarray, max_iterations: int = 1000) -> np.ndarray:
        """
        Asynchronously update neurons until convergence (energy minimum).

        Update rule: s_i = sign(Σ_j w_ij * s_j)

        Args:
            state: Initial (partial) schedule
            max_iterations: Max update steps

        Returns:
            Converged schedule (nearest attractor)
        """
        current = state.flatten()
        current = 2*current - 1  # Convert to -1/+1

        for iteration in range(max_iterations):
            # Pick random neuron to update
            i = np.random.randint(0, self.n_neurons)

            # Compute weighted input
            input_i = self.weights[i] @ current

            # Update neuron
            old_value = current[i]
            current[i] = 1 if input_i > 0 else -1

            # Check for convergence (no neuron changes)
            if iteration % 100 == 0:
                # Test full sweep
                converged = True
                for j in range(self.n_neurons):
                    input_j = self.weights[j] @ current
                    new_val = 1 if input_j > 0 else -1
                    if new_val != current[j]:
                        converged = False
                        break

                if converged:
                    logger.debug(f"Converged after {iteration} iterations")
                    break

        # Convert back to 0/1
        result = (current + 1) / 2
        return result.reshape(self.n_faculty, self.n_slots)

    def retrieve_schedule(
        self,
        partial_schedule: dict,
        constraints: dict = None
    ) -> np.ndarray:
        """
        Given partial schedule, retrieve complete schedule.

        Args:
            partial_schedule: Known (faculty, slot) assignments
            constraints: Hard constraints (must be satisfied)

        Returns:
            Complete schedule (converged attractor)
        """
        # Initialize state with partial information
        state = np.random.rand(self.n_faculty, self.n_slots)  # Random initialization

        # Clamp known assignments
        for (faculty_idx, slot_idx), value in partial_schedule.items():
            state[faculty_idx, slot_idx] = value

        # Run network dynamics to convergence
        converged_state = self.update_async(state)

        # Apply constraints
        if constraints:
            converged_state = self._apply_constraints(converged_state, constraints)

        return converged_state

    def get_attractor_landscape(self) -> dict:
        """
        Analyze energy landscape: find all attractors and their basins.

        Returns:
            Dict with attractor analysis
        """
        attractors = []

        # Test multiple random initializations
        for _ in range(100):
            random_init = np.random.rand(self.n_faculty, self.n_slots)
            converged = self.update_async(random_init)

            # Check if this is a new attractor
            is_new = True
            for existing_attractor in attractors:
                if np.allclose(converged, existing_attractor['pattern']):
                    # Same attractor, increment basin count
                    existing_attractor['basin_size'] += 1
                    is_new = False
                    break

            if is_new:
                attractors.append({
                    'pattern': converged,
                    'energy': self.compute_energy(converged),
                    'basin_size': 1
                })

        # Sort by basin size (larger basin = more stable/common)
        attractors.sort(key=lambda x: -x['basin_size'])

        return {
            'n_attractors': len(attractors),
            'attractors': attractors,
            'most_stable': attractors[0] if attractors else None
        }
```

#### Advanced: Modern Hopfield Networks (Dense Associative Memory)

```python
class ModernHopfieldScheduler:
    """
    Modern Hopfield Network with exponential storage capacity.

    Based on 2025 research: uses softmax/attention mechanism
    for retrieval instead of classic sign activation.

    Storage capacity: Exponential in number of neurons (vs. linear for classic Hopfield)
    """

    def __init__(self, feature_dim: int = 128):
        self.feature_dim = feature_dim
        self.stored_patterns = []  # List of stored schedule embeddings

    def store_pattern(self, schedule_embedding: np.ndarray):
        """
        Store schedule as high-dimensional embedding.

        Args:
            schedule_embedding: Vector representation of schedule (dim=feature_dim)
        """
        self.stored_patterns.append(schedule_embedding)

    def retrieve_pattern(
        self,
        query: np.ndarray,
        beta: float = 1.0
    ) -> np.ndarray:
        """
        Retrieve stored pattern using modern Hopfield update.

        Update rule: output = Σ_i softmax(β * query · pattern_i) * pattern_i

        This is equivalent to self-attention in Transformers!

        Args:
            query: Query embedding (partial schedule)
            beta: Inverse temperature (higher = sharper retrieval)

        Returns:
            Retrieved pattern (nearest stored schedule)
        """
        if not self.stored_patterns:
            return query

        # Compute similarities (attention scores)
        patterns_matrix = np.stack(self.stored_patterns)
        similarities = patterns_matrix @ query  # Shape: (n_patterns,)

        # Softmax to get retrieval probabilities
        exp_similarities = np.exp(beta * similarities)
        probabilities = exp_similarities / exp_similarities.sum()

        # Weighted combination of stored patterns
        retrieved = (patterns_matrix.T @ probabilities).T

        return retrieved

    def iterative_retrieval(
        self,
        initial_query: np.ndarray,
        n_iterations: int = 5
    ) -> np.ndarray:
        """
        Iteratively refine retrieval (converge to attractor).

        query_t+1 = retrieve_pattern(query_t)

        Args:
            initial_query: Initial partial schedule embedding
            n_iterations: Number of refinement iterations

        Returns:
            Converged pattern
        """
        query = initial_query

        for i in range(n_iterations):
            query = self.retrieve_pattern(query)

            # Early stopping if converged
            if i > 0:
                delta = np.linalg.norm(query - prev_query)
                if delta < 1e-5:
                    logger.debug(f"Converged after {i+1} iterations")
                    break

            prev_query = query.copy()

        return query
```

### Balancing Stability and Plasticity

**Challenge:** Attractors provide stability but can be too rigid. How to allow adaptation while maintaining useful attractor structure?

**Solutions:**

1. **Attractor Plasticity:**
   ```python
   def update_attractor(self, attractor_id: int, feedback: dict):
       """
       Slightly modify stored attractor based on feedback.

       Allows attractors to evolve over time while maintaining core structure.
       """
       old_pattern = self.stored_patterns[attractor_id]

       # Compute gradient based on feedback
       satisfaction_score = feedback['average_satisfaction']

       if satisfaction_score < 0.5:
           # Bad outcome: move attractor away from this solution
           adjustment = -0.1 * old_pattern
       else:
           # Good outcome: reinforce this attractor
           adjustment = 0.1 * old_pattern

       # Update with momentum
       new_pattern = 0.9 * old_pattern + 0.1 * adjustment
       self.stored_patterns[attractor_id] = new_pattern
   ```

2. **Metastable Attractors:**
   ```python
   def add_noise_for_exploration(self, state: np.ndarray, temperature: float = 0.1):
       """
       Add thermal noise to escape weak attractors.

       Simulated annealing: high temp early (explore), low temp late (exploit).
       """
       noise = np.random.randn(*state.shape) * temperature
       return state + noise
   ```

3. **Hierarchical Attractors:**
   ```python
   class HierarchicalAttractorNetwork:
       """
       Multiple timescales of stability:
       - Fast dynamics: day-to-day adjustments (shallow attractors)
       - Slow dynamics: weekly patterns (medium attractors)
       - Stable structure: monthly templates (deep attractors)
       """
       def __init__(self):
           self.fast_network = HopfieldSchedulerNetwork()   # Shallow energy landscape
           self.medium_network = HopfieldSchedulerNetwork() # Medium depth
           self.slow_network = HopfieldSchedulerNetwork()   # Deep attractors
   ```

---

## 6. Predictive Coding

### Core Neuroscience Principle

**The brain is a prediction machine that constantly generates predictions and minimizes prediction errors.**

**Key Framework:**
1. **Top-down predictions:** Higher brain areas predict lower-level sensory input
2. **Bottom-up errors:** Actual input compared to prediction → prediction error
3. **Learning:** Update internal model to minimize future prediction errors
4. **Active inference:** Take actions to make predictions come true (instead of just updating beliefs)

**Hierarchical Processing:**
```
Level 3: Abstract patterns (monthly schedule templates)
   ↓ prediction
Level 2: Weekly patterns (clinic rotations)
   ↓ prediction
Level 1: Daily assignments (specific faculty-slot pairs)
   ↓ prediction
Sensory input: Actual schedule outcomes, faculty feedback
```

**Free Energy Principle:**
Minimize variational free energy F = prediction error + complexity

### Application to Scheduling

**Schedule Prediction:**
System predicts how successful a proposed schedule will be. Actual outcome compared to prediction → learning signal.

**Preference Prediction:**
Predict faculty satisfaction with assignment. Prediction error drives preference learning.

**Active Scheduling:**
Generate schedules that minimize *expected* prediction error (choose assignments we're confident about).

### Implementation Ideas

#### Architecture: Predictive Coding Scheduler

```python
class PredictiveCodingScheduler:
    """
    Hierarchical predictive coding for schedule generation.

    Each level predicts the level below and updates based on prediction errors.
    """

    def __init__(self):
        # Hierarchical representations
        self.level_3 = {}  # Abstract: monthly templates
        self.level_2 = {}  # Medium: weekly rotations
        self.level_1 = {}  # Concrete: daily assignments

        # Precision (inverse variance) for each level
        self.precision_3 = 1.0
        self.precision_2 = 2.0
        self.precision_1 = 5.0  # Most precise at bottom

    def predict_downward(
        self,
        level: int,
        representation: dict
    ) -> dict:
        """
        Generate prediction for level below.

        Args:
            level: Current level (3, 2, or 1)
            representation: Current level's representation

        Returns:
            Predicted representation for level below
        """
        if level == 3:
            # Predict weekly patterns from monthly template
            monthly_template = representation
            predicted_weekly = self._template_to_weekly(monthly_template)
            return predicted_weekly

        elif level == 2:
            # Predict daily assignments from weekly patterns
            weekly_patterns = representation
            predicted_daily = self._weekly_to_daily(weekly_patterns)
            return predicted_daily

        else:
            # Level 1: no level below
            return representation

    def compute_prediction_error(
        self,
        predicted: dict,
        actual: dict,
        precision: float
    ) -> tuple[dict, float]:
        """
        Compute prediction error: ε = actual - predicted

        Weighted by precision (confidence in prediction).

        Args:
            predicted: What we expected
            actual: What actually happened
            precision: How confident we are (inverse variance)

        Returns:
            (prediction_error_dict, total_error)
        """
        error = {}
        total = 0.0

        for key in set(predicted.keys()) | set(actual.keys()):
            pred_val = predicted.get(key, 0)
            actual_val = actual.get(key, 0)

            raw_error = actual_val - pred_val
            weighted_error = precision * raw_error

            error[key] = weighted_error
            total += weighted_error ** 2

        return error, total

    def update_representation(
        self,
        level: int,
        current_rep: dict,
        prediction_error: dict,
        learning_rate: float = 0.01
    ) -> dict:
        """
        Update representation to reduce prediction error.

        Gradient descent on free energy:
        rep_new = rep_old - lr * ∂F/∂rep

        Args:
            level: Which level to update
            current_rep: Current representation
            prediction_error: Error from level below
            learning_rate: Update step size

        Returns:
            Updated representation
        """
        updated = {}

        for key, value in current_rep.items():
            error = prediction_error.get(key, 0)

            # Update in direction that reduces error
            updated[key] = value + learning_rate * error

        return updated

    def hierarchical_inference(
        self,
        sensory_input: dict,
        n_iterations: int = 10
    ) -> dict:
        """
        Infer hierarchical schedule representations from bottom-up input.

        Implements predictive coding message passing:
        - Bottom-up: prediction errors
        - Top-down: predictions
        - Iterate until convergence

        Args:
            sensory_input: Actual assignments and feedback (level 1)
            n_iterations: Number of inference iterations

        Returns:
            Inferred representations at all levels
        """
        # Initialize representations
        rep_1 = sensory_input.copy()
        rep_2 = self._aggregate_to_weekly(rep_1)
        rep_3 = self._aggregate_to_monthly(rep_2)

        for iteration in range(n_iterations):
            # Level 3 → 2: predict weekly from monthly
            pred_2 = self.predict_downward(3, rep_3)
            error_2, _ = self.compute_prediction_error(pred_2, rep_2, self.precision_2)

            # Update level 3 based on error from level 2
            rep_3 = self.update_representation(3, rep_3, error_2)

            # Level 2 → 1: predict daily from weekly
            pred_1 = self.predict_downward(2, rep_2)
            error_1, _ = self.compute_prediction_error(pred_1, rep_1, self.precision_1)

            # Update level 2 based on error from level 1
            rep_2 = self.update_representation(2, rep_2, error_1)

            # Level 1: update based on sensory input
            error_sensory, total_error = self.compute_prediction_error(
                pred_1, sensory_input, self.precision_1
            )
            rep_1 = self.update_representation(1, rep_1, error_sensory)

            # Check convergence
            if total_error < 0.01:
                logger.debug(f"Converged after {iteration+1} iterations")
                break

        return {
            'level_1': rep_1,
            'level_2': rep_2,
            'level_3': rep_3
        }

    def active_inference_scheduling(
        self,
        preferences: dict,
        constraints: dict
    ) -> dict:
        """
        Active inference: generate schedule that minimizes EXPECTED free energy.

        Instead of just predicting, choose actions (assignments) that:
        1. Are expected to have low prediction error (confidence)
        2. Resolve uncertainty (information gain)
        3. Achieve goals (high utility)

        Args:
            preferences: Faculty preferences
            constraints: ACGME constraints

        Returns:
            Generated schedule
        """
        # Explore multiple candidate schedules
        candidates = self._generate_candidate_schedules(preferences, constraints)

        best_schedule = None
        min_expected_free_energy = float('inf')

        for candidate in candidates:
            # Compute expected free energy for this schedule
            expected_error = self._predict_satisfaction_error(candidate, preferences)
            complexity = self._compute_schedule_complexity(candidate)

            # Free energy = prediction error + complexity
            # (We penalize complex/unusual schedules)
            expected_free_energy = expected_error + 0.1 * complexity

            if expected_free_energy < min_expected_free_energy:
                min_expected_free_energy = expected_free_energy
                best_schedule = candidate

        logger.info(
            f"Selected schedule with expected free energy: "
            f"{min_expected_free_energy:.3f}"
        )

        return best_schedule
```

#### Advanced: Precision-Weighted Learning

```python
class PrecisionWeightedScheduler:
    """
    Weight learning by precision (confidence).

    High-confidence predictions have more influence.
    Low-confidence predictions are ignored or explored.
    """

    def __init__(self):
        self.predictions = {}  # (faculty, slot) -> predicted satisfaction
        self.precisions = {}   # (faculty, slot) -> confidence

    def update_with_precision_weighting(
        self,
        faculty_id: UUID,
        slot_id: UUID,
        actual_satisfaction: float,
        learning_rate: float = 0.1
    ):
        """
        Update prediction weighted by precision.

        High precision (confident) → small updates
        Low precision (uncertain) → large updates
        """
        key = (faculty_id, slot_id)

        # Get current values
        predicted = self.predictions.get(key, 0.5)
        precision = self.precisions.get(key, 1.0)

        # Prediction error
        error = actual_satisfaction - predicted

        # Precision-weighted update
        # High precision → resist change (we were confident)
        # Low precision → change more (we were uncertain)
        effective_lr = learning_rate / precision

        new_prediction = predicted + effective_lr * error

        # Update precision based on error magnitude
        # Consistently correct → increase precision
        # Inconsistent → decrease precision
        if abs(error) < 0.1:
            new_precision = min(10.0, precision * 1.1)
        else:
            new_precision = max(0.1, precision * 0.9)

        self.predictions[key] = new_prediction
        self.precisions[key] = new_precision

    def choose_exploration_vs_exploitation(
        self,
        candidate_assignments: list[tuple[UUID, UUID]]
    ) -> tuple[UUID, UUID]:
        """
        Choose assignment to maximize information gain.

        Exploration: choose low-precision (uncertain) assignments
        Exploitation: choose high-precision (confident) assignments

        This balances trying new things vs. sticking with what works.
        """
        # Compute expected free energy for each candidate
        scores = []

        for faculty_id, slot_id in candidate_assignments:
            key = (faculty_id, slot_id)

            predicted_satisfaction = self.predictions.get(key, 0.5)
            precision = self.precisions.get(key, 1.0)

            # Pragmatic value: expected utility (predicted satisfaction)
            pragmatic = predicted_satisfaction

            # Epistemic value: information gain (inverse of precision)
            epistemic = 1.0 / precision

            # Expected free energy (to minimize):
            # G = -pragmatic_value + epistemic_value
            # (We want high utility AND high information gain)
            expected_free_energy = -pragmatic + 0.3 * epistemic

            scores.append((faculty_id, slot_id, expected_free_energy))

        # Choose assignment with lowest expected free energy
        best = min(scores, key=lambda x: x[2])

        return (best[0], best[1])
```

### Balancing Stability and Plasticity

**Challenge:** How much to trust predictions vs. update based on new data?

**Solutions:**

1. **Adaptive Precision:**
   ```python
   # Increase precision (trust predictions more) when consistent
   # Decrease precision (explore more) when volatile

   if recent_errors_small:
       precision *= 1.05  # Trust predictions more
   elif recent_errors_large:
       precision *= 0.95  # Be more skeptical
   ```

2. **Hierarchical Time Scales:**
   ```python
   # Higher levels update slowly (stable)
   # Lower levels update quickly (plastic)

   learning_rate_level_3 = 0.001  # Slow: monthly templates
   learning_rate_level_2 = 0.01   # Medium: weekly patterns
   learning_rate_level_1 = 0.1    # Fast: daily details
   ```

3. **Meta-Learning Precision:**
   ```python
   def learn_optimal_precision(self, historical_errors: list[float]):
       """
       Learn how confident we should be based on past performance.

       If we're consistently over-confident (large errors despite high precision),
       reduce global precision scaling.
       """
       # Compute calibration: are prediction errors proportional to precision?
       for error, precision in zip(historical_errors, self.historical_precisions):
           expected_error = 1.0 / sqrt(precision)
           calibration_error = abs(error - expected_error)
           # Update precision prior
   ```

---

## 7. Neuromodulation

### Core Neuroscience Principle

**Global biochemical signals (neuromodulators) adjust neural processing across the brain** based on behavioral context.

**Major Neuromodulators:**

1. **Dopamine:**
   - Signals reward prediction error: actual_reward - expected_reward
   - Positive error → strengthen actions that led here
   - Negative error → weaken actions
   - Controls learning rate dynamically

2. **Serotonin:**
   - Regulates time horizon of predictions
   - High serotonin → patient, long-term planning
   - Low serotonin → impulsive, short-term focus
   - Modulates punishment sensitivity

3. **Noradrenaline (Norepinephrine):**
   - Signals unexpected uncertainty
   - Controls exploration vs. exploitation
   - High → reset beliefs, explore
   - Low → exploit current model

4. **Acetylcholine:**
   - Signals expected uncertainty
   - Controls learning rate based on known volatility
   - High → learn faster in known-volatile environments

**Computational Theory (2025):**
Neuromodulators implement meta-parameters that adjust how the brain learns and decides:
- **Dopamine:** Learning rate modulation
- **Serotonin:** Temporal discount factor
- **Noradrenaline:** Exploration temperature
- **Acetylcholine:** Attention / memory update rate

### Application to Scheduling

**Dynamic Learning Rate:**
Modulate how quickly system adapts to new preferences based on context (crisis vs. normal operation).

**Exploration vs. Exploitation:**
During normal operations, exploit known preferences (low exploration). During disruptions, explore new arrangements (high exploration).

**Time Horizon Adjustment:**
In stable periods, optimize long-term (semester-level) patterns. In volatile periods, focus on short-term (week-level) stability.

### Implementation Ideas

#### Architecture: Neuromodulated Scheduler

```python
class NeuromodulatedScheduler:
    """
    Scheduling system with neuromodulator-inspired meta-parameter control.

    Global context signals adjust learning, exploration, and planning horizons.
    """

    def __init__(self):
        # Core preference network
        self.preference_network = HebbianPreferenceNetwork()

        # Neuromodulator levels (0-1 scale)
        self.dopamine = 0.5      # Reward prediction error / learning rate
        self.serotonin = 0.5     # Time horizon / patience
        self.noradrenaline = 0.5  # Exploration / uncertainty response
        self.acetylcholine = 0.5  # Attention / known volatility

        # History for computing modulator levels
        self.reward_history = []
        self.uncertainty_history = []

    def compute_dopamine_signal(
        self,
        actual_satisfaction: float,
        predicted_satisfaction: float
    ) -> float:
        """
        Dopamine = Reward Prediction Error (RPE)

        RPE = actual_reward - predicted_reward

        Positive: Better than expected → strengthen
        Negative: Worse than expected → weaken

        Args:
            actual_satisfaction: Actual outcome (0-1)
            predicted_satisfaction: What we predicted (0-1)

        Returns:
            Dopamine level (0-1)
        """
        rpe = actual_satisfaction - predicted_satisfaction

        # Map RPE to dopamine level
        # RPE = +1 → dopamine = 1.0 (maximal)
        # RPE = 0  → dopamine = 0.5 (baseline)
        # RPE = -1 → dopamine = 0.0 (minimal)

        dopamine = 0.5 + 0.5 * rpe
        dopamine = max(0.0, min(1.0, dopamine))

        return dopamine

    def compute_serotonin_signal(
        self,
        recent_punishment_rate: float,
        schedule_volatility: float
    ) -> float:
        """
        Serotonin regulates time horizon and punishment sensitivity.

        High punishment/volatility → low serotonin → short-term focus
        Low punishment/volatility → high serotonin → long-term planning

        Args:
            recent_punishment_rate: Fraction of recent bad outcomes
            schedule_volatility: How much schedule changes

        Returns:
            Serotonin level (0-1)
        """
        # Inverse relationship: punishment reduces serotonin
        serotonin = 1.0 - 0.5 * recent_punishment_rate - 0.3 * schedule_volatility
        return max(0.0, min(1.0, serotonin))

    def compute_noradrenaline_signal(
        self,
        unexpected_uncertainty: float,
        context_change: bool = False
    ) -> float:
        """
        Noradrenaline signals unexpected uncertainty.

        High when: surprising events, context shifts, novel situations
        Low when: stable, predictable environment

        Modulates exploration: high NE → explore, low NE → exploit

        Args:
            unexpected_uncertainty: Surprise magnitude
            context_change: Whether major context shift occurred

        Returns:
            Noradrenaline level (0-1)
        """
        noradrenaline = unexpected_uncertainty

        # Context change (e.g., new semester, staff turnover) → spike NE
        if context_change:
            noradrenaline = min(1.0, noradrenaline + 0.5)

        return noradrenaline

    def compute_acetylcholine_signal(
        self,
        expected_volatility: float,
        attention_required: float
    ) -> float:
        """
        Acetylcholine signals expected uncertainty and attention needs.

        High when: known-volatile environment, attention needed
        Low when: stable, routine environment

        Modulates learning rate for expected volatility.

        Args:
            expected_volatility: Known schedule volatility
            attention_required: How much focus needed

        Returns:
            Acetylcholine level (0-1)
        """
        acetylcholine = 0.5 * expected_volatility + 0.5 * attention_required
        return acetylcholine

    def modulated_learning_rate(self) -> float:
        """
        Compute effective learning rate based on neuromodulators.

        Dopamine: Scales learning by prediction error
        Acetylcholine: Scales learning by expected volatility

        Returns:
            Effective learning rate (0-1)
        """
        base_lr = 0.1

        # Dopamine modulation: learn more when surprised
        dopamine_factor = 0.5 + self.dopamine

        # Acetylcholine modulation: learn more in volatile environments
        ach_factor = 0.5 + self.acetylcholine

        effective_lr = base_lr * dopamine_factor * ach_factor

        return min(0.5, effective_lr)

    def modulated_exploration_temperature(self) -> float:
        """
        Compute exploration temperature based on neuromodulators.

        Noradrenaline: Higher → more exploration
        Serotonin: Higher → more patience, less impulsive exploration

        Returns:
            Temperature for softmax exploration (>0)
        """
        # Noradrenaline increases exploration
        ne_contribution = 2.0 * self.noradrenaline

        # Serotonin decreases impulsive exploration
        serotonin_damping = 0.5 / (0.1 + self.serotonin)

        temperature = ne_contribution * serotonin_damping

        return max(0.1, temperature)

    def modulated_time_horizon(self) -> int:
        """
        Compute planning time horizon based on serotonin.

        High serotonin → long-term planning (months)
        Low serotonin → short-term focus (weeks)

        Returns:
            Planning horizon in days
        """
        # Serotonin maps to time horizon
        # 1.0 → 90 days (semester-level)
        # 0.5 → 30 days (month-level)
        # 0.0 → 7 days (week-level)

        min_horizon = 7
        max_horizon = 90

        horizon = min_horizon + (max_horizon - min_horizon) * self.serotonin

        return int(horizon)

    def update_neuromodulators(
        self,
        schedule_outcome: dict,
        context: dict
    ):
        """
        Update all neuromodulator levels based on recent experience.

        Args:
            schedule_outcome: Results of recent schedule
            context: Environmental context
        """
        # Compute dopamine from reward prediction error
        actual_sat = schedule_outcome.get('average_satisfaction', 0.5)
        predicted_sat = schedule_outcome.get('predicted_satisfaction', 0.5)
        self.dopamine = self.compute_dopamine_signal(actual_sat, predicted_sat)

        # Compute serotonin from punishment rate and volatility
        punishment_rate = schedule_outcome.get('violation_rate', 0.0)
        volatility = context.get('schedule_volatility', 0.0)
        self.serotonin = self.compute_serotonin_signal(punishment_rate, volatility)

        # Compute noradrenaline from unexpected uncertainty
        surprise = schedule_outcome.get('surprise_magnitude', 0.0)
        context_change = context.get('major_change', False)
        self.noradrenaline = self.compute_noradrenaline_signal(surprise, context_change)

        # Compute acetylcholine from expected volatility
        expected_vol = context.get('expected_volatility', 0.0)
        attention = context.get('attention_required', 0.0)
        self.acetylcholine = self.compute_acetylcholine_signal(expected_vol, attention)

        logger.info(
            f"Neuromodulator levels - DA: {self.dopamine:.2f}, "
            f"5-HT: {self.serotonin:.2f}, NE: {self.noradrenaline:.2f}, "
            f"ACh: {self.acetylcholine:.2f}"
        )

    def learn_with_modulation(
        self,
        faculty_id: UUID,
        slot_id: UUID,
        satisfaction: float
    ):
        """
        Update preferences with neuromodulator-adjusted learning.

        Uses dopamine to scale learning rate and noradrenaline for exploration.
        """
        # Get modulated learning rate
        learning_rate = self.modulated_learning_rate()

        # Update preference network with modulated LR
        self.preference_network.learning_rate = learning_rate
        self.preference_network.strengthen_association(
            faculty_id, slot_id, satisfaction
        )

    def select_assignment_with_modulation(
        self,
        candidate_assignments: list[tuple[UUID, UUID, float]]
    ) -> tuple[UUID, UUID]:
        """
        Select assignment using neuromodulator-adjusted exploration.

        High noradrenaline → more random exploration
        Low noradrenaline → more greedy exploitation

        Args:
            candidate_assignments: List of (faculty, slot, preference_score)

        Returns:
            Selected (faculty_id, slot_id)
        """
        # Get exploration temperature
        temperature = self.modulated_exploration_temperature()

        # Softmax selection with temperature
        scores = np.array([score for _, _, score in candidate_assignments])
        exp_scores = np.exp(scores / temperature)
        probabilities = exp_scores / exp_scores.sum()

        # Sample according to probabilities
        idx = np.random.choice(len(candidate_assignments), p=probabilities)
        faculty_id, slot_id, _ = candidate_assignments[idx]

        return faculty_id, slot_id
```

#### Advanced: Multi-Agent Neuromodulation

```python
class MultiAgentNeuromodulatedScheduler:
    """
    Different 'agents' (services, departments) have different neuromodulator profiles.

    Emergency department: High noradrenaline (volatile, exploratory)
    Outpatient clinic: High serotonin (stable, long-term)
    Research: High dopamine (reward-driven learning)
    """

    def __init__(self):
        self.agents = {}  # service_id -> NeuromodulatedScheduler

    def create_agent(
        self,
        service_id: str,
        baseline_dopamine: float = 0.5,
        baseline_serotonin: float = 0.5,
        baseline_noradrenaline: float = 0.5,
        baseline_acetylcholine: float = 0.5
    ):
        """
        Create scheduling agent with specific neuromodulator profile.

        Args:
            service_id: Service identifier
            baseline_dopamine: Reward sensitivity
            baseline_serotonin: Time horizon / stability
            baseline_noradrenaline: Exploration tendency
            baseline_acetylcholine: Attention / volatility handling
        """
        agent = NeuromodulatedScheduler()
        agent.dopamine = baseline_dopamine
        agent.serotonin = baseline_serotonin
        agent.noradrenaline = baseline_noradrenaline
        agent.acetylcholine = baseline_acetylcholine

        self.agents[service_id] = agent

    def get_agent_for_service(self, service_type: str) -> NeuromodulatedScheduler:
        """Get appropriate agent based on service characteristics."""

        # Emergency services: high volatility, high exploration
        if service_type == 'emergency':
            if 'emergency' not in self.agents:
                self.create_agent(
                    'emergency',
                    baseline_noradrenaline=0.8,  # High exploration
                    baseline_serotonin=0.3,      # Short-term focus
                    baseline_acetylcholine=0.7   # High attention
                )
            return self.agents['emergency']

        # Outpatient clinic: low volatility, long-term planning
        elif service_type == 'outpatient':
            if 'outpatient' not in self.agents:
                self.create_agent(
                    'outpatient',
                    baseline_noradrenaline=0.2,  # Low exploration
                    baseline_serotonin=0.8,      # Long-term focus
                    baseline_acetylcholine=0.3   # Low volatility
                )
            return self.agents['outpatient']

        # Research/elective: reward-driven, flexible
        elif service_type == 'research':
            if 'research' not in self.agents:
                self.create_agent(
                    'research',
                    baseline_dopamine=0.8,       # High reward sensitivity
                    baseline_serotonin=0.6,      # Medium time horizon
                    baseline_noradrenaline=0.5   # Medium exploration
                )
            return self.agents['research']

        # Default agent
        else:
            if 'default' not in self.agents:
                self.create_agent('default')
            return self.agents['default']
```

### Balancing Stability and Plasticity

**Challenge:** Neuromodulation can cause instability if levels swing too rapidly. Need damping and homeostasis.

**Solutions:**

1. **Slow Neuromodulator Dynamics:**
   ```python
   def update_with_smoothing(self, new_level: float, alpha: float = 0.1):
       """
       Exponential moving average of neuromodulator levels.

       Prevents sudden swings from single events.
       """
       self.dopamine = (1 - alpha) * self.dopamine + alpha * new_level
   ```

2. **Homeostatic Regulation:**
   ```python
   def homeostatic_regulation(self):
       """
       Push neuromodulators back toward baseline over time.

       Prevents getting stuck in extreme states.
       """
       baseline = 0.5
       decay_rate = 0.05

       self.dopamine += decay_rate * (baseline - self.dopamine)
       self.serotonin += decay_rate * (baseline - self.serotonin)
       self.noradrenaline += decay_rate * (baseline - self.noradrenaline)
       self.acetylcholine += decay_rate * (baseline - self.acetylcholine)
   ```

3. **Context-Dependent Baselines:**
   ```python
   def get_context_baseline(self, context: str) -> dict:
       """
       Different contexts have different neuromodulator set-points.

       Crisis mode: high NE baseline
       Recovery mode: high 5-HT baseline
       Learning mode: high DA baseline
       """
       baselines = {
           'crisis': {
               'dopamine': 0.3,
               'serotonin': 0.2,
               'noradrenaline': 0.9,
               'acetylcholine': 0.8
           },
           'normal': {
               'dopamine': 0.5,
               'serotonin': 0.6,
               'noradrenaline': 0.3,
               'acetylcholine': 0.4
           },
           'learning': {
               'dopamine': 0.8,
               'serotonin': 0.5,
               'noradrenaline': 0.5,
               'acetylcholine': 0.6
           }
       }

       return baselines.get(context, baselines['normal'])
   ```

---

## 8. Integration Strategy

### How Neural Concepts Complement Existing System

The scheduling system already has:
1. **Transcription Factors** (gene regulation) - Constraint modulation
2. **Stigmergy** (swarm intelligence) - Pheromone-based preferences

Neural computation adds:
1. **Hebbian Learning** - Direct associative preference learning
2. **Lateral Inhibition** - Competitive assignment resolution
3. **Neural Plasticity** - Continual adaptation without forgetting
4. **Sparse Coding** - Efficient schedule representation
5. **Attractor Networks** - Template-based schedule generation
6. **Predictive Coding** - Error-driven learning and active inference
7. **Neuromodulation** - Context-aware meta-parameter tuning

### Unified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SCHEDULING ENGINE                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              NEURAL LEARNING LAYER (NEW)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Hebbian    │  │   Lateral    │  │   Predictive    │   │
│  │  Preference  │→ │  Inhibition  │→ │     Coding      │   │
│  │   Network    │  │   Resolver   │  │   Validator     │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Attractor  │  │    Sparse    │  │ Neuromodulation │   │
│  │   Network    │  │   Encoder    │  │   Controller    │   │
│  │  (Templates) │  │ (Compression)│  │ (Meta-params)   │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          BIOLOGICAL METAPHOR LAYER (EXISTING)                │
│                                                              │
│  ┌──────────────────┐         ┌────────────────────────┐    │
│  │  Transcription   │         │     Stigmergy          │    │
│  │    Factors       │         │  (Pheromone Trails)    │    │
│  │ (Gene Regulation)│         │                        │    │
│  └──────────────────┘         └────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         RESILIENCE FRAMEWORK (EXISTING)                      │
│  - Utilization Monitoring                                   │
│  - N-1/N-2 Contingency                                      │
│  - Hub Analysis                                             │
│  - Defense in Depth                                         │
└─────────────────────────────────────────────────────────────┘
```

### Interaction Patterns

#### Pattern 1: Hebbian Learning + Stigmergy
```python
def integrated_preference_learning(
    faculty_id: UUID,
    slot_id: UUID,
    satisfaction: float
):
    """
    Use both Hebbian and stigmergy for preference learning.

    Hebbian: Direct associative strengthening
    Stigmergy: Pheromone trail reinforcement
    """
    # Hebbian update: strengthen connection
    hebbian_network.strengthen_association(faculty_id, slot_id, satisfaction)

    # Stigmergy update: reinforce trail
    stigmergy.record_signal(
        faculty_id,
        SignalType.HIGH_SATISFACTION if satisfaction > 0.6 else SignalType.LOW_SATISFACTION,
        slot_id=slot_id,
        strength_change=satisfaction * 0.1
    )

    # Combine predictions
    hebbian_score = hebbian_network.get_preference_score(faculty_id, slot_id)
    trail = stigmergy.get_faculty_preferences(faculty_id, min_strength=0.1)
    stigmergy_score = trail[0].strength if trail else 0.5

    # Weighted combination
    combined_score = 0.6 * hebbian_score + 0.4 * stigmergy_score

    return combined_score
```

#### Pattern 2: Attractor Networks + Transcription Factors
```python
def modulated_attractor_scheduling(
    constraints: dict,
    tf_scheduler: TranscriptionFactorScheduler,
    hopfield_net: HopfieldSchedulerNetwork
):
    """
    Use transcription factors to modulate attractor network.

    TF state adjusts which attractors are accessible (chromatin state).
    """
    # Get current TF-modulated constraint weights
    constraint_weights = tf_scheduler.get_constraint_weights()

    # Adjust Hopfield network weights based on TF state
    for constraint_id, (weight, _) in constraint_weights.items():
        # High TF activation → strengthen this attractor basin
        # Low TF activation → weaken this attractor basin
        hopfield_net.modulate_attractor_strength(constraint_id, weight)

    # Run attractor dynamics with modulated landscape
    schedule = hopfield_net.retrieve_schedule(partial_schedule={})

    return schedule
```

#### Pattern 3: Predictive Coding + Resilience
```python
def predictive_resilience_monitoring(
    predictive_scheduler: PredictiveCodingScheduler,
    resilience_service: ResilienceService
):
    """
    Use predictive coding to anticipate resilience failures.

    Prediction errors signal emerging resilience risks.
    """
    # Predict expected utilization
    predicted_util = predictive_scheduler.predict_downward(3, monthly_template)

    # Actual utilization from resilience service
    health_report = resilience_service.check_health(faculty, blocks, assignments)
    actual_util = health_report.utilization.utilization_rate

    # Compute prediction error
    error = actual_util - predicted_util

    # Large positive error → utilization higher than expected → risk
    if error > 0.1:
        logger.warning(
            f"Utilization prediction error: {error:.1%}. "
            f"Actual: {actual_util:.0%}, Predicted: {predicted_util:.0%}. "
            f"Increasing resilience monitoring frequency."
        )
        # Trigger more frequent resilience checks
        resilience_service.config.check_interval_hours = 1.0

    # Update predictions
    predictive_scheduler.update_representation(3, monthly_template, error)
```

#### Pattern 4: Neuromodulation + All Systems
```python
class GlobalNeuromodulatedScheduler:
    """
    Neuromodulation as top-level meta-controller.

    Adjusts all subsystems based on global context.
    """

    def __init__(self):
        self.neuromod = NeuromodulatedScheduler()
        self.hebbian = HebbianPreferenceNetwork()
        self.stigmergy = StigmergicScheduler()
        self.tf_scheduler = TranscriptionFactorScheduler()
        self.predictive = PredictiveCodingScheduler()

    def schedule_with_global_modulation(
        self,
        context: dict,
        outcome_history: list
    ):
        """
        Use neuromodulators to coordinate all subsystems.
        """
        # Update neuromodulator levels based on recent outcomes
        self.neuromod.update_neuromodulators(
            outcome_history[-1] if outcome_history else {},
            context
        )

        # Get modulated meta-parameters
        learning_rate = self.neuromod.modulated_learning_rate()
        exploration_temp = self.neuromod.modulated_exploration_temperature()
        time_horizon = self.neuromod.modulated_time_horizon()

        # Apply to Hebbian learning
        self.hebbian.learning_rate = learning_rate

        # Apply to stigmergy
        self.stigmergy.evaporation_rate = 0.05 + 0.1 * self.neuromod.noradrenaline

        # Apply to transcription factors
        # High dopamine → amplify activator TFs
        # Low dopamine → dampen activators
        for tf in self.tf_scheduler.transcription_factors.values():
            if tf.tf_type == TFType.ACTIVATOR:
                tf.activation_strength *= (0.5 + 0.5 * self.neuromod.dopamine)

        # Apply to predictive coding
        self.predictive.precision_1 *= (0.5 + 0.5 * self.neuromod.acetylcholine)

        # Generate schedule with modulated systems
        # ... scheduling logic using all subsystems ...
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Objectives:**
- Implement core Hebbian learning
- Add lateral inhibition to constraint solver
- Integrate with existing stigmergy system

**Deliverables:**
1. `backend/app/neural/hebbian.py` - `HebbianPreferenceNetwork` class
2. `backend/app/neural/lateral_inhibition.py` - `LateralInhibitionScheduler` class
3. Integration tests with stigmergy
4. Performance benchmarks

**Success Metrics:**
- Hebbian network learns preferences with >80% accuracy
- Lateral inhibition resolves conflicts faster than greedy algorithm
- Combined Hebbian+Stigmergy improves satisfaction by 10%

### Phase 2: Memory and Templates (Weeks 5-8)

**Objectives:**
- Implement attractor networks for template storage
- Add sparse coding for efficient schedule representation
- Build pattern library from historical schedules

**Deliverables:**
1. `backend/app/neural/attractors.py` - `HopfieldSchedulerNetwork` and `ModernHopfieldScheduler`
2. `backend/app/neural/sparse_coding.py` - `SparseScheduleEncoder`
3. Template database migration
4. Schedule compression utilities

**Success Metrics:**
- Attractor network stores 20+ successful templates
- Partial schedules (50% complete) converge to valid full schedules
- Sparse coding achieves 70%+ compression with 95%+ reconstruction accuracy

### Phase 3: Predictive and Adaptive (Weeks 9-12)

**Objectives:**
- Implement predictive coding for error-driven learning
- Add neural plasticity mechanisms (EWC, synaptic scaling)
- Enable continual learning without catastrophic forgetting

**Deliverables:**
1. `backend/app/neural/predictive_coding.py` - `PredictiveCodingScheduler`
2. `backend/app/neural/plasticity.py` - `AdaptivePreferenceNetwork`, `ContinualLearningScheduler`
3. Importance weight tracking for EWC
4. Continual learning evaluation harness

**Success Metrics:**
- Predictive coding reduces prediction error by 30% after 10 schedules
- System adapts to new preferences without forgetting old ones (>85% retention)
- Plasticity mechanisms enable learning over 100+ schedules without degradation

### Phase 4: Meta-Control (Weeks 13-16)

**Objectives:**
- Implement neuromodulation system
- Create context-aware meta-parameter tuning
- Integrate all neural components with existing systems

**Deliverables:**
1. `backend/app/neural/neuromodulation.py` - `NeuromodulatedScheduler`
2. `backend/app/neural/integrated_scheduler.py` - `GlobalNeuromodulatedScheduler`
3. Context detection and modulator level computation
4. Full system integration tests

**Success Metrics:**
- Neuromodulation adapts learning rate appropriately (crisis vs. normal)
- System explores more during disruptions, exploits during stability
- Integrated system outperforms baseline by 25% on composite metric

### Phase 5: Validation and Optimization (Weeks 17-20)

**Objectives:**
- Comprehensive testing on historical data
- Performance optimization
- Documentation and deployment

**Deliverables:**
1. Evaluation report on 2+ years of historical schedules
2. Performance optimization (target: <5s for schedule generation)
3. API documentation and examples
4. Production deployment with monitoring

**Success Metrics:**
- System matches or exceeds human scheduler quality on historical data
- Real-time schedule generation (<5 seconds)
- Zero catastrophic forgetting incidents in validation
- Successful integration with existing resilience framework

### Dependency Graph

```
Phase 1 (Hebbian + Lateral Inhibition)
    │
    ├─→ Phase 2 (Attractors + Sparse Coding)
    │       │
    │       └─→ Phase 3 (Predictive + Plasticity)
    │               │
    └───────────────┴─→ Phase 4 (Neuromodulation + Integration)
                            │
                            └─→ Phase 5 (Validation + Deployment)
```

### Risk Mitigation

**Risk 1: Computational Complexity**
- **Mitigation:** Implement efficient sparse matrix operations, use caching, profile extensively
- **Fallback:** Reduce network size, use approximate methods

**Risk 2: Catastrophic Forgetting**
- **Mitigation:** Implement EWC and experience replay from day 1, test continually
- **Fallback:** Maintain separate networks for different time periods

**Risk 3: Integration Complexity**
- **Mitigation:** Modular design with clear interfaces, comprehensive integration tests
- **Fallback:** Deploy neural components as optional enhancement, not required

**Risk 4: Tuning Difficulty**
- **Mitigation:** Extensive hyperparameter search, adaptive mechanisms
- **Fallback:** Use conservative defaults, allow manual override

---

## 10. References

### Hebbian Learning

- [Hebbian theory - Wikipedia](https://en.wikipedia.org/wiki/Hebbian_theory)
- [Hebbian Learning - The Decision Lab](https://thedecisionlab.com/reference-guide/neuroscience/hebbian-learning)
- [Classic Hebbian learning endows feed-forward networks with sufficient adaptability in challenging reinforcement learning tasks | Journal of Neurophysiology](https://journals.physiology.org/doi/full/10.1152/jn.00712.2020)
- [Learning and criticality in a self-organizing model of connectome growth | Scientific Reports](https://www.nature.com/articles/s41598-025-16377-8)

### Lateral Inhibition

- [Dynamics of Winner-Take-All Competition in Recurrent Neural Networks With Lateral Inhibition | IEEE Transactions on Neural Networks](https://dl.acm.org/doi/10.1109/TNN.2006.883724)
- [Inhibition SNN: unveiling the efficacy of various lateral inhibition learning in image pattern recognition | Discover Applied Sciences](https://link.springer.com/article/10.1007/s42452-024-06332-z)
- [Solving constraint-satisfaction problems with distributed neocortical-like neuronal networks - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5930080/)
- [Frontiers | Neuronal networks with NMDARs and lateral inhibition implement winner-takes-all](https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2015.00012/full)

### Neural Plasticity

- [Frontiers in Neuroscience 2025 | Neuroplasticity-Driven Learning Optimization](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1588570/pdf)
- [Learning the Plasticity: Plasticity-Driven Learning Framework in Spiking Neural Networks](https://arxiv.org/html/2308.12063v2)
- [Frontiers | Reward-optimizing learning using stochastic release plasticity](https://www.frontiersin.org/journals/neural-circuits/articles/10.3389/fncir.2025.1618506/full)
- [Adaptive Synaptic Scaling in Spiking Networks for Continual Learning and Enhanced Robustness - PubMed](https://pubmed.ncbi.nlm.nih.gov/38536699/)

### Sparse Coding

- [Methods of Sparse Measurement Matrix Optimization for Compressed Sensing - IET Signal Processing 2025](https://ietresearch.onlinelibrary.wiley.com/doi/abs/10.1049/sil2/1233853)
- [Sparse Transform and Compressed Sensing Methods to Improve Efficiency and Quality in MRI | MDPI 2025](https://www.mdpi.com/1424-8220/25/16/5137)
- [Efficient sparse coding algorithms | NIPS](https://dl.acm.org/doi/10.5555/2976456.2976557)

### Attractor Networks

- [Energy Landscape-Aware Vision Transformers: Layerwise Dynamics and Adaptive Task-Specific Training via Hopfield States | NeurIPS 2025](https://openreview.net/forum?id=Z6aBp0AJI1)
- [Classifying States of the Hopfield Network with Improved Accuracy, Generalization, and Interpretability](https://arxiv.org/html/2503.03018v1)
- [Input-driven dynamics for robust memory retrieval in Hopfield networks - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12017325/)
- [Self-orthogonalizing attractor neural networks emerging from the free energy principle](https://pni-lab.github.io/fep-attractor-network/)

### Predictive Coding

- [Predictive coding - Wikipedia](https://en.wikipedia.org/wiki/Predictive_coding)
- [Predictions not commands: active inference in the motor system - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3637647/)
- [Active sensing with predictive coding and uncertainty minimization: Patterns](https://www.cell.com/patterns/fulltext/S2666-3899(24)00097-7)
- [The empirical status of predictive coding and active inference - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0149763423004426)

### Neuromodulation

- [Modulating the neuromodulators: dopamine, serotonin and the endocannabinoid system - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8159866/)
- [Frontiers | Monoaminergic Neuromodulation of Sensory Processing](https://www.frontiersin.org/journals/neural-circuits/articles/10.3389/fncir.2018.00051/full)
- [Neuromodulatory Systems and Their Interactions: A Review of Models, Theories, and Experiments - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5744617/)
- [Neuromodulation and Neurophysiology on the Timescale of Learning and Decision-Making - PubMed](https://pubmed.ncbi.nlm.nih.gov/35363533/)

### Continual Learning & Stability-Plasticity

- [Escaping Stability-Plasticity Dilemma in Online Continual Learning for Motion Forecasting via Synergetic Memory Rehearsal](https://arxiv.org/html/2508.19571v1)
- [Addressing Loss of Plasticity and Catastrophic Forgetting in Continual Learning | ICLR 2025](https://openreview.net/forum?id=sKPzAXoylB)
- [Bayesian continual learning and forgetting in neural networks | Nature Communications](https://www.nature.com/articles/s41467-025-64601-w)
- [Overcoming catastrophic forgetting in neural networks | PNAS](https://www.pnas.org/doi/10.1073/pnas.1611835114)

---

## Conclusion

Neural computation offers a rich set of principles for adaptive, intelligent scheduling:

1. **Hebbian Learning** - Learn preferences associatively from experience
2. **Lateral Inhibition** - Resolve conflicts through competitive dynamics
3. **Neural Plasticity** - Adapt continuously without catastrophic forgetting
4. **Sparse Coding** - Represent schedules efficiently
5. **Attractor Networks** - Store and retrieve successful templates
6. **Predictive Coding** - Minimize prediction errors proactively
7. **Neuromodulation** - Adjust meta-parameters based on context

These concepts complement the existing transcription factor and stigmergy systems, creating a multi-layered architecture that combines:
- **Gene regulation metaphors** (context-sensitive constraint modulation)
- **Swarm intelligence** (emergent preference patterns)
- **Neural computation** (adaptive learning and memory)

The result is a scheduling system that is:
- **Adaptive:** Learns from experience and adjusts to changing conditions
- **Robust:** Maintains stable core patterns while flexibly handling disruptions
- **Efficient:** Uses sparse representations and attractor dynamics for fast inference
- **Intelligent:** Predicts outcomes and minimizes expected errors
- **Context-aware:** Adjusts behavior based on global system state

This neural layer transforms the scheduler from a reactive constraint solver into a proactive, learning system that gets better with experience.

---

**End of Research Report**
