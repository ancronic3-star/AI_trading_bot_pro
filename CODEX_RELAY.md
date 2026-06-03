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

Timestamp: 2026-06-03T15:31:08Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed at 2026-06-03T15:28:53Z.
- Latest supervised DRY observe completed: exit 0, ticks=5, elapsed_sec=43.4.
- DRY=true, LIVE=false.
- PFID present in environment: yes.
- COINBASE_KEY_FILE present in environment: yes.

Current blocker:
- The previous opened=0 blocker has changed: DRY observe can now open a candidate under a DRY-only observe probe.
- New current blocker: no credible positive dry profitability evidence yet. One paper position is open, but realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD at latest mark.
- Normal all-pass DRY gate is still breadth/dmid constrained: latest readiness shows all_pass_candidates=0 and observe_open_candidate_present=false for normal gates.
- Preflight/feed lane is usable but green-breadth blocked: latest preflight reports cache_refresh_required=false, supported=false, timestamp_ratio=0.9109, liquid=13, blocker=green_breadth.
- U=0 / stale-feed cause is not the current blocker: latest tick_diag has U=120, S=393, brf=120, and preflight timestamp_ratio=0.9109.
- Liquid subset coverage remains thin: latest cache regime has quote_volume_ge_min=13 and dmid_ge_min_and_quote_volume_ge_min=0.
- Green breadth remains weak: market_green_ratio=0.4667 vs dry_min_market_green_ratio=0.85; market_dmid_bps=30.5869; market_breadth_n=120; source=recent_candle.
- Missing product/cache gap status: latest preflight reports no refresh required; previous refresh completed 392/393 with 1 failed.
- Continue DRY observe for mark/exit/P&L evidence before resuming Profit Score tuning.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Existing lane files still changed locally: C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Added a DRY-only observe probe path in run_manager that can open a paper signal only when failures are limited to configured dmid/market_breadth cases and floor checks pass.
- Added probe settings in run_settings.json: DRY_OBSERVE_PROBE_ENABLED=true, allowed failures dmid and market_breadth, min probe dmid=-20.0 bps, min probe market dmid=0.0 bps.
- Added tests covering allowed probe failures and dmid/market floor requirements.
- No Profit Score tuning was performed while opened was 0.

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=1, closed=0, wins=0, losses=0.
- Material open evidence: PAPER_BUY_SIGNAL opened ADA-USD at 2026-06-03T15:28:14Z with dry_observe_probe=true, blocked_by=dry, dry_pnl_result=opened.
- ADA-USD evidence: score=0.9896, spread=4.6805/5.0 bps, TOB=4061.9/500 USD, quote_volume=507464.6802/250000 USD, trough_pct=0.25/0.3, recent dmid=-14.0581 bps, probe dmid floor=-20.0 bps, market_dmid_bps=30.5869, market_green_ratio=0.4667/0.85.
- No credible positive dry profitability evidence yet because the open position is flat at latest mark and no closed win exists.

Verification evidence:
- python -m unittest discover -s tests -p 'test_koko_dry_candidate_rank.py': 11 OK.
- python -m unittest discover -s tests -p 'test_koko_dry_observe_readiness.py': 6 OK.
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py: OK.
- run_settings.json JSON parse: OK.
- 5-tick supervised DRY observe: exit 0, opened=1, open_count=1, closed=0, wins=0, losses=0, blocked_open=0.

Guardrails:
- Coinbase/order placement path not touched by this relay update or the latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue bounded DRY observe with DRY=true and LIVE=false to collect mark/exit evidence for the open ADA-USD paper position.
- If unrealized or realized P&L moves materially, report immediately.
- If the DRY probe trends negative, tighten or disable probe settings and report the blocker.

User action required:
- No.

Reporting note:
- Gmail connector should be used for material status email while local SMTP reporter env remains unavailable.
