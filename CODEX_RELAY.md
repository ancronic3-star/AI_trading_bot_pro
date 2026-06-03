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

Timestamp: 2026-06-03T22:28:42Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local run marker: stale pid=856 ts=21:52:27; process is not running.
- Latest local DRY observe wait probe: completed with a 5-second env cap, DRY=true, LIVE=false, no new DRY opens.
- TDI Factor reporting destination: tdifactorToday@gmail.com.
- TDI Factor summary cadence: every two hours; no duplicate/no-fluff updates.
- No duplicate/no-fluff email rule remains active.

Current blocker:
- Primary blocker in the latest cache/preflight window: green_breadth.
- Current cache support: cache_supported=false because green_ratio=0.2215 vs min 0.8500, green_shortfall=0.6285.
- Timestamp coverage is usable: timestamp_ratio=0.9593, timestamp_shortfall=0.
- Liquid subset coverage is usable at the full cache level: liquid_subset=22 vs required 10, liquid_shortfall=0.
- Dmid/liquidity overlap is not usable in the current window: dmid_liquidity_overlap=0 and dmid_liquidity_range_overlap=0.
- Best ranked observe subset is also not openable: mode=dmid_desc, green_ratio=0.6667, liquid_subset=3, dmid_liquidity_overlap=0.
- U=0 / stale-feed is not the current cause; latest reporter evidence has U=120, S=393, drysig=0, dryopen=0.
- Missing product/cache gap is not the current cause: files_present=393, missing_files=0.
- Previous runtime evidence still matters: cache-liquid+dmid candidates were skipped early by trough, dryliqskip=trough:7, dryliqskip_top includes ENA-USD qv=955,798 rdmid=143.11 score=0.9613.
- DRY-only trough probe was added so trough-only candidates can continue to normal dry quality gates when DRY_OBSERVE_TROUGH_PROBE_ENABLED=true, but the latest bounded sample did not exercise it because preflight stopped on green_breadth/dmid_liquidity_overlap=0 first.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- opened=11 historically; blocked_open=46; quarantined=7.
- No new DRY opens in the latest bounded samples.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.
- Direct runtime dry_pnl_score.json is currently reset/empty, but TDI reporter status resolves the prior material dry P&L snapshot above; no positive-profit evidence was found.

Patch/change evidence:
- Readiness now parses and promotes dryliqskip and dryliqskip_top for cache-liquid+dmid candidates skipped before PAPER_BUY_SIGNAL logging.
- TDI status reporting now uses promoted dryliqskip evidence when it is the clearer blocker, includes dryliqskip in readiness evidence, and marks dead local run markers as stale.
- Added DRY-only trough probe in run_manager: only enabled when DRY=true and DRY_OBSERVE_TROUGH_PROBE_ENABLED=true, only for reason=trough, and only after spread, tob_usd, quote_volume, candle range, and dmid gates pass.
- Added DRY_OBSERVE_TROUGH_PROBE_ENABLED=true to run_settings.json; DRY remains true and LIVE remains false.
- Supervisor observe-window wait now reads KOKO_SUPERVISOR_WAIT_FOR_OBSERVE_WINDOW, KOKO_SUPERVISOR_OBSERVE_WINDOW_POLL_SEC, and KOKO_SUPERVISOR_OBSERVE_WINDOW_MAX_WAIT_SEC from env or run_settings.json, with env taking priority.
- Added run_settings wait controls: KOKO_SUPERVISOR_WAIT_FOR_OBSERVE_WINDOW=true, poll_sec=300, max_wait_sec=7200 so unattended DRY observe waits for a usable market window instead of ending immediately on a transient preflight miss.
- No scoring thresholds were tuned.
- Coinbase/order placement path was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 12 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 21 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 19 OK in local runtime.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 18 OK in local runtime.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py tools\run_koko_dry_supervised.py: OK in local runtime.
- Latest bounded DRY wait probe used env max_wait_sec=5, refreshed 392/393 products, and proved the wait loop logs/checks the current blocker without running the full two-hour wait in this interactive turn.
- Cloud checkout is a slim handoff tree; focused runtime tests were run against C:\ai_trading_bot_koko.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Continue data/preflight lane, not Profit Score tuning.
- Let unattended DRY observe wait for a cache window with usable green breadth and dmid/liquidity overlap instead of ending immediately on a transient bad preflight window.
- Then rerun DRY observe with the DRY-only trough probe enabled and verify whether candidates can open.
- Keep focus on data/preflight/openability while opened=0; do not tune Profit Score yet.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
