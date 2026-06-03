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

Timestamp: 2026-06-03T15:13:04Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed at 2026-06-03T15:08:25Z.
- Latest supervised DRY observe completed: exit 0, ticks=3, elapsed_sec=25.3.
- run_active artifact: logs/run_active.json reports pid=24332, ts=15:08:00; no active supervised trading process was left running after the observe in the prior process check.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: opened=0, open_count=0, closed=0, wins=0, losses=0.
- Feed/preflight lane is usable enough to evaluate: supervisor preflight cache guard saw cache_refresh_required=false, supported=true, timestamp_ratio=0.8753, liquid=14, blocker empty before the latest observe.
- Latest readiness is scoped to the latest local run and shows signals=393, all_pass_candidates=0, one_gate_near_miss_present=true, dominant_blocker=trough.
- Liquid subset coverage: signals=18, all_pass=0, one_gate_counts dmid=5; liquid blockers are dmid=5, tob_usd=5, trough=8.
- Latest tick_diag coverage: tick=3, U=120, S=393, drysig=0, dryopen=0, dryblk=0, tdmid=393, tdmidnz=60, tdmidok=8.
- Latest drynear: ETH-USD failed only dmid with score=0.9986, spread=0.05/5.00, TOB=3648/500, quote_volume=8815416/250000, recent_candle_dmid=-1.72/40.00, tick_dmid=0.43/10.00, twarm=1.
- Closest readiness one-gate near miss: ADA-USD failed only recent-candle dmid at 14.0384/40.00 with quote_volume=507464.6802/250000, spread=4.687/5.00, TOB=2626/500, tick_dmid_warmed=false.
- U=0 / stale-feed cause is not the current blocker: latest tick_diag has U=120 and preflight timestamp_ratio=0.8753. The open blocker is candidate gate alignment after usable feed, especially recent-candle dmid plus trough/breadth mix.
- Missing product/cache gap status: preflight refresh previously refreshed 392/393 and failed 1; latest preflight still reports supported=true and blocker empty.
- Do not tune Profit Score while opened=0; next action remains DRY open-lane/feed diagnostics and longer observe once diagnostics are rich enough.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py
- C:\ai_trading_bot_koko\tests\test_tdi_logger.py
- Earlier lane files remain changed: tools\run_koko_dry_supervised.py, tests\test_run_koko_dry_supervised_preflight.py, tools\koko_cache_market_regime.py, tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied:
- Readiness now filters PAPER_BUY_SIGNAL rows with --since-local-start/marker, matching tick_diag filtering and removing stale historical near-miss pollution.
- Paper signals and drynear diagnostics now expose tick_dmid_warmed/twarm so unwarmed tick samples and real weak tick movement are distinguishable.
- Readiness now mirrors runtime warm-sample logic: explicitly unwarmed tick dmid does not count as a tick_dmid failure when DRY_TICK_DMID_REQUIRE_WARM_SAMPLE is true.
- Runtime candle-cache path lookup now has a short TTL path cache to stop per-signal glob scans across the candle cache.
- TDI snapshot logger now rotates oversized tdi_snapshots.jsonl before append. Existing oversized file was rotated to tdi_snapshots.20260603T150805Z.rotated.jsonl; fresh tdi_snapshots.jsonl was about 0.9 MB after smoke observe.

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=0, closed=0, wins=0, losses=0.
- No credible positive dry profitability evidence yet because opened=0.

Verification evidence:
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py managers\logging_manager\tdi_logger.py: OK.
- test_koko_dry_candidate_rank.py: 9 OK.
- test_koko_dry_observe_readiness.py: 5 OK.
- test_tdi_logger.py: 1 OK.
- Latest bounded DRY observe with supervisor preflight refresh enabled: exit 0, ticks=3, opened=0, dry P&L flat.

Guardrails:
- Coinbase/order placement path not touched by this relay update or the latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Reporting note:
- Local SMTP reporter still lacks SMTP env and writes .eml outbox files instead of sending directly; Gmail connector was used for material status email while this local env gap remains.
