"""
Exit Rules — the position-management state machine from the user's
`exit_rules_spec.md` ("Exit Rules Spec — Daily Timeframe Swing/Position
Trades"), implemented exactly as ordered in that document. Each of the
5 rules is its own discrete function per the spec's own "Implementation
note", called in sequence by `backtest/exit_rules_engine.py`.

Two operational choices made where the spec explicitly flags ambiguity
("flag if encountered, do not guess" / confirmed by the user before
implementation began):

- **ATR-trailing addition (spec's "ADDITION" section)**: user confirmed
  build BOTH — the original flat +6% lock above +12% profit, and the
  ATR-trailing alternative — as a config toggle
  (`enable_atr_trailing_above_lock`), so every strategy retested gets
  run through both and the two are compared, not one silently chosen.
- **"Moved sideways/against thesis" (rule 2, time stop)** has no numeric
  definition in the spec. Operationalized here as "hasn't yet reached
  the rule-1 breakeven-ratchet trigger (+4% by default)" — reusing an
  already-defined threshold from elsewhere in the SAME spec rather than
  inventing a new, unrelated number. Exposed as its own config field
  (`progress_threshold_pct`) so it can be changed independently if this
  reading turns out wrong.
- **Rule 3's 20-30% partial-take fraction** is implemented as a fixed
  25% (the range's midpoint) rather than left unautomated, since the
  spec lists it as one of the 5 numbered rules to implement, not purely
  discretionary color commentary (unlike rule 1's 3%-vs-5% stop choice,
  which the spec explicitly defaults away from — "otherwise default to
  5% always" — so 5% is used unconditionally here too).
- **Rule 4/5 re-triggering**: rule 4 ("sell 50% of remaining position")
  can fire more than once over a trade's life if price reclaims EMA(8)
  after a prior rule-4 trigger and later closes below it again — treated
  as a fresh rule-4 event each time, since the spec doesn't say
  otherwise and "protect a winner from round-tripping" reads as an
  ongoing behavior, not a one-shot. Rule 5 ("failed reclaim / EMA(4)x
  EMA(8) cross") is only checked on days immediately following an ACTIVE
  (not yet reclaimed) rule-4 trigger, matching "only relevant to the
  remaining position after rule 4 has fired."

Fill timing: rule 1 (hard stop) fills IMMEDIATELY within the bar it's
breached, at the stop price itself — matching every other stop mechanism
already in this project (atr/structure methods in backtest/engine.py)
and the spec's own explicit "INTRABAR, immediate... do not wait for the
daily close" instruction. Rules 2-5 are detected on a bar's CLOSE but
filled at the NEXT bar's OPEN — the spec doesn't specify fill mechanics
at this granularity, but this matches the SAME next-bar-open discipline
already used everywhere else in this project for close-based signals
(see backtest/engine.py's `trailing_indicator`/`signal_exit` methods) —
you cannot realistically fill at the exact close of the bar whose close
just triggered the decision.
"""

from dataclasses import dataclass

import pandas as pd

DEFAULT_INITIAL_STOP_PCT = 5.0
DEFAULT_BREAKEVEN_TRIGGER_PCT = 4.0
DEFAULT_LOCK_TRIGGER_PCT = 12.0
DEFAULT_LOCK_PCT = 6.0
DEFAULT_TIME_STOP_TIGHTEN_DAYS = 5
DEFAULT_TIME_STOP_TIGHTEN_PCT = 3.0
DEFAULT_TIME_STOP_EXIT_DAYS = 6
DEFAULT_PROGRESS_THRESHOLD_PCT = 4.0
DEFAULT_PARTIAL_PROFIT_TRIGGER_PCT = 20.0
DEFAULT_PARTIAL_PROFIT_FRACTION = 0.25
DEFAULT_EMA_FAST = 4
DEFAULT_EMA_SLOW = 8
DEFAULT_ATR_TRAILING_MULT = 2.5
DEFAULT_ATR_COL = "vlt_atr"


