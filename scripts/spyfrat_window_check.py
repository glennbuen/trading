import sys
sys.path.insert(0, '/workspaces/trading')
from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward
from cryptobot.engines.moving_averages import bollinger_bands

ex = ExchangeProvider(exchange_id='okx')
md = MarketDataProvider(ex)

for symbol in ["BTC/USDT", "ETH/USDT"]:
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)
    def signal_fn(d, _pre=pre_merged):
        d2 = compute_volatility(d.copy())
        basis, upper, lower = bollinger_bands(d2["close"], 50, 0.20)
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        d2["pr_ephr"] = _pre["pr_ephr"].iloc[-len(d2):].values
        below_lower = d2["close"] < lower
        d2["spyfrat_exit_signal"] = below_lower.fillna(False) | d2["pr_ephr"].fillna(False)
        return d2
    stop_target = StopTargetConfig(method="signal_exit", exit_signal_col="spyfrat_exit_signal", atr_mult_stop=1.5)
    windows = run_walk_forward(pre_merged, signal_fn, "long_signal", None, RiskLimits(), stop_target,
                                window_days=180, step_days=180)
    print(f"\n--- SPYFRAT {symbol} ---")
    for w in windows:
        r = w.result
        print(f"  {w.label}: {r.num_trades} trades, PF={r.profit_factor}, win%={r.win_rate_pct}, net%={r.net_return_pct}")
