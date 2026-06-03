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

Timestamp: 2026-06-03T16:33:05Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T16:32:46Z after 4 ticks with DRY=true and LIVE=false.
- Material Gmail status sent to tdifactorToday@gmail.com: message id 19e8e56ffd0902dc.
- Previous TDI snapshot logger access-violation blocker remains mitigated by TDI_SNAPSHOT_ENABLED=false and tdi_logger hardening.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L is negative after five DRY paper probe losses: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Main broad blocker remains green_breadth; latest open-lane blockers are dmid/spread with drysig=0 and dryopen=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, chk=393, brf=25, tdmid=393, tdmidnz=22, tdmidok=4.
- Latest readiness after patch has all_pass_candidates=0 and observe_probe_candidate_present=false for the new 16:32 run.
- The earlier NEAR market-breadth-only mismatch is fixed in readiness: it is no longer reported as all-pass and is only marked probe-eligible when DRY observe probe floors allow it.
- Current nearest fresh candidate: NEAR-USD is blocked by spread only, spread=7.0671 bps vs max=5.0, dmid=49.1573 bps, quote_volume=1898059.8699 USD, tob=4349.13 USD.
- Current latest tick_diag drynear is BTC-USD blocked by dmid|market_breadth: recent dmid=-57.26/40.00, market_green_ratio=0.2583/0.8500, dryopen=0.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\run_settings.json
- Existing lane files still changed locally: C:\ai_trading_bot_koko\managers\run_manager\run_manager.py, C:\ai_trading_bot_koko\managers\logging_manager\tdi_logger.py, C:\ai_trading_bot_koko\tools\tdi_status_reporter.py, C:\ai_trading_bot_koko\tests\test_tdi_logger.py, C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py, C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Changes applied in this update:
- Patched tools/koko_dry_observe_readiness.py so market_breadth-blocked candidates are no longer counted as all-pass.
- Added dry_observe_probe eligibility reporting to readiness output, mirroring runtime floors/failure allow-list.
- Set DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0 in run_settings.json so a market-breadth-only DRY observe probe can open when product gates pass.
- Added regression tests for market-breadth all-pass mismatch and probe eligibility.
- Added runtime probe test for the disabled market-dmid floor case.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- DRY remains true and LIVE remains false.

Dry Profit Score evidence:
- Current Profit Score observed in local reporter: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 8 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 13 OK.
- py_compile tools\koko_dry_observe_readiness.py managers\run_manager\run_manager.py: OK via isolated PYTHONPYCACHEPREFIX.
- Bounded supervised DRY observe after patch: exit 0, ticks=4, drysig=0, dryopen=0.
- Latest readiness regenerated after patch for 2026-06-03T16:32:00Z window: all_pass_candidates=0, observe_probe_candidate_present=false, signals=393.
- Settings check remains: DRY=True, LIVE=False, allowed probe failures=[market_breadth], DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS=-999999.0, TP=8.0, SL=0.8.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe and data/preflight coverage checks until a product-level candidate is all-pass or market-breadth-only probe-eligible again.
- Current immediate open-lane focus: spread on NEAR-style dmid/liquid candidates and dmid on liquid majors while green breadth remains weak.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.

User action required:
- No.

Reporting note:
- Gmail connector is the actual delivery path while local SMTP env is unavailable.
- Latest material status email was sent to tdifactorToday@gmail.com.
