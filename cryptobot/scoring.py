"""
Signal Scoring — architecture spec §14-15: an explainable, configurable
weighted score combining market structure, price action, volume,
liquidity, and risk/reward into one number, with every component visible
— no single indicator is allowed to trigger a trade by itself (§15).

General-purpose scoring layer over the engine outputs already built
(Phases 2-3), not tied to any one strategy — reusable across all 4
strategies once the remaining 3 are built (Phase 11's comparison).
Default weights match the spec's own worked example (25/25/20/15/15 =
100); every weight and every tier threshold is a dataclass field, none
hardcoded — per spec §14: "these numbers are NOT fixed. Make all weights
configurable and test them."

Decoupled by design: `SignalInputs` is a small, explicit set of already-
extracted values (trend state, whether a breakout/confirming candle
happened, relative volume, whether a liquidity sweep fired, entry/stop/
target). Mapping a specific strategy's own column names onto these
fields is the CALLER's job (see scripts/demo_signal_scoring.py for
Breakout+Retest's mapping) — this module never reads a DataFrame or
knows a strategy's column-naming convention, so it stays reusable as
strategies 2-4 get built with different engines composed differently.

Building this does NOT retroactively change how Breakout+Retest's
entry_signal is computed (Phase 4) — that strategy keeps its own hard
AND-gated logic, already evaluated and rejected on real evidence (Phase
6). This module is demonstrated against its real historical signals for
illustration, not as a fix or a re-evaluation.
"""

from dataclasses import dataclass, field

import pandas as pd

VOLUME_TIERS = [(3.0, 1.0), (2.0, 0.8), (1.5, 0.6), (1.2, 0.4), (1.0, 0.2)]
RISK_REWARD_TIERS = [(3.0, 1.0), (2.5, 0.85), (2.0, 0.70), (1.5, 0.50), (1.0, 0.25)]


@dataclass
class ScoringWeights:
    market_structure: float = 25.0
    price_action: float = 25.0
    volume: float = 20.0
    liquidity: float = 15.0
    risk_reward: float = 15.0

    @property
    def total(self) -> float:
        return (self.market_structure + self.price_action + self.volume +
                self.liquidity + self.risk_reward)


DEFAULT_WEIGHTS = ScoringWeights()


@dataclass
class SignalInputs:
    symbol: str
    side: str                     # "long" | "short"
    setup_label: str              # e.g. "Breakout + Retest"
    trend_state: str              # market_structure.trend_state: "up"|"down"|"transition"|"undefined"
    breakout_in_direction: bool
    confirming_candle: bool       # a strong or rejection candle supporting the direction
    relative_volume: float
    liquidity_sweep: bool
    equal_level: bool             # equal highs/lows at the relevant level (weaker liquidity signal)
    entry: float
    stop: float
    target: float


@dataclass
class SignalScore:
    symbol: str
    side: str
    setup_label: str
    trend_state: str
    relative_volume: float
    liquidity_sweep: bool
    r_multiple: float
    component_scores: dict
    weights: ScoringWeights

    @property
    def total_score(self) -> float:
        return round(sum(self.component_scores.values()), 1)

    @property
    def max_score(self) -> float:
        return round(self.weights.total, 1)

    def explain(self) -> str:
        """Formatted to match the architecture spec §14 worked example
        exactly, so a printed SignalScore reads the same way the spec's
        own illustration does."""
        structure_label = {"up": "Bullish", "down": "Bearish",
                            "transition": "Transition", "undefined": "Undefined"}.get(self.trend_state, "Unknown")
        rel_vol_str = f"{self.relative_volume:.1f}x" if pd.notna(self.relative_volume) else "n/a"
        rr_str = f"{self.r_multiple:.1f}R" if pd.notna(self.r_multiple) else "n/a"
        lines = [
            f"{self.symbol} {self.side.upper()}",
            f"Structure: {structure_label}",
            f"Setup: {self.setup_label}",
            f"Relative Volume: {rel_vol_str}",
            f"Liquidity Sweep: {'Yes' if self.liquidity_sweep else 'No'}",
            f"Risk/Reward: {rr_str}",
            f"Score: {self.total_score:.0f}/{self.max_score:.0f}",
        ]
        return "\n".join(lines)


def _tiered_fraction(value: float, tiers: list[tuple[float, float]]) -> float:
    """tiers sorted descending by threshold. Returns the fraction for the
    highest threshold `value` clears, 0.0 if it clears none."""
    if value is None or pd.isna(value):
        return 0.0
    for threshold, fraction in tiers:
        if value >= threshold:
            return fraction
    return 0.0


def market_structure_score(trend_state: str, side: str, weight: float) -> float:
    target_state = "up" if side == "long" else "down"
    if trend_state == target_state:
        return weight
    if trend_state == "transition":
        return weight * 0.5
    return 0.0


def price_action_score(breakout_in_direction: bool, confirming_candle: bool, weight: float) -> float:
    score = 0.0
    if breakout_in_direction:
        score += weight * 0.5
    if confirming_candle:
        score += weight * 0.5
    return score


def volume_score(relative_volume: float, weight: float) -> float:
    return weight * _tiered_fraction(relative_volume, VOLUME_TIERS)


def liquidity_score(sweep_reversal: bool, equal_level: bool, weight: float) -> float:
    if sweep_reversal:
        return weight
    if equal_level:
        return weight * 0.5
    return 0.0


def risk_reward_multiple(entry: float, stop: float, target: float) -> float:
    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return 0.0
    return abs(target - entry) / stop_dist


def risk_reward_score(r_multiple: float, weight: float) -> float:
    return weight * _tiered_fraction(r_multiple, RISK_REWARD_TIERS)


def score_signal(inputs: SignalInputs, weights: ScoringWeights = DEFAULT_WEIGHTS) -> SignalScore:
    r = risk_reward_multiple(inputs.entry, inputs.stop, inputs.target)
    components = {
        "market_structure": round(market_structure_score(inputs.trend_state, inputs.side,
                                                           weights.market_structure), 2),
        "price_action": round(price_action_score(inputs.breakout_in_direction, inputs.confirming_candle,
                                                   weights.price_action), 2),
        "volume": round(volume_score(inputs.relative_volume, weights.volume), 2),
        "liquidity": round(liquidity_score(inputs.liquidity_sweep, inputs.equal_level,
                                            weights.liquidity), 2),
        "risk_reward": round(risk_reward_score(r, weights.risk_reward), 2),
    }
    return SignalScore(
        symbol=inputs.symbol, side=inputs.side, setup_label=inputs.setup_label,
        trend_state=inputs.trend_state, relative_volume=inputs.relative_volume,
        liquidity_sweep=inputs.liquidity_sweep, r_multiple=round(r, 3),
        component_scores=components, weights=weights,
    )