@dataclass
class ExitRulesConfig:
    initial_stop_pct: float = DEFAULT_INITIAL_STOP_PCT
    breakeven_trigger_pct: float = DEFAULT_BREAKEVEN_TRIGGER_PCT
    lock_trigger_pct: float = DEFAULT_LOCK_TRIGGER_PCT
    lock_pct: float = DEFAULT_LOCK_PCT
    time_stop_tighten_days: int = DEFAULT_TIME_STOP_TIGHTEN_DAYS
    time_stop_tighten_pct: float = DEFAULT_TIME_STOP_TIGHTEN_PCT
    time_stop_exit_days: int = DEFAULT_TIME_STOP_EXIT_DAYS
    progress_threshold_pct: float = DEFAULT_PROGRESS_THRESHOLD_PCT
    partial_profit_trigger_pct: float = DEFAULT_PARTIAL_PROFIT_TRIGGER_PCT
    partial_profit_fraction: float = DEFAULT_PARTIAL_PROFIT_FRACTION
    ema_fast_period: int = DEFAULT_EMA_FAST
    ema_slow_period: int = DEFAULT_EMA_SLOW
    ema_fast_col: str = "exit_ema_fast"
    ema_slow_col: str = "exit_ema_slow"
    enable_atr_trailing_above_lock: bool = False
    atr_trailing_mult: float = DEFAULT_ATR_TRAILING_MULT
    atr_col: str = DEFAULT_ATR_COL


def attach_exit_indicators(df: pd.DataFrame, cfg: ExitRulesConfig) -> pd.DataFrame:
    """Adds the EMA(4)/EMA(8) columns rules 4-5 need, computed on close
    price (standard EMA, already-tested `engines.moving_averages.ema`).
    Callers must attach this to a strategy's own signal_fn output BEFORE
    handing it to run_walk_forward, same as any other engine — the exit
    rules engine itself only ever reads pre-computed columns, it doesn't
    compute indicators, matching this project's separation between
    engines and the backtest loop."""
    from cryptobot.engines.moving_averages import ema
    d = df.copy()
    d[cfg.ema_fast_col] = ema(d["close"], cfg.ema_fast_period)
    d[cfg.ema_slow_col] = ema(d["close"], cfg.ema_slow_period)
    return d


@dataclass
class ExitAction:
    kind: str          # "full" | "partial"
    reason: str
    fraction: float = 1.0  # of the CURRENT remaining size


def initial_stop_price(entry_price: float, side: str, cfg: ExitRulesConfig) -> float:
    pct = cfg.initial_stop_pct / 100
    return entry_price * (1 - pct) if side == "long" else entry_price * (1 + pct)


def profit_pct(entry_price: float, price: float, side: str) -> float:
    if side == "long":
        return (price - entry_price) / entry_price * 100
    return (entry_price - price) / entry_price * 100


def check_hard_stop(position: dict, bar: pd.Series) -> ExitAction | None:
    """Rule 1 — INTRABAR, immediate, always checked first. Uses the
    bar's own low/high (this project's existing convention for "did
    price touch this level during the bar", the same check every other
    stop mechanism in backtest/engine.py already uses)."""
    hit = (bar["low"] <= position["stop"]) if position["side"] == "long" else (bar["high"] >= position["stop"])
    return ExitAction(kind="full", reason="hard_stop") if hit else None


def update_ratchet_and_time_tighten(position: dict, bar: pd.Series, cfg: ExitRulesConfig) -> None:
    """Rule 1's ratchet tiers (breakeven at +4%, lock at +12% - flat +6%
    or the ATR-trailing alternative) plus rule 2's day-5 stop-tightening
    half (not an exit - just moves the stop). Mutates `position` in
    place: `stop` (only ever moves in the favorable direction - checked
    via max/min, never loosens) and `highest_favorable_price` (the
    running extreme since entry, used by the ATR-trailing variant)."""
    price = bar["close"]
    side = position["side"]
    p = profit_pct(position["entry"], price, side)

    if side == "long":
        position["highest_favorable_price"] = max(position["highest_favorable_price"], bar["high"])
    else:
        position["highest_favorable_price"] = min(position["highest_favorable_price"], bar["low"])

    if p >= cfg.lock_trigger_pct:
        if cfg.enable_atr_trailing_above_lock:
            atr = bar.get(cfg.atr_col)
            if atr is not None and pd.notna(atr) and atr > 0:
                if side == "long":
                    candidate = position["highest_favorable_price"] - cfg.atr_trailing_mult * atr
                    position["stop"] = max(position["stop"], candidate)
                else:
                    candidate = position["highest_favorable_price"] + cfg.atr_trailing_mult * atr
                    position["stop"] = min(position["stop"], candidate)
        else:
            lock_price = (position["entry"] * (1 + cfg.lock_pct / 100) if side == "long"
                          else position["entry"] * (1 - cfg.lock_pct / 100))
            position["stop"] = max(position["stop"], lock_price) if side == "long" else min(position["stop"], lock_price)
    elif p >= cfg.breakeven_trigger_pct:
        position["stop"] = max(position["stop"], position["entry"]) if side == "long" else min(position["stop"], position["entry"])

    if position["days_in_trade"] == cfg.time_stop_tighten_days and not position["time_stop_tightened"]:
        if p < cfg.progress_threshold_pct:
            tighten_price = (position["entry"] * (1 - cfg.time_stop_tighten_pct / 100) if side == "long"
                              else position["entry"] * (1 + cfg.time_stop_tighten_pct / 100))
            position["stop"] = max(position["stop"], tighten_price) if side == "long" else min(position["stop"], tighten_price)
        position["time_stop_tightened"] = True


