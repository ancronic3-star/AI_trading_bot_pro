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

## Codex relay status update

Timestamp: 2026-06-04T00:59:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only reporting/evidence lane.
- TDI status reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is now reported as green_breadth+liquid+dmid overlap=0 (liquid=23, dmid=27).
- This keeps green breadth visible while preserving the actionable openability blocker instead of collapsing everything to green_breadth.
- Latest readiness remains: signals=377, liquid=23, dmid=27, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics remain improved but not sufficient: tick_diag_rows=8, max_tick_dmid_nonzero=230, max_tick_dmid_ready=114, tick_dmid_warmed_seen=true.
- Market breadth remains red: latest_mbr=0.1667/0.8500, latest_mdmid=-32.17/-999999.00.
- Runtime near miss remains ETH-USD/HYPE-style dmid|market_breadth failures, not an openable dry candidate.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Refreshed local evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Updated accumulated evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Fresh runtime-near forward latest batch: signals=10, horizon_min=5, avg_net_forward_close_bps=-37.0502, positive_net_close_rate=0.0000.
- Accumulated runtime-near forward history now has signals_unique=20; best_reason=dmid|market_breadth avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.
- This remains negative evidence and argues against loosening gates just to force opens.

Patch/change evidence:
- TDI reporter main blocker now composes cache-regime blockers with entry-openability blockers.
- Subject/body now report green_breadth+liquid+dmid overlap=0 (liquid=23, dmid=27) when both conditions are true.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\tdi_status_reporter.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 22 OK.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --horizon-min 5 --granularity 60 --limit 10 --tp-pct 8.0 --sl-pct 0.8 --out logs\runtime_near_forward_outcomes_latest.json --history-out logs\runtime_near_forward_outcomes_history.json: OK, history_signals_unique=20.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth+liquid+dmid overlap=0 (liquid=23, dmid=27).
- No lingering python.exe process after checks.
- Outbox count stayed 260; newest outbox remained tdi_status_20260604T005201Z.eml.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Keep observing only when cache/breadth suggests a plausible openability window; current breadth/overlap evidence is negative.
- Continue accumulating runtime-near forward evidence once near misses mature.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:55:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Fresh local DRY feed/cache patch applied and bounded observe completed 8/8 ticks without the prior candle-cache hang/access violation.
- Full recent-candle cache refresh completed for 120 runtime products: refreshed=120, failed=0, workers=4.
- Latest status reporter previews and monitor checks did not send email; no Coinbase/order path was touched.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled.

Current blocker:
- Primary blocker remains preflight/feed/openability coverage plus red market breadth, not Profit Score tuning.
- Crash blocker improved: the previous _trough_fetch_cached_candles / _dry_recent_candle_metrics / _dry_dmid_gate hang did not recur during the 8-tick observe.
- Timestamp coverage improved at direct cache probe scope: 109/120 runtime products timestamp-usable after refresh.
- Readiness from the bounded observe: signals=377, liquid=23, dmid=27, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics improved but are still insufficient: tick_diag_rows=8, max_tick_dmid_nonzero=230, max_tick_dmid_ready=114, tick_dmid_warmed_seen=true.
- Market breadth remains the dominant live blocker: latest_mbr=0.1667/0.8500, latest_mdmid=-32.17/-999999.00.
- Runtime near miss remains ETH-USD: failures=dmid|market_breadth, qv=13,820,015, rdmid=10.36/40.00, spread=0.06/5.00, tob=686/500.
- Best-ranked cache scope still cannot support opens: green=0.4667, liquid=1/10, dmid_liq_overlap=0, dmid_range_overlap=0, probe_quote_overlap=1, probe_range_overlap=0.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Refreshed cache evidence: C:\Users\13144\OneDrive\Documents\AI_trading_bot_pro_cloud_work\logs\backtests\_cache\candles
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals=10, horizon_min=5, best_reason=tob_usd|dmid|market_breadth, avg_net_close_bps=-65.2049, positive_net_close_rate=0.0000.

