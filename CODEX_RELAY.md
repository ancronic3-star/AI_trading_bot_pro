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

Timestamp: 2026-06-03T14:39:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally.
- Latest local DRY observe task: local pid=19092 ts=2026-06-03T14:37:26Z.
- Latest supervised DRY observe completed: exit 0, elapsed 46.0 seconds, ticks=5.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: dryopen=0, drysig=0, dryblk=0.
- Data/preflight feed coverage is now usable after cache refresh; do not tune profit scoring while opened=0.
- Latest runtime preflight after refresh: files_checked=393, files_present=393, timestamp_usable_files=347, timestamp_usable_ratio=0.883, quote_volume_ge_min=17, dmid_ge_min=29, dmid_ge_min_and_quote_volume_ge_min=3.
- Ranked top-120 preflight is supported: mode=timestamp_liquid_green_dmid_desc, timestamp_usable_ratio=1.0, green_ratio=0.8667, liquid_subset_products=17, would_pass_configured_regime=true.
- Latest drygate after observe points to dmid/score/open-lane gating, not stale feed coverage. Latest near miss: HYPE-USD dmid with score=0.9908, spread=2.77/5.00, TOB=510/500, quote_volume=1792800/250000, recent_candle_dmid=36.20/40.00, tick_dmid=16.62/10.00.

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
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\koko_cache_market_regime.py: OK for touched cache preflight file and earlier dry lane files.
- Public DRY recent-candle cache refresh: refreshed=393, failed=0.
- Runtime preflight after refresh: observe_window_worthwhile=true, ranked_observe_supported=true, cache_refresh_required=false.

Guardrails:
- Coinbase/order placement path not changed in this relay update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact.
