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

Timestamp: 2026-06-03T18:33:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe/mark task: completed exit 0 on 2026-06-03 after 12 ticks with DRY=true and LIVE=false; local pid=19780, start ts=18:22:02Z.
- Latest preflight refresh: completed and now reports cache_market_regime_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true.
- Latest readiness task: regenerated for since_local_start=2026-06-03 13:22:02 and wrote logs/dry_observe_readiness_latest.json.
- Latest cache regime evidence: regenerated in logs/cache_market_regime_latest.json after aggregate quote-volume and ranked-probe alignment patch.
- TDI Factor Gmail heartbeat automation: active as hourly-tdi-factor-gmail-status, scheduled every two hours.
- Immediate material-event Gmail status sent through Gmail connector to tdifactorToday@gmail.com, id=19e8ec28b1e12587.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- DRY observe can now open the candidate lane from preflight/feed coverage, but opened remains 0 after the latest 12-tick run.
- Current blocker is actual runtime entry gates on the only liquid+dmid overlap product, not Profit Score tuning.
- U=0 / stale-feed cause is not current: latest tick stream has U=120, S=393, brf=80, drysig=0, dryopen=0.
- Timestamp coverage is usable: timestamp_usable_ratio=0.8728 vs min=0.8500.
- Liquid subset is usable: liquid_subset_products=18 vs min=10.
- Broad green breadth is red in the full universe: green_ratio=0.1518 vs min=0.8500; ranked probe explicitly allows the market_breadth/green_breadth-only preflight failure.
- Ranked probe preflight is now usable: best_probe_observe mode=timestamp_liquid_green_dmid_desc, products=120, timestamp_usable_ratio=1.0000, liquid_subset_products=18, dmid_liquidity_overlap=1, green_ratio=0.4756, blocker=green_breadth only.
- Runtime entry coverage found 2 liquid+dmid overlap products but 0 liquid+dmid+spread+tob overlap products.
- OPN-USD was the top overlap: recent dmid=434.2581 bps, recent quote volume=785748.1589 USD in runtime readiness, but it was rejected by spread=71.4689 bps > 5, tob=401.4661 USD < 500, trough_pct=1.0 > 0.3, and tick_dmid not warmed.
- Book metric source coverage remains thin: book_metric_source_present_ratio=0.0738 and liquid_dmid overlap products have missing book_metric_source in readiness.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so local git status is unavailable here.

Changes applied in this update:
- Fixed recent quote-volume semantics in cache preflight and runtime DRY recent-candle metrics: quote volume now sums usable recent-window candles instead of using the best single candle.
- Added runtime regression coverage that `_dry_recent_candle_metrics` sums recent quote volume.
- Added ranked-probe preflight support so observe can proceed when all hard data gates pass and the only ranked-scope blocker is allowed market_breadth/green_breadth.
- Wired supervisor preflight to pass `DRY_OBSERVE_PROBE_ALLOWED_FAILURES` into cache-regime reporting.
- Added CLI support for `--observe-probe-allowed-failures`.
- Refreshed cache regime with `--observe-probe-allowed-failures market_breadth`: supported=true, observe_window_worthwhile=true, ranked_probe=true, blockers=[].
- Ran a 12-tick DRY-only supervised observe after preflight became worthwhile; opened remained 0.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- opened=6 historically; latest 12-tick observe window produced drysig=0 and dryopen=0.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Cache regime: files_present=393, timestamp_usable_ratio=0.8728, green_ratio=0.1518, liquid_subset=18, dmid_ge_min_and_quote_volume_ge_min=1.
- Cache promotion hint: cache_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true, best_probe_observe=timestamp_liquid_green_dmid_desc, best_probe_green=0.4756, best_probe_liquid=18, best_probe_dmid_liquidity_overlap=1.
- Readiness: signals=393, quote_volume_usable=23, dmid_usable=18, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, spread_usable=42, tob_usable=115, trough_seeded=360.
- Latest tick_diag: U=120, S=393, brf=80, drysig=0, dryopen=0, mbr=0.4333/0.8500, mdmid=9.86/-999999.
- Top overlap product: OPN-USD with recent dmid=434.2581 bps and runtime recent quote volume=785748.1589 USD; rejected by spread/tob/trough/tick-warm gates.
- Near misses after OPN include ETH-USD, SOL-USD, NEAR-USD, ADA-USD, XRP-USD blocked by dmid.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 18 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 14 OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 2 OK.
- py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py managers\run_manager\run_manager.py: OK.
- Gmail subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | OPN book/trough gates.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: book metric source coverage for liquid+dmid overlap candidates, spread/tob freshness, trough/tick-warm causes, and product/cache gaps.
- Do not tune Profit Score while dryopen=0.
- Keep DRY observe only when cache preflight shows dmid_liquidity_overlap > 0 and observe_window_worthwhile=true.
- When liquid+dmid+spread+tob overlap appears and dry opens resume, collect dry P&L improvement evidence.
- Keep DRY=true and LIVE=false.

User action required:
- No.
