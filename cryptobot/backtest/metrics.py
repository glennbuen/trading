"""
Backtest metrics — computed from a trades list + a per-bar equity curve,
kept separate from the simulation loop (backtest/engine.py) so metrics
are independently testable against hand-built trade lists without running
a full simulation (architecture spec §23).
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Trade:
    side: str
    entry_dt: pd.Timestamp
    exit_dt: pd.Timestamp
    entry_price: float
    exit_price: float
    stop_price: float
    size: float
    pnl: float
    fees: float
    exit_reason: str
    r_multiple: float  # pnl / initial risk amount
    holding_bars: int


@dataclass
class BacktestResult:
    trades: list = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    starting_equity: float = 0.0
    final_equity: float = 0.0
    rejected_signals: list = field(default_factory=list)  # spec §31: journal rejections too

    # metrics (populated by compute_metrics)
    num_trades: int = 0
    win_rate_pct: float = 0.0
    profit_factor: float = float("nan")
    expectancy: float = 0.0
    net_return_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_r_multiple: float = 0.0
    max_drawdown_pct: float = 0.0
    max_consecutive_losses: int = 0
    sharpe: float = float("nan")
    sortino: float = float("nan")
    exposure_pct: float = 0.0
    avg_holding_bars: float = 0.0
    total_fees: float = 0.0


def _max_consecutive_losses(trades: list) -> int:
    streak = 0
    worst = 0
    for t in trades:
        if t.pnl <= 0:
            streak += 1
            worst = max(worst, streak)
        else:
            streak = 0
    return worst


def _max_drawdown_pct(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    peak = equity_curve.cummax()
    dd = (peak - equity_curve) / peak.replace(0, np.nan)
    return float(dd.max(skipna=True) * 100) if dd.notna().any() else 0.0


def _sharpe_sortino(equity_curve: pd.Series, periods_per_year: float = 365.0) -> tuple[float, float]:
    """Computed from DAILY-resampled equity returns (crypto trades 24/7,
    so 365 periods/year rather than a stock market's ~252). Returns
    (nan, nan) when there isn't enough history to compute a meaningful
    standard deviation."""
    if equity_curve.empty or len(equity_curve) < 2:
        return float("nan"), float("nan")
    daily = equity_curve.resample("1D").last().ffill()
    returns = daily.pct_change().dropna()
    if len(returns) < 2 or returns.std() == 0:
        return float("nan"), float("nan")
    sharpe = (returns.mean() / returns.std()) * np.sqrt(periods_per_year)
    downside = returns[returns < 0]
    if len(downside) < 2 or downside.std() == 0:
        sortino = float("nan")
    else:
        sortino = (returns.mean() / downside.std()) * np.sqrt(periods_per_year)
    return float(sharpe), float(sortino)


def compute_metrics(trades: list, equity_curve: pd.Series, starting_equity: float,
                     total_bars: int) -> BacktestResult:
    result = BacktestResult(trades=trades, equity_curve=equity_curve,
                             starting_equity=starting_equity,
                             final_equity=equity_curve.iloc[-1] if len(equity_curve) else starting_equity)

    if not trades:
        result.net_return_pct = 0.0
        return result

    pnls = np.array([t.pnl for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]

    result.num_trades = len(trades)
    result.win_rate_pct = round(len(wins) / len(trades) * 100, 2)
    gross_win = wins.sum() if len(wins) else 0.0
    gross_loss = abs(losses.sum()) if len(losses) else 0.0
    result.profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf")
    result.expectancy = round(pnls.mean(), 4)
    result.avg_win = round(wins.mean(), 4) if len(wins) else 0.0
    result.avg_loss = round(losses.mean(), 4) if len(losses) else 0.0
    result.avg_r_multiple = round(np.mean([t.r_multiple for t in trades]), 3)
    result.max_consecutive_losses = _max_consecutive_losses(trades)
    result.total_fees = round(sum(t.fees for t in trades), 4)
    result.avg_holding_bars = round(np.mean([t.holding_bars for t in trades]), 2)
    result.exposure_pct = round(sum(t.holding_bars for t in trades) / total_bars * 100, 2) if total_bars else 0.0

    result.net_return_pct = round((result.final_equity - starting_equity) / starting_equity * 100, 2)
    result.max_drawdown_pct = round(_max_drawdown_pct(equity_curve), 2)
    sharpe, sortino = _sharpe_sortino(equity_curve)
    result.sharpe = round(sharpe, 3) if not np.isnan(sharpe) else float("nan")
    result.sortino = round(sortino, 3) if not np.isnan(sortino) else float("nan")

    return result
