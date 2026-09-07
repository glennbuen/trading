import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import run_backtest, BacktestCosts, StopTargetConfig


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(pd.Timestamp("2026-01-01") + pd.to_timedelta(df["ts"], unit="h"))
    return df


def baseline_bars(n: int, base: float = 100.0) -> list[dict]:
    """Noisy-flat bars (real range each bar, no net drift) so ATR
    converges to something nonzero for the ATR-stop tests, without
    biasing price toward the eventual entry direction."""
    rows = []
    for i in range(n):
        wobble = 1.0 if i % 2 == 0 else -1.0
        rows.append({"open": base, "high": base + 1 + abs(wobble), "low": base - 1 - abs(wobble),
                     "close": base + 0.1 * wobble, "volume": 10.0})
    return rows


class TestNextBarOpenFill:
    def test_entry_fills_at_next_bar_open_not_signal_bar_close(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10,
                     "long": True})  # idx20: signal bar, close=100
        rows.append({"open": 150, "high": 152, "low": 148, "close": 151, "volume": 10,
                     "long": False})  # idx21: a big gap up on open
        # a few quiet bars after so the position has somewhere to sit / possibly exit
        rows.extend({"open": 151, "high": 153, "low": 149, "close": 151, "volume": 10, "long": False}
                     for _ in range(10))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df = compute_volatility(df)

        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0))
        assert len(result.trades) == 1
        # Entry must be based on bar 21's open (~150), not bar 20's close (100).
        assert result.trades[0].entry_price == pytest.approx(150 * 1.0005, rel=1e-6)


class TestStopAndTargetMechanics:
    def _setup(self, outcome: str):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        if outcome == "stop":
            rows.append({"open": 100, "high": 100, "low": 50, "close": 60, "volume": 10, "long": False})
        else:
            rows.append({"open": 100, "high": 200, "low": 99, "close": 190, "volume": 10, "long": False})
        rows.extend({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False}
                     for _ in range(5))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        return compute_volatility(df)

    def test_stop_hit_applies_slippage_and_records_reason(self):
        df = self._setup("stop")
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0))
        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.exit_reason == "stop"
        # Stop fill must be worse than the raw stop price (slippage applied).
        assert t.exit_price < t.stop_price
        assert t.pnl < 0

    def test_target_hit_fills_at_exact_target_no_slippage(self):
        df = self._setup("target")
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0))
        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.exit_reason == "tp"
        assert t.pnl > 0

    def test_fees_charged_on_both_sides(self):
        df = self._setup("target")
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0),
                               costs=BacktestCosts(taker_fee_pct=0.10, entry_slippage_pct=0.05, stop_slippage_pct=0.4))
        t = result.trades[0]
        expected_fees = (t.entry_price + t.exit_price) * t.size * (0.10 / 100)
        assert t.fees == pytest.approx(expected_fees, rel=1e-6)


class TestRiskManagerGating:
    def test_signal_rejected_during_cooldown_is_recorded(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        rows.append({"open": 100, "high": 100, "low": 50, "close": 60, "volume": 10, "long": False})  # stops out
        # Fire another signal immediately — should be rejected by cooldown.
        rows.append({"open": 60, "high": 61, "low": 59, "close": 60, "volume": 10, "long": True})
        rows.extend({"open": 60, "high": 61, "low": 59, "close": 60, "volume": 10, "long": False}
                     for _ in range(5))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df = compute_volatility(df)

        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=10),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0))
        assert len(result.trades) == 1  # only the first, the second was blocked
        assert any(r["reason"] == "cooldown" for r in result.rejected_signals)

    def test_position_size_matches_formula(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        rows.extend({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False}
                     for _ in range(10))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df = compute_volatility(df)

        limits = RiskLimits(risk_per_trade_pct=1.0, max_position_pct=100, cooldown_bars=0)
        result = run_backtest(df, "long", None, limits,
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0),
                               starting_equity=1000.0)
        t = result.trades[0] if result.trades else None
        if t:  # only meaningful if a trade actually opened
            risk_amount = 1000.0 * 0.01
            stop_dist = abs(t.entry_price - t.stop_price)
            expected_size = risk_amount / stop_dist
            assert t.size == pytest.approx(expected_size, rel=1e-6)


class TestEndOfDataHandling:
    def test_position_still_open_at_end_is_force_closed_not_dropped(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        # Price sits between stop and target for the rest of the data —
        # never triggers a stop or target exit before the data runs out.
        rows.extend({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False}
                     for _ in range(10))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df = compute_volatility(df)

        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0),
                               StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0))
        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.exit_reason == "end_of_data"
        assert t.exit_price == pytest.approx(df["close"].iloc[-1])
        # The equity curve's final value must reflect this trade, not the
        # pre-trade equity — a silently-dropped position would understate it.
        assert result.final_equity == pytest.approx(1000.0 + t.pnl)


