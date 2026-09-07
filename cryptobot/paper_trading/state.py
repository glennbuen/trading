"""
Paper Trading State — persisted state for a single symbol's paper-traded
position, trade history, and risk-manager state, so a scheduled/cron-
invoked check script resumes correctly across restarts. JSON-backed
(human-inspectable, no DB dependency for a system this low-frequency —
TITA trades roughly once every 2-4 weeks per the holdout validation).

Deliberately plain dataclasses + explicit to_dict/from_dict, not a
generic serializer — matches this project's style elsewhere (no magic,
every field's round-trip is visible in the code).
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class PaperPosition:
    side: str
    entry_price: float
    entry_dt: str  # ISO timestamp string
    entry_bar_index: int
    stop: float
    tp: float | None
    size: float
    risk_amount: float
    notional_pct: float
    pending_exit: bool = False


@dataclass
class PaperTrade:
    side: str
    entry_dt: str
    exit_dt: str
    entry_price: float
    exit_price: float
    stop_price: float
    size: float
    pnl: float
    fees: float
    exit_reason: str
    r_multiple: float


@dataclass
class RiskManagerSnapshot:
    equity: float
    day_start_equity: float
    week_start_equity: float
    consecutive_losses: int
    halted_until: str | None
    emergency_shutdown: bool
    open_positions: int
    exposure_pct: float
    last_trade_close_bar: int | None
    day_start_date: str | None
    week_start_key: list | None


@dataclass
class PaperTradingState:
    symbol: str
    strategy: str
    starting_equity: float
    bar_index: int = 0
    last_processed_ts: int | None = None
    position: PaperPosition | None = None
    trades: list = field(default_factory=list)  # list[PaperTrade]
    risk: RiskManagerSnapshot | None = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "starting_equity": self.starting_equity,
            "bar_index": self.bar_index,
            "last_processed_ts": self.last_processed_ts,
            "position": asdict(self.position) if self.position else None,
            "trades": [asdict(t) for t in self.trades],
            "risk": asdict(self.risk) if self.risk else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PaperTradingState":
        return cls(
            symbol=d["symbol"],
            strategy=d["strategy"],
            starting_equity=d["starting_equity"],
            bar_index=d.get("bar_index", 0),
            last_processed_ts=d.get("last_processed_ts"),
            position=PaperPosition(**d["position"]) if d.get("position") else None,
            trades=[PaperTrade(**t) for t in d.get("trades", [])],
            risk=RiskManagerSnapshot(**d["risk"]) if d.get("risk") else None,
        )


def load_state(path: str, symbol: str, strategy: str, starting_equity: float) -> PaperTradingState:
    p = Path(path)
    if p.exists():
        return PaperTradingState.from_dict(json.loads(p.read_text()))
    return PaperTradingState(symbol=symbol, strategy=strategy, starting_equity=starting_equity)


def save_state(state: PaperTradingState, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state.to_dict(), indent=2))
