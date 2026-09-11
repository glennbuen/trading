# TITA — Top-20-Market-Cap Screen (2026-09-11)

Prompted by: "we can screen crypto with tita? coinmarketcap.com" — this
is that screen, run properly rather than assumed. See
`scripts/backtest_tita_top20.py`.

## Honesty note, stated up front

**This is a screen, not a validation.** TITA's actual evidentiary
backing (`docs/TITA_HOLDOUT_VALIDATION.md` — PF 2.60 BTC / 1.79 ETH) came
from three layers: a 16-window walk-forward, a 40-cell parameter
sensitivity sweep, and a genuine held-out final-year check. This run is
only the first of those three layers, applied to 13 new symbols. Clearing
a PF>1.2 bar here means "worth taking to the next layer," not "validated"
— treat every result below accordingly, especially the more eye-catching
ones.

## Method

Universe: top 20 coinmarketcap.com ranks as of 2026-09-11, minus 5
stablecoins (USDT, USDC, USDe, DAI, USD1 — a long-only momentum signal
has nothing to say about an asset pegged to $1). BTC/ETH re-run alongside
the new names as an in-run consistency check against the published
numbers. Same unchanged TITA signal (`alma_window=9, rsi_length=14,
rsi_lower=50, rsi_upper=55`), same `StopTargetConfig` (`trailing_indicator`
on `tita_alma`, `atr_mult_stop=1.5`), same `RiskLimits()` defaults, same
walk-forward scheme (3000 daily candles, 180-day windows) as every prior
TITA evaluation in this project. Nothing tuned, no easier bar for the new
names.

## Result

| Rank | Symbol | Candles | Span | Trades | Win% | PF | AvgR | ChainDD% |
|---|---|---|---|---|---|---|---|---|
| 1 | BTC/USDT | 3000 | 2018-06-26 → 2026-09-11 | 164 | 34.76 | 1.79 | 0.228 | 2.28 |
| 2 | ETH/USDT | 3000 | 2018-06-26 → 2026-09-11 | 157 | 40.13 | 1.74 | 0.200 | 3.81 |
| 4 | BNB/USDT | 1361 | 2022-12-21 → 2026-09-11 | 77 | 37.66 | 1.08 | 0.024 | 4.50 |
| 5 | XRP/USDT | 2446 | 2020-01-01 → 2026-09-11 | 133 | 21.05 | 1.28 | 0.099 | 9.13 |
| 7 | SOL/USDT | 2172 | 2020-10-01 → 2026-09-11 | 126 | 32.54 | 2.00 | 0.285 | 4.50 |
| 8 | TRX/USDT | 2446 | 2020-01-01 → 2026-09-11 | 142 | 34.51 | 1.22 | 0.057 | 4.98 |
| 9 | HYPE/USDT | 312 | 2025-11-04 → 2026-09-11 | 13 | 23.08 | 0.70 | -0.070 | 0.89 |
| 10 | ZEC/USDT | 292 | 2025-11-24 → 2026-09-11 | 9 | 22.22 | 1.76 | 0.291 | 1.68 |
| 11 | DOGE/USDT | 2446 | 2020-01-01 → 2026-09-11 | 118 | 33.05 | 2.75 | 0.482 | 2.59 |
| 12 | XMR/USDT | — | — | — | — | — | — | — |
| 13 | LINK/USDT | 2446 | 2020-01-01 → 2026-09-11 | 136 | 36.76 | 1.58 | 0.146 | 3.08 |
| 14 | LEO/USDT | 2446 | 2020-01-01 → 2026-09-11 | 172 | 23.26 | 0.53 | -0.153 | 13.07 |
| 15 | ADA/USDT | 2446 | 2020-01-01 → 2026-09-11 | 122 | 31.97 | 1.51 | 0.155 | 2.98 |
| 16 | XLM/USDT | 2446 | 2020-01-01 → 2026-09-11 | 122 | 40.16 | **4.78** | 0.911 | 2.54 |
| 20 | BCH/USDT | 2446 | 2020-01-01 → 2026-09-11 | 139 | 30.94 | 1.46 | 0.139 | 3.55 |

XMR/USDT: not tradeable on OKX (`okx does not have market symbol
XMR/USDT`) — this project's only data source, per every existing script
— skipped, not scored.

## Reading the results

**Clears PF>1.2 on a well-sampled run (100+ trades) — worth a second
layer of testing**: XLM (4.78, the standout), DOGE (2.75), SOL (2.00),
LINK (1.58), ADA (1.51), BCH (1.46).

**Marginal — clears 1.2 but the average R-multiple is weak** (small edge
per trade even if PF is technically over the line): XRP (1.28, AvgR
0.099), TRX (1.22, AvgR 0.057). Not rejected outright, but the weakest
of the passing group.

**Fails outright, well-sampled (not a small-sample fluke)**: BNB (1.08,
77 trades), LEO (0.53, 172 trades — a genuine loser, not noise).

**Rejected on sample size, regardless of the headline number** — the
same discipline that disqualified MAMA/BOPIS/CALMA/SPYFRAT Core System
elsewhere in this project: HYPE (13 trades, only listed since Nov 2025)
and **ZEC (9 trades)** — ZEC's 1.76 PF looks tempting but 9 trades proves
nothing; this is exactly the thin-sample-artifact pattern this project
has repeatedly had to guard against.

## What this does NOT mean

None of these six passing names are validated, paper-trading-ready, or
even holdout-checked yet. This screen answers "does TITA's signal show
*any* edge on this symbol's full history" — it does not answer "is that
edge robust to small parameter changes" (the sensitivity-sweep question)
or "does it hold up on data the original discovery never touched" (the
holdout question). Both of those layers are unrun for every symbol in
this table except BTC/ETH.

## Suggested next step

Run the same parameter sensitivity sweep (`scripts/
parameter_sensitivity_tita.py`'s pattern) and a holdout validation
(`scripts/holdout_validation_tita.py`'s pattern) on the three strongest —
**XLM, DOGE, SOL** — before considering paper trading any of them
alongside BTC/ETH. Not yet run as of this doc.
