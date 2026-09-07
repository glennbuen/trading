import sys
sys.path.insert(0, '/workspaces/trading')
from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.strategies.spyfrat_system import compute_spyfrat_system, bollinger_breakout_up
from cryptobot.strategies.support_20pct import compute_support_20pct
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct
from scripts.evaluate_strategy import aggregate
from cryptobot.engines.moving_averages import bollinger_bands

ex = ExchangeProvider(exchange_id='okx')
md = MarketDataProvider(ex)

print(f"\n{'='*70}\nSPYFRAT CORE SYSTEM (1d, window=180d)\n{'='*70}")
for symbol in ["BTC/USDT", "ETH/USDT"]:
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    # pre-merge weekly RSI onto daily ONCE (multi-timeframe, can't be
    # recomputed per-window without losing the earlier weeks' history)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)
    def signal_fn(d, _pre=pre_merged):
        d2 = compute_volatility(d.copy())
        basis, upper, lower = bollinger_bands(d2["close"], 50, 0.20)
        d2["spyfrat_bb_upper"] = upper
        d2["spyfrat_bb_lower"] = lower
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        # re-attach the pre-merged ephr/phr columns by position (same index/order)
        d2["pr_ephr"] = _pre["pr_ephr"].reindex(d2.index).values if len(d2) == len(_pre) else _pre["pr_ephr"].iloc[-len(d2):].values
        below_lower = d2["close"] < lower
        d2["spyfrat_exit_signal"] = below_lower.fillna(False) | d2["pr_ephr"].fillna(False)
        return d2
    stop_target = StopTargetConfig(method="signal_exit", exit_signal_col="spyfrat_exit_signal", atr_mult_stop=1.5)
    windows = run_walk_forward(pre_merged, signal_fn, "long_signal", None, RiskLimits(), stop_target,
                                window_days=180, step_days=180)
    agg = aggregate(windows)
    chained_dd = chained_max_drawdown_pct(windows)
    print(f"  {symbol} ({len(daily)} candles): {agg.get('total_trades',0)} trades, PF={agg.get('profit_factor')}, "
          f"win%={agg.get('win_rate_pct')}, avgR={agg.get('avg_r_multiple')}, "
          f"windows={agg.get('windows_profitable')}/{agg.get('windows_total')}, chainedDD%={round(chained_dd,2)}")

print(f"\n{'='*70}\n20% SUPPORT BOUNCE (1d, window=180d)\n{'='*70}")
def signal_fn2(d):
    d2 = compute_volatility(d.copy())
    return compute_support_20pct(d2)
stop_target2 = StopTargetConfig(method="structure", structure_stop_col="s20_support_level", atr_mult_stop=1.5)
for symbol in ["BTC/USDT", "ETH/USDT"]:
    df = md.get_ohlcv(symbol, "1d", 3000)
    windows = run_walk_forward(df, signal_fn2, "long_signal", None, RiskLimits(), stop_target2,
                                window_days=180, step_days=180)
    agg = aggregate(windows)
    chained_dd = chained_max_drawdown_pct(windows)
    print(f"  {symbol} ({len(df)} candles): {agg.get('total_trades',0)} trades, PF={agg.get('profit_factor')}, "
          f"win%={agg.get('win_rate_pct')}, avgR={agg.get('avg_r_multiple')}, "
          f"windows={agg.get('windows_profitable')}/{agg.get('windows_total')}, chainedDD%={round(chained_dd,2)}")
