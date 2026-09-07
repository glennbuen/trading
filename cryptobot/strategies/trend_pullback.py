"""
Strategy C: Trend Pullback (architecture spec §10).

Sequence:
  1. Established trend     — market_structure.trend_state == 'up' (long) /
                              'down' (short) at the moment of the impulse.
  2. Strong impulse         — a strong candle (price_action.is_strong_bullish
                              /bearish) IN the trend direction, anchoring a
                              new episode (episode_id = cumsum(event), the
                              same technique used in Breakout+Retest).
  3. Controlled retracement + 4. Structure preservation — the worst point
                              (lowest low for an uptrend, highest high for
                              a downtrend) reached since the impulse must
                              stay on the healthy side of the confirmed
                              swing level as it stood just BEFORE the
                              impulse (`.shift(1)`, the same "level fixed
                              at the moment of the triggering event"
                              convention used throughout this project's
                              other multi-bar patterns). Once violated it
                              stays violated for the rest of the episode —
                              falls out naturally from cummin/cummax, no
                              extra bookkeeping needed.
  5. Pullback volume contraction — at least one bar after the impulse
                              shows below-average volume
                              (volume.is_volume_contraction) — the
                              "healthy, low-conviction pullback" read
                              this repo's earlier standalone bots'
                              comments referenced (Wyckoff/Darvas
                              effort-vs-result), made concrete and
                              testable here.
  6. Continuation confirmation + 7. Volume expansion — price closes
                              beyond the highest (long) / lowest (short)
                              point reached since the impulse — the trend
                              has actually resumed, not just "hasn't
                              broken down yet" — WITH volume expansion
                              again.

Same vectorized episode-scan technique as Breakout+Retest
(groupby(episode_id).cummax()/.cumsum(), all backward-only) rather than a
bar-by-bar loop. No lookahead: every engine column consumed here is
already lookahead-safe in its own module (docs/ARCHITECTURE.md); this
module adds no new temporal decisions, only sequencing over already-safe
columns.
"""

import pandas as pd

from cryptobot.utils import bars_since
from cryptobot.engines import market_structure as ms
from cryptobot.engines import price_action as pa
from cryptobot.engines import volume as vol

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_VOLUME_LOOKBACK = vol.DEFAULT_LOOKBACK
DEFAULT_EXPANSION_THRESHOLD = vol.DEFAULT_EXPANSION_THRESHOLD
DEFAULT_CONTRACTION_THRESHOLD = vol.DEFAULT_CONTRACTION_THRESHOLD


def _scan_one_direction(df: pd.DataFrame, impulse_event: pd.Series, structure_level: pd.Series,
                         extreme_col: pd.Series, pullback_col: pd.Series, trend_up: bool,
                         volume_lookback: int, expansion_threshold: float,
                         contraction_threshold: float) -> pd.DataFrame:
    episode_id = impulse_event.cumsum()
    in_episode = episode_id > 0

    level_at_impulse = structure_level.shift(1).where(impulse_event).ffill()

    if trend_up:
        pullback_extreme_so_far = pullback_col.groupby(episode_id).cummin()
        structure_preserved = (pullback_extreme_so_far > level_at_impulse) & in_episode
        prior_extreme = extreme_col.groupby(episode_id).cummax().shift(1)
        continuation = df["close"] > prior_extreme
    else:
        pullback_extreme_so_far = pullback_col.groupby(episode_id).cummax()
        structure_preserved = (pullback_extreme_so_far < level_at_impulse) & in_episode
        prior_extreme = extreme_col.groupby(episode_id).cummin().shift(1)
        continuation = df["close"] < prior_extreme

    since_impulse = bars_since(impulse_event)
    contraction = vol.is_volume_contraction(df, volume_lookback, contraction_threshold)
    contraction_seen = (contraction & (since_impulse >= 1)).groupby(episode_id).cummax().astype(bool)

    expansion_confirm = vol.is_volume_expansion(df, volume_lookback, expansion_threshold)

    confirmation_raw = (structure_preserved & contraction_seen & continuation &
                        expansion_confirm & in_episode)
    is_first_in_episode = confirmation_raw.groupby(episode_id).cumsum() == 1
    entry_signal = confirmation_raw & is_first_in_episode

    result = pd.DataFrame(index=df.index)
    result["episode_id"] = episode_id
    result["impulse_event"] = impulse_event
    result["structure_level"] = level_at_impulse
    result["structure_preserved"] = structure_preserved
    result["contraction_seen"] = contraction_seen
    result["entry_signal"] = entry_signal
    return result


def scan_trend_pullback_bullish(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                                 structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                                 volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                                 expansion_threshold: float = DEFAULT_EXPANSION_THRESHOLD,
                                 contraction_threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.DataFrame:
    trend = ms.trend_state(df, structure_left, structure_right)
    impulse_event = pa.is_strong_bullish(df) & (trend == "up")
    structure_level = ms.support(df, structure_left, structure_right)
    return _scan_one_direction(df, impulse_event, structure_level, extreme_col=df["high"],
                                pullback_col=df["low"], trend_up=True,
                                volume_lookback=volume_lookback,
                                expansion_threshold=expansion_threshold,
                                contraction_threshold=contraction_threshold)


def scan_trend_pullback_bearish(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                                 structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                                 volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                                 expansion_threshold: float = DEFAULT_EXPANSION_THRESHOLD,
                                 contraction_threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.DataFrame:
    trend = ms.trend_state(df, structure_left, structure_right)
    impulse_event = pa.is_strong_bearish(df) & (trend == "down")
    structure_level = ms.resistance(df, structure_left, structure_right)
    return _scan_one_direction(df, impulse_event, structure_level, extreme_col=df["low"],
                                pullback_col=df["high"], trend_up=False,
                                volume_lookback=volume_lookback,
                                expansion_threshold=expansion_threshold,
                                contraction_threshold=contraction_threshold)


def compute_trend_pullback(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                            structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                            volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                            expansion_threshold: float = DEFAULT_EXPANSION_THRESHOLD,
                            contraction_threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.DataFrame:
    """Convenience: both directions attached to a copy of df, prefixed
    tp_long_ / tp_short_ (same convention as compute_breakout_retest)."""
    d = df.copy()
    kwargs = dict(structure_left=structure_left, structure_right=structure_right,
                  volume_lookback=volume_lookback, expansion_threshold=expansion_threshold,
                  contraction_threshold=contraction_threshold)
    long_result = scan_trend_pullback_bullish(df, **kwargs)
    short_result = scan_trend_pullback_bearish(df, **kwargs)
    for col in long_result.columns:
        d[f"tp_long_{col}"] = long_result[col]
    for col in short_result.columns:
        d[f"tp_short_{col}"] = short_result[col]
    return d