Patch/change evidence:
- Recent candle cache lookup now checks direct 1d/2d/7d cache file names before broad glob scanning and caches path misses briefly.
- Recent candle metrics can use bounded stale cache rows when the strict recent window misses, with stale_cache_used surfaced for diagnostics instead of silently reporting dmid=0.
- Missing-SMTP reporting now throttles against the newest existing outbox file if state lacks last_outbox_epoch.
- A throttled outbox attempt restores last_hourly_epoch from last_outbox_epoch so the next one-shot monitor returns hourly_not_due.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile managers\run_manager\run_manager.py tools\tdi_status_reporter.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 24 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 21 OK.
- Bounded observe command run_manager.run_loop(console=False, ticks=8): completed with exit code 0.
- Readiness regeneration for since-local-start 2026-06-03 19:49:27: OK.
- TDI status reporter --no-send preview: sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.
- Monitor one-shot verification: outbox count stayed 260 -> 260; first pass reason=outbox_throttled, second pass reason=hourly_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Continue DRY observe only when cache/breadth conditions are likely to improve; current market breadth is too red for opens.
- Keep collecting runtime-near forward evidence once candidates mature.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:45:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Fresh bounded local DRY observe was attempted with DRY=true and LIVE=false.
- The observe produced five activity ticks, then exited with a hang/access-violation dump.
- Hang evidence: C:\ai_trading_bot_koko\logs\hang_dump_7888.log points through _trough_fetch_cached_candles / _dry_recent_candle_metrics / _dry_dmid_gate.
- Latest status reporter preview was --no-send; no email was sent outside the two-hour cadence.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Primary blocker remains preflight/feed/openability coverage, not Profit Score tuning.
- New runtime blocker: bounded DRY observe now reaches ticks but crashes/hangs in the candle/cache dmid lane before usable opens.
- U=0 / stale feed is not current cause: U=120, S=393, brf=80.
- Missing product/cache gap is not the whole cause: readiness has signals=377 and book_gap=false, but liquid candidates lack usable dmid.
- Latest readiness generated_at_utc=2026-06-04T00:38:52Z.
- Coverage: signals=377, liquid=5, dmid=0, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics: tick_diag_rows=5, max_tick_dmid_nonzero=288, max_tick_dmid_ready=14, tick_dmid_warmed_seen=true.
- Green breadth is unusable in the latest fresh window: latest_mbr=0.0000/0.8500, latest_mdmid=0.00/-999999.00.
- Liquid missing dmid: BTC-USD, ETH-USD, ZEC-USD, XRP-USD, DOGE-USD.
- Closest runtime near miss: BTC-USD at ts_utc=2026-06-04T00:35:38Z, qv=2,953,902, rdmid=0.00, failures=dmid|market_breadth.
- Best-ranked cache scope still reports openability gaps: mode=dmid_desc, green=0.5464, liquid=9/10, dmid_liq_overlap=0, dmid_range_overlap=0, probe_quote_overlap=0, probe_range_overlap=0.
- Best-ranked shortfalls: green_shortfall=0.3036, liquid_shortfall=1, dmid_liq_shortfall=1, range_shortfall=1.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- New runtime failure evidence: C:\ai_trading_bot_koko\logs\hang_dump_7888.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals=10, horizon_min=5, best_reason=tob_usd|dmid|market_breadth, avg_net_close_bps=-65.2049, positive_net_close_rate=0.0000.

Patch/change evidence:
- Missing-SMTP outbox writes are now throttled by the two-hour reporting cadence instead of writing duplicate .eml files on every material-event check.
- hourly_not_due and outbox_throttled no longer advance last_hourly_epoch.
- Direct tdi_status_monitor.py --once import path now works from script execution.
- Direct monitor --once verification returned sent=false reason=hourly_not_due and did not increase outbox count.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- No lingering python.exe monitor process after verification.
- Outbox count stayed at 258 after the patched monitor check; newest outbox file remained tdi_status_20260604T004001Z.eml from before/around the throttle patch.
- python -m py_compile tools\tdi_status_reporter.py tools\tdi_status_monitor.py tools\koko_dry_observe_readiness.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 19 OK.
- python tools\tdi_status_reporter.py --mode hourly --event two_hour_summary --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Fix the candle/cache dmid observe crash first so DRY observe can run long enough to build usable market coverage.
- Continue bounded DRY observe until liquid>=10, dmid_liq_overlap>0, dmid_range_overlap/probe overlap, and green breadth can support actual dry opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:33:11Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY reporting patch completed cleanly with DRY=true and LIVE=false.
- Latest status reporter preview was --no-send; no email was sent outside the two-hour cadence.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Primary blocker remains market coverage/openability, not Profit Score tuning.
- Status subject still reports green_breadth, but the refined evidence now shows the actionable cache-ranked blocker stack.
- U=0 / stale feed is not current cause: U=120, S=393, brf=80.
- Missing product/cache gap is not current cause for the current observe sample: signals=343.
- Latest readiness generated_at_utc=2026-06-04T00:23:50Z.
- Coverage: signals=343, liquid=6, dmid=3, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics: tick_diag_rows=3, max_tick_dmid_nonzero=59, max_tick_dmid_ready=20, tick_dmid_warmed_seen=true.
- Green breadth remains short: latest_mbr=0.3500/0.8500, latest_mdmid=6.28/-999999.00.
- Best-ranked cache scope now reports the missing openability details: mode=dmid_desc, green=0.5464, liquid=9/10, dmid_liq_overlap=0, dmid_range_overlap=0, probe_quote_overlap=0, probe_range_overlap=0.
- Best-ranked shortfalls: green_shortfall=0.3036, liquid_shortfall=1, dmid_liq_shortfall=1, range_shortfall=1.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- Credible positive dry profitability evidence is not present yet.

