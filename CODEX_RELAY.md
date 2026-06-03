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

Timestamp: 2026-06-03T19:46:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 on 2026-06-03 after 4 ticks with DRY=true and LIVE=false; start marker 2026-06-03 13:42:29 America/Chicago.
- Latest preflight refresh before observe: completed and reports cache_market_regime_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true.
- Latest cache regime evidence: logs/cache_market_regime_latest.json reports timestamp_usable_ratio=0.8855, liquid_subset_products=19, dmid_ge_min_and_quote_volume_ge_min=2, best_probe_observe=timestamp_liquid_green_dmid_desc, best_probe_green=0.6106, best_probe_liquid=19, best_probe_dmid_liquidity_overlap=2, blocker=green_breadth only.
- Latest readiness task: regenerated for since_local_start=2026-06-03 13:42:29 and wrote logs/dry_observe_readiness_latest.json.
- Latest readiness evidence: signals=333, book_metric_source_present=259, book_metric_source_missing=74, book_metric_source_present_ratio=0.7778, paper_signal_book_source_gap=0, actionable_book_coverage_gap=false.
- TDI Factor Gmail heartbeat automation cadence: every two hours, plus immediate material events.
- Immediate material-event Gmail status sent through Gmail connector to tdifactorToday@gmail.com for this patch/test/observe update.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- DRY observe still opened 0 positions, but the current blocker is feed/preflight market coverage, not Profit Score tuning.
- Book metric source coverage gap is materially improved and no longer the readiness blocker: paper_signal_book_source_gap=0 and actionable_book_coverage_gap=false.
- U=0 / stale-feed cause is not current: latest tick stream has U=120 and S=393.
- Timestamp coverage is usable from preflight: timestamp_usable_ratio=0.8855 vs min=0.8500.
- Liquid subset coverage is usable from preflight: liquid_subset_products=19 vs min=10.
- Preflight had liquid+dmid overlap=2, but latest short readiness window has current liquid_dmid_overlap=0 and liquid_dmid_spread_tob_overlap=0 after market movement.
- Latest short readiness has dmid_usable=6 and quote_volume_usable=8.
- Dominant runtime blocker is trough with nearest runtime misses also failing dmid and market_breadth.
- Closest current runtime near miss: XRP-USD blocked by dmid and market_breadth; spread=0.82 bps <= 5, top-of-book=3348 USD >= 500, recent quote volume=2990059 USD, recent dmid=-4.94 bps < 40, market_green=0.65 < 0.85, market_dmid=24.4.
- Green breadth remains below the configured threshold in runtime: market_green=0.65 vs min=0.85 on the closest near miss.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so local git status is unavailable here.

Changes applied in this update:
- Allowed source-less inline book metric dictionaries with mid/spread/top-of-book fields to be refreshed instead of skipped when single refresh is superseded.
- Prioritized batch book refresh budget toward recent timestamp + liquid + dmid overlap candidates before lower-actionability rows, without increasing API budget.
- Added trough-block dry logging of book_metric_source and prefetch_tob_usd so readiness can see refreshed source even when trough blocks before dry-gate logging.
- Added regression tests for source-less inline book metrics and refresh-budget prioritization of liquid+dmid overlap.
- Refreshed cache regime with `--observe-probe-allowed-failures market_breadth`: supported=true, observe_window_worthwhile=true, ranked_probe=true, blockers=[] except allowed green_breadth.
- Ran DRY-only supervised observe after patch; opened remained 0.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- opened=6 historically; latest observe windows produced dryopen=0.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Cache regime: files_present=393, timestamp_usable_ratio=0.8855, liquid_subset=19, dmid_ge_min_and_quote_volume_ge_min=2.
- Cache promotion hint: cache_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true, best_probe_observe=timestamp_liquid_green_dmid_desc, best_probe_green=0.6106, best_probe_liquid=19, best_probe_dmid_liquidity_overlap=2.
- Latest readiness: signals=333, quote_volume_usable=8, dmid_usable=6, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Latest readiness book coverage: book_metric_source_present=259, book_metric_source_missing=74, present_ratio=0.7778, paper_signal_book_source_gap=0.
- Latest tick stream: U=120, S=393; stale-feed/U=0 is not the active cause.
- Latest closest near miss: XRP-USD, blocked by dmid and market_breadth while spread and top-of-book pass.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 16 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 16 OK.
- python -m py_compile managers\run_manager\run_manager.py: OK.
- Gmail subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | dmid/green breadth.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: liquid+dmid overlap recurrence, green breadth, dmid coverage, stale/cache gaps, and current trough causes.
- Do not tune Profit Score while dryopen=0.
- Keep DRY observe only when cache preflight shows dmid_liquidity_overlap > 0 and observe_window_worthwhile=true.
- When liquid+dmid+spread+tob overlap appears and dry opens resume, collect dry P&L improvement evidence.
- Keep DRY=true and LIVE=false.

User action required:
- No.
