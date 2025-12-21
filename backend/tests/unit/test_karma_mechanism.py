"""Tests for karma-based swap allocation mechanism."""
import pytest

from app.services.karma_mechanism import KarmaAccount, KarmaMechanism


class TestKarmaAccount:
    """Test suite for KarmaAccount dataclass."""

    def test_account_creation(self):
        """Test basic account creation."""
        account = KarmaAccount(
            provider_id="dr_smith",
            balance=100.0,
            lifetime_earned=0.0,
            lifetime_spent=0.0,
        )

        assert account.provider_id == "dr_smith"
        assert account.balance == 100.0
        assert account.lifetime_earned == 0.0
        assert account.lifetime_spent == 0.0


class TestKarmaMechanismAccountManagement:
    """Test suite for account management operations."""

    def test_create_account(self):
        """Test creating a new karma account."""
        karma = KarmaMechanism(initial_balance=100.0)
        account = karma.create_account("dr_smith")

        assert account.provider_id == "dr_smith"
        assert account.balance == 100.0
        assert account.lifetime_earned == 0.0
        assert account.lifetime_spent == 0.0

    def test_create_duplicate_account_raises_error(self):
        """Test that creating duplicate account raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        with pytest.raises(ValueError, match="Account already exists"):
            karma.create_account("dr_smith")

    def test_get_balance(self):
        """Test retrieving account balance."""
        karma = KarmaMechanism(initial_balance=150.0)
        karma.create_account("dr_jones")

        balance = karma.get_balance("dr_jones")
        assert balance == 150.0

    def test_get_balance_nonexistent_account_raises_error(self):
        """Test that getting balance for nonexistent account raises KeyError."""
        karma = KarmaMechanism(initial_balance=100.0)

        with pytest.raises(KeyError, match="No account found"):
            karma.get_balance("nonexistent")

    def test_get_accounts(self):
        """Test retrieving all accounts."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        accounts = karma.get_accounts()

        assert len(accounts) == 3
        assert "dr_smith" in accounts
        assert "dr_jones" in accounts
        assert "dr_patel" in accounts
        assert all(acc.balance == 100.0 for acc in accounts.values())


class TestKarmaMechanismBidding:
    """Test suite for bidding operations."""

    def test_submit_valid_bid(self):
        """Test submitting a valid bid."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        result = karma.submit_bid("dr_smith", "swap_123", 30.0)

        assert result is True
        bids = karma.get_bids("swap_123")
        assert len(bids) == 1
        assert bids[0] == ("dr_smith", 30.0)

    def test_submit_bid_exceeds_balance(self):
        """Test that bid exceeding balance is rejected."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        result = karma.submit_bid("dr_smith", "swap_123", 150.0)

        assert result is False
        bids = karma.get_bids("swap_123")
        assert len(bids) == 0

    def test_submit_bid_nonexistent_account_raises_error(self):
        """Test that bidding with nonexistent account raises KeyError."""
        karma = KarmaMechanism(initial_balance=100.0)

        with pytest.raises(KeyError, match="No account found"):
            karma.submit_bid("nonexistent", "swap_123", 50.0)

    def test_submit_negative_bid_raises_error(self):
        """Test that negative bid raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        with pytest.raises(ValueError, match="Bid amount must be positive"):
            karma.submit_bid("dr_smith", "swap_123", -10.0)

    def test_submit_zero_bid_raises_error(self):
        """Test that zero bid raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        with pytest.raises(ValueError, match="Bid amount must be positive"):
            karma.submit_bid("dr_smith", "swap_123", 0.0)

    def test_submit_multiple_bids_same_swap(self):
        """Test multiple providers bidding on same swap."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        bids = karma.get_bids("swap_123")
        assert len(bids) == 3

    def test_update_existing_bid(self):
        """Test updating an existing bid for a swap."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_smith", "swap_123", 50.0)  # Update

        bids = karma.get_bids("swap_123")
        assert len(bids) == 1
        assert bids[0] == ("dr_smith", 50.0)

    def test_get_bids_sorted_by_amount(self):
        """Test that get_bids returns bids sorted by amount (descending)."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        bids = karma.get_bids("swap_123")

        # Should be sorted descending
        assert bids[0] == ("dr_jones", 45.0)
        assert bids[1] == ("dr_smith", 30.0)
        assert bids[2] == ("dr_patel", 20.0)

    def test_get_bids_nonexistent_swap(self):
        """Test getting bids for nonexistent swap returns empty list."""
        karma = KarmaMechanism(initial_balance=100.0)

        bids = karma.get_bids("nonexistent_swap")
        assert bids == []


class TestKarmaMechanismResolution:
    """Test suite for swap resolution."""

    def test_resolve_swap_highest_bidder_wins(self):
        """Test that highest bidder wins the swap."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        winner, amount = karma.resolve_swap("swap_123")

        assert winner == "dr_jones"
        assert amount == 45.0

    def test_resolve_swap_single_bidder(self):
        """Test resolving swap with only one bidder."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        karma.submit_bid("dr_smith", "swap_123", 30.0)

        winner, amount = karma.resolve_swap("swap_123")

        assert winner == "dr_smith"
        assert amount == 30.0

    def test_resolve_swap_no_bids_raises_error(self):
        """Test that resolving swap with no bids raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)

        with pytest.raises(ValueError, match="No bids found"):
            karma.resolve_swap("swap_123")


