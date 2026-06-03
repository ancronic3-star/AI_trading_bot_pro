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

Timestamp: 2026-06-03T15:22:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed at 2026-06-03T15:21:58Z.
- Latest supervised DRY observe completed: exit 0, ticks=3, elapsed_sec=23.6.
- Prior longer supervised DRY observe also completed: exit 0, ticks=8, elapsed_sec=77.3.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: opened=0, open_count=0, closed=0, wins=0, losses=0.
- Preflight/feed lane is usable but breadth-blocked: latest preflight reports cache_refresh_required=false, supported=false, timestamp_ratio=0.9109, liquid=13, blocker=green_breadth.
- Latest readiness is scoped to the latest local run and shows signals=393, all_pass_candidates=0, one_gate_near_miss_present=true, dominant_blocker=spread.
- Latest tick_diag coverage: tick=3, U=120, S=393, brf=120, drysig=0, dryopen=0, dryblk=0, tdmid=393, tdmidnz=39, tdmidok=3.
- Current green-breadth evidence is now structured in readiness: market_green_ratio=0.4667 vs dry_min_market_green_ratio=0.85, market_breadth_n=120, market_breadth_source=recent_candle, market_dmid_bps=30.59.
- Latest current-tick near candidates fail market_breadth plus dmid: ETH-USD dmid|market_breadth, SOL-USD dmid|market_breadth, ADA-USD dmid|market_breadth; BTC-USD and XRP-USD also add tob.
- Closest paper-signal one-gate near miss remains dmid only: ADA-USD recent-candle dmid=-14.0581/40.00 with spread, TOB, quote volume, and trough passing on tick 1.
- U=0 / stale-feed cause is not the current blocker: latest tick_diag has U=120 and preflight timestamp_ratio=0.9109.
- Missing product/cache gap status: latest preflight reports no refresh required; previous refresh completed 392/393 with 1 failed.
- Do not tune Profit Score while opened=0; next action remains DRY open-lane/feed/preflight alignment around green breadth and dmid, not score tuning.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py, C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, tools\run_koko_dry_supervised.py, tests\test_run_koko_dry_supervised_preflight.py, tools\koko_cache_market_regime.py, tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Runtime tick diagnostics now emit drynear_top with up to five near candidates each tick, instead of only one drynear candidate.
- Runtime drynear/drynear_top now include market-breadth details: mbr=value/min, mdmid=value/min, mbn=sample count, msrc=source.
- Readiness parses drynear_top into tick_diag_coverage.latest_near_candidates and near_tail with structured fields for failures, score, spread, TOB, quote volume, recent dmid, tick dmid, warm state, market green ratio, market dmid, breadth sample count, and breadth source.
- This was diagnostics/data-lane only. No score thresholds were tuned.

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=0, closed=0, wins=0, losses=0.
- No credible positive dry profitability evidence yet because opened=0.

Verification evidence:
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py: OK.
- test_koko_dry_candidate_rank.py: 9 OK.
- test_koko_dry_observe_readiness.py: 6 OK.
- 8-tick supervised DRY observe: exit 0, opened=0, green_breadth blocker exposed.
- 3-tick supervised DRY observe after diagnostics patch: exit 0, opened=0, structured market breadth fields present in readiness.

Guardrails:
- Coinbase/order placement path not touched by this relay update or the latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Reporting note:
- Gmail connector is being used for material status email while local SMTP reporter env remains unavailable.
