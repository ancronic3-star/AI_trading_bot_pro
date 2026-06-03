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

Timestamp: 2026-06-03T17:08:36Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T17:01:52Z after 4 ticks with DRY=true and LIVE=false.
- Latest local preflight refresh completed before the run: refreshed=391, failed=2, cache_market_regime_supported=true, timestamp_ratio=0.8728, liquid_subset_products=12, blocker=none.
- Latest local readiness task: regenerated at 2026-06-03T17:03:54Z for since_local_start=2026-06-03 12:01:00.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L remains negative: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Profit Score evidence: 12/100 as computed by tools/tdi_status_reporter.py from five closed losses and negative net P&L; the P&L summary file does not store a literal score field.
- Do not tune Profit Score while opened=0 / dryopen=0.
- U=0 / stale-feed cause is not current: latest observed tick_diag has U=120, S=393, chk=393, brf=80, tdmid=393, tdmidnz=259, tdmidok=5.
- Actionable book refresh cap reaches the configured target: DRY_ACTIONABLE_BOOK_REFRESH_TOP_N=80, max_book_refresh_count=80, target_refreshed_book_gap=0.
- Runtime market breadth passed strongly in the latest supervised observe: market_green_ratio=0.9333 vs min=0.85, market_dmid_bps=70.81 vs disabled floor -999999.0.
- Fresh canonical cache-regime preflight now passes configured regime support: cache_market_regime_supported=true, timestamp_usable_ratio=0.8728, liquid_subset_products=12 vs min=10, blocker=none.
- Latest readiness fresh window has signals=393, all_pass_candidates=0, observe_probe_candidate_present=false, observe_runtime_probe_candidate_present=false.
- Current runtime near blockers are dmid-focused: runtime_failure_combos={dmid:16, tob|dmid:4}.
- Closest runtime near miss: SUI-USD blocked by dmid only, spr=2.45/5.00, tob=714/500, qv=547490/250000, rdmid=8.56/40.00, market_green_ratio=0.9333/0.8500.
- Dominant paper-signal blocker is trough, but liquid/runtime near misses still fail dmid; no blind score or gate tuning applied.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Prior lane files still changed locally: C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\run_settings.json.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Read CODEX_RELAY.md from ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot and confirmed RELAY_FILE_VISIBLE=yes.
- Updated this relay status block with the latest local Cloud task status, current blocker, files changed, and dry Profit Score evidence.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score: 12/100, computed by reporter from P&L summary.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- CODEX_RELAY.md fetched successfully from GitHub branch codex/cloud-ready-koko-bot before this write.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 13 OK.
- py_compile tools\koko_dry_observe_readiness.py: OK.
- Fresh bounded supervised DRY observe: exit 0, ticks=4, drysig=0, dryopen=0, brf=80.
- Fresh preflight cache-regime after refresh: supported=true, timestamp_ratio=0.8728, liquid=12, blocker=none.
- Fresh readiness metadata: generated_at_utc=2026-06-03T17:03:54Z, since_local_start=2026-06-03 12:01:00, signals=393.
- Settings remain: DRY=true, LIVE=false, allowed probe failures=[market_breadth], DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0, static TP=8.0, static SL=0.8.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe with usable data/preflight coverage and wait for dmid-positive liquid candidates or an all-pass/probe candidate.
- Before any DRY-only gate change, require stronger evidence than the current near-miss set; current near-miss dmid values are below even the positive backtest dmid16/dmid20 regimes.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.
