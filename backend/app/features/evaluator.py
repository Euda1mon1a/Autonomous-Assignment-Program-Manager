"""Feature flag evaluation logic.

Evaluates feature flags based on:
- Boolean on/off state
- Percentage rollouts (gradual releases)
- User targeting (specific user IDs)
- Role targeting (specific user roles)
- Environment targeting (dev/staging/production)
- A/B testing variants
- Flag dependencies (prerequisite flags)
"""

import hashlib
from typing import Any


class FeatureFlagEvaluator:
    """
    Evaluates feature flags based on various targeting rules.

    Uses consistent hashing for percentage rollouts to ensure
    the same user always gets the same result.
    """

    def __init__(self, environment: str | None = None) -> None:
        """
        Initialize feature flag evaluator.

        Args:
            environment: Current environment (development, staging, production)
        """
        self.environment = environment or "production"

    def evaluate(
        self,
        flag_data: dict[str, Any],
        user_id: str | None = None,
        user_role: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None, str]:
        """
        Evaluate a feature flag for given context.

        Args:
            flag_data: Feature flag configuration
            user_id: User ID for targeting
            user_role: User role for targeting
            context: Additional context for evaluation

        Returns:
            Tuple of (enabled: bool, variant: str | None, reason: str)
        """
        context = context or {}

        # Check if flag is globally disabled
        if not flag_data.get("enabled", False):
            return False, None, "Flag is globally disabled"

            # Check environment targeting
        if not self._check_environment(flag_data):
            return False, None, f"Environment {self.environment} not targeted"

            # Check dependencies (prerequisite flags must be enabled)
            # Note: This would require access to other flags, so we skip for now
            # In a full implementation, we'd recursively evaluate dependencies

            # Check user ID targeting
        if not self._check_user_targeting(flag_data, user_id):
            return False, None, "User not in target list"

            # Check role targeting
        if not self._check_role_targeting(flag_data, user_role):
            return False, None, "User role not in target list"

            # Evaluate based on flag type
        flag_type = flag_data.get("flag_type", "boolean")

        if flag_type == "boolean":
            return True, None, "Flag is enabled"

        elif flag_type == "percentage":
            rollout_percentage = flag_data.get("rollout_percentage", 0.0)
            if self._is_in_rollout(user_id, flag_data["key"], rollout_percentage):
                return True, None, f"User in {rollout_percentage * 100}% rollout"
            else:
                return False, None, f"User not in {rollout_percentage * 100}% rollout"

        elif flag_type == "variant":
            variant = self._get_variant(
                user_id, flag_data["key"], flag_data.get("variants", {})
            )
            if variant:
                return True, variant, f"Assigned to variant: {variant}"
            else:
                return False, None, "No variant assigned"

        return False, None, "Unknown flag type"

    def _check_environment(self, flag_data: dict[str, Any]) -> bool:
        """
        Check if current environment is targeted.

        Args:
            flag_data: Feature flag configuration

        Returns:
            True if environment matches or no targeting specified
        """
        target_envs = flag_data.get("environments")
        if target_envs is None:
            return True  # No targeting = all environments

        return self.environment in target_envs

    def _check_user_targeting(
        self, flag_data: dict[str, Any], user_id: str | None
    ) -> bool:
        """
        Check if user is in target list.

        Args:
            flag_data: Feature flag configuration
            user_id: User ID to check

        Returns:
            True if user matches or no targeting specified
        """
        target_user_ids = flag_data.get("target_user_ids")
        if target_user_ids is None:
            return True  # No targeting = all users

        if user_id is None:
            return False  # User required but not provided

        return user_id in target_user_ids

    def _check_role_targeting(
        self, flag_data: dict[str, Any], user_role: str | None
    ) -> bool:
        """
        Check if user role is in target list.

        Args:
            flag_data: Feature flag configuration
            user_role: User role to check

        Returns:
            True if role matches or no targeting specified
        """
        target_roles = flag_data.get("target_roles")
        if target_roles is None:
            return True  # No targeting = all roles

        if user_role is None:
            return False  # Role required but not provided

        return user_role in target_roles

    def _is_in_rollout(
        self, user_id: str | None, flag_key: str, rollout_percentage: float
    ) -> bool:
        """
        Determine if user is in percentage rollout using consistent hashing.

        Uses MD5 hash of user_id + flag_key to deterministically assign users
        to rollout buckets. Same user + flag always gives same result.

        Args:
            user_id: User ID for hashing
            flag_key: Flag key for hashing
            rollout_percentage: Percentage of users to include (0.0 - 1.0)

        Returns:
            True if user is in rollout percentage
        """
        if user_id is None:
            # No user ID, use random-like behavior based on flag key alone
            # This means anonymous users will always get same result for same flag
            hash_input = flag_key
        else:
            # Combine user ID and flag key for deterministic hashing
            hash_input = f"{user_id}:{flag_key}"

            # Hash the input
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()

        # Convert first 8 hex chars to integer (0 to 2^32-1)
        hash_int = int(hash_value[:8], 16)

        # Normalize to 0.0 - 1.0
        hash_normalized = hash_int / (2**32 - 1)

        # User is in rollout if their hash is less than the rollout percentage
        return hash_normalized < rollout_percentage

    def _get_variant(
        self, user_id: str | None, flag_key: str, variants: dict[str, float]
    ) -> str | None:
        """
        Assign user to an A/B test variant using consistent hashing.

        Variants are specified as a dict mapping variant name to weight.
        Weights must sum to 1.0.

        Example:
            {"control": 0.5, "variant_a": 0.3, "variant_b": 0.2}

        Args:
            user_id: User ID for hashing
            flag_key: Flag key for hashing
            variants: Map of variant name to weight (0.0 - 1.0)

        Returns:
            Variant name, or None if no variants
        """
        if not variants:
            return None

            # Hash user + flag to get consistent variant assignment
        if user_id is None:
            hash_input = flag_key
        else:
            hash_input = f"{user_id}:{flag_key}"

        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)
        hash_normalized = hash_int / (2**32 - 1)

        # Assign to variant based on cumulative weights
        cumulative_weight = 0.0
        for variant_name, weight in sorted(variants.items()):
            cumulative_weight += weight
            if hash_normalized < cumulative_weight:
                return variant_name

                # Fallback to last variant (handles floating point errors)
        return list(variants.keys())[-1] if variants else None

    def evaluate_dependencies(
        self,
        flag_data: dict[str, Any],
        all_flags: dict[str, dict[str, Any]],
        user_id: str | None = None,
        user_role: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None, str]:
        """
        Evaluate a feature flag including dependency checks.

        Recursively evaluates all dependency flags to ensure prerequisites
        are met before enabling the flag.

        Args:
            flag_data: Feature flag configuration
            all_flags: Map of all available flags (key -> data)
            user_id: User ID for targeting
            user_role: User role for targeting
            context: Additional context for evaluation

        Returns:
            Tuple of (enabled: bool, variant: str | None, reason: str)
        """
        # Check dependencies first
        dependencies = flag_data.get("dependencies", [])
        if dependencies:
            for dep_key in dependencies:
                dep_flag = all_flags.get(dep_key)
                if dep_flag is None:
                    return False, None, f"Dependency flag '{dep_key}' not found"

                    # Recursively evaluate dependency
                dep_enabled, _, dep_reason = self.evaluate_dependencies(
                    dep_flag, all_flags, user_id, user_role, context
                )

                if not dep_enabled:
                    return (
                        False,
                        None,
                        f"Dependency '{dep_key}' not enabled: {dep_reason}",
                    )

                    # All dependencies satisfied, evaluate this flag
        return self.evaluate(flag_data, user_id, user_role, context)
