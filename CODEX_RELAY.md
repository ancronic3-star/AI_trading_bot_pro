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

Timestamp: 2026-06-03T16:27:07Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:24:24Z with DRY=true and LIVE=false.
- Latest reporter state: local pid=3264 ts=16:24:19, current status timestamp 2026-06-03T16:27:04Z.
- Previous TDI snapshot logger access-violation blocker remains mitigated by TDI_SNAPSHOT_ENABLED=false and tdi_logger hardening.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Main blocker remains green_breadth, not stale feed and not missing product/cache coverage.
- Latest cache regime coverage: files_present=393, missing_files=0, timestamp_usable_ratio=0.9288.
- Liquid subset coverage exists: quote_volume_ge_min=18, liquid_subset_products=18, min_liquid_subset_products=10.
- Profitable overlap remains thin: dmid_ge_min_and_quote_volume_ge_min=1.
- Green breadth remains weak: cache green_ratio=0.1006 versus DRY_MIN_MARKET_GREEN_RATIO=0.85.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, chk=393, brf=25, tdmid=393, drysig=0, dryopen=0.
- Runtime drynear shows NEAR-USD as market_breadth-only at tick 1: score=0.9844, spread=3.50/5.00 bps, tob=756/500 USD, quote_volume=4130522/250000 USD, recent dmid=49.16/40.00 bps, market_green_ratio=0.2833/0.8500.
- Readiness output currently reports observe_open_candidate_present=true and all_pass_candidates containing NEAR-USD, while runtime still shows drysig=0 and dryopen=0. This is the next data/preflight/open-lane issue to inspect before any Profit Score tuning.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_tdi_logger.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Updated CODEX_RELAY.md with RELAY_FILE_VISIBLE=yes and the latest DRY observe/feed coverage status.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- Latest supervised DRY observe task completed exit 0.
- Latest readiness/cache refresh completed with timestamp/cache and liquid subset coverage usable.
- Reporter state subject basis remains: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | green_breadth.
- Previously verified tests remain: test_tdi_status_reporter.py 2 OK, test_koko_dry_candidate_rank.py 12 OK, test_tdi_logger.py 3 OK, and py_compile OK for reporter/run_manager/tdi_logger.

Guardrails:
- Coinbase/order placement path not touched by this relay update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Inspect the readiness/runtime mismatch where NEAR-USD appears as a market-breadth-only observe candidate but runtime still reports drysig=0 and dryopen=0.
- Keep work in the data/preflight/open-lane path: timestamp coverage, liquid subset coverage, green breadth, U=0/stale feed causes, and missing product/cache gaps.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.

Reporting note:
- Gmail connector remains the actual delivery path while local SMTP env is unavailable.
- Local reporter failed-SMTP dedupe is patched to avoid every-minute outbox spam, and no-send previews no longer suppress real reports.
