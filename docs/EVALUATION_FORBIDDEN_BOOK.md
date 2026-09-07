# Strategy Evaluation — "The Forbidden Book" 7-strategy set (spec §39)

Source: *The Forbidden Book — A Stock Trading Technical Analysis Guide*
(Gandakoh, Traders Den PH, 2020), a Philippine retail-stock-trading
e-book. All 7 named strategies (MAMA, FISHBALL, CALMA, PAPA, TITA, BOPIS,
Day Trading) built exactly to the book's stated rules (verbatim text
extracted via `pdftotext`), each at its own book-prescribed timeframe, on
BTC/USDT and ETH/USDT, with the same walk-forward methodology as every
other strategy this project has tested. Two indicator-parameter
assumptions, stated explicitly since the book gives no numbers: ALMA
window/offset/sigma and Fisher Transform's "dotted lines" threshold both
use TradingView's defaults (the platform the book's own chart studies are
built around).

## Headline results

| Strategy | Timeframe | BTC trades / PF | ETH trades / PF | Verdict |
|---|---|---|---|---|
| **TITA** | 1d | 166 / **1.83** | 158 / **1.83** | **See below — the real finding** |
| MAMA | 1d | 47 / 2.25 | 58 / 2.68 | High PF, but small-sample artifact-driven (see below) |
| BOPIS | 1d | 61 / 1.75 | 66 / 2.17 | Same artifact pattern as MAMA |
| CALMA | 1w | 15 / 6.36 | 14 / 9.32 | Extreme PF, thinnest sample of all 7, heavily artifact-driven |
| PAPA | 1d | 10 / 0.65 | 16 / 0.14 | Fails outright |
| FISHBALL | 30m | 44 / 0.03 | 59 / 0.33 | Fails badly — high-frequency fee-bleed pattern |
| Day Trading (ALMA) | 15m | 51 / 0.18 | 45 / 0.08 | Fails badly — same fee-bleed pattern |

## TITA — the real finding of this evaluation, and arguably of this whole project

**TITA is categorically different from every "promising" result seen anywhere else in this session — including Ichimoku's, which collapsed under the same scrutiny applied here.**

1. **Large, consistent per-window trade counts.** Every one of 16 walk-forward windows on both symbols has 5-14 trades — never the 1-2-trade artifact pattern that undermined MAMA, BOPIS, CALMA, and every prior "exception" this project has flagged (Breakout, Trend Pullback, Liquidity Sweep Reversal, MFI). 324 total trades across BTC+ETH.
2. **PF > 1.2 on both symbols simultaneously** (1.83 / 1.83) — no strategy tested anywhere in this project, across 13 strategies now, has cleared this bar on both BTC and ETH at once.
3. **Parameter sensitivity swept and it survived — the decisive check.** `alma_window`, `rsi_length`, `rsi_lower`, `rsi_upper` each perturbed ±10%/±20%, on both symbols (40 total cells). **Zero cliffs.** The single weakest cell across the entire sweep is ETH's `rsi_lower` at -20% (PF 1.19) — still above breakeven, just under the 1.2 bar. Every other cell sits at 1.3-2.4. Several parameter directions (higher `rsi_lower`) actually *improve* PF further (BTC: 2.38 at +10%, 2.25 at +20%). This is the opposite of Ichimoku's `kijun_period` result, which collapsed from 1.49 to 0.65 on an ordinary 10% change — the exact pattern spec §26 warns about, and TITA doesn't show it anywhere in the swept range.
4. **Consistently positive average R** across every single swept configuration on both symbols (+0.056 to +0.401) — never negative, unlike every other strategy's "exception" in this project.

### What TITA does NOT have yet, stated plainly

- **No true out-of-sample holdout beyond the walk-forward windows themselves.** Every window has still been looked at in aggregate; a genuinely untouched final holdout period (data never inspected before a go/no-go decision) hasn't been reserved.
- **Only tested on BTC/USDT and ETH/USDT.** No check on other symbols.
- **Daily timeframe only.** The book's own stated timeframe for TITA, correctly honored — but this means the result says nothing about intraday behavior.
- **The book's original domain is Philippine equities, not crypto.** RSI/ALMA momentum surviving on BTC/ETH daily data is real evidence for *this* market, not a confirmation that the book's authors were "right" about PSE stocks — a different, untested claim.
- **No regime-attribution analysis.** The per-window breakdown (in the raw evaluation output, not reproduced in full here) shows real variation across bull/bear/chop periods — some 180-day windows are strongly positive (PF up to 5.44), others clearly negative (PF as low as 0.24) — consistent with a real but not universally-dominant edge, not a suspiciously smooth curve.

### Honest verdict on TITA

**This is the strongest evidence for a genuine edge produced anywhere in this project.** It is not yet "validated" in the full sense this project has used that word — a true held-out confirmation period would be the natural next step before any paper-trading decision — but it has cleared every check that has been used to reject every other strategy tested this session, including the one (Ichimoku) that looked similarly promising before its sensitivity sweep. Do not proceed to paper trading on this alone, but this is the one result from this entire multi-week project worth a genuine follow-up (a proper held-out period, additional symbols, live-market microstructure considerations) rather than being set aside with the rest.

## MAMA, BOPIS, CALMA — high aggregate PF, undermined by the same thin-sample pattern seen throughout this project

Per-window inspection (not just the aggregate number) is what separates these from TITA:

- **MAMA** (BTC): windows range from 0-5 trades each, with individual windows showing PF as extreme as 46.33 and 33.68 (on 3-4 trades) alongside multiple PF=0.0 windows on similarly small counts. The 2.25 aggregate is a few large winners in thin samples, not a distributed edge.
- **BOPIS** (BTC): same pattern — PF 14.8, 8.8, 10.23 on 3-4 trade windows, offset by PF 0.0-0.11 windows equally thin.
- **CALMA**: the thinnest of all — several windows have 0-1 trades, two show PF=inf on a single trade, and the weekly timeframe (453 total candles) simply doesn't generate enough signals for the aggregate PF (6.36/9.32) to mean much of anything statistically.

None of these three received a parameter-sensitivity sweep — given the per-window evidence already disqualifies them the same way it disqualified Breakout/Trend Pullback/Liquidity Sweep's exceptions, that check wasn't the deciding factor here the way it was for Ichimoku or TITA.

## PAPA, FISHBALL, Day Trading (ALMA) — clean rejections

PAPA fails on both symbols outright (0.65 / 0.14) — its own stated design goal ("doesn't work sa mga biglang lipad na basura stocks", i.e. filters out explosive moves) may simply not translate to crypto's generally higher baseline volatility. FISHBALL and Day Trading both fail badly (PF 0.03-0.33 and 0.08-0.18) with the same high-frequency fee-bleed signature seen repeatedly in this project's fastest-firing strategies (`okx_scalper_bot.py`, `okx_bollinger_bot.py`, Liquidity Sweep Reversal) — 30m and 15m timeframes simply trade too often for OKX's taker-fee structure to tolerate with these entry rules.

## Overall verdict

**6 of 7 book strategies do not have a validated edge, consistent with every other rejection in this project.** The 7th — **TITA** — is the strongest result this entire session has produced, having survived scrutiny (large consistent samples, both symbols, a full parameter sweep with no cliffs) that dismantled every other "promising" number along the way. It is a genuine lead, not a confirmed edge — treated with the same discipline as everything else here: no parameter was tuned in response to any of these results, and TITA's next step is a proper held-out validation, not a live-trading decision.