class TestKarmaMechanismSettlement:
    """Test suite for karma settlement."""

    def test_settle_winner_pays_losers_receive(self):
        """Test that winner pays and losers receive redistribution."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        karma.settle("swap_123")

        # dr_jones wins and pays 45.0
        assert karma.get_balance("dr_jones") == 100.0 - 45.0
        assert karma.accounts["dr_jones"].lifetime_spent == 45.0

        # dr_smith and dr_patel each receive 45.0 / 2 = 22.5
        assert karma.get_balance("dr_smith") == 100.0 + 22.5
        assert karma.accounts["dr_smith"].lifetime_earned == 22.5

        assert karma.get_balance("dr_patel") == 100.0 + 22.5
        assert karma.accounts["dr_patel"].lifetime_earned == 22.5

    def test_settle_single_bidder_no_redistribution(self):
        """Test settling with single bidder (no losers to redistribute to)."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.settle("swap_123")

        # Winner pays, no one to redistribute to
        assert karma.get_balance("dr_smith") == 70.0
        assert karma.accounts["dr_smith"].lifetime_spent == 30.0
        assert karma.accounts["dr_smith"].lifetime_earned == 0.0

    def test_settle_clears_bids(self):
        """Test that settlement clears bids for the swap."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)

        karma.settle("swap_123")

        # Bids should be cleared
        bids = karma.get_bids("swap_123")
        assert len(bids) == 0

    def test_settle_updates_lifetime_stats(self):
        """Test that settlement updates lifetime earned and spent correctly."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")

        # First swap
        karma.submit_bid("dr_smith", "swap_1", 20.0)
        karma.submit_bid("dr_jones", "swap_1", 30.0)
        karma.settle("swap_1")

        # Second swap
        karma.submit_bid("dr_smith", "swap_2", 40.0)
        karma.submit_bid("dr_jones", "swap_2", 25.0)
        karma.settle("swap_2")

        # dr_jones won swap_1 (spent 30, earned 0)
        # dr_jones lost swap_2 (spent 0, earned 40/1 = 40)
        assert karma.accounts["dr_jones"].lifetime_spent == 30.0
        assert karma.accounts["dr_jones"].lifetime_earned == 40.0

        # dr_smith lost swap_1 (spent 0, earned 30/1 = 30)
        # dr_smith won swap_2 (spent 40, earned 0)
        assert karma.accounts["dr_smith"].lifetime_spent == 40.0
        assert karma.accounts["dr_smith"].lifetime_earned == 30.0