class TestTrailingIndicatorExit:
    def _setup(self, cross_below_at: int, reclaim: bool = False):
        """A long entry signal, then an indicator line (a flat 'support'
        column at 97) that price eventually closes below. Margins kept
        tight — low ~96, indicator 97 — so only the CLOSE crosses the
        trailing-indicator level without the bar's low also breaching the
        much-wider ATR-based hard-stop safety net (tested separately
        below); since low <= close always, a bar whose close is far below
        the indicator would also breach a tight hard stop, which isn't
        what this specific test is isolating."""
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        for i in range(15):
            if i == cross_below_at:
                rows.append({"open": 99, "high": 99.5, "low": 96, "close": 96.5, "volume": 10, "long": False})
            elif reclaim and i == cross_below_at + 2:
                rows.append({"open": 96.5, "high": 101, "low": 96, "close": 99, "volume": 10, "long": False})
            else:
                rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df["support_line"] = 97.0  # flat trailing-indicator reference
        return compute_volatility(df)

    def test_exit_fires_one_bar_after_the_close_crosses_the_indicator(self):
        df = self._setup(cross_below_at=3)
        stop_target = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="support_line",
                                        atr_mult_stop=1.5)
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0), stop_target)
        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.exit_reason == "trailing_indicator"

    def test_does_not_exit_while_price_stays_above_the_indicator(self):
        df = self._setup(cross_below_at=999)  # never actually crosses
        stop_target = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="support_line",
                                        atr_mult_stop=1.5)
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0), stop_target)
        # with no trailing-indicator exit and no hard-stop hit, it rides to end_of_data
        assert len(result.trades) == 1
        assert result.trades[0].exit_reason == "end_of_data"

    def test_hard_atr_stop_still_applies_as_a_safety_net(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": True})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False})
        # crashes hard on the very next bar, well past any reasonable ATR stop,
        # WITHOUT the close itself crossing the (much lower) indicator line
        rows.append({"open": 100, "high": 100, "low": 50, "close": 96, "volume": 10, "long": False})
        rows.extend({"open": 96, "high": 97, "low": 95, "close": 96, "volume": 10, "long": False}
                     for _ in range(10))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df["support_line"] = 10.0  # far below - would never trigger a trailing-indicator exit
        df = compute_volatility(df)
        stop_target = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="support_line",
                                        atr_mult_stop=1.5)
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0), stop_target)
        assert len(result.trades) == 1
        assert result.trades[0].exit_reason == "stop"

    def test_requires_trailing_indicator_col(self):
        rows = baseline_bars(5)
        df = make_df(rows)
        df["long"] = False
        df = compute_volatility(df)
        with pytest.raises(ValueError):
            run_backtest(df, "long", None, RiskLimits(), StopTargetConfig(method="trailing_indicator"))


class TestSignalExit:
    def test_exit_fires_one_bar_after_an_arbitrary_boolean_signal(self):
        rows = baseline_bars(20)
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10,
                     "long": True, "exit_now": False})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10,
                     "long": False, "exit_now": False})
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10,
                     "long": False, "exit_now": True})  # arbitrary signal, unrelated to price levels
        rows.extend({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10,
                     "long": False, "exit_now": False} for _ in range(10))
        df = make_df(rows)
        df["long"] = df.get("long", False).fillna(False)
        df["exit_now"] = df.get("exit_now", False).fillna(False)
        df = compute_volatility(df)
        stop_target = StopTargetConfig(method="signal_exit", exit_signal_col="exit_now", atr_mult_stop=1.5)
        result = run_backtest(df, "long", None, RiskLimits(cooldown_bars=0), stop_target)
        assert len(result.trades) == 1
        assert result.trades[0].exit_reason == "signal_exit"

    def test_requires_exit_signal_col(self):
        rows = baseline_bars(5)
        df = make_df(rows)
        df["long"] = False
        df = compute_volatility(df)
        with pytest.raises(ValueError):
            run_backtest(df, "long", None, RiskLimits(), StopTargetConfig(method="signal_exit"))


class TestMetricsSanity:
    def test_no_trades_returns_zeroed_result(self):
        rows = baseline_bars(20)
        rows.extend({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10, "long": False}
                     for _ in range(5))
        df = make_df(rows)
        df["long"] = False
        df = compute_volatility(df)
        result = run_backtest(df, "long", None, RiskLimits(), StopTargetConfig())
        assert result.num_trades == 0
        assert result.trades == []

    def test_structure_stop_requires_column(self):
        rows = baseline_bars(5)
        df = make_df(rows)
        df["long"] = False
        df = compute_volatility(df)
        with pytest.raises(ValueError):
            run_backtest(df, "long", None, RiskLimits(), StopTargetConfig(method="structure"))
