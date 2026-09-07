# Strategy Evaluation — SWAG Trading System (Jared Odulio)

Source: the user's own description of a YouTube video ("The SWAG Trading
System" by Jared Odulio) watched 2026-09-06 — the third Philippine
retail-trading source tested this project (after *The Forbidden Book*
and the SPYFRAT/Investagrams deck), but the first supplied as a plain
text description rather than an extracted document. Built exactly to
that description's 4 components: Parabolic SAR (trend filter), EMA13
"trigger" crossing SMA20 "base" from below (buy) or above (sell), and
MFI (money-flow direction as entry confirmation, overbought/oversold as
exit) — all composed from already-tested engines
(`engines/parabolic_sar.py`, `engines/moving_averages.py`,
`engines/money_flow_index.py`), no new engine code required.

Two operationalization choices, stated up front (full detail in
`cryptobot/strategies/swag.py`'s module docstring): "about to cross" is
read as the cross event itself, not a predictive pre-cross signal (this
project's no-lookahead discipline doesn't allow forecasting a cross that
hasn't completed); "money flowing in/out" is read as the simplest
literal MFI-midline test (MFI > 50), with the overbought/oversold half
of MFI's stated role wired as the exit condition instead, reusing
`money_flow_index.py`'s existing `cross_down_from_overbought` — the same
standard MFI reversal-sell trigger this project's separate
`mfi_reversal.py` strategy already uses, not a new invention.

## Headline results

| Symbol | Timeframe | Trades | PF | Win% | Windows profitable | Verdict |
|---|---|---|---|---|---|---|
| BTC/USDT | 1h | 109 | 0.52 | 28.44 | 2/7 | Fails |
| ETH/USDT | 1h | 102 | 0.53 | 22.55 | 1/7 | Fails |
| BTC/USDT | 1d | 43 | 1.26 | 37.21 | 6/16 | Crosses 1.2, but see below |
| ETH/USDT | 1d | 44 | 0.89 | 36.36 | 6/16 | Fails |

## 1h — fails outright on both symbols

PF 0.52/0.53, worse than a coin flip after fees, with only 1-2 of 7
windows net profitable on either symbol. Same high-frequency
fee-bleed-from-overtrading signature seen repeatedly in this project's
fastest-firing strategies (`okx_scalper_bot.py`, Liquidity Sweep
Reversal, MFI Reversal's 1h config, "Forbidden Book"'s FISHBALL/Day
Trading). Not a close call.

## 1d — the familiar single-symbol pattern, confirmed by a thin per-window sample

BTC/USDT crosses the 1.2 threshold that this project treats as the entry
point for further scrutiny (1.26) — but ETH/USDT, the same strategy, same
parameters, same timeframe, fails (0.89). This is the exact "works on
one symbol only" pattern flagged as disqualifying every time it has
appeared in this project (Breakout Strategy A, Trend Pullback's one
exception, 20% Support Bounce) — the strategy needs to clear the bar on
*both* symbols simultaneously to warrant a parameter-sensitivity sweep,
the standard this project has held since TITA and SPYFRAT Core System
were the only two strategies (of 15 tested before this one) to actually
do that.

Even taken alone, BTC's 1.26 doesn't survive a look at its own per-window
detail: of its 6 "profitable" windows, several are 1-3 trades with
extreme profit factors (2021-06-06: 1 trade, PF=inf; 2020-12-08: 3
trades, PF=30.37; 2019-12-14: 3 trades, PF=5.12; 2020-06-11: 2 trades,
PF=4.8) — the same thin-sample signature that has undermined every
other superficially-promising number in this project that wasn't TITA.
No sensitivity sweep was run — the strategy fails the cross-symbol bar
before that check would add anything.

## Overall verdict

**SWAG does not clear the bar for further evaluation on either
timeframe tested.** 1h fails outright on both symbols; 1d fails on ETH
and only marginally, thinly exceeds 1.2 on BTC in a way that per-window
inspection immediately disqualifies — consistent with, not an exception
to, the pattern this project has seen in every other single-symbol
"exception" (Breakout A, Trend Pullback, 20% Support Bounce). No
parameter was tuned in response to any of these results. Do not proceed
to paper trading.
