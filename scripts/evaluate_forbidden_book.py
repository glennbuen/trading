import sys
sys.path.insert(0, '.')
from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct
from scripts.evaluate_strategy import aggregate

from cryptobot.strategies.mama import compute_mama
from cryptobot.strategies.fishball import compute_fishball
from cryptobot.strategies.calma import compute_calma
from cryptobot.strategies.papa import compute_papa
from cryptobot.strategies.tita import compute_tita
from cryptobot.strategies.bopis import compute_bopis
from cryptobot.strategies.day_trading_alma import compute_day_trading_alma

ex = ExchangeProvider(exchange_id='okx')
md = MarketDataProvider(ex)

CONFIGS = [
    ("MAMA", "1d", 3000, 180, compute_mama, StopTargetConfig(method="trailing_indicator", trailing_indicator_col="mama_alma", atr_mult_stop=1.5)),
    ("FISHBALL", "30m", 3000, 15, compute_fishball, StopTargetConfig(method="signal_exit", exit_signal_col="fishball_exit_signal", atr_mult_stop=1.5)),
    ("CALMA", "1w", 500, 365, compute_calma, StopTargetConfig(method="trailing_indicator", trailing_indicator_col="calma_alma", atr_mult_stop=1.5)),
    ("PAPA", "1d", 3000, 180, compute_papa, StopTargetConfig(method="signal_exit", exit_signal_col="papa_exit_signal", atr_mult_stop=1.5)),
    ("TITA", "1d", 3000, 180, compute_tita, StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma", atr_mult_stop=1.5)),
    ("BOPIS", "1d", 3000, 180, compute_bopis, StopTargetConfig(method="trailing_indicator", trailing_indicator_col="bopis_ema9", atr_mult_stop=1.5)),
    ("DAY_TRADING", "15m", 3000, 7, compute_day_trading_alma, StopTargetConfig(method="trailing_indicator", trailing_indicator_col="dt_alma", atr_mult_stop=1.5)),
]

for name, tf, n, wd, strategy_fn, stop_target in CONFIGS:
    print(f"\n{'='*70}\n{name} ({tf}, window={wd}d)\n{'='*70}")
    for symbol in ["BTC/USDT", "ETH/USDT"]:
        df = md.get_ohlcv(symbol, tf, n)
        def signal_fn(d, _fn=strategy_fn):
            d2 = compute_volatility(d.copy())
            d2 = _fn(d2)
            return d2
        windows = run_walk_forward(df, signal_fn, "long_signal", None,
                                    RiskLimits(), stop_target, window_days=wd, step_days=wd)
        agg = aggregate(windows)
        chained_dd = chained_max_drawdown_pct(windows)
        print(f"  {symbol} ({len(df)} candles, {df['dt'].iloc[0].date()}->{df['dt'].iloc[-1].date()}): "
              f"{agg.get('total_trades',0)} trades, PF={agg.get('profit_factor')}, "
              f"win%={agg.get('win_rate_pct')}, avgR={agg.get('avg_r_multiple')}, "
              f"windows={agg.get('windows_profitable')}/{agg.get('windows_total')}, "
              f"chainedDD%={round(chained_dd,2)}")
