# Claude Code prompt — OKX trend bot setup

Paste the block below into Claude Code, in a folder where you've placed `okx_trend_bot.py`.

---

## Prompt to paste

```
I have a Python crypto trading bot at okx_trend_bot.py that trades BTC/USDT on
OKX via ccxt. I need you to help me set it up as a git repo and run a
validation pipeline. Do NOT modify the trading logic unless I ask — the
strategy has been designed deliberately and I want to test it as-is first.

TASK 1 — Repo setup
- Initialise a git repo here
- Create a .gitignore containing: .env, bot_state.json, bot.log,
  fng_cache.json, __pycache__/, *.pyc, venv/, .venv/
- Create a .env.example (no real values) with placeholders for
  OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE
- Create a requirements.txt with ccxt, pandas, numpy
- Create a README.md documenting the CLI flags and the 5-stage validation
  pipeline (backtest -> paper -> demo -> live)
- Make the initial commit. Do NOT create a remote or push — I'll do that.

TASK 2 — Verify it runs
- Install dependencies
- Run: python okx_trend_bot.py --help
- Confirm no import errors and all flags are present

TASK 3 — Run the backtest matrix
Run each of these against real OKX data and collect results into a markdown
comparison table (profit factor, trades, win rate, max drawdown, and
fees_as_pct_of_gross_win for each):

  python okx_trend_bot.py --backtest 3000 --day --minimal --adaptive-st
  python okx_trend_bot.py --backtest 3000 --day --minimal
  python okx_trend_bot.py --backtest 3000 --day
  python okx_trend_bot.py --backtest 3000 --day --minimal --adaptive-st --vwap-bands
  python okx_trend_bot.py --backtest 3000 --minimal --adaptive-st

If OKX returns fewer candles than requested (their API paginates), tell me the
actual count returned rather than silently proceeding — I need to know if I'm
testing on less data than I think.

TASK 4 — Robustness check
Re-run the best-performing config from Task 3 on ETH/USDT and SOL/USDT using
the SAME parameters (don't re-tune per symbol). I'm checking for consistency,
not looking for the best symbol. Report all three side by side.

TASK 5 — Honest assessment
Tell me plainly:
- Is the profit factor above 1.2 with more than 20 trades? If not, say so
  directly and do not suggest parameter tuning to fix it.
- Do results hold across all three symbols, or only one? If only one, flag
  that as likely curve-fitting rather than a real edge.
- What percentage of gross wins went to fees?

IMPORTANT CONSTRAINTS
- Do not tune parameters to improve backtest results. If results are poor,
  report that honestly. Overfitting to historical data is the failure mode
  I'm trying to avoid.
- Do not add new indicators. The system deliberately uses only two
  (SuperTrend + VWAP) after testing showed that stacking correlated
  indicators reduced signal quality.
- Do not run --live or --demo. Backtest only.
- Never write API keys into any tracked file.
```

---

## After Claude Code finishes

If profit factor is **above 1.2** with **20+ trades** and results are broadly
consistent across BTC/ETH/SOL, proceed to paper mode:

```bash
python okx_trend_bot.py --day --minimal --adaptive-st
```

If profit factor is **below 1.0**, stop. The strategy doesn't have an edge on
real data, and no amount of parameter tuning will honestly fix that.

## Second prompt — VPS deployment (only after backtest passes)

```
The backtest passed. Help me deploy this to my VPS.

- Walk me through generating an SSH key and adding it to GitHub so I can
  clone the private repo on the VPS
- Create a systemd service file for running the bot with --demo --day
  --minimal --adaptive-st, with Restart=always
- Note: EnvironmentFile in systemd does NOT parse "export" prefixes, so
  give me the correct .env format for systemd specifically
- Give me the commands to enable, start, and tail logs for the service

Do not put credentials in any file that git tracks.
```
