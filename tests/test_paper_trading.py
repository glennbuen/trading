"""
Tests for cryptobot/paper_trading/ — the incremental live-decision
engine. Uses hand-built single-row/few-row "signal_df" fixtures (this
module doesn't compute indicators itself, it just consumes whatever
compute_* already produced) plus a fake clock (`now_ms`) to control
which bar counts as "closed".
"""

import json

import pandas as pd
import pytest

from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig, BacktestCosts
from cryptobot.paper_trading.state import PaperTradingState, PaperPosition, load_state, save_state
from cryptobot.paper_trading.engine import latest_closed_bar, check_and_update
from cryptobot.paper_trading.risk_bridge import snapshot_risk_manager, restore_risk_manager
from cryptobot.risk.risk_manager import RiskManager

TF_MS = 86_400_000  # 1d
DAY0 = pd.Timestamp("2026-01-01", tz="UTC")


def make_bars(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = [int((DAY0 + pd.Timedelta(days=i)).timestamp() * 1000) for i in range(len(df))]
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


def base_bar(close=100.0, alma=95.0, atr=5.0, long_signal=False):
    return {"open": close, "high": close + 1, "low": close - 1, "close": close,
            "volume": 10.0, "tita_alma": alma, "vlt_atr": atr, "long_signal": long_signal}


class TestLatestClosedBar:
    def test_excludes_still_forming_candle(self):
        df = make_bars([base_bar(), base_bar(), base_bar()])
        now_ms = int(df["ts"].iloc[-1]) + 1000  # "now" is only 1s after the last candle opened
        bar = latest_closed_bar(df, TF_MS, now_ms)
        assert bar is not None
        assert bar["ts"] == df["ts"].iloc[-2]  # second-to-last is the last CLOSED one

    def test_returns_none_if_nothing_has_closed_yet(self):
        df = make_bars([base_bar()])
        now_ms = int(df["ts"].iloc[0]) + 1000
        assert latest_closed_bar(df, TF_MS, now_ms) is None


class TestEntryAndExit:
    def _stop_target(self):
        return StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma",
                                 atr_mult_stop=1.5)

    def _now_after(self, df):
        return int(df["ts"].iloc[-1]) + TF_MS  # last bar itself just closed

    def test_opens_a_position_on_a_fresh_long_signal(self):
        df = make_bars([base_bar(), base_bar(long_signal=True, close=100, alma=95, atr=5)])
        state = PaperTradingState(symbol="BTC/USDT", strategy="tita", starting_equity=1000.0)
        result = check_and_update(state, df, TF_MS, self._now_after(df), "long_signal", None,
                                   self._stop_target(), RiskLimits(cooldown_bars=0),
                                   live_price=100.5, live_dt=DAY0 + pd.Timedelta(days=2))
        assert result["action"] == "entered"
        assert state.position is not None
        assert state.position.side == "long"
        # stop = entry - max(|entry-structure|, atr*1.5); no structure col here -> atr floor = 5*1.5=7.5
        assert state.position.stop == pytest.approx(100.5 * 1.0005 - 7.5, rel=1e-3)

    def test_no_entry_without_a_signal(self):
        df = make_bars([base_bar(), base_bar(long_signal=False)])
        state = PaperTradingState(symbol="BTC/USDT", strategy="tita", starting_equity=1000.0)
        result = check_and_update(state, df, TF_MS, self._now_after(df), "long_signal", None,
                                   self._stop_target(), RiskLimits(), live_price=100.5,
                                   live_dt=DAY0 + pd.Timedelta(days=2))
        assert result["action"] == "none"
        assert state.position is None

    def test_hard_stop_hit_closes_immediately_at_stop_price(self):
        state = PaperTradingState(
            symbol="BTC/USDT", strategy="tita", starting_equity=1000.0,
            position=PaperPosition(side="long", entry_price=100.0, entry_dt=str(DAY0),
                                    entry_bar_index=1, stop=90.0, tp=None, size=1.0,
                                    risk_amount=10.0, notional_pct=10.0),
        )
        df = make_bars([base_bar(close=85, alma=95, atr=5)])  # low = 84, below stop=90
        result = check_and_update(state, df, TF_MS, self._now_after(df), "long_signal", None,
                                   self._stop_target(), RiskLimits(), live_price=85.0,
                                   live_dt=DAY0 + pd.Timedelta(days=1))
        assert result["action"] == "exited"
        assert state.position is None
        assert len(state.trades) == 1
        assert state.trades[0].exit_reason == "stop"
        assert state.trades[0].exit_price == pytest.approx(90.0 * (1 - 0.4 / 100), rel=1e-3)

    def test_trailing_indicator_cross_sets_pending_then_fills_next_check(self):
        state = PaperTradingState(
            symbol="BTC/USDT", strategy="tita", starting_equity=1000.0,
            position=PaperPosition(side="long", entry_price=100.0, entry_dt=str(DAY0),
                                    entry_bar_index=1, stop=80.0, tp=None, size=1.0,
                                    risk_amount=10.0, notional_pct=10.0),
        )
        # close (96) crosses below ALMA (98), but stays well above the hard stop (80)
        df = make_bars([base_bar(close=96, alma=98, atr=5)])
        r1 = check_and_update(state, df, TF_MS, self._now_after(df), "long_signal", None,
                               self._stop_target(), RiskLimits(), live_price=96.0,
                               live_dt=DAY0 + pd.Timedelta(days=1))
        assert r1["action"] == "none"  # cross detected, but fill deferred to next check
        assert state.position is not None
        assert state.position.pending_exit is True

        df2 = make_bars([base_bar(close=96, alma=98, atr=5), base_bar(close=95, alma=97, atr=5)])
        now2 = int(df2["ts"].iloc[-1]) + TF_MS
        r2 = check_and_update(state, df2, TF_MS, now2, "long_signal", None,
                               self._stop_target(), RiskLimits(), live_price=95.0,
                               live_dt=DAY0 + pd.Timedelta(days=2))
        assert r2["action"] == "exited"
        assert state.position is None
        assert state.trades[0].exit_reason == "trailing_indicator"
        assert state.trades[0].exit_price == pytest.approx(95.0 * (1 - 0.05 / 100), rel=1e-3)

    def test_rerunning_on_the_same_closed_bar_is_a_no_op(self):
        df = make_bars([base_bar(), base_bar(long_signal=True)])
        state = PaperTradingState(symbol="BTC/USDT", strategy="tita", starting_equity=1000.0)
        now_ms = self._now_after(df)
        r1 = check_and_update(state, df, TF_MS, now_ms, "long_signal", None,
                               self._stop_target(), RiskLimits(cooldown_bars=0), live_price=100.5,
                               live_dt=DAY0 + pd.Timedelta(days=2))
        assert r1["action"] == "entered"
        r2 = check_and_update(state, df, TF_MS, now_ms, "long_signal", None,
                               self._stop_target(), RiskLimits(cooldown_bars=0), live_price=999.0,
                               live_dt=DAY0 + pd.Timedelta(days=2))
        assert r2["action"] == "already_processed"
        # a second (bogus) fill price must NOT have touched the already-open position
        assert state.position.entry_price != pytest.approx(999.0)

    def test_no_closed_bar_yet_does_nothing(self):
        df = make_bars([base_bar(long_signal=True)])
        state = PaperTradingState(symbol="BTC/USDT", strategy="tita", starting_equity=1000.0)
        now_ms = int(df["ts"].iloc[0]) + 1000  # candle still forming
        result = check_and_update(state, df, TF_MS, now_ms, "long_signal", None,
                                   self._stop_target(), RiskLimits(), live_price=100.0,
                                   live_dt=DAY0)
        assert result["action"] == "no_closed_bar_yet"
        assert state.position is None


