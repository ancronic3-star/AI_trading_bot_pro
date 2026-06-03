# KOKO Cloud Engine Relay

This file is the fallback relay when issue comments are unavailable.

Current source branch: codex/cloud-ready-koko-bot

Standing state:
- DRY remains true.
- LIVE remains false.
- Keep Coinbase/order guardrail intact.
- Keep static TP/SL safety intact.
- Stay out of website/app/mobile/native lanes.

Use this file for approved instructions, report requests, and status handoffs related to KOKO Cloud engine work.

## Relay test

Timestamp: 2026-06-01

Test message:
Relay write path from ChatGPT to GitHub file is working.

Codex check requested:
If Codex can read this file, report back through the available Cloud/GitHub/task channel with: RELAY_FILE_VISIBLE=yes.

## Codex relay status update

Timestamp: 2026-06-03T21:33:16Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY supervised entry-overlap sample: completed after bounded re-sampling, DRY=true, LIVE=false.
- Latest local monitor snapshot: 2026-06-03T21:33:16Z, DRY=true, LIVE=false.
- TDI Factor reporting destination: tdifactorToday@gmail.com.
- TDI Factor summary cadence: every two hours only, plus immediate material-event emails.
- No duplicate/no-fluff email rule remains active.

Current blocker:
- Primary blocker: runtime near-miss ADA-USD blocked by dmid.
- Latest readiness slice has signals=0, open_candidate=false, probe_candidate=false.
- Runtime near miss evidence: ADA-USD failed dmid only, qv=1,255,689 vs 250,000, rdmid=19.81 bps vs 40.00, spread=4.94 bps vs 5.00, top-of-book=4,332 vs 500.
- Latest tick diagnostic: U=120, S=393, brf=80, drysig=0, dryopen=0.
- Cache support remains usable: cache_supported=true.
- Timestamp coverage is usable: timestamp_ratio=0.9237, timestamp_shortfall=0.
- Liquid subset coverage is usable: liquid_subset=24 vs required 10, liquid_shortfall=0.
- Green breadth remains short: green_ratio=0.7948 vs required 0.8500, green_shortfall=0.0552.
- U=0 / stale-feed is not the current cause.
- Missing product/cache gap is not the current cause.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_reporter_state.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- opened=11 historically; blocked_open=46; quarantined=7.
- Latest dry ledger positive-exit evidence: ETH-USD and XRP-USD closed via profit_protect at 2026-06-03T21:15:01Z.
- ETH-USD profit_protect evidence: peak=35.6220 bps, close=21.0164 bps, pnl_usd=0.00630493.
- XRP-USD profit_protect evidence: peak=29.9638 bps, close=13.3172 bps, pnl_usd=0.00399517.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Patch/change evidence:
- DRY supervisor now has a bounded wait/re-sample lane for entry overlap when cache says observe is worthwhile but the first runtime entry sample is not actionable.
- DRY readiness reporting now carries runtime near-miss blockers when the paper-signal slice is empty.
- TDI status reporting now prefers the closest runtime near miss for the main blocker when signals=0.
- Reporting cadence is confirmed as two-hour summaries through TDI_REPORT_HOURLY_SEC=7200.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 14 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 18 OK in local runtime.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 9 OK in local runtime.
- python -m py_compile tools\run_koko_dry_supervised.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK in local runtime.
- Cloud checkout is a slim handoff tree; local reporter/readiness test files are not present there, so those focused tests were run against C:\ai_trading_bot_koko.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Stay in the data/preflight lane until runtime entry overlap returns and dryopen can become nonzero.
- Focus on dmid/spread/top-book/trough runtime causes rather than Profit Score tuning.
- Resume DRY observe candidate opening only after usable runtime market coverage returns.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
