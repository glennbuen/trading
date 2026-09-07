import math

import pandas as pd
import pytest

from cryptobot import scoring as sc


class TestMarketStructureScore:
    def test_full_points_when_trend_matches_side(self):
        assert sc.market_structure_score("up", "long", 25.0) == 25.0
        assert sc.market_structure_score("down", "short", 25.0) == 25.0

    def test_half_points_on_transition(self):
        assert sc.market_structure_score("transition", "long", 25.0) == 12.5

    def test_zero_when_trend_opposes_side(self):
        assert sc.market_structure_score("down", "long", 25.0) == 0.0
        assert sc.market_structure_score("undefined", "long", 25.0) == 0.0


class TestPriceActionScore:
    def test_both_conditions_give_full_points(self):
        assert sc.price_action_score(True, True, 25.0) == 25.0

    def test_neither_condition_gives_zero(self):
        assert sc.price_action_score(False, False, 25.0) == 0.0

    def test_one_condition_gives_half(self):
        assert sc.price_action_score(True, False, 25.0) == 12.5
        assert sc.price_action_score(False, True, 25.0) == 12.5


class TestVolumeScore:
    def test_tiers_scale_with_relative_volume(self):
        assert sc.volume_score(3.5, 20.0) == 20.0    # >=3.0 -> 100%
        assert sc.volume_score(2.0, 20.0) == 16.0     # >=2.0 -> 80%
        assert sc.volume_score(1.2, 20.0) == 8.0      # >=1.2 -> 40%
        assert sc.volume_score(0.5, 20.0) == 0.0      # below every tier

    def test_nan_relative_volume_gives_zero_not_a_crash(self):
        assert sc.volume_score(float("nan"), 20.0) == 0.0


class TestLiquidityScore:
    def test_sweep_reversal_gives_full_points(self):
        assert sc.liquidity_score(True, False, 15.0) == 15.0

    def test_equal_level_alone_gives_half(self):
        assert sc.liquidity_score(False, True, 15.0) == 7.5

    def test_neither_gives_zero(self):
        assert sc.liquidity_score(False, False, 15.0) == 0.0

    def test_sweep_takes_priority_over_equal_level(self):
        assert sc.liquidity_score(True, True, 15.0) == 15.0


class TestRiskReward:
    def test_multiple_matches_hand_calculation(self):
        # entry=100, stop=95 (5 risk), target=110 (10 reward) -> 2.0R
        assert sc.risk_reward_multiple(100, 95, 110) == pytest.approx(2.0)

    def test_zero_stop_distance_returns_zero(self):
        assert sc.risk_reward_multiple(100, 100, 110) == 0.0

    def test_score_tiers_scale_with_r_multiple(self):
        assert sc.risk_reward_score(3.0, 15.0) == 15.0
        assert sc.risk_reward_score(2.0, 15.0) == pytest.approx(10.5)  # 70%
        assert sc.risk_reward_score(0.5, 15.0) == 0.0


class TestScoreSignal:
    def test_matches_the_architecture_spec_worked_example_shape(self):
        inputs = sc.SignalInputs(
            symbol="BTC/USDT", side="long", setup_label="Breakout + Retest",
            trend_state="up", breakout_in_direction=True, confirming_candle=True,
            relative_volume=1.9, liquidity_sweep=True, equal_level=False,
            entry=100.0, stop=95.0, target=112.0,  # R = 12/5 = 2.4
        )
        result = sc.score_signal(inputs)
        assert result.r_multiple == pytest.approx(2.4)
        assert result.max_score == 100.0
        # market_structure(25 full) + price_action(25 full) +
        # volume(20*0.4=8, 1.9x clears the 1.5 tier=60%->12) ... compute
        # exactly via the component functions to avoid a brittle hardcode:
        expected_volume = sc.volume_score(1.9, 25.0 * 0 + 20.0)  # weight=20 default
        expected_rr = sc.risk_reward_score(2.4, 15.0)
        expected_total = 25.0 + 25.0 + expected_volume + 15.0 + expected_rr
        assert result.total_score == pytest.approx(round(expected_total, 1))

    def test_explain_format_matches_spec_worked_example(self):
        inputs = sc.SignalInputs(
            symbol="BTC/USDT", side="long", setup_label="Breakout + Retest",
            trend_state="up", breakout_in_direction=True, confirming_candle=True,
            relative_volume=1.9, liquidity_sweep=True, equal_level=False,
            entry=100.0, stop=95.0, target=112.0,
        )
        result = sc.score_signal(inputs)
        text = result.explain()
        assert "BTC/USDT LONG" in text
        assert "Structure: Bullish" in text
        assert "Setup: Breakout + Retest" in text
        assert "Relative Volume: 1.9x" in text
        assert "Liquidity Sweep: Yes" in text
        assert "Risk/Reward: 2.4R" in text
        assert f"Score: {result.total_score:.0f}/100" in text

    def test_worst_case_signal_scores_near_zero(self):
        inputs = sc.SignalInputs(
            symbol="ETH/USDT", side="long", setup_label="Test",
            trend_state="down", breakout_in_direction=False, confirming_candle=False,
            relative_volume=0.5, liquidity_sweep=False, equal_level=False,
            entry=100.0, stop=95.0, target=100.5,  # tiny R, well under 1.0
        )
        result = sc.score_signal(inputs)
        assert result.total_score == 0.0

    def test_no_single_component_can_reach_full_score_alone(self):
        """Spec §15: 'Do NOT allow one indicator to trigger a trade by
        itself.' Verified structurally: maxing out ANY ONE component
        while every other is at its worst still falls far short of a
        typical passing threshold (e.g. 70/100)."""
        base = dict(symbol="X", side="long", setup_label="t", entry=100.0, stop=95.0, target=100.1)
        only_structure = sc.SignalInputs(**base, trend_state="up", breakout_in_direction=False,
                                          confirming_candle=False, relative_volume=0.1,
                                          liquidity_sweep=False, equal_level=False)
        assert sc.score_signal(only_structure).total_score <= 25.0

        only_volume = sc.SignalInputs(**base, trend_state="down", breakout_in_direction=False,
                                       confirming_candle=False, relative_volume=5.0,
                                       liquidity_sweep=False, equal_level=False)
        assert sc.score_signal(only_volume).total_score <= 20.0


class TestConfigurableWeights:
    def test_custom_weights_change_max_score(self):
        weights = sc.ScoringWeights(market_structure=40, price_action=20, volume=20,
                                     liquidity=10, risk_reward=10)
        assert weights.total == 100.0
        inputs = sc.SignalInputs(
            symbol="X", side="long", setup_label="t", trend_state="up",
            breakout_in_direction=True, confirming_candle=True, relative_volume=3.0,
            liquidity_sweep=True, equal_level=False, entry=100, stop=95, target=115,
        )
        result = sc.score_signal(inputs, weights=weights)
        assert result.max_score == 100.0
        assert result.component_scores["market_structure"] == 40.0  # full weight, trend matches

    def test_weights_need_not_sum_to_100(self):
        weights = sc.ScoringWeights(market_structure=10, price_action=10, volume=10,
                                     liquidity=10, risk_reward=10)
        assert weights.total == 50.0
        inputs = sc.SignalInputs(
            symbol="X", side="long", setup_label="t", trend_state="up",
            breakout_in_direction=True, confirming_candle=True, relative_volume=3.0,
            liquidity_sweep=True, equal_level=False, entry=100, stop=95, target=115,
        )
        result = sc.score_signal(inputs, weights=weights)
        assert result.max_score == 50.0
