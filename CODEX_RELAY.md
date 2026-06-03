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

Timestamp: 2026-06-03T14:23:03Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally.
- Latest local DRY observe task: local pid=23800 ts=2026-06-03T14:21:19Z.
- Latest supervised DRY observe completed: exit 0, elapsed 28.3 seconds, ticks=3.
- DRY=true, LIVE=false.

Current blocker:
- DRY observe still opens no candidates: dryopen=0, drysig=0.
- Current evidence points to open-candidate gate/coverage blockers, not profit scoring.
- Latest readiness blocker summary: dominant blocker spread; liquid subset all_pass=0; one near-miss HYPE-USD blocked only by tick_dmid in tick-1 paper signal diagnostics.
- Latest tick_diag coverage proves later-tick tick-dmid feed is visible: max_tick_dmid_nonzero=77, max_tick_dmid_usable=15, brf capped at 120.

Files changed in current local worktree for this lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py

Dry Profit Score evidence:
- Current Profit Score: 0/100.
- dry P&L: realized=0.00 USD, unrealized=0.00 USD, net=0.00 USD.
- open/closed/wins/losses: open=0, closed=0, wins=0, losses=0.
- No credible positive dry profitability evidence yet because opened=0.

Verification evidence:
- test_koko_dry_candidate_rank.py: 4 OK.
- test_koko_dry_observe_readiness.py: 3 OK.
- test_koko_cache_market_regime.py: 14 OK.
- py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py: OK.

Guardrails:
- Coinbase/order placement path not changed in this relay update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact.
