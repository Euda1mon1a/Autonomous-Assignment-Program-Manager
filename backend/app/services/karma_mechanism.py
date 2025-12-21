"""Karma-based swap allocation mechanism.

This module implements a fair, non-monetary allocation system for repeated swap bidding.
The Karma mechanism creates a closed economy where providers can bid for swaps using karma
points, with redistribution ensuring long-term fairness.

Key Properties:
    - Self-contained: No external currency required
    - Fair: Providers who give in now are rewarded in the future
    - Efficient: High-urgency providers can outbid when needed
    - Budget-balanced: Total karma is conserved across the system
"""
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class KarmaAccount:
    """Represents a provider's karma account.

    Attributes:
        provider_id: Unique identifier for the provider (faculty member)
        balance: Current available karma for bidding
        lifetime_earned: Total karma earned through redistribution
        lifetime_spent: Total karma spent on winning bids
    """

    provider_id: str
    balance: float
    lifetime_earned: float = 0.0
    lifetime_spent: float = 0.0


@dataclass
class KarmaMechanism:
    """Implements karma-based swap allocation and settlement.

    The mechanism operates as a closed economy where:
    1. Winners pay their bid amount (karma is debited)
    2. Losers receive equal share of the winner's payment (karma is credited)
    3. Total karma remains constant (budget-balanced)

    This creates incentives for fair participation: providers who lose bids
    accumulate karma to use in future high-priority situations.

    Attributes:
        initial_balance: Starting karma for new accounts
        accounts: Dictionary mapping provider_id to KarmaAccount
        bids: Dictionary mapping swap_id to list of (provider_id, bid_amount) tuples
    """

    initial_balance: float = 100.0
    accounts: dict[str, KarmaAccount] = field(default_factory=dict)
    bids: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    # Class constant for minimum Gini coefficient target
    MIN_GINI_TARGET: ClassVar[float] = 0.05

    def create_account(self, provider_id: str) -> KarmaAccount:
        """Create a new karma account for a provider.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            KarmaAccount: The newly created account

        Raises:
            ValueError: If account already exists for this provider
        """
        if provider_id in self.accounts:
            raise ValueError(f"Account already exists for provider {provider_id}")

        account = KarmaAccount(
            provider_id=provider_id,
            balance=self.initial_balance,
            lifetime_earned=0.0,
            lifetime_spent=0.0,
        )
        self.accounts[provider_id] = account
        return account

    def get_balance(self, provider_id: str) -> float:
        """Get the current karma balance for a provider.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            float: Current karma balance

        Raises:
            KeyError: If provider account does not exist
        """
        if provider_id not in self.accounts:
            raise KeyError(f"No account found for provider {provider_id}")
        return self.accounts[provider_id].balance

    def get_accounts(self) -> dict[str, KarmaAccount]:
        """Get all karma accounts.

        Returns:
            dict[str, KarmaAccount]: Dictionary of all accounts
        """
        return self.accounts.copy()

    def submit_bid(self, provider_id: str, swap_id: str, bid_amount: float) -> bool:
        """Submit a bid for a swap opportunity.

        Args:
            provider_id: Unique identifier for the provider
            swap_id: Unique identifier for the swap
            bid_amount: Amount of karma to bid (must be positive)

        Returns:
            bool: True if bid was accepted, False otherwise

        Raises:
            KeyError: If provider account does not exist
            ValueError: If bid amount is invalid (negative or zero)
        """
        if provider_id not in self.accounts:
            raise KeyError(f"No account found for provider {provider_id}")

        if bid_amount <= 0:
            raise ValueError("Bid amount must be positive")

        account = self.accounts[provider_id]

        # Validate bid does not exceed balance
        if bid_amount > account.balance:
            return False

        # Record bid for swap
        if swap_id not in self.bids:
            self.bids[swap_id] = []

        # Check if provider already has a bid for this swap
        existing_bid_index = next(
            (i for i, (pid, _) in enumerate(self.bids[swap_id]) if pid == provider_id),
            None,
        )

        if existing_bid_index is not None:
            # Update existing bid
            self.bids[swap_id][existing_bid_index] = (provider_id, bid_amount)
        else:
            # Add new bid
            self.bids[swap_id].append((provider_id, bid_amount))

        return True

    def get_bids(self, swap_id: str) -> list[tuple[str, float]]:
        """Get all bids for a swap, sorted by bid amount (descending).

        Args:
            swap_id: Unique identifier for the swap

        Returns:
            list[tuple[str, float]]: List of (provider_id, bid_amount) sorted by bid amount
        """
        if swap_id not in self.bids:
            return []

        # Sort bids by amount (descending)
        return sorted(self.bids[swap_id], key=lambda x: x[1], reverse=True)

    def resolve_swap(self, swap_id: str) -> tuple[str, float]:
        """Resolve a swap by determining the winner (highest bidder).

        Args:
            swap_id: Unique identifier for the swap

        Returns:
            tuple[str, float]: (winner_provider_id, winning_bid_amount)

        Raises:
            ValueError: If no bids exist for this swap
        """
        if swap_id not in self.bids or len(self.bids[swap_id]) == 0:
            raise ValueError(f"No bids found for swap {swap_id}")

        # Get sorted bids (highest first)
        sorted_bids = self.get_bids(swap_id)

        # Winner is highest bidder
        winner_id, winning_bid = sorted_bids[0]

        return winner_id, winning_bid

    def settle(self, swap_id: str) -> None:
        """Settle a swap by updating karma balances.

        Settlement rules:
        - Winner: K_new = K_old - bid_amount
        - Each loser: K_new = K_old + (winning_bid / num_losers)

        This ensures budget balance: karma paid by winner is redistributed to losers.

        Args:
            swap_id: Unique identifier for the swap

        Raises:
            ValueError: If swap cannot be resolved or settled
        """
        # Resolve to get winner
        winner_id, winning_bid = self.resolve_swap(swap_id)

        # Get all bids for this swap
        all_bids = self.bids[swap_id]

        # Identify losers (everyone except winner)
        losers = [provider_id for provider_id, _ in all_bids if provider_id != winner_id]

        # Debit winner's account
        winner_account = self.accounts[winner_id]
        winner_account.balance -= winning_bid
        winner_account.lifetime_spent += winning_bid

        # Redistribute to losers (if any)
        if len(losers) > 0:
            redistribution_amount = winning_bid / len(losers)

            for loser_id in losers:
                loser_account = self.accounts[loser_id]
                loser_account.balance += redistribution_amount
                loser_account.lifetime_earned += redistribution_amount

        # Clear bids for this swap
        del self.bids[swap_id]

    def get_gini_coefficient(self) -> float:
        """Calculate the Gini coefficient of karma distribution.

        The Gini coefficient measures inequality in the distribution of karma balances.
        - 0.0 = Perfect equality (everyone has the same balance)
        - 1.0 = Perfect inequality (one person has all karma)

        Returns:
            float: Gini coefficient (0.0 to 1.0)

        Raises:
            ValueError: If no accounts exist
        """
        if len(self.accounts) == 0:
            raise ValueError("Cannot calculate Gini coefficient with no accounts")

        if len(self.accounts) == 1:
            return 0.0

        # Get all balances sorted
        balances = sorted([account.balance for account in self.accounts.values()])
        n = len(balances)

        # Calculate Gini coefficient using the formula:
        # G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
        # where x_i is the i-th smallest value
        total_balance = sum(balances)

        if total_balance == 0:
            return 0.0

        cumulative_sum = sum((i + 1) * balance for i, balance in enumerate(balances))
        gini = (2 * cumulative_sum) / (n * total_balance) - (n + 1) / n

        return gini

    def should_rebalance(self, threshold: float = 0.3) -> bool:
        """Check if karma should be rebalanced based on inequality threshold.

        Args:
            threshold: Maximum acceptable Gini coefficient (default: 0.3)

        Returns:
            bool: True if rebalancing is recommended, False otherwise
        """
        if len(self.accounts) <= 1:
            return False

        try:
            current_gini = self.get_gini_coefficient()
            return current_gini > threshold
        except ValueError:
            return False

    def rebalance(self, target_gini: float = 0.1) -> None:
        """Redistribute karma to reduce inequality.

        This method redistributes karma from high-balance accounts to low-balance
        accounts to achieve a target Gini coefficient. The total karma remains constant.

        The algorithm:
        1. Calculate mean balance
        2. Move balances closer to the mean
        3. Iterate until target Gini is achieved or close enough

        Args:
            target_gini: Desired Gini coefficient after rebalancing (default: 0.1)

        Raises:
            ValueError: If target_gini is invalid or no accounts exist
        """
        if target_gini < self.MIN_GINI_TARGET or target_gini >= 1.0:
            raise ValueError(
                f"Target Gini must be between {self.MIN_GINI_TARGET} and 1.0"
            )

        if len(self.accounts) <= 1:
            return

        # Calculate mean balance
        total_karma = sum(account.balance for account in self.accounts.values())
        mean_balance = total_karma / len(self.accounts)

        # Iteratively move balances toward mean
        max_iterations = 100
        convergence_factor = 0.5  # How much to move toward mean each iteration

        for _ in range(max_iterations):
            current_gini = self.get_gini_coefficient()

            if current_gini <= target_gini:
                break

            # Move each balance toward the mean
            for account in self.accounts.values():
                difference = mean_balance - account.balance
                adjustment = difference * convergence_factor
                account.balance += adjustment

        # Final normalization to ensure total karma is preserved
        final_total = sum(account.balance for account in self.accounts.values())
        if final_total > 0:
            correction_factor = total_karma / final_total
            for account in self.accounts.values():
                account.balance *= correction_factor

    def calculate_effective_bid(
        self, provider_id: str, raw_bid: float, urgency: float
    ) -> float:
        """Calculate effective bid with urgency weighting.

        This method allows providers to signal urgency, which multiplies the
        effective bid value. Higher urgency increases the bid's competitiveness
        without changing the actual karma amount spent if won.

        Args:
            provider_id: Unique identifier for the provider
            raw_bid: Base karma amount to bid
            urgency: Urgency multiplier (typically 0.5 to 2.0)
                    1.0 = normal urgency
                    < 1.0 = low urgency (bid counts for less)
                    > 1.0 = high urgency (bid counts for more)

        Returns:
            float: Effective bid amount (raw_bid * urgency)

        Raises:
            ValueError: If urgency is negative or zero
            KeyError: If provider account does not exist

        Note:
            The winner still pays only the raw_bid, not the effective bid.
            This allows for signaling without changing the economic balance.
        """
        if provider_id not in self.accounts:
            raise KeyError(f"No account found for provider {provider_id}")

        if urgency <= 0:
            raise ValueError("Urgency must be positive")

        return raw_bid * urgency

    def to_dict(self) -> dict:
        """Serialize the karma mechanism state to a dictionary.

        Returns:
            dict: Serialized state containing:
                - initial_balance: Initial balance for new accounts
                - accounts: List of account dictionaries
                - bids: Dictionary of swap_id to bid lists
        """
        return {
            "initial_balance": self.initial_balance,
            "accounts": [
                {
                    "provider_id": account.provider_id,
                    "balance": account.balance,
                    "lifetime_earned": account.lifetime_earned,
                    "lifetime_spent": account.lifetime_spent,
                }
                for account in self.accounts.values()
            ],
            "bids": {
                swap_id: [(provider_id, bid) for provider_id, bid in bid_list]
                for swap_id, bid_list in self.bids.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KarmaMechanism":
        """Deserialize karma mechanism state from a dictionary.

        Args:
            data: Serialized state dictionary (from to_dict)

        Returns:
            KarmaMechanism: Reconstructed karma mechanism instance

        Raises:
            KeyError: If required fields are missing from data
            ValueError: If data is invalid
        """
        mechanism = cls(initial_balance=data["initial_balance"])

        # Restore accounts
        for account_data in data["accounts"]:
            account = KarmaAccount(
                provider_id=account_data["provider_id"],
                balance=account_data["balance"],
                lifetime_earned=account_data["lifetime_earned"],
                lifetime_spent=account_data["lifetime_spent"],
            )
            mechanism.accounts[account.provider_id] = account

        # Restore bids
        for swap_id, bid_list in data["bids"].items():
            mechanism.bids[swap_id] = [
                (provider_id, bid) for provider_id, bid in bid_list
            ]

        return mechanism
