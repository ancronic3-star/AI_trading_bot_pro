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

Timestamp: 2026-06-03T14:58:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally.
- Latest local supervised DRY observe task: completed at 2026-06-03T14:54:23Z.
- Latest supervised DRY observe completed: exit 0, ticks=4, elapsed_sec=36.6.
- No run_koko_dry_supervised/run_manager trading process left running from this observe.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: opened=0, open_count=0, closed=0, wins=0, losses=0.
- Data/preflight cache lane is now usable: supervisor preflight cache guard saw cache_refresh_required=false, supported=true, timestamp_ratio=0.883, liquid=16, blocker empty before the latest observe.
- Previous stale timestamp blocker was handled by automatic public recent-candle cache refresh inside tools/run_koko_dry_supervised.py; earlier refresh result was refreshed=392, failed=1, supported=true, timestamp_ratio=0.883, liquid=16.
- Remaining blocker is current open-lane eligibility, not Profit Score tuning: latest drynear evidence shows candidates missing actual dmid thresholds after usable cache coverage. ETH-USD had recent_candle_dmid=17.67/40.00 then tick_dmid near 0.70/10.00; LINK-USD had recent_candle_dmid=30.77/40.00 and tick_dmid=1.77/10.00.
- U=0/stale-feed false cause reduced: tick dmid now distinguishes unwarmed first samples from real tick movement. Unwarmed tick confirmation no longer blocks when recent-candle dmid passes, while warmed tick dmid below DRY_MIN_TICK_DMID_BPS still blocks.
- Do not tune profit scoring while opened=0; next action should stay in runtime open-lane diagnostics and candidate/feed alignment.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest_runtime_window.json

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=0, closed=0, wins=0, losses=0.
- No credible positive dry profitability evidence yet because opened=0.

Verification evidence:
- py_compile managers\run_manager\run_manager.py tools\run_koko_dry_supervised.py tools\koko_cache_market_regime.py: OK.
- test_koko_dry_candidate_rank.py: 8 OK.
- test_run_koko_dry_supervised_preflight.py: 2 OK.
- test_koko_cache_market_regime.py: 15 OK.
- Earlier test_koko_dry_observe_readiness.py: 3 OK.
- Latest bounded DRY observe with supervisor preflight refresh enabled: exit 0, ticks=4, opened=0, dry P&L flat.

Guardrails:
- Coinbase/order placement path not touched by this relay update or the latest patches.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