class TestRiskGating:
    def test_rejects_entry_during_cooldown(self):
        state = PaperTradingState(symbol="BTC/USDT", strategy="tita", starting_equity=1000.0, bar_index=5)
        # simulate a just-closed losing trade at bar_index=5
        rm = RiskManager(RiskLimits(cooldown_bars=10), 1000.0)
        rm.mark_time(DAY0)
        rm.register_position_closed(-10.0, DAY0, 5, 5.0)
        state.risk = snapshot_risk_manager(rm)

        df = make_bars([base_bar(long_signal=True)])
        now_ms = int(df["ts"].iloc[0]) + TF_MS
        result = check_and_update(state, df, TF_MS, now_ms, "long_signal", None,
                                   StopTargetConfig(method="trailing_indicator",
                                                     trailing_indicator_col="tita_alma", atr_mult_stop=1.5),
                                   RiskLimits(cooldown_bars=10), live_price=100.0,
                                   live_dt=DAY0 + pd.Timedelta(days=1))
        assert result["action"] == "signal_rejected"
        assert result["reason"] == "cooldown"
        assert state.position is None


class TestRRFilterIntegration:
    def test_entry_rejected_when_rr_below_min(self):
        df = make_bars([base_bar(long_signal=True, close=100, alma=95, atr=1)])
        df["structure_stop"] = 99.0
        df["structure_target"] = 100.5  # tiny reward vs a much larger risk once ATR floor applies
        state = PaperTradingState(symbol="BTC/USDT", strategy="x", starting_equity=1000.0)
        stop_target = StopTargetConfig(method="structure", structure_stop_col="structure_stop",
                                        structure_target_col="structure_target", min_rr=2.5,
                                        atr_mult_stop=1.5)
        now_ms = int(df["ts"].iloc[-1]) + TF_MS
        result = check_and_update(state, df, TF_MS, now_ms, "long_signal", None, stop_target,
                                   RiskLimits(cooldown_bars=0), live_price=100.0,
                                   live_dt=DAY0 + pd.Timedelta(days=1))
        assert result["action"] == "signal_rejected"
        assert result["reason"] == "rr_below_min"
        assert state.position is None


