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

Timestamp: 2026-06-03T22:42:24Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local run marker: stale pid=13936 ts=22:36:07; process completed bounded sample.
- Latest local DRY supervised sample: completed entry sample plus one continuous tick, DRY=true, LIVE=false, no new DRY opens.
- TDI Factor reporting destination: tdifactorToday@gmail.com.
- TDI Factor summary cadence: every two hours; no duplicate/no-fluff updates.
- No duplicate/no-fluff email rule remains active.

Current blocker:
- Primary blocker moved past cache preflight into candidate openability: liquid+dmid overlap=0 in the runtime readiness sample.
- Current cache support: cache_supported=true because ranked probe observe is supported; broad green is still weak but no longer terminal for preflight.
- Timestamp coverage is usable: timestamp_ratio=0.8830, timestamp_shortfall=0.
- Liquid subset coverage is usable at the full cache level: liquid_subset=16 vs required 10, liquid_shortfall=0.
- Main dmid/liquidity overlap remains zero in runtime readiness: liquid=3, dmid=4, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Best ranked probe observe: mode=dmid_desc, green_ratio=0.7125, liquid_subset=2, probe_quote_volume_overlap=3, probe_quote_volume_range_overlap=2.
- Probe quote candidates are now explicit in reporting: BILL-USD, LIGHTER-USD, DEGEN-USD.
- Probe quote range-clean candidates are now explicit in reporting: BILL-USD, LIGHTER-USD.
- Runtime mapping shows BILL-USD is the closest active probe candidate but currently fails book gates: spr=5.7514 bps vs max 5.0, tob_usd=15.61 vs min 500, qv=208,024 vs main 250k, rdmid=91.65.
- LIGHTER-USD and DEGEN-USD appear in cache probe diagnostics but were not current actionable runtime probe candidates in the latest one-tick sample; older runtime rows show LIGHTER spread/tob miss and DEGEN spread/tob/dmid miss.
- U=0 / stale-feed is not the current cause; latest reporter evidence has U=120, S=393, drysig=0, dryopen=0.
- Missing product/cache gap is not the current cause: files_present=393, missing_files=0.
- Entry sample no longer stops the full block when cache-ranked probe evidence is present; latest bounded sample reached continuous_start and continuous_done.
- Runtime readiness still has no open/probe candidate from the one-tick sample; dominant blocker is trough/spread/tob/quote quality.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
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
- Cache preflight now mirrors DRY observe probe quote-volume semantics: it counts probe_quote_volume_overlap separately from the main 250k liquidity gate using DRY_OBSERVE_PROBE_MIN_QUOTE_VOLUME_USD and DRY_OBSERVE_PROBE_MIN_QUOTE_FAILURE_DMID_BPS.
- DRY_OBSERVE_PROBE_ALLOWED_FAILURES now includes quote_volume alongside market_breadth, still DRY-only and still constrained by the 50k quote probe floor and dmid floor.
- Entry-preflight continuation now honors cache-ranked probe support, so a one-tick readiness spread/top-book gap does not end the full DRY block when cache preflight says a ranked probe window is worthwhile.
- Cache preflight now emits top_timestamp_usable_probe_quote_candidates and top_timestamp_usable_probe_quote_range_candidates.
- TDI reporter now includes best_probe fields and probe candidate IDs in readiness evidence, so Gmail/relay can name the cache probe candidates without manual log parsing.
- No scoring thresholds were tuned.
- Coinbase/order placement path was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 12 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 21 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 21 OK in local runtime.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 19 OK in local runtime.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 20 OK in local runtime.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py tools\run_koko_dry_supervised.py tools\koko_cache_market_regime.py: OK in local runtime.
- Latest bounded DRY sample with KOKO_SUPERVISOR_MAX_CYCLES=2 reached continuous_start ticks=1 and continuous_done elapsed_sec=0.6 after the entry sample.
- Latest reporter preview was no-send/hourly_not_due and included probe_quote_candidates=BILL-USD|LIGHTER-USD|DEGEN-USD plus probe_quote_range_candidates=BILL-USD|LIGHTER-USD.
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
- Continue candidate openability inside DRY observe now that cache preflight and entry preflight no longer stop early.
- Continue runtime openability from the named candidates: BILL-USD is closest but needs current spread/top-book to improve; do not tune score or weaken book gates.
- Rerun longer DRY observe only after confirming the probe/openability evidence path, then resume dry P&L improvement.
- Keep focus on data/preflight/openability while opened=0; do not tune Profit Score yet.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
