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

Timestamp: 2026-06-03T15:48:16Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed at 2026-06-03T15:48:16Z.
- Latest completed supervised DRY observe: exit 0, ticks=12, elapsed_sec=107.5.
- Prior supervised DRY observe attempt at 2026-06-03T15:39:41Z failed/non-zero after a Coinbase best-bid/ask data read hang and Windows access violation; hang dump: C:\ai_trading_bot_koko\logs\hang_dump_18312.log.
- DRY=true, LIVE=false.
- PFID present in environment: yes.
- COINBASE_KEY_FILE present in environment: yes.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after two DRY paper probe losses: realized=-0.02282457 USD, unrealized=0.00 USD, net=-0.02282457 USD.
- Open/closed/wins/losses: open=0, closed=2, wins=0, losses=2.
- ADA-USD closed loss_trim at -60.8472 bps / -0.01825415 USD.
- BTC-USD closed loss_trim at -15.2347 bps / -0.00457042 USD.
- Probe was tightened after this evidence: DRY_OBSERVE_PROBE_MIN_DMID_BPS is now 0.0, so negative recent-dmid probe opens are blocked; DRY_OBSERVE_PROBE_MAX_SPREAD_BPS is 5.0.
- Normal all-pass DRY gate remains breadth/dmid constrained: latest readiness has all_pass_candidates=0 and observe_open_candidate_present=false.
- Latest preflight/feed status is usable but regime-blocked: refreshed=393, failed=0, timestamp_ratio=0.8957, liquid=18, blocker=green_breadth.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, brf=25, tdmidnz=263, tdmidok=166.
- Liquid subset coverage exists but profitable overlap is absent: quote_volume_ge_min=18, dmid_ge_min_and_quote_volume_ge_min=0, timestamp_usable_and_quote_volume_ge_min green_ratio=0.0.
- Green breadth is weak: latest cache green_ratio=0.1203; latest runtime market_green_ratio=0.45 vs dry_min_market_green_ratio=0.85.
- Missing product/cache gap is not current: files_present=393/393 and latest preflight refresh failed=0.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Tightened the DRY-only observe probe after loss evidence: negative recent-dmid probe entries are now rejected via DRY_OBSERVE_PROBE_MIN_DMID_BPS=0.0.
- Added DRY_OBSERVE_PROBE_MAX_SPREAD_BPS handling in run_manager and tests; current cap is 5.0 bps, matching the normal dry spread gate while the dmid floor blocks the observed losing pattern.
- Reduced DRY_ACTIONABLE_BOOK_REFRESH_TOP_N to 25 to keep actionable book refresh coverage but avoid the prior 120-product data-read burst that hung in Coinbase get_best_bid_ask.
- No Profit Score tuning was performed.
- Coinbase/order placement path was not touched.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.02282457 USD, unrealized=0.00 USD, net=-0.02282457 USD.
- open/closed/wins/losses: open=0, closed=2, wins=0, losses=2.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p 'test_koko_dry_candidate_rank.py': 11 OK.
- py_compile managers\run_manager\run_manager.py: OK.
- run_settings.json JSON parse/settings check: DRY=True, LIVE=False, probe min dmid=0.0, probe max spread=5.0, refresh top N=25, TP=8.0, SL=0.8.
- 8-tick supervised DRY observe after actionable-refresh throttle: exit 0, no crash, no opens.
- 12-tick supervised DRY observe after probe settings adjustment: exit 0, no opens, no new losses.
- Readiness regenerated to C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json.
- Cache regime regenerated to C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json.

Guardrails:
- Coinbase/order placement path not touched by this relay update or latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue bounded DRY observe only when liquid candidates stop showing negative recent dmid, or add a DRY-only diagnostic lane for positive-dmid but low-quote-volume candidates without weakening live/order safety.
- Keep focus on data/preflight/open-lane coverage, not Profit Score tuning, while no credible positive P&L exists.

User action required:
- No.

Reporting note:
- Gmail connector should be used for material status email while local SMTP reporter env remains unavailable.
