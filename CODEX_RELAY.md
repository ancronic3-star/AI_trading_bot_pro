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

Timestamp: 2026-06-03T20:53:38Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY task: completed; stale run_active.json recorded pid=5312 at 20:49:35, and that process is no longer running.
- Latest entry-preflight sample closed the SUI-USD dry open with opened_delta=0 and closed_delta=1, then skipped full observe because entry spread/top-book overlap was still zero.
- Latest local monitor snapshot: local pid=5312 ts=20:49:35, DRY=true, LIVE=false.
- TDI Factor Gmail/reporting cadence remains two-hour summaries plus immediate material events only; no duplicate/spam updates.

Current blocker:
- Primary blocker: entry spread/top-book overlap=0.
- Latest readiness: signals=371, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, observe_open_candidate_present=false, observe_probe_candidate_present=false.
- Closest current entry shortfall: USELESS-USD spread_excess=5.63 bps with top-of-book shortfall=0.
- Green breadth is weak: green_ratio=0.1868 vs required 0.8500; best ranked green=0.5795.
- Timestamp coverage is usable: timestamp_ratio=0.8779 and timestamp_shortfall=0.
- Liquid subset coverage is usable: liquid_subset=25 vs required 10, liquid_shortfall=0.
- U=0 / stale-feed is not the current cause: latest tick shows U=120, S=393, brf=80.
- Missing product/cache gap is not current in latest evidence: cache_supported=true.
- Do not tune Profit Score while open_count=0 and dryopen=0.

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
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_monitor_state.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_reporter_state.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 19/100.
- dry P&L: realized=-0.06120051 USD, unrealized=0.00000000 USD, net=-0.06120051 USD.
- open/closed/wins/losses: open=0, closed=8, wins=1, losses=7.
- opened=8 historically; blocked_open=42; quarantined=6.
- Latest dry ledger event: SUI-USD closed via loss_trim at 2026-06-03T20:49:40Z.
- Latest SUI-USD close evidence: -73.9189 bps, -0.02217568 USD.
- Prior positive evidence still exists but was not retained: SUI-USD was previously marked as high as unrealized_pnl_bps=+74.5349 before reversing.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Latest entry readiness: entry_liquid_dmid_spread_tob_overlap_gap=true, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0.
- Book metric coverage: source_present=116, source_missing=255, present_ratio=0.3127.
- Dmid coverage: dmid_present=371, dmid_usable=7, dmid_usable_ratio=0.0189.
- Liquid coverage: quote_volume_present=371, quote_volume_usable=29, liquid_dmid_overlap=2.
- Top-book coverage: tob_usable=113, tob_usable_ratio=0.3046.
- Latest tick diagnostic: tick=1 U=120 S=393 top=393 chk=393 brf=80 drysig=0 dryopen=0.
- Dominant blockers: spread=270, trough_wait=46, trough=23, tob_usd=22, dmid=10.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 12 OK.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 19 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 18 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 7 OK.
- python -m py_compile tools\run_koko_dry_supervised.py: OK after duplicate-report suppression patch.
- python -m json.tool run_settings.json: OK.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- TDI report cadence remains TDI_REPORT_HOURLY_SEC=7200.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Stay in the data/preflight lane until entry spread/top-book overlap returns and dryopen can become nonzero.
- Investigate why positive dry marks were allowed to reverse into loss_trim without changing static TP/SL or Coinbase/order code.
- Do not keep tuning score while open_count=0 and dryopen=0.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