def check_time_stop_exit(position: dict, bar: pd.Series, cfg: ExitRulesConfig) -> ExitAction | None:
    """Rule 2's exit-trigger half: "hasn't moved per expectations" after
    the configured window (default 6 days) -> full exit allowed."""
    p = profit_pct(position["entry"], bar["close"], position["side"])
    if position["days_in_trade"] >= cfg.time_stop_exit_days and p < cfg.progress_threshold_pct:
        return ExitAction(kind="full", reason="time_stop")
    return None


def check_partial_profit_take(position: dict, bar: pd.Series, cfg: ExitRulesConfig) -> ExitAction | None:
    """Rule 3 — one-time, non-exit-triggering partial take once
    unrealized gain first reaches the trigger (+20% default)."""
    if position["partial_profit_taken"]:
        return None
    p = profit_pct(position["entry"], bar["close"], position["side"])
    if p >= cfg.partial_profit_trigger_pct:
        position["partial_profit_taken"] = True
        return ExitAction(kind="partial", reason="partial_profit_take", fraction=cfg.partial_profit_fraction)
    return None


def check_ema8_derisk(position: dict, bar: pd.Series, ema_fast_col: str, ema_slow_col: str,
                       cfg: ExitRulesConfig) -> ExitAction | None:
    """Rule 4 — only checked while NOT already watching for rule 5 (i.e.
    not currently in an active, unreclaimed rule-4 state). Close beyond
    EMA(8) against the position -> sell 50% of what remains, and start
    watching for rule 5."""
    if position["rule4_active"]:
        return None
    slow = bar.get(ema_slow_col)
    if slow is None or pd.isna(slow):
        return None
    broke = (bar["close"] < slow) if position["side"] == "long" else (bar["close"] > slow)
    if broke:
        position["rule4_active"] = True
        return ExitAction(kind="partial", reason="ema8_derisk", fraction=0.5)
    return None


def check_ema_failed_reclaim(position: dict, bar: pd.Series, prev_bar: pd.Series,
                              ema_fast_col: str, ema_slow_col: str, cfg: ExitRulesConfig) -> ExitAction | None:
    """Rule 5 — only relevant while `rule4_active` (a rule-4 trigger is
    still unresolved). Exits the remainder if price fails to reclaim
    EMA(8) the day after a rule-4 trigger, OR EMA(4) crosses below (long)
    / above (short) EMA(8). A successful reclaim resets `rule4_active`
    to False - a LATER close back below EMA(8) is then treated as a
    fresh rule-4 event, not an immediate rule-5 exit (see module
    docstring)."""
    if not position["rule4_active"]:
        return None
    slow = bar.get(ema_slow_col)
    fast = bar.get(ema_fast_col)
    prev_slow = prev_bar.get(ema_slow_col) if prev_bar is not None else None
    prev_fast = prev_bar.get(ema_fast_col) if prev_bar is not None else None
    if slow is None or pd.isna(slow) or fast is None or pd.isna(fast):
        return None

    side = position["side"]
    reclaimed = (bar["close"] > slow) if side == "long" else (bar["close"] < slow)

    cross_against = False
    if prev_fast is not None and prev_slow is not None and pd.notna(prev_fast) and pd.notna(prev_slow):
        if side == "long":
            cross_against = (fast < slow) and (prev_fast >= prev_slow)
        else:
            cross_against = (fast > slow) and (prev_fast <= prev_slow)

    if not reclaimed or cross_against:
        return ExitAction(kind="full", reason="ema_failed_reclaim_or_cross")

    position["rule4_active"] = False
    return None