Runtime near forward history evidence:
- Accumulated runtime_near_forward history remains negative.
- History currently has signals=10, signals_unique=10, horizon_min=5.
- dmid|market_breadth group: signals=9, avg_net_forward_close_bps=-65.5874, positive_net_close_rate=0.0000.
- tob_usd|dmid|market_breadth group: signals=1, avg_net_forward_close_bps=-65.2049, positive_net_close_rate=0.0000.
- This remains negative evidence and argues against loosening gates just to force opens.

Patch/change evidence:
- TDI status reporting now includes best_ranked/best_probe dmid-liquidity overlap, range overlap, probe overlap, liquid minimum, and shortfall fields.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 15 OK.
- python tools\tdi_status_reporter.py --mode hourly --event two_hour_summary --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth, body includes best_ranked_dmid_liq_overlap=0, best_ranked_liquid_shortfall=1, best_ranked_dmid_liq_shortfall=1, best_ranked_range_shortfall=1.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence remains two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Continue bounded DRY observe until best-ranked coverage shows liquid>=10, dmid_liq_overlap>0, and dmid_range_overlap/probe overlap can support actual dry opens.
- Keep accumulating runtime_near_forward history across observe windows.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:30:28Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY evidence update completed cleanly with DRY=true and LIVE=false.
- Latest status reporter preview was --no-send; no email was sent outside the two-hour cadence.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Primary blocker remains green_breadth plus recent/tick dmid alignment, not Profit Score tuning.
- U=0 / stale feed is not current cause: U=120, S=393, brf=80.
- Missing product/cache gap is not current cause for the current observe sample: signals=343.
- Latest readiness generated_at_utc=2026-06-04T00:23:50Z.
- Coverage: signals=343, liquid=6, dmid=3, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics: tick_diag_rows=3, max_tick_dmid_nonzero=59, max_tick_dmid_ready=20, tick_dmid_warmed_seen=true.
- Green breadth remains short: latest_mbr=0.3500/0.8500, latest_mdmid=6.28/-999999.00.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- New accumulated evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Refreshed latest evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- Credible positive dry profitability evidence is not present yet.

Runtime near forward history evidence:
- Runtime-near forward history now preserves source=runtime_near_misses and dedupes by signal_key.
- TDI status reporting now prefers logs\runtime_near_forward_outcomes_history.json when present, falling back to latest otherwise.
- History currently has signals=10, signals_unique=10, horizon_min=5.
- dmid|market_breadth group: signals=9, avg_net_forward_close_bps=-65.5874, positive_net_close_rate=0.0000.
- tob_usd|dmid|market_breadth group: signals=1, avg_net_forward_close_bps=-65.2049, positive_net_close_rate=0.0000.
- Latest no-send status preview includes runtime_near_forward signals=10 horizon_min=5 best_reason=tob_usd|dmid|market_breadth avg_net_close_bps=-65.2049 positive_net_close_rate=0.0000.
- This remains negative evidence and argues against loosening gates just to force opens.

Patch/change evidence:
- Forward outcome history merge now preserves source labels.
- Reporter reads accumulated runtime-near forward history by default when available.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_koko_paper_signal_forward_outcomes.py": 8 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 15 OK.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --horizon-min 5 --granularity 60 --limit 10 --tp-pct 8.0 --sl-pct 0.8 --out logs\runtime_near_forward_outcomes_latest.json --history-out logs\runtime_near_forward_outcomes_history.json: OK, history_signals_unique=10.
- python tools\tdi_status_reporter.py --mode hourly --event two_hour_summary --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence remains two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Continue bounded DRY observe until market breadth/dmid coverage produces actual openable candidates.
- Accumulate runtime_near_forward history across observe windows and use it to distinguish positive recovery from negative near-miss churn.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:27:24Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY readiness regeneration completed cleanly with DRY=true and LIVE=false.
- Latest status reporter preview was --no-send; no email was sent outside the two-hour cadence.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Primary blocker remains green_breadth plus recent/tick dmid alignment, not Profit Score tuning.
- U=0 / stale feed is not current cause: U=120, S=393, brf=80.
- Missing product/cache gap is not current cause for the current observe sample: signals=343.
- Latest readiness generated_at_utc=2026-06-04T00:23:50Z.
- Coverage: signals=343, liquid=6, dmid=3, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Tick diagnostics: tick_diag_rows=3, max_tick_dmid_nonzero=59, max_tick_dmid_ready=20, tick_dmid_warmed_seen=true.
- Green breadth remains short: latest_mbr=0.3500/0.8500, latest_mdmid=6.28/-999999.00.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Closest runtime near miss is timestamped: ETH-USD at ts_utc=2026-06-04T00:19:24Z, entry_mid=1815.415, qv=4,584,462, rdmid=10.36/40.00, tdmid=4.90/10.00, spr=0.06/5.00, tob=3439/500, failures=dmid|market_breadth.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- New local evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- Credible positive dry profitability evidence is not present yet.

