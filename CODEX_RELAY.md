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

Timestamp: 2026-06-03T20:18:16Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY task: completed exit 0 on 2026-06-03 with DRY=true and LIVE=false.
- Latest wait-mode observe smoke found an actionable ranked preflight window and ran instead of skipping.
- Latest 12-tick DRY observe closed the prior SUI-USD open as the first dry win.
- Added an entry preflight sample in the supervised DRY runner so the runner samples one DRY tick after candle/cache preflight and records actual spread/top-book entry readiness before spending a full observe block.
- Latest entry-preflight sample found real entry overlap and opened SUI-USD again; latest follow-up marked it open and negative.
- TDI Factor Gmail reporting cadence: every two hours plus immediate material events. User update cadence should now be two-hour email summaries unless a material event occurs.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- The old opened=0/preflight-feed blocker is no longer current: DRY observe opened SUI-USD again after entry preflight found a real all-pass candidate.
- Current blocker is negative total dry net P&L with one open SUI-USD position currently negative; not Profit Score tuning.
- Latest entry readiness: signals=368, observe_open_candidate_present=true, liquid_dmid_overlap=6, liquid_dmid_spread_tob_overlap=1, dominant_blocker=spread.
- Entry spread/top-book overlap is no longer zero in the current evidence.
- U=0 / stale-feed cause is not current in the latest evidence; cache files are present and mtime_fresh_ratio=1.0.
- Missing product/cache gap is not current: files_present=393, missing_files=0.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Added preflight wait-for-observe-window mode in the supervised DRY runner so DRY observe can wait for usable coverage instead of ending at a red preflight snapshot.
- Added entry-preflight sample logic in tools\run_koko_dry_supervised.py: after candle/cache preflight passes, the runner can take one DRY sample tick, regenerate readiness, and continue only when the sample opens, finds an all-pass candidate, or finds an eligible probe candidate.
- Added supervisor tests for the entry-preflight continue/skip decisions.
- Preserved the preflight skip when the window remains non-actionable.
- Changed TDI Factor periodic email summary cadence to two hours through code default and run_settings.json.
- Set DRY_PNL_MAX_OPEN_POSITIONS=4 for DRY-only evidence collection; BUY_MAX_OPEN stayed 1.
- Ran DRY observe after wait-mode and entry sample found usable coverage; prior SUI-USD closed as a win and a new SUI-USD dry open is currently negative.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.03902483 USD, unrealized=-0.00332635 USD, net=-0.04235118 USD.
- open/closed/wins/losses: open=1, closed=7, wins=1, losses=6.
- opened=8 historically; latest open is SUI-USD.
- Prior SUI-USD close evidence: +12.7924 bps, +0.00383772 USD, first win.
- Current SUI-USD open mark: unrealized_pnl_bps=-11.0878, unrealized_pnl_usd=-0.00332635.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Latest entry readiness: signals=368, observe_open_candidate_present=true, entry_liquid_dmid_spread_tob_overlap_gap=false, liquid_dmid_overlap=6, liquid_dmid_spread_tob_overlap=1.
- Latest entry sample evidence: opened_delta=1, closed_delta=0, signals=365, liquid_dmid=6, liquid_dmid_spread_tob=1.
- Latest follow-up evidence: open remained 1 and unrealized improved from -0.00443514 USD to -0.00332635 USD.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 10 OK.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 19 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 18 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 7 OK.
- python -m py_compile tools\run_koko_dry_supervised.py tools\koko_dry_observe_readiness.py: OK.
- python -m py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py: OK from prior check.
- python -m py_compile managers\run_manager\run_manager.py tools\tdi_status_reporter.py tools\tdi_status_monitor.py: OK.
- python -m json.tool run_settings.json: OK.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Continue DRY observe only through the data/preflight lane with wait-for-observe-window and entry-preflight sample enabled.
- Do not tune Profit Score while fresh dry opens are unavailable.
- Let the current SUI-USD dry ledger position mark/close under existing static TP/SL and dry-cycle exit rules.
- Collect more dry P&L evidence until net dry P&L improves materially or a new blocker appears.
- Keep DRY=true and LIVE=false.

User action required:
- No.
