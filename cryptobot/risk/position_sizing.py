"""
Position sizing — mathematical, not arbitrary (architecture spec §17).

size = (equity * risk_pct) / stop_distance, capped so notional exposure
never exceeds max_position_pct of equity. Same formula validated across
all 7 standalone bots earlier in this project.
"""


def calculate_size(equity: float, risk_pct: float, entry_price: float, stop_price: float,
                    max_position_pct: float) -> float:
    """
    Returns position size in base-asset units (e.g. BTC, not USDT).
    Returns 0.0 for any degenerate input (zero/negative equity, zero stop
    distance, non-positive entry price) rather than raising or dividing by
    zero — a strategy signal should never be able to crash sizing.
    """
    if equity <= 0 or entry_price <= 0:
        return 0.0
    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 0:
        return 0.0

    risk_amount = equity * (risk_pct / 100)
    size = risk_amount / stop_distance

    max_notional = equity * (max_position_pct / 100)
    max_size = max_notional / entry_price
    return min(size, max_size)
