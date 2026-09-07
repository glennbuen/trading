import sys
sys.path.insert(0, '.')
from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.strategies.tita import compute_tita
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct

ex = ExchangeProvider(exchange_id='okx')
md = MarketDataProvider(ex)

BASELINE = {"alma_window": 9, "rsi_length": 14, "rsi_lower": 50, "rsi_upper": 55}
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

def run_variant(df, param, value):
    params = dict(BASELINE)
    params[param] = value
    def signal_fn(d, p=params):
        d2 = compute_volatility(d.copy())
        return compute_tita(d2, alma_window=p["alma_window"], rsi_length=p["rsi_length"],
                             rsi_lower=p["rsi_lower"], rsi_upper=p["rsi_upper"])
    stop_target = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma", atr_mult_stop=1.5)
    windows = run_walk_forward(df, signal_fn, "long_signal", None, RiskLimits(), stop_target,
                                window_days=180, step_days=180)
    agg = aggregate(windows)
    agg["chained_dd"] = round(chained_max_drawdown_pct(windows), 2)
    return agg

df_btc = md.get_ohlcv("BTC/USDT", "1d", 3000)
df_eth = md.get_ohlcv("ETH/USDT", "1d", 3000)

for symbol, df in [("BTC/USDT", df_btc), ("ETH/USDT", df_eth)]:
    print(f"\n{'='*80}\nTITA sensitivity — {symbol} (baseline PF was {'1.83' if symbol=='BTC/USDT' else '1.83'})\n{'='*80}")
    for param, baseline_value in BASELINE.items():
        print(f"\n--- {param} (baseline={baseline_value}) ---")
        for pct in PERTS:
            value = baseline_value * (1 + pct/100)
            if param in ("alma_window", "rsi_length"):
                value = max(2, round(value))
            agg = run_variant(df, param, value)
            label = "baseline" if pct == 0 else f"{pct:+d}%"
            print(f"  {label:>8} {value:>8.3f} trades={agg['total_trades']:>4} win%={agg['win_rate_pct']:>6} "
                  f"PF={agg['profit_factor']:>6} avgR={agg['avg_r_multiple']:>7} chainDD%={agg['chained_dd']:>6}")
