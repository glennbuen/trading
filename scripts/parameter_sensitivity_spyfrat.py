import sys
sys.path.insert(0, '/workspaces/trading')
from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct
from cryptobot.engines.moving_averages import bollinger_bands

ex = ExchangeProvider(exchange_id='okx')
md = MarketDataProvider(ex)

BASELINE = {"bb_length": 50, "bb_std": 0.20}
PERTS = [-20, -10, 0, 10, 20]

def aggregate(windows):
    all_trades = [t for w in windows for t in w.result.trades]
    if not all_trades:
        return {"total_trades": 0, "profit_factor": float("nan"), "win_rate_pct": 0.0, "avg_r_multiple": float("nan")}
    wins = [t for t in all_trades if t.pnl > 0]
    losses = [t for t in all_trades if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    return {
        "total_trades": len(all_trades),
        "win_rate_pct": round(len(wins) / len(all_trades) * 100, 2),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_r_multiple": round(sum(t.r_multiple for t in all_trades) / len(all_trades), 3),
    }

def run_variant(daily, pre_merged, param, value):
    params = dict(BASELINE)
    params[param] = value
    def signal_fn(d, p=params, _pre=pre_merged):
        d2 = compute_volatility(d.copy())
        basis, upper, lower = bollinger_bands(d2["close"], p["bb_length"], p["bb_std"])
        above = d2["close"] > upper
        was_above = above.shift(1).fillna(False).astype(bool)
        d2["long_signal"] = above & ~was_above
        d2["pr_ephr"] = _pre["pr_ephr"].iloc[-len(d2):].values
        below_lower = d2["close"] < lower
        d2["spyfrat_exit_signal"] = below_lower.fillna(False) | d2["pr_ephr"].fillna(False)
        return d2
    stop_target = StopTargetConfig(method="signal_exit", exit_signal_col="spyfrat_exit_signal", atr_mult_stop=1.5)
    windows = run_walk_forward(daily, signal_fn, "long_signal", None, RiskLimits(), stop_target,
                                window_days=180, step_days=180)
    agg = aggregate(windows)
    agg["chained_dd"] = round(chained_max_drawdown_pct(windows), 2)
    return agg

for symbol in ["BTC/USDT", "ETH/USDT"]:
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)
    print(f"\n{'='*80}\nSPYFRAT sensitivity — {symbol}\n{'='*80}")
    for param, baseline_value in BASELINE.items():
        print(f"\n--- {param} (baseline={baseline_value}) ---")
        for pct in PERTS:
            value = baseline_value * (1 + pct/100)
            if param == "bb_length":
                value = max(5, round(value))
            agg = run_variant(daily, pre_merged, param, value)
            label = "baseline" if pct == 0 else f"{pct:+d}%"
            print(f"  {label:>8} {value:>8.3f} trades={agg['total_trades']:>4} win%={agg['win_rate_pct']:>6} "
                  f"PF={agg['profit_factor']:>6} avgR={agg['avg_r_multiple']:>7} chainDD%={agg['chained_dd']:>6}")