Runtime near forward evidence:
- Added timestamped runtime_near_misses so candidates now carry local_ts and ts_utc from tick_diag rows.
- Added DRY-only runtime-near forward analysis path using readiness runtime_near_misses.
- Latest runtime_near_forward_outcomes_latest.json: signals=10, horizon_min=5.
- dmid|market_breadth group: signals=9, avg_net_forward_close_bps=-65.5874, positive_net_close_rate=0.0000.
- tob_usd|dmid|market_breadth group: signals=1, avg_net_forward_close_bps=-65.2049, positive_net_close_rate=0.0000.
- This is negative evidence and argues against loosening gates just to force opens.

Patch/change evidence:
- Readiness tick_diag parsing now adds local_ts and derived ts_utc to tick rows, latest_near_candidates, near_tail, and runtime_near_misses.
- Runtime near misses can now be anchored to real observe moments for forward checks.
- Forward outcome tooling can analyze readiness runtime_near_misses and skips unmatured candidates before the requested horizon has elapsed.
- TDI status reporting now includes runtime_near_forward evidence in no-send/two-hour preview output.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\koko_dry_observe_readiness.py tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_koko_paper_signal_forward_outcomes.py": 8 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 14 OK.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-03 19:19:00" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --horizon-min 5 --granularity 60 --limit 10 --tp-pct 8.0 --sl-pct 0.8 --out logs\runtime_near_forward_outcomes_latest.json: OK.
- python tools\tdi_status_reporter.py --mode hourly --event two_hour_summary --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth, body includes runtime_near_forward.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence remains two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Continue DRY observe until market breadth/dmid coverage produces actual openable candidates.
- Use timestamped runtime_near_forward evidence to avoid loosening gates into negative forward expectancy.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:21:35Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY diagnostic sample completed cleanly with DRY=true and LIVE=false.
- Latest readiness evidence was regenerated from the 2026-06-03 19:19:00 local DRY-only diagnostic sample.
- No live trading was enabled and no Coinbase/order placement path was touched.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No status email was sent during this relay update.

Current blocker:
- Primary blocker remains preflight/feed market coverage, specifically green breadth plus recent/tick dmid alignment, not Profit Score tuning.
- U=0 / stale feed is not the current cause: tick_diag shows U=120, S=393, brf=80.
- Missing product/cache gap is not the current cause: S=393 and latest readiness signals=343.
- Timestamp/tick coverage is usable enough to observe: tick_diag_rows=3, max_tick_dmid_nonzero=59, max_tick_dmid_ready=20, tick_dmid_warmed_seen=true.
- Liquid subset is too thin against dmid: quote_volume_usable=6, dmid_usable=3, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Green breadth is the clearest runtime blocker: latest_mbr=0.3500/0.8500 and latest_mdmid=6.28/-999999.00.
- Still no opens: max_drysig=0, max_dryopen=0, all_pass_candidates=0.
- Closest runtime near miss: ETH-USD had mid=1815.415, qv=4,584,462, spr=0.06/5.00, tob=3439/500, rdmid=10.36/40.00, tdmid=4.90/10.00, twarm=1, but failed dmid and market_breadth.
- Runtime near miss mids are now plausible per product: BTC around 64203-64241, ETH around 1814-1815, ADA around 0.20095-0.20125, DOGE around 0.09154-0.09160, NEAR around 2.827-2.8325.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Runtime evidence updated by fresh manual DRY observe: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- Credible positive dry profitability evidence is not present yet.
- Latest 3-tick diagnostic sample did not change dry P&L and did not create any open dry position.

Patch/change evidence:
- Added and corrected mid= diagnostics in drynear/drynear_top so runtime near misses use the candidate metric mid rather than a stale loop value.
- Readiness parser now retains mid and entry_mid from drynear diagnostics.
- Status evidence keeps structured market breadth/dmid fields so two-hour emails can distinguish green breadth failure from stale/missing feed coverage.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 13 OK.
- Latest readiness file generated_at_utc=2026-06-04T00:19:32Z.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence remains two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Keep DRY observe focused on usable market coverage and candidate openability.
- Add timestamped near-miss evidence for runtime candidates now that drynear mids are reliable.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T00:13:26Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY supervised sample completed cleanly with DRY=true and LIVE=false.
- Latest run reached entry preflight, then continuous_start ticks=15 and continuous_done elapsed_sec=131.1.
- Fresh manual DRY-only observe sample completed 24 ticks from local start 2026-06-03 19:09:10 without invoking the supervisor status-email hook.
- No Python observe process remains running.
- Latest status reporter preview was a no-send two_hour_summary; no email was sent outside the two-hour cadence.
- Routine status email cadence is two hours: TDI_REPORT_HOURLY_SEC=7200.
- Latest no-send status preview now includes structured runtime breadth evidence from tick diagnostics.

