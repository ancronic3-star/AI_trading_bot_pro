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

Timestamp: 2026-06-03T16:57:12Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:49:38Z after 4 ticks with DRY=true and LIVE=false.
- Latest local preflight cache status write: completed at 2026-06-03T16:56:43Z via tools/run_koko_dry_supervised.py::_ensure_recent_candle_cache.
- Latest local status task: readiness regenerated for fresh since window 2026-06-03T16:49:00Z.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Profit Score evidence: 12/100 as computed by tools/tdi_status_reporter.py from five closed losses and negative net P&L; the P&L summary file does not store a literal score field.
- Do not tune Profit Score while opened=0 / dryopen=0.
- U=0 / stale-feed cause is not current in the latest supervised observe: tick_diag had U=120, S=393, chk=393, brf=80, tdmid=393, tdmidnz=52, tdmidok=1.
- Actionable book refresh cap reaches the configured target: DRY_ACTIONABLE_BOOK_REFRESH_TOP_N=80, max_book_refresh_count=80, target_refreshed_book_gap=0.
- Runtime broad green breadth passed in the latest supervised observe: market_green_ratio=0.8667 vs min=0.85, market_dmid_bps=51.07 vs disabled floor -999999.0.
- Fresh canonical cache-regime preflight now reports timestamp coverage usable: timestamp_usable_files=356/393, timestamp_usable_ratio=0.9059, would_pass_timestamp_usable=true.
- Fresh canonical cache-regime preflight reports liquid subset coverage usable: liquid_subset_products=18 vs min=10.
- Fresh canonical cache-regime preflight reports no missing product/cache gap: files_present=393, files_checked=393, missing_files=0.
- Fresh canonical cache-regime preflight blocker is green_breadth: green_ratio=0.3379 vs min=0.85, would_pass_green_ratio=false.
- Latest readiness fresh window still has all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false.
- Current runtime near blockers are dmid-only: runtime_failure_combos={dmid:19, tob|dmid:1}.
- Closest runtime near miss remains HYPE-USD blocked by dmid only: spr=2.78/5.00, tob=4131/500, qv=1696324/250000, rdmid=31.96/40.00.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\run_settings.json
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Fixed tools/run_koko_dry_supervised.py so the canonical cache-regime report path resolves dynamically from the active ROOT and writes logs/cache_market_regime_latest.json during preflight checks.
- Fixed tests/test_run_koko_dry_supervised_preflight.py so temp-cache status assertions read the emitted file before the temp workspace is deleted.
- Preserved prior observe-readiness book coverage work: actionable_book_coverage_gap means runtime brf missed target; paper signal book-source gaps are reported separately.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score: 12/100, computed by reporter from P&L summary.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 2 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 12 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 13 OK.
- py_compile tools\run_koko_dry_supervised.py tools\koko_dry_observe_readiness.py: OK.
- Direct preflight write verification: _ensure_recent_candle_cache returned enabled=true, refreshed=false, and wrote logs/cache_market_regime_latest.json with timestamp_usable_ratio=0.9059, liquid_subset_products=18, missing_files=0, blocker=green_breadth.
- Earlier bounded supervised DRY observe after book-coverage patch: exit 0, ticks=4, drysig=0, dryopen=0, brf=80.
- Settings remain: DRY=true, LIVE=false, allowed probe failures=[market_breadth], DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0, static TP=8.0, static SL=0.8.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe/data coverage until product-level all-pass or an approved probe candidate appears.
- Immediate focus: monitor for dmid-positive liquid candidates now that timestamp coverage, liquid subset coverage, feed presence, cache presence, and runtime book-refresh coverage are usable.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.
