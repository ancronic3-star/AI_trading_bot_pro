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

Timestamp: 2026-06-03T18:54:38Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 on 2026-06-03 after 8 ticks with DRY=true and LIVE=false; start marker 2026-06-03 13:49:58 America/Chicago.
- Latest preflight refresh before observe: completed; refreshed=393, failed=0, cache_market_regime_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true.
- Latest cache regime evidence: logs/cache_market_regime_latest.json reports timestamp_usable_ratio=0.8499 after refresh, liquid_subset_products=17, and blocker=timestamp_coverage at the configured global threshold edge; ranked-probe support still allows observe.
- Latest readiness task: regenerated for since_local_start=2026-06-03 13:49:58 and wrote logs/dry_observe_readiness_latest.json.
- Latest readiness evidence: signals=323, book_metric_source_present=270, book_metric_source_missing=53, book_metric_source_present_ratio=0.8359, paper_signal_book_source_gap=0, actionable_book_coverage_gap=false.
- TDI Factor Gmail heartbeat automation cadence: every two hours, plus immediate material events.
- Immediate material-event Gmail status sent through Gmail connector to tdifactorToday@gmail.com for this patch/test/observe update.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- DRY observe still opened 0 positions, but the current blocker is feed/preflight market coverage and top-of-book candidate readiness, not Profit Score tuning.
- Book metric source coverage gap is materially improved and no longer the readiness blocker: paper_signal_book_source_gap=0 and actionable_book_coverage_gap=false.
- U=0 / stale-feed cause is not current: latest tick stream has U=120 and S=393.
- Timestamp coverage is borderline after refresh: timestamp_usable_ratio=0.8499 vs min=0.8500.
- Liquid subset coverage remains usable: liquid_subset_products=17 vs min=10.
- Runtime green breadth is currently usable: latest runtime near misses report market_green=0.9833 vs min=0.8500 and market_dmid=65.11.
- Latest readiness has quote_volume_usable=6, dmid_usable=23, liquid_dmid_overlap=1, and liquid_dmid_spread_tob_overlap=0.
- Closest liquid+dmid candidate is WLD-USD with spread passing and dmid/liquidity passing, blocked only by top-of-book depth: dmid=81.7121 bps, qv=474363.9786 USD, spread=1.9255 bps, tob=22.5465 USD, tob_shortfall=477.4535 USD.
- Dominant paper-signal blocker remains trough, but current open-candidate blocker for the liquid+dmid lane is top-of-book depth.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so local git status is unavailable here.

Changes applied in this update:
- Added readiness promotion for the closest liquid+dmid product that misses only spread/top-of-book overlap.
- Added status reporter wording so the main blocker names the concrete candidate and spread/top-of-book shortfall instead of only reporting `entry spread/tob overlap=0`.
- Added regression tests for closest spread/top-of-book shortfall promotion and email/report evidence.
- Regenerated readiness after an 8-tick DRY observe; opened remained 0.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- opened=6 historically; latest 8-tick observe produced dryopen=0.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Cache regime: files_present=393, timestamp_usable_ratio=0.8499, liquid_subset=17, cache_supported=true after refresh.
- Latest readiness: signals=323, quote_volume_usable=6, dmid_usable=23, liquid_dmid_overlap=1, liquid_dmid_spread_tob_overlap=0.
- Latest readiness book coverage: book_metric_source_present=270, book_metric_source_missing=53, present_ratio=0.8359, paper_signal_book_source_gap=0.
- Latest tick stream: U=120, S=393, brf=80; stale-feed/U=0 is not the active cause.
- Latest closest liquid+dmid spread/top-of-book shortfall: WLD-USD, top-of-book shortfall=477.4535 USD.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 16 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 6 OK.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- Gmail subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | WLD top-of-book.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: timestamp coverage edge, top-of-book/depth recurrence for liquid+dmid candidates, stale/cache gaps, and current trough causes.
- Do not tune Profit Score while dryopen=0.
- Keep DRY observe only when cache preflight shows dmid_liquidity_overlap > 0 and observe_window_worthwhile=true.
- When liquid+dmid+spread+tob overlap appears and dry opens resume, collect dry P&L improvement evidence.
- Keep DRY=true and LIVE=false.

User action required:
- No.
