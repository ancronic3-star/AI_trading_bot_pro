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

Timestamp: 2026-06-03T21:16:46Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY mark task: completed, pid=23636, start ts=21:14:55.
- Latest local monitor snapshot: 2026-06-03T21:16:02Z, DRY=true, LIVE=false.
- TDI Factor Gmail/reporting cadence remains two-hour summaries plus immediate material events only; no duplicate/spam updates.
- Material patch applied: DRY-only profit-protect exit logic now tracks peak dry P&L and can close a positive giveback as profit_protect before it decays into loss_trim.
- Material patch applied: DRY entry gate now enforces DRY_PNL_MAX_NEGATIVE_OPEN_SHARE when configured.
- Material config update applied: cloud template profit-protect thresholds now match runtime tighter settings, min_peak=15 bps, giveback=10 bps, retain=2 bps.

Current blocker:
- Primary blocker: entry spread/top-book overlap=0.
- Latest readiness: signals=330, liquid_dmid_overlap=7, liquid_dmid_spread_tob_overlap=0, observe_open_candidate_present=false, observe_probe_candidate_present=false.
- Closest current entry shortfall: MON-USD spread_excess=4.82 bps with top-of-book shortfall=0.
- Green breadth is still short: green_ratio=0.7190 vs required 0.8500; best ranked green=1.0000.
- Timestamp coverage is usable: timestamp_ratio=0.9466 and timestamp_shortfall=0.
- Liquid subset coverage is usable: liquid_subset=30 vs required 10, liquid_shortfall=0.
- U=0 / stale-feed is not the current cause: latest tick shows U=120, S=393, brf=80.
- Missing product/cache gap is not current in latest evidence: cache_supported=true.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko_cloud_source\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko_cloud_source\run_settings.template.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_monitor_state.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_reporter_state.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- opened=11 historically; blocked_open=46; quarantined=7.
- Latest dry ledger events: ETH-USD and XRP-USD closed via profit_protect at 2026-06-03T21:15:01Z after the tighter thresholds were applied.
- ETH-USD profit_protect evidence: peak=35.6220 bps, close=21.0164 bps, pnl_usd=0.00630493.
- XRP-USD profit_protect evidence: peak=29.9638 bps, close=13.3172 bps, pnl_usd=0.00399517.
- HBAR-USD counter-evidence before the tighter thresholds: peak=19.2971 bps, later closed loss_trim at -14.6190 bps, pnl_usd=-0.00438571.
- Profit-protect test evidence: synthetic dry ledger test marks SUI-USD from +80.0 bps down to +55.0 bps and closes as exit_reason=profit_protect, with static TP/SL unchanged.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Latest entry readiness: entry_liquid_dmid_spread_tob_overlap_gap=true, liquid_dmid_overlap=7, liquid_dmid_spread_tob_overlap=0.
- Book metric coverage: source_present=217, source_missing=113, present_ratio=0.6576.
- Dmid coverage: dmid_present=330, dmid_usable=117, dmid_usable_ratio=0.3545.
- Liquid coverage: quote_volume_present=330, quote_volume_usable=10, liquid_dmid_overlap=7.
- Top-book coverage: tob_usable=80, tob_usable_ratio=0.2424.
- Latest tick diagnostic: tick=1 U=120 S=393 top=393 chk=393 brf=80 drysig=0 dryopen=0.
- Dominant blockers: trough=177, spread=118, trough_wait=29, tob_usd=5, dmid=1.

Verification evidence:
- python -m unittest tests.test_cloud_only_corrections: 6 OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 12 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 18 OK.
- python -m py_compile managers\run_manager\run_manager.py: OK in local runtime.
- python -m py_compile managers\run_manager\run_manager.py: OK in cloud checkout.
- python -m json.tool run_settings.json: OK.
- python -m json.tool run_settings.template.json: OK in cloud checkout.
- 2026-06-03T21:14:55Z direct DRY mark sample: completed with DRY=true and LIVE=false; ETH-USD and XRP-USD closed via profit_protect.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- TDI report cadence remains two-hour summaries: TDI_REPORT_HOURLY_SEC=7200.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Runtime profit-protect settings now active without changing static TP/SL: enabled=true, min_peak=15 bps, giveback=10 bps, retain=2 bps.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Stay in the data/preflight lane until entry spread/top-book overlap returns and dryopen can become nonzero.
- Resume DRY observe only when entry spread/top-book overlap returns; profit-protect will then collect evidence on future positive dry opens.
- Do not keep tuning score while open_count=0 and dryopen=0.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