Current blocker:
- Primary blocker is now green_breadth / market+dmid overlap, not timestamp coverage.
- Preflight no longer stops on stale tail timestamp coverage when ranked timestamp/liquid coverage is usable.
- Cache evidence: timestamp_ratio=0.7888 globally, but ranked_timestamp_observe_supported=true, ranked_liquid_timestamp_observe_supported=true, dry_observe_coverage_supported=true.
- Tail stale cache remains visible: tail_cache_refresh_required=true, timestamp_outside_window_files=83.
- Missing product/cache gap is not current cause: missing_files=0, S=393.
- U=0 / stale feed is not current cause: U=120.
- Latest readiness from the fresh 24-tick sample: signals=355, liquid=13, dmid=4, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Warmed tick diagnostics are available: tick_diag_rows=24, tick_diag_dmid_nonzero=211, tick_diag_dmid_ready=56, tick_diag_warmed_seen=true.
- Structured market breadth evidence is explicit: latest_mbr=0.4417/0.8500, max_near_mbr=0.4417, latest_mdmid=13.79/-999999.00, max_near_mdmid=13.79.
- Still no opens: max_drysig=0, max_dryopen=0, all_pass_candidates=0.
- Runtime near evidence: WLD-USD had qv=634,459, rdmid=20.56, spr=3.77, tob=1703, tick_dmid=19.81, but failed recent-candle dmid and market_breadth.
- Reporter cache evidence: green_ratio=0.2398 vs green_min=0.8500, best_ranked=dmid_desc, best_ranked_green=0.5464, best_ranked_liquid=9.
- Do not tune Profit Score while dryopen=0/open_count=0.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Runtime evidence updated by fresh manual DRY observe: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- Credible positive dry profitability evidence is not present yet.
- Fresh 24-tick sample did not change dry P&L and did not create any open dry position.
- Latest status subject preview: [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.

Patch/change evidence:
- Cache preflight now distinguishes full-universe stale tail timestamp coverage from ranked actionable timestamp/liquid coverage.
- Missing selected product/cache files still require refresh; only stale tail products can be bypassed when ranked timestamp coverage is usable.
- Supervisor preflight now allows DRY observe to proceed when dry_observe_coverage_supported=true, while keeping actual open gates unchanged.
- Entry preflight now continues into the bounded DRY observe block when cache coverage supports observing, so tick-dmid can warm beyond first-tick twarm=0.
- Readiness now promotes latest/peak runtime market breadth and market dmid from tick diagnostics.
- TDI status reporting now includes latest_mbr/max_near_mbr and latest_mdmid/max_near_mdmid so two-hour emails can distinguish real green breadth failure from stale/missing feed coverage.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 22 OK.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 22 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 13 OK.
- Latest bounded DRY observe reached continuous_start ticks=15 and continuous_done elapsed_sec=131.1.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-03 18:58:20" --out logs\dry_observe_readiness_latest.json: OK.
- Fresh manual DRY observe run_loop(console=False, ticks=24): OK, elapsed_sec=218.2.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-03 19:09:10" --out logs\dry_observe_readiness_latest.json: OK.
- Latest reporter preview command completed with --no-send and subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth, including latest_mbr=0.4417/0.8500 and runtime_near=WLD-USD.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence remains two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Continue DRY observe in bounded samples while market breadth/dmid overlap is the blocker.
- Do not tune score until dryopen/open_count is nonzero or a candidate can pass data/openability gates.
- Watch for green breadth recovery and liquid+dmid overlap; then resume dry P&L improvement from actual open/close evidence.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-03T23:44:43Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest visible remote branch status: ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot at 211e3cd before this relay update.
- Latest local DRY supervised verify completed with DRY=true, LIVE=false, no Python observe process left running.
- Latest status reporter preview was no-send by request/tooling; no email was sent during this relay update.
- Routine TDI/KOKO status email cadence is two hours per latest user instruction; no duplicate/no-fluff emails, and material/safety events only when truly material.

Current blocker:
- Primary blocker remains data/preflight/openability, not Profit Score tuning.
- Latest reporter subject blocker: cache-liquid candidates blocked by trough (4; top OPN-USD).
- Latest readiness evidence: signals=368, U=120, S=393, brf=80, drysig=0, dryopen=0, max_drysig=0, max_dryopen=0.
- Timestamp coverage is usable: timestamp_ratio=0.8575, timestamp_shortfall=0.0000.
- Liquid subset coverage is usable at cache level: liquid_subset=18 vs required 10, liquid_shortfall=0.
- Green breadth is still short in the broader cache view: green_ratio=0.6739 vs min 0.8500, green_shortfall=0.1761; best_ranked=dmid_desc has green=1.0000 and liquid=15.
- Runtime liquid/dmid overlap exists but does not open: liquid=14, dmid=30, liquid_dmid_overlap=3, liquid_dmid_spread_tob_overlap=1.
- Tick diagnostics show warmup is now visible but not enough for opens: tick_diag_rows=4, tick_diag_dmid_nonzero=52, tick_diag_dmid_ready=2, tick_diag_warmed_seen=true, but current paper coverage still has tick_dmid_ready=0 and max_dryopen=0.
- U=0 / stale-feed is not the current cause; latest evidence has U=120.
- Missing product/cache gap is not the current cause; latest evidence has S=393.
- Named openability evidence: OPN-USD trough candidate rejected by spread with qv=311,911, rdmid=83.02, score=0.8332, refreshed top-book source=actionable_book_refresh_batch, prior top-book=686, spread=12.40 bps vs max 5.00.
- Runtime near miss: NEAR-USD has qv=1,901,311, rdmid=77.71, spread=3.53, tob=1141, but remains blocked by tick_dmid/dmid confirmation in current readiness.
- Probe quote candidates surfaced by reporter: NEAR-USD, HYPE-USD, WLD-USD, ICP-USD, LIGHTER-USD.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- opened=12 historically; blocked_open=50; quarantined=8.
- No new DRY opens in latest post-patch verification.
- Credible positive dry profitability evidence is not present yet.
- Forward evidence is mixed and not sufficient to resume score tuning: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, but broader forward dmid avg_net_close_bps=-136.7681 and supported_ranked_modes=0.

Patch/change evidence:
- Runtime preflight/readiness now blocks first-tick unwarmed tick-dmid candidates instead of allowing apparent recent-candle dmid passes to open on tdmid=0/twarm=0.
- Readiness reporting now treats unwarmed tick-dmid as non-openable when warm sample is required and exposes max tick diagnostic drysig/dryopen fields.
- TDI status reporting now includes tick diagnostic readiness evidence so status emails/previews do not hide earlier dryopen/drysig evidence inside the sample window.
- No Profit Score thresholds were tuned in this patch.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 22 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 13 OK.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- Post-patch short DRY verify completed with no first-tick unwarmed DRY open; latest readiness has dryopen=0 and max_dryopen=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting guardrail remains in force: tdifactorToday@gmail.com is the single TDI/KOKO reporting inbox; routine updates every two hours unless a true material/safety event requires an immediate report.

Next action:
- Continue bounded DRY observe after the tick-dmid warmup patch long enough for warmed tick candidates to appear.
- Keep focus on timestamp/liquid/green/feed/openability coverage and candidate opening; do not tune score while dryopen=0/open_count=0.
- Regenerate readiness and status evidence after the next observe run, then resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No for DRY/LIVE safety or relay visibility.
- Yes only if direct local SMTP delivery is required from this runtime: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or use an authenticated Gmail connector path.

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

## Codex relay status update

Timestamp: 2026-06-03T23:09:46Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest visible remote branch status: ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot at d4dcf43 before this relay update.
- Latest local supervisor marker: stale pid=5820, started 2026-06-03T23:04:38Z, DRY=true, LIVE=false.
- Latest bounded supervisor sample exited cleanly but did not produce a new observe tick because KOKO_SUPERVISOR_PREFLIGHT_REFRESH=0 caused preflight_observe_skip blocker=observe_window.
- Latest usable bounded tick evidence remains the 2026-06-03T22:58:21Z sample with dryliqskip_top trough probe rejection metrics.
- TDI Factor reporting destination remains tdifactorToday@gmail.com.
- Routine TDI/KOKO email cadence is two hours: TDI_REPORT_HOURLY_SEC=7200.
- SMTP delivery is currently blocked by missing sender env values: user, password, sender. Reporter wrote local .eml outbox files instead of delivering Gmail messages.

Current blocker:
- Primary blocker remains data/preflight/openability, not Profit Score.
- Latest reporter subject blocker: timestamp_coverage.
- Current usable runtime readiness evidence: signals=324, U=120, S=393, brf=80, drysig=0, dryopen=0, liquid=4, dmid=5, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0, dryliqskip=trough:4.
- Named probe/openability misses from latest usable tick:
  - ZEC-USD rejected by trough probe on spread: spr=5.7414 vs max 5.0000, qv=9,948,525, rdmid=56.26.
  - WLD-USD rejected by trough probe on spread: spr=7.3706 vs max 5.0000, qv=1,068,713, rdmid=49.98.
  - ENA-USD rejected by trough probe on spread: spr=17.5901 vs max 5.0000, qv=376,736, rdmid=44.05.
  - MON-USD rejected by trough probe on top-book: tob=51.4198 vs min 500, qv=281,123, rdmid=44.01.
- Cache support remains enough to continue observe: cache_supported=true, timestamp_ratio=0.8473, liquid_subset=19, best_probe=dmid_desc, best_probe_quote_overlap=5, best_probe_range_overlap=5.
- Green breadth remains weak: green_ratio=0.2374 vs min 0.8500.
- U=0 / stale-feed is not the current cause; U=120.
- Missing product/cache gap is not the current cause; S=393 and cache files are present.
- Current blocker for reporting delivery: missing SMTP/Gmail sender credentials in local env, so local reporter cannot send directly even though it can render status emails.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- blocked_open=46, opened=11 historically, quarantined=7.
- No new DRY opens in latest usable verification.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- TDI reporting cadence is confirmed at two hours via TDI_REPORT_HOURLY_SEC=7200.
- Reporter previews/samples are deduped; recent attempts were skipped as hourly_not_due except delivery attempts that failed because SMTP env is missing.
- DRY-only trough-skip probe diagnostics remain active and parse/report spread/top-book rejection details.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 13 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 22 OK.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- Latest reporter state shows last_status event=two_hour_summary, sent=false, reason=hourly_not_due after the failed SMTP delivery window.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting guardrail remains in force: tdifactorToday@gmail.com is the single TDI/KOKO reporting inbox, with routine updates every two hours unless a material event requires an immediate report.

Next action:
- Keep data/preflight focus until DRY observe can actually open candidates.
- Run the next bounded DRY observe sample with a usable observe window or with preflight refresh enabled so it produces a fresh tick containing book source diagnostics.
- Resolve Gmail delivery by providing SMTP/Gmail sender env values or routing through the authenticated Gmail connector.
- Do not tune Profit Score while opened/open_count remains 0.

User action required:
- Yes for unattended local SMTP delivery: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or equivalent SMTP/Gmail env values.
- No user action required for DRY/LIVE safety; DRY remains true and LIVE remains false.

## Codex relay status update

Timestamp: 2026-06-03T23:00:41Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local run marker: stale pid=20240 ts=22:58:16.
- Latest bounded DRY sample produced runtime tick evidence, but the supervisor command exited nonzero during the second preflight refresh after emitting the tick; no live trading was enabled.
- TDI reporter preview was no-send with reason=hourly_not_due; no email was sent because the two-hour cadence was not due.

Current blocker:
- Still data/preflight/openability, not Profit Score.
- Latest reporter subject blocker: timestamp_coverage.
- Runtime readiness now has richer early-skip evidence:
  - signals=324
  - U=120, S=393, brf=80
  - drysig=0, dryopen=0
  - liquid=4, dmid=5
  - liquid_dmid_overlap=0
  - liquid_dmid_spread_tob_overlap=0
  - dryliqskip=trough:4
- The current named trough/probe blockers are now explicit:
  - ZEC-USD: qv=9,948,525, rdmid=56.26, rejected by trough probe on spread 5.7414 vs max 5.0000.
  - WLD-USD: qv=1,068,713, rdmid=49.98, rejected by trough probe on spread 7.3706 vs max 5.0000.
  - ENA-USD: qv=376,736, rdmid=44.05, rejected by trough probe on spread 17.5901 vs max 5.0000.
  - MON-USD: qv=281,123, rdmid=44.01, rejected by trough probe on top-book 51.4198 vs min 500.
- Cache evidence remains supportive enough to continue observe:
  - cache_supported=true
  - timestamp_ratio=0.8473, timestamp shortfall=0.0027
  - liquid_subset=19 vs min 10
  - green_ratio=0.2374 remains weak
  - best_probe=dmid_desc, best_probe_green=0.6421, best_probe_liquid=3
  - best_probe_quote_overlap=5, best_probe_range_overlap=5
  - probe_quote_candidates=ZEC-USD|WLD-USD|MON-USD|ENA-USD|FARTCOIN-USD
  - probe_quote_range_candidates=ZEC-USD|WLD-USD|MON-USD|ENA-USD|FARTCOIN-USD
- U=0 / stale feed is not the current cause; U=120.
- Missing product/cache gap is not the current cause; S=393 and cache refresh had broad coverage, with two Coinbase candle refresh failures in the sample.
- Current named candidates fail strict spread/top-book gates, so do not tune score and do not weaken gates without separate approval.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- blocked_open=46, opened=11, quarantined=7.
- No new DRY opens in latest verification.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added DRY-only trough-skip probe rejection metrics to dryliqskip_top.
- The runtime tick line now includes fields such as tprej, spr/sprmax, tob/tobmin, quote floors, range floors, and dmid floors when those metrics are available.
- Readiness parsing now preserves those fields as structured evidence.
- TDI reporter now includes compact probe rejection details in the status evidence string, so Gmail summaries can name the real openability blocker without manual log parsing.
- This is diagnostics/preflight reporting only; no trading threshold was lowered.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.
- No score tuning was done.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 13 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 22 OK.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- Bounded DRY verification produced a current tick with richer dryliqskip_top evidence.
- Reporter preview after the patch included dryliqskip_top=ZEC-USD:reason=trough:qv=9948525:rdmid=56.26:score=0.5913:tprej=spread:spr=5.74/5.00 and was not sent because hourly_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting guardrail remains in force: tdifactorToday@gmail.com is the single TDI/KOKO reporting inbox, with two-hour summaries unless separately directed otherwise.

Next action:
- Continue DRY observe openability from named candidates.
- Investigate whether current spread/top-book failures are transient book-state misses or a ranking/refresh window issue.
- Do not tune Profit Score while opened/open_count remains 0.
- Keep data/preflight focus: timestamp coverage, liquid subset coverage, green breadth, U/stale-feed causes, and product/cache gaps.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-03T22:49:15Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local run marker: stale pid=16564 ts=22:47:10.
- Latest bounded DRY supervised sample reached continuous_start and continuous_done after entry sampling.
- DRY=true and LIVE=false.
- No new DRY opens.
- TDI Factor reporting destination remains tdifactorToday@gmail.com.
- TDI Factor reporting cadence is every two hours unless a material event occurs.
- Latest reporter preview was no-send with reason=hourly_not_due; no email was sent.

Current blocker:
- Primary blocker is still data/preflight/openability, not Profit Score.
- Latest reporter subject blocker: timestamp_coverage.
- Runtime readiness still has open_count=0 and no open candidate.
- Latest readiness evidence: signals=323, liquid=4, dmid=2, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0, U=120, S=393, drysig=0, dryopen=0.
- Latest cache evidence: cache_supported=true, timestamp_ratio=0.7964, green_ratio=0.1949, liquid_subset=16.
- Best ranked/probe cache mode remains dmid_desc with best_probe_green=0.5542, best_probe_liquid=2, best_probe_quote_overlap=1, best_probe_range_overlap=1.
- Latest probe quote candidate named by cache/reporting: WLD-USD.
- Latest dryliqskip evidence: trough:1, top WLD-USD reason=trough qv=973650 rdmid=51.83 score=0.7189.
- Runtime near miss remains BTC-USD with failures=dmid|market_breadth, qv=27118726, rdmid=-10.00, spr=0.00, tob=2090.
- Earlier probe candidate BILL-USD was successfully refreshed by the new batch-priority patch, but did not become openable: latest row had spr_bps=3.4556 passing the 5 bps spread gate, but tob_usd=1.1284 vs min 500 and dry_recent_candle_dmid_bps=-5.7471 vs required probe dmid 40.
- DEGEN-USD and LIGHTER-USD remained non-openable in the checked rows because of spread/top-book/dmid misses.
- U=0 / stale feed is not the current cause; U remains 120 and cache files are present.
- Missing product/cache gap is not the current cause; latest cache refresh had files present and supported cache evidence.
- Do not tune Profit Score while opened/open_count remains 0.

Files changed in current lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.05528612 USD, unrealized=0.00000000 USD, net=-0.05528612 USD.
- open/closed/wins/losses: open=0, closed=11, wins=3, losses=8.
- No new DRY opens in the latest bounded verification.
- Overall dry net remains negative; credible positive dry profitability evidence is not yet present.
- Forward evidence from reporter: dry_open_forward signals=1 horizon_min=10 avg_net_close_bps=41.3940 positive_net_close_rate=1.0000, but this is not enough to override the negative realized/net P&L and open_count=0.

Patch/change evidence:
- Added DRY-only refresh priority in _dry_batch_refresh_actionable_book_metrics so probe-floor quote candidates are refreshed inside the book-metric cap.
- Probe refresh priority uses DRY_OBSERVE_PROBE_ALLOWED_FAILURES, DRY_OBSERVE_PROBE_MIN_QUOTE_VOLUME_USD, and DRY_OBSERVE_PROBE_MIN_QUOTE_FAILURE_DMID_BPS.
- Priority now ranks full main candidates first, probe quote candidates second, then timestamp+quote, timestamp+dmid, timestamp, and finally dmid/quote tie-breakers.
- This patch only changes which DRY candidates get fresh book metrics; it does not weaken spread/top-book/dmid gates.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.
- No score tuning was done.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 22 OK.
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 21 OK.
- python -m py_compile managers\run_manager\run_manager.py: OK.
- Bounded DRY supervised verification printed two ticks and logs reached continuous_done; no new opens and dry P&L unchanged.
- Latest reporter preview included current Profit Score 26/100, negative dry net P&L, and no-send hourly_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting guardrail remains in force: tdifactorToday@gmail.com is the single TDI/KOKO reporting inbox, with two-hour summaries and immediate material-event reports only.

Next action:
- Keep working the data/preflight lane until DRY observe can actually open candidates.
- Continue investigating timestamp coverage, liquid subset coverage, green breadth, stale-feed/U causes, and product/cache gaps as openability blockers.
- Continue runtime openability evidence for named candidates and identify whether top-book/dmid alignment is naturally appearing under the current guardrails.
- Do not tune Profit Score while opened=0.

User action required:
- No.
