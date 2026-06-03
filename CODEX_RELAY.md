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

Timestamp: 2026-06-03T14:44:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally.
- Latest local DRY observe task: local pid completed at 2026-06-03T14:43:08Z.
- Latest supervised DRY observe completed: exit 0, ticks=2.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: dryopen=0, drysig=0, dryblk=0.
- Data/preflight feed coverage is now usable after cache refresh; do not tune profit scoring while opened=0.
- Runtime preflight after refresh: files_checked=393, files_present=393, timestamp_usable_files=347, timestamp_usable_ratio=0.883, quote_volume_ge_min=17, dmid_ge_min=29, dmid_ge_min_and_quote_volume_ge_min=3.
- Ranked top-120 preflight is supported: mode=timestamp_liquid_green_dmid_desc, timestamp_usable_ratio=1.0, green_ratio=0.8667, liquid_subset_products=17, would_pass_configured_regime=true.
- Latest drygate after the 2-tick observe points to current recent-candle/tick dmid misses, not stale timestamp coverage. Latest near miss: ETH-USD dmid with score=0.9999, spread=0.05/5.00, TOB=1025/500, quote_volume=8489366/250000, recent_candle_dmid=-11.32/40.00, tick_dmid=-5.78/10.00.
- Added diagnostics clarify upstream trough-blocked paper signals by separating dry_shadow_recent_dmid_bps and dry_shadow_tick_dmid_bps. This prevents tick-dmid warmup from masquerading as stale recent-candle feed.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest_runtime_window.json

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=0, closed=0, wins=0, losses=0.
- No credible positive dry profitability evidence yet because opened=0.

Verification evidence:
- test_koko_dry_candidate_rank.py: 5 OK.
- test_koko_dry_observe_readiness.py: 3 OK.
- test_koko_cache_market_regime.py: 15 OK.
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\koko_cache_market_regime.py: OK.
- Public DRY recent-candle cache refresh: refreshed=393, failed=0.
- Runtime preflight after refresh: observe_window_worthwhile=true, ranked_observe_supported=true, cache_refresh_required=false.
- Latest 2-tick DRY observe: exit 0, opened=0, dry P&L flat.

Guardrails:
- Coinbase/order placement path not changed in this relay update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact.
