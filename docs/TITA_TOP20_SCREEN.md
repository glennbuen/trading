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

## Follow-up: sensitivity sweep + holdout on XLM/DOGE/SOL (2026-09-11)

Run via `scripts/validate_tita_new_symbols.py`, same method as
`parameter_sensitivity_tita.py` and `holdout_validation_tita.py`.

**Sensitivity sweep**: all three passed cleanly — no real cliffs across
the 5×4 perturbation grid. XLM's `rsi_lower` knob dipped to PF 0.84 on
the two downward perturbations (worth noting, not a collapse).

**Holdout (most recent 365 days, isolated)** — the headline PF conceals
more than it reveals here:

| Symbol | Holdout PF | Trades | Q1 (Sep-Dec) | Q2 (Dec-Mar) | Q3 (Mar-Jun) | Q4 (Jun-Sep) |
|---|---|---|---|---|---|---|
| XLM | 5.09 | 15 | 0.00 | 0.05 | 10.43 | 5.77 |
| DOGE | 1.12 | 13 | 0.07 | 0.23 | 0.04 | 4.50 |
| SOL | 2.81 | 17 | 0.39 | 0.49 | 1.58 | 6.68 |

All three show the same shape: flat-to-losing across the first half of
the holdout year, with the entire aggregate result riding on the last
one or two quarters. This differs from BTC/ETH's own holdout pattern
(BTC: 5.96 → 0.28 → 1.18 → 4.60 — strongest quarter was the *first*
one), so it isn't simply "the whole crypto market ran in Q3/Q4" — it
looks more like something alt-specific happened in that window that
BTC didn't fully share. Worth treating as an open question, not a
settled explanation.

**Verdict per symbol:**
- **DOGE — set aside.** PF=1.12 is barely breakeven; 3 of 4 quarters
  were clear losers. The full-history screen's PF=2.75 has not been
  holding up recently — exactly what the holdout check exists to catch.
- **XLM — impressive number, fragile shape.** PF=5.09 on 15 trades where
  2 quarters were near-total losses and 2 were extraordinarily hot
  (10.43, 5.77) is a small sample carried by two lucky quarters, not a
  demonstrated steady edge. Clean sensitivity sweep is a real point in
  its favor; the holdout number itself isn't trustworthy yet.
- **SOL — the most credible of the three, still not paper-trading-ready.**
  Front-loaded to the second half, but as a gradient (0.39 → 0.49 → 1.58
  → 6.68) rather than a cliff, positive net return even in the weaker
  early quarters, and a clean sensitivity sweep.

**Decision as of this doc: none of the three proceed to paper trading.**
The quarterly lumpiness is a real yellow flag on all three, to varying
degrees. If revisited, SOL is the one worth another look after more
data accumulates outside its one hot stretch; DOGE is not worth
pursuing further on this evidence.
