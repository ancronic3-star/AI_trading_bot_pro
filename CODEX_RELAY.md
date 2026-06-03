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

Timestamp: 2026-06-03T16:43:44Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:32:46Z after 4 ticks with DRY=true and LIVE=false.
- Latest local status task: readiness regenerated for fresh since window 2026-06-03T16:32:00Z.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Profit Score remains 12/100.
- Do not tune Profit Score while opened=0 / dryopen=0.
- Broad cache blocker remains green_breadth: green_ratio=0.1006 vs min=0.85.
- Timestamp coverage is usable: timestamp_usable_ratio=0.9288, timestamp_missing_files=0.
- Product/cache coverage is usable: files_present=393, missing_files=0.
- Liquid subset coverage is usable but thin: liquid_subset_products=18 vs min=10, quote_volume_ge_min=18, dmid_ge_min_and_quote_volume_ge_min=1.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, chk=393, brf=25, tdmid=393, tdmidnz=22, tdmidok=4.
- Latest readiness fresh window has all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false.
- Runtime drynear blockers now surface as multi-gate combos: dmid|market_breadth=18 and tob|dmid|market_breadth=2.
- Closest runtime near miss: ZEC-USD blocked by dmid|market_breadth, spr=1.32/5.00, tob=533/500, qv=3287566/250000, rdmid=14.66/40.00, tick_dmid=11.96/10.00, market_green_ratio=0.2583/0.8500.
- Closest paper one-gate near miss: NEAR-USD blocked by spread only, spread=7.0671 bps vs max=5.0, dmid=49.1573 bps, quote_volume=1898059.8699 USD, tob=4349.13 USD.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\run_settings.json
- Existing lane files still changed locally: C:\ai_trading_bot_koko\managers\run_manager\run_manager.py, C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tools\tdi_status_reporter.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Patched tools/koko_dry_observe_readiness.py so readiness reports runtime_near_misses from tick_diag drynear/drynear_top lines.
- Added runtime_failure_combos and closest_runtime_near_miss promotion evidence.
- Fixed --since-ts-utc filtering for tick_diag so old drynear candidates do not leak into fresh windows.
- Kept market_breadth-blocked candidates out of all_pass_candidates and exposed probe eligibility separately.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 10 OK.
- py_compile tools\koko_dry_observe_readiness.py: OK via isolated PYTHONPYCACHEPREFIX.
- Latest readiness regenerated after patch for 2026-06-03T16:32:00Z window: all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false, signals=393, tick_diag_rows=4.
- Bounded supervised DRY observe after patch: exit 0, ticks=4, drysig=0, dryopen=0.
- Settings check remains: DRY=True, LIVE=False, allowed probe failures=[market_breadth], DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0, TP=8.0, SL=0.8.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe and data/preflight coverage checks until a product-level candidate is all-pass or market-breadth-only probe-eligible again.
- Current immediate open-lane focus: green breadth and dmid on liquid majors; spread remains the only paper one-gate blocker for the NEAR-style candidate.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.