class TestKarmaMechanismBudgetBalance:
    """Test suite for budget balance property."""

    def test_total_karma_conserved_after_settlement(self):
        """Test that total karma is conserved after settlement."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Calculate initial total
        initial_total = sum(acc.balance for acc in karma.accounts.values())

        # Run swap
        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)
        karma.settle("swap_123")

        # Calculate final total
        final_total = sum(acc.balance for acc in karma.accounts.values())

        # Total should be conserved
        assert abs(initial_total - final_total) < 1e-10

    def test_total_karma_conserved_multiple_swaps(self):
        """Test that total karma is conserved across multiple swaps."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        initial_total = sum(acc.balance for acc in karma.accounts.values())

        # Multiple swaps
        for i in range(5):
            karma.submit_bid("dr_smith", f"swap_{i}", 10.0 + i * 5)
            karma.submit_bid("dr_jones", f"swap_{i}", 20.0 + i * 3)
            karma.submit_bid("dr_patel", f"swap_{i}", 15.0 + i * 4)
            karma.settle(f"swap_{i}")

        final_total = sum(acc.balance for acc in karma.accounts.values())

        # Total should still be conserved
        assert abs(initial_total - final_total) < 1e-10


class TestKarmaMechanismGiniCoefficient:
    """Test suite for Gini coefficient calculation."""

    def test_gini_coefficient_perfect_equality(self):
        """Test Gini coefficient when all have equal balance."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        gini = karma.get_gini_coefficient()

        # All have same balance, Gini should be ~0
        assert abs(gini) < 1e-10

    def test_gini_coefficient_inequality(self):
        """Test Gini coefficient with unequal distribution."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Create inequality
        karma.accounts["dr_smith"].balance = 150.0
        karma.accounts["dr_jones"].balance = 100.0
        karma.accounts["dr_patel"].balance = 50.0

        gini = karma.get_gini_coefficient()

        # Should have some inequality
        assert 0.0 < gini < 1.0

    def test_gini_coefficient_single_account(self):
        """Test Gini coefficient with single account returns 0."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        gini = karma.get_gini_coefficient()

        assert gini == 0.0

    def test_gini_coefficient_no_accounts_raises_error(self):
        """Test that Gini calculation with no accounts raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)

        with pytest.raises(ValueError, match="Cannot calculate Gini"):
            karma.get_gini_coefficient()

    def test_gini_coefficient_zero_total_balance(self):
        """Test Gini coefficient when total balance is zero."""
        karma = KarmaMechanism(initial_balance=0.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")

        gini = karma.get_gini_coefficient()

        # When all balances are 0, Gini should be 0
        assert gini == 0.0


class TestKarmaMechanismRebalancing:
    """Test suite for karma rebalancing."""

    def test_should_rebalance_high_inequality(self):
        """Test that should_rebalance returns True when inequality is high."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Create high inequality
        karma.accounts["dr_smith"].balance = 200.0
        karma.accounts["dr_jones"].balance = 50.0
        karma.accounts["dr_patel"].balance = 50.0

        assert karma.should_rebalance(threshold=0.3) is True

    def test_should_rebalance_low_inequality(self):
        """Test that should_rebalance returns False when inequality is low."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # All roughly equal
        assert karma.should_rebalance(threshold=0.3) is False

    def test_rebalance_reduces_gini(self):
        """Test that rebalancing reduces Gini coefficient."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Create inequality
        karma.accounts["dr_smith"].balance = 200.0
        karma.accounts["dr_jones"].balance = 50.0
        karma.accounts["dr_patel"].balance = 50.0

        gini_before = karma.get_gini_coefficient()
        karma.rebalance(target_gini=0.1)
        gini_after = karma.get_gini_coefficient()

        assert gini_after < gini_before
        assert gini_after <= 0.15  # Should be close to target

    def test_rebalance_preserves_total_karma(self):
        """Test that rebalancing preserves total karma."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Create inequality
        karma.accounts["dr_smith"].balance = 200.0
        karma.accounts["dr_jones"].balance = 50.0
        karma.accounts["dr_patel"].balance = 50.0

        total_before = sum(acc.balance for acc in karma.accounts.values())
        karma.rebalance(target_gini=0.1)
        total_after = sum(acc.balance for acc in karma.accounts.values())

        assert abs(total_before - total_after) < 1e-6

    def test_rebalance_invalid_target_gini_raises_error(self):
        """Test that invalid target Gini raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")

        with pytest.raises(ValueError, match="Target Gini must be"):
            karma.rebalance(target_gini=1.5)

        with pytest.raises(ValueError, match="Target Gini must be"):
            karma.rebalance(target_gini=0.01)  # Below MIN_GINI_TARGET

    def test_rebalance_single_account_no_op(self):
        """Test that rebalancing with single account is no-op."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        balance_before = karma.get_balance("dr_smith")
        karma.rebalance(target_gini=0.1)
        balance_after = karma.get_balance("dr_smith")

        assert balance_before == balance_after


class TestKarmaMechanismEffectiveBid:
    """Test suite for urgency-weighted bidding."""

    def test_calculate_effective_bid_normal_urgency(self):
        """Test effective bid with normal urgency (1.0)."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        effective_bid = karma.calculate_effective_bid("dr_smith", 50.0, urgency=1.0)

        assert effective_bid == 50.0

    def test_calculate_effective_bid_high_urgency(self):
        """Test effective bid with high urgency."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        effective_bid = karma.calculate_effective_bid("dr_smith", 50.0, urgency=1.5)

        assert effective_bid == 75.0

    def test_calculate_effective_bid_low_urgency(self):
        """Test effective bid with low urgency."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        effective_bid = karma.calculate_effective_bid("dr_smith", 50.0, urgency=0.5)

        assert effective_bid == 25.0

    def test_calculate_effective_bid_nonexistent_account_raises_error(self):
        """Test that effective bid for nonexistent account raises KeyError."""
        karma = KarmaMechanism(initial_balance=100.0)

        with pytest.raises(KeyError, match="No account found"):
            karma.calculate_effective_bid("nonexistent", 50.0, urgency=1.0)

    def test_calculate_effective_bid_negative_urgency_raises_error(self):
        """Test that negative urgency raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        with pytest.raises(ValueError, match="Urgency must be positive"):
            karma.calculate_effective_bid("dr_smith", 50.0, urgency=-1.0)

    def test_calculate_effective_bid_zero_urgency_raises_error(self):
        """Test that zero urgency raises ValueError."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")

        with pytest.raises(ValueError, match="Urgency must be positive"):
            karma.calculate_effective_bid("dr_smith", 50.0, urgency=0.0)


class TestKarmaMechanismSerialization:
    """Test suite for state serialization and deserialization."""

    def test_to_dict_serialization(self):
        """Test serializing karma mechanism to dictionary."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)

        data = karma.to_dict()

        assert data["initial_balance"] == 100.0
        assert len(data["accounts"]) == 2
        assert "swap_123" in data["bids"]
        assert len(data["bids"]["swap_123"]) == 2

    def test_from_dict_deserialization(self):
        """Test deserializing karma mechanism from dictionary."""
        data = {
            "initial_balance": 150.0,
            "accounts": [
                {
                    "provider_id": "dr_smith",
                    "balance": 120.0,
                    "lifetime_earned": 20.0,
                    "lifetime_spent": 50.0,
                },
                {
                    "provider_id": "dr_jones",
                    "balance": 180.0,
                    "lifetime_earned": 80.0,
                    "lifetime_spent": 0.0,
                },
            ],
            "bids": {
                "swap_123": [("dr_smith", 30.0), ("dr_jones", 45.0)],
            },
        }

        karma = KarmaMechanism.from_dict(data)

        assert karma.initial_balance == 150.0
        assert len(karma.accounts) == 2
        assert karma.get_balance("dr_smith") == 120.0
        assert karma.get_balance("dr_jones") == 180.0
        assert karma.accounts["dr_smith"].lifetime_earned == 20.0
        assert karma.accounts["dr_smith"].lifetime_spent == 50.0
        assert len(karma.get_bids("swap_123")) == 2

    def test_round_trip_serialization(self):
        """Test that serialization and deserialization are consistent."""
        karma = KarmaMechanism(initial_balance=100.0)
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        # Serialize
        data = karma.to_dict()

        # Deserialize
        karma_restored = KarmaMechanism.from_dict(data)

        # Verify all state is preserved
        assert karma_restored.initial_balance == karma.initial_balance
        assert len(karma_restored.accounts) == len(karma.accounts)
        assert karma_restored.get_balance("dr_smith") == karma.get_balance("dr_smith")
        assert karma_restored.get_balance("dr_jones") == karma.get_balance("dr_jones")
        assert karma_restored.get_balance("dr_patel") == karma.get_balance("dr_patel")
        assert karma_restored.get_bids("swap_123") == karma.get_bids("swap_123")


class TestKarmaMechanismIntegration:
    """Integration tests for complete use cases."""

    def test_complete_swap_workflow(self):
        """Test complete workflow from account creation through settlement."""
        karma = KarmaMechanism(initial_balance=100.0)

        # Create accounts
        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Bidding for a swap
        karma.submit_bid("dr_smith", "swap_123", 30.0)
        karma.submit_bid("dr_jones", "swap_123", 45.0)
        karma.submit_bid("dr_patel", "swap_123", 20.0)

        # Resolve
        winner, amount = karma.resolve_swap("swap_123")
        assert winner == "dr_jones"
        assert amount == 45.0

        # Settle
        karma.settle("swap_123")

        # Verify final balances
        assert karma.get_balance("dr_jones") == 55.0  # 100 - 45
        assert karma.get_balance("dr_smith") == 122.5  # 100 + 45/2
        assert karma.get_balance("dr_patel") == 122.5  # 100 + 45/2

        # Verify budget balance
        total = sum(acc.balance for acc in karma.accounts.values())
        assert abs(total - 300.0) < 1e-10

    def test_multiple_swaps_fairness(self):
        """Test that multiple swaps result in fair redistribution."""
        karma = KarmaMechanism(initial_balance=100.0)

        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Swap 1: dr_jones wins
        karma.submit_bid("dr_smith", "swap_1", 30.0)
        karma.submit_bid("dr_jones", "swap_1", 50.0)
        karma.submit_bid("dr_patel", "swap_1", 20.0)
        karma.settle("swap_1")

        # Now dr_smith and dr_patel have more karma
        # Swap 2: dr_smith wins
        karma.submit_bid("dr_smith", "swap_2", 60.0)
        karma.submit_bid("dr_jones", "swap_2", 30.0)
        karma.submit_bid("dr_patel", "swap_2", 40.0)
        karma.settle("swap_2")

        # Verify everyone has participated and received redistribution
        assert karma.accounts["dr_jones"].lifetime_spent > 0
        assert karma.accounts["dr_jones"].lifetime_earned > 0
        assert karma.accounts["dr_smith"].lifetime_spent > 0
        assert karma.accounts["dr_smith"].lifetime_earned > 0
        assert karma.accounts["dr_patel"].lifetime_earned > 0

        # Verify budget balance maintained
        total = sum(acc.balance for acc in karma.accounts.values())
        assert abs(total - 300.0) < 1e-10

    def test_rebalancing_after_inequality(self):
        """Test rebalancing after natural inequality develops."""
        karma = KarmaMechanism(initial_balance=100.0)

        karma.create_account("dr_smith")
        karma.create_account("dr_jones")
        karma.create_account("dr_patel")

        # Run many swaps where dr_jones keeps losing
        for i in range(5):
            karma.submit_bid("dr_smith", f"swap_{i}", 50.0)
            karma.submit_bid("dr_jones", f"swap_{i}", 10.0)
            karma.submit_bid("dr_patel", f"swap_{i}", 20.0)
            karma.settle(f"swap_{i}")

        # Check inequality
        assert karma.should_rebalance(threshold=0.3)

        # Rebalance
        total_before = sum(acc.balance for acc in karma.accounts.values())
        karma.rebalance(target_gini=0.1)
        total_after = sum(acc.balance for acc in karma.accounts.values())

        # Verify inequality reduced and budget maintained
        assert not karma.should_rebalance(threshold=0.3)
        assert abs(total_before - total_after) < 1e-6
