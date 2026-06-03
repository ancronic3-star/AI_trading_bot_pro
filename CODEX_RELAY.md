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

Timestamp: 2026-06-03T15:59:15Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: failed/non-zero after running ticks 1-6.
- Latest failure: Windows access violation while writing TDI snapshot JSON append; hang dump: C:\ai_trading_bot_koko\logs\hang_dump_6872.log.
- Previous Coinbase best-bid/ask data-read hang was mitigated by reducing actionable book refresh width; current failure is in TDI snapshot logging, not Coinbase/order placement.
- DRY=true, LIVE=false.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after three DRY paper probe losses: realized=-0.02983764 USD, unrealized=0.00 USD, net=-0.02983764 USD.
- Open/closed/wins/losses: open=0, closed=3, wins=0, losses=3.
- ADA-USD closed loss_trim at -60.8472 bps / -0.01825415 USD.
- BTC-USD closed loss_trim at -15.2347 bps / -0.00457042 USD.
- JITOSOL-USD closed loss_trim at -23.3769 bps / -0.00701307 USD.
- Latest root cause found: DRY observe probe branch ordering allowed a weak JITOSOL-USD open when failures included quote_volume plus dmid/market_breadth; the quote-volume floor was not enforced first.
- Fix applied: quote_volume failures now always require DRY_OBSERVE_PROBE_MIN_QUOTE_FAILURE_DMID_BPS and DRY_OBSERVE_PROBE_MIN_QUOTE_VOLUME_USD before a DRY observe probe open is allowed.
- Current active blocker after that fix: TDI snapshot append access violation prevents reliable supervised observe coverage.
- Normal all-pass DRY gate remains breadth/dmid constrained; latest known readiness had all_pass_candidates=0 and observe_open_candidate_present=false.
- U=0 / stale-feed cause is not current in latest known diagnostics: U=120, refreshed/signals available, and missing product/cache gap was not current.
- Liquid subset coverage exists but profitable overlap remains weak: quote_volume_ge_min=18 and dmid_ge_min_and_quote_volume_ge_min=0 in latest known cache regime evidence.
- Green breadth remains weak: latest known cache green_ratio=0.1203; latest runtime market_green_ratio=0.45 vs dry_min_market_green_ratio=0.85.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Added quote-volume DRY observe probe settings: DRY_OBSERVE_PROBE_MIN_QUOTE_FAILURE_DMID_BPS=40.0 and DRY_OBSERVE_PROBE_MIN_QUOTE_VOLUME_USD=50000.0.
- Fixed DRY observe probe decision order so quote_volume failures cannot slip through the lower generic dmid/market-breadth branch.
- Added regression coverage for the JITOSOL pattern: failures=[dmid, quote_volume, market_breadth], dmid_bps=5.3, quote_usd=257 must reject with quote_failure_dmid_floor.
- Kept DRY_ACTIONABLE_BOOK_REFRESH_TOP_N=25 to avoid broad Coinbase best-bid/ask read bursts.
- No Profit Score tuning was performed while opened/evidence stayed unusable.
- Coinbase/order placement path was not touched.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.02983764 USD, unrealized=0.00 USD, net=-0.02983764 USD.
- open/closed/wins/losses: open=0, closed=3, wins=0, losses=3.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p 'test_koko_dry_candidate_rank.py': 12 OK.
- py_compile managers\run_manager\run_manager.py: OK.
- run_settings.json JSON parse/settings check: DRY=True, LIVE=False, allowed failures include dmid/quote_volume/market_breadth, quote-failure dmid floor=40.0, quote-volume floor=50000.0, TP=8.0, SL=0.8.
- Short supervised DRY observe after fix: non-zero/failure; JITOSOL was closed loss_trim on tick 1 and no new opens were recorded before the TDI logger access violation.

Guardrails:
- Coinbase/order placement path not touched by this relay update or latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Fix the TDI snapshot logging/access-violation blocker so supervised DRY observe can run long enough to measure timestamp coverage, liquid subset coverage, green breadth, stale-feed causes, and missing product/cache gaps.
- Regenerate dry observe readiness and cache market regime evidence after the logger fix.
- Resume DRY-only observe coverage work before any dry P&L improvement tuning.

User action required:
- No.

Reporting note:
- Gmail connector should be used for material status email while local SMTP reporter env remains unavailable.
- Do not send duplicate/noise emails; send material state changes and hourly summaries only.
