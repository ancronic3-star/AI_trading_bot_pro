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

Timestamp: 2026-06-03T19:51:14Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY task: completed exit 0 on 2026-06-03 with DRY=true and LIVE=false.
- Latest wait-mode observe smoke found an actionable ranked preflight window and ran instead of skipping.
- Latest actionable preflight before first open: refreshed=393, failed=0, supported=True, timestamp_usable_ratio=0.9186, liquid_subset_products=21, blocker=none.
- Latest 6-tick observe after DRY cap change completed exit 0: refreshed=391, failed=2, supported=True by ranked/probe path, timestamp_usable_ratio=0.8499, liquid_subset_products=19, blocker=timestamp_coverage.
- TDI Factor Gmail reporting cadence: every two hours plus immediate material events. User update cadence should now be two-hour email summaries unless a material event occurs.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- The old opened=0/preflight-feed blocker is no longer absolute: DRY observe opened SUI-USD when ranked preflight became actionable.
- Current dry profitability blocker remains negative total net P&L, not Profit Score tuning.
- Latest cache regime still shows full-universe timestamp coverage borderline: timestamp_usable_ratio=0.8499 vs min=0.850.
- Liquid subset coverage is usable: liquid_subset_products=19 vs min=10.
- Full-universe green breadth remains weak: green_ratio=0.6809 vs min=0.85.
- Ranked observe subset is usable: best_ranked_observe timestamp_usable_ratio=1.0, green_ratio=0.9667, dmid_liquidity_range_overlap=4, would_pass_configured_regime=true.
- U=0 / stale-feed cause is not current in the latest evidence; cache files are present and mtime_fresh_ratio=1.0.
- Missing product/cache gap is not current: files_present=393, missing_files=0.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Added preflight wait-for-observe-window mode in the supervised DRY runner so DRY observe can wait for usable coverage instead of ending at a red preflight snapshot.
- Preserved the preflight skip when the window remains non-actionable.
- Changed TDI Factor periodic email summary cadence to two hours through code default and run_settings.json.
- Set DRY_PNL_MAX_OPEN_POSITIONS=4 for DRY-only evidence collection; BUY_MAX_OPEN stayed 1.
- Ran DRY observe after wait-mode found usable coverage; SUI-USD opened in dry ledger.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=+0.00383772 USD, net=-0.03902483 USD.
- open/closed/wins/losses: open=1, closed=6, wins=0, losses=6.
- opened=7 historically; latest open is SUI-USD.
- Latest open SUI-USD mark: unrealized_pnl_bps=+12.7924, unrealized_pnl_usd=+0.00383772.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Latest cache regime: files_present=393, missing_files=0, timestamp_usable_ratio=0.8499, liquid_subset_products=19, dmid_liquidity_range_overlap=4, full-universe blocker=timestamp_coverage plus green_breadth.
- Ranked observe subset: timestamp_usable_ratio=1.0, green_ratio=0.9667, liquid_subset_products=19, dmid_liquidity_range_overlap=4, would_pass_configured_regime=true.
- Latest actionable observe run: preflight timestamp_usable_ratio=0.9186, liquid_subset_products=21, blocker=none, dryopen=1.
- Latest 6-tick continuation: open remained 1 and unrealized improved from +0.002193 to +0.003838 USD.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 7 OK.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 19 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 18 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 7 OK.
- python -m py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py: OK.
- python -m py_compile managers\run_manager\run_manager.py tools\tdi_status_reporter.py tools\tdi_status_monitor.py: OK.
- python -m json.tool run_settings.json: OK.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Continue DRY observe only through the data/preflight lane with wait-for-observe-window enabled.
- Do not tune Profit Score while fresh dry opens are unavailable.
- Let the open SUI-USD dry ledger position mark/close under existing static TP/SL and dry-cycle exit rules.
- Collect more dry P&L evidence until net dry P&L improves materially or a new blocker appears.
- Keep DRY=true and LIVE=false.

User action required:
- No.
