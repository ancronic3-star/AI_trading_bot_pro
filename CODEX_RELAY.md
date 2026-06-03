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

Timestamp: 2026-06-03T16:14:53Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:14:28Z after 8 ticks with DRY=true and LIVE=false.
- Previous TDI snapshot logger access-violation blocker was mitigated by disabling TDI snapshot file writes in DRY settings via TDI_SNAPSHOT_ENABLED=false and hardening tdi_logger JSON sanitization.
- Latest hang_dump files after the patch are timeout stack snapshots during loop sleep, not fatal access violations.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Weak-dmid probe pattern is rejected as unprofitable: ADA, BTC, JITOSOL, DOGE, and HYPE all closed loss_trim.
- Latest HYPE-USD weak-dmid probe closed loss_trim at -12.5174 bps / -0.00375522 USD.
- DRY observe probe was tightened after loss evidence: allowed failures now only [market_breadth], and DRY_OBSERVE_PROBE_MIN_DMID_BPS=40.0. It can no longer waive the dmid gate.
- Latest post-tightening readiness: all_pass_candidates=0, observe_open_candidate_present=false, drysig=0, dryopen=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, chk=393, brf=25, tdmid=393, tdmidnz=20, tdmidok=3.
- Timestamp/cache coverage is usable: files_present=393, missing_files=0, timestamp_usable_ratio=0.9135.
- Liquid subset coverage exists: quote_volume_ge_min=16, liquid_subset_products=16, min_liquid_subset_products=10.
- Profitable overlap is thin: dmid_ge_min_and_quote_volume_ge_min=1.
- Green breadth remains weak: cache green_ratio=0.1613 and runtime market_green_ratio=0.4583 vs dry_min_market_green_ratio=0.85.
- Main blocker is market breadth/dmid, not missing product/cache coverage and not stale feed.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_tdi_logger.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Hardened TDI snapshot logger JSON serialization and added TDI_SNAPSHOT_ENABLED=false to keep DRY observe stable while preserving TDI scoring.
- Added tdi_logger tests for disabled snapshot no-op and JSON-safe payload sanitization.
- Tightened DRY observe probe so weak-dmid candidates are no longer opened: only market_breadth can be waived by the probe.
- Updated candidate-rank tests for market-breadth-only probe behavior; kept quote-volume helper coverage for explicitly configured experiments.
- Patched TDI status reporter throttling so failed local SMTP attempts still advance hourly/material dedupe state and do not generate every-minute outbox spam.
- No Profit Score tuning was performed.
- Coinbase/order placement path was not touched.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p 'test_koko_dry_candidate_rank.py': 12 OK.
- python -m unittest discover -s tests -p 'test_tdi_logger.py': 3 OK.
- py_compile managers\run_manager\run_manager.py managers\logging_manager\tdi_logger.py tools\tdi_status_reporter.py: OK.
- run_settings.json parse/settings check: DRY=True, LIVE=False, DRY_OBSERVE_PROBE_ALLOWED_FAILURES=[market_breadth], DRY_OBSERVE_PROBE_MIN_DMID_BPS=40.0, TDI_SNAPSHOT_ENABLED=False, TP=8.0, SL=0.8.
- Supervised DRY observe after TDI snapshot mitigation: exit 0, ticks=8.
- Supervised DRY observe after probe tightening: exit 0, ticks=8, no new opens after HYPE closed; latest drysig=0 and dryopen=0.
- Readiness regenerated to C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json.
- Cache regime regenerated to C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json using configured runtime candle cache.

Guardrails:
- Coinbase/order placement path not touched by this relay update or latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe when market breadth/dmid improves enough to produce all-pass or market-breadth-only candidates.
- Do not tune Profit Score while opened=0 and no credible positive P&L exists.
- Keep collecting coverage evidence and monitor for true liquid+dmid overlap.

User action required:
- No.

Reporting note:
- Gmail connector remains the actual delivery path while local SMTP env is unavailable.
- Local reporter failed-SMTP dedupe is patched to avoid every-minute outbox spam.