class TestStatePersistence:
    def test_round_trips_through_json(self, tmp_path):
        state = PaperTradingState(
            symbol="ETH/USDT", strategy="tita", starting_equity=1000.0, bar_index=3,
            last_processed_ts=123456,
            position=PaperPosition(side="long", entry_price=50.0, entry_dt="2026-01-01T00:00:00Z",
                                    entry_bar_index=2, stop=45.0, tp=None, size=2.0,
                                    risk_amount=5.0, notional_pct=10.0, pending_exit=True),
        )
        path = str(tmp_path / "state.json")
        save_state(state, path)
        loaded = load_state(path, "ETH/USDT", "tita", 1000.0)
        assert loaded.bar_index == 3
        assert loaded.last_processed_ts == 123456
        assert loaded.position.stop == pytest.approx(45.0)
        assert loaded.position.pending_exit is True

    def test_loading_a_missing_file_returns_a_fresh_state(self, tmp_path):
        path = str(tmp_path / "does_not_exist.json")
        state = load_state(path, "BTC/USDT", "tita", 1000.0)
        assert state.position is None
        assert state.trades == []
        assert state.bar_index == 0


class TestRiskBridgeRoundTrip:
    def test_restore_reproduces_gating_behavior(self):
        rm = RiskManager(RiskLimits(max_consecutive_losses=2, halt_cooldown_hours=24), 1000.0)
        rm.mark_time(DAY0)
        rm.register_position_closed(-10.0, DAY0, 1, 5.0)
        rm.register_position_closed(-10.0, DAY0, 2, 5.0)  # 2nd consecutive loss -> halt triggers
        snap = snapshot_risk_manager(rm)

        restored = restore_risk_manager(RiskLimits(max_consecutive_losses=2, halt_cooldown_hours=24),
                                         snap, 1000.0)
        allowed, reason = restored.can_open_position(DAY0 + pd.Timedelta(hours=1), 3)
        assert not allowed
        assert reason == "circuit_breaker_halt"
