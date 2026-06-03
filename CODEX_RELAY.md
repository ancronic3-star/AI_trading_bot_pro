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

Timestamp: 2026-06-03T16:51:40Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:49:38Z after 4 ticks with DRY=true and LIVE=false.
- Latest local status task: readiness regenerated for fresh since window 2026-06-03T16:49:00Z.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Profit Score remains 12/100.
- Do not tune Profit Score while opened=0 / dryopen=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, chk=393, brf=80, tdmid=393, tdmidnz=52, tdmidok=1.
- Actionable book refresh cap now reaches the configured target: DRY_ACTIONABLE_BOOK_REFRESH_TOP_N=80, max_book_refresh_count=80, target_refreshed_book_gap=0.
- Broad green breadth passed in the fresh run: market_green_ratio=0.8667 vs min=0.85, market_dmid_bps=51.07 vs disabled floor -999999.0.
- Latest readiness fresh window has all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false.
- Current runtime near blockers are dmid-only: runtime_failure_combos={dmid:19, tob|dmid:1}.
- Closest runtime near miss: HYPE-USD blocked by dmid only, spr=2.78/5.00, tob=4131/500, qv=1696324/250000, rdmid=31.96/40.00, market_green_ratio=0.8667/0.8500.
- Closest paper one-gate near miss: HYPE-USD blocked by dmid only, dmid=31.9578/40.00, spr=2.7747/5.00, tob=1297.41/500, qv=1696324.0493/250000.
- Product/cache coverage remains usable: latest preflight refresh refreshed=392, failed=1, timestamp_ratio=0.9059, liquid=18, blocker=green_breadth in cache-regime preflight, but runtime breadth passed during observe.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\run_settings.json
- Existing lane files still changed locally: C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py, C:\ai_trading_bot_koko\managers\run_manager\run_manager.py, C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tools\tdi_status_reporter.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Added book_coverage_hint to tools/koko_dry_observe_readiness.py.
- Corrected book coverage semantics so actionable_book_coverage_gap only means runtime brf missed the configured refresh target; paper-signal book source attribution is reported separately.
- Raised DRY_ACTIONABLE_BOOK_REFRESH_TOP_N from 25 to 80 in run_settings.json.
- Added readiness tests for sparse book-source reporting and for no coverage gap when brf reaches the target.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 12 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 13 OK.
- py_compile tools\koko_dry_observe_readiness.py: OK via isolated PYTHONPYCACHEPREFIX.
- Bounded supervised DRY observe after patch: exit 0, ticks=4, drysig=0, dryopen=0, brf=80.
- Latest readiness regenerated after patch for 2026-06-03T16:49:00Z window: all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false, signals=393, tick_diag_rows=4, target_refreshed_book_gap=0.
- Settings check remains: DRY=True, LIVE=False, allowed probe failures=[market_breadth], DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0, TP=8.0, SL=0.8.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe/data coverage until a product-level all-pass or approved probe candidate appears.
- Current immediate focus: wait/monitor for dmid-positive liquid candidates now that timestamp, feed, book refresh, and runtime green breadth are usable in the latest observe window.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.
