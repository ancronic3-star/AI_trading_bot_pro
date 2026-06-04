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

Timestamp: 2026-06-04T09:29:58Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: third bounded DRY observe, explicit runtime candle cache refresh, runtime product coverage diagnostic, mature 5-minute recovery/dry_pnl_guard/runtime-near/all-reason forward refresh, ranked/threshold/gap refresh, validation, and reporter no-send preview.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered patch_applied with --no-send; no email was sent.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Current blocker is data/preflight plus market breadth/dmid, not Profit Score tuning.
- The cache stale-feed lane improved materially after refresh: runtime candle cache went from 393 stale products to 355 present and 38 stale.
- Cache refresh covered 391 of 393 runtime products; public candle fetch failed for ORCA-USD and ZAMA-USD.
- U/stale feed is not the open blocker now: readiness shows U=120, S=393, brf=120, book_gap=false, timestamp_usable=355/393.
- Liquid subset is usable: quote_volume_usable=486 and liquid_min evidence remains satisfied.
- Green breadth is not usable: latest_mbr=0.0333/0.8500 in readiness, cache-regime green_ratio=0.0822/0.8500, and market_dmid=-104.95.
- Runtime near-miss now surfaces NEAR-USD blocked by dmid; readiness also shows dmid|market_breadth as the current runtime-near blocker.
- Third DRY observe opened no candidates: drysig=0, dryopen=0, dryblk=0 for the latest tick diagnostics, and no new ledger blocked_open rows were added after the second window.
- Forward gap is still sparse exact-window coverage: products_checked=10, classifications=sparse_exact_window:10.
- Runtime product coverage now reports repeat_sparse_in_runtime=15, led by DRIFT-USD=4, CBETH-USD=3, DRV-USD=3, ENS-USD=3, and KTA-USD=3.
- Fresh all-reason forward evidence remains negative overall: signals=376, no_forward_candles=124, dmid avg_net_close_bps=-36.5690, spread avg_net_close_bps=-75.5684.
- Recovery-forward remains negative: signals=10, best_reason=recovery|dmid|tob_usd|book_pressure, avg_net_close_bps=-12.1750, positive_net_close_rate=0.0000.
- Runtime-near latest remains negative: signals=10, best_reason=dmid|market_breadth, avg_net_close_bps=-41.2666, positive_net_close_rate=0.0000.
- Ranked forward remains unsupported: supported_ranked_modes=0, best_ranked mode=liquidity_desc, avg_net_close_bps=-32.9954.
- Threshold sweep remains unsupported: configs=231, supported=0, best_avg_net_close_bps=-25.0738.
- Interpretation: DRY observe now has usable timestamp/cache coverage, but the current window is red breadth/negative dmid with repeat sparse-product gaps. Do not tune Profit Score while opened=0.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_runtime_product_coverage.py
- C:\ai_trading_bot_koko\tests\test_koko_runtime_product_coverage.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\runtime_product_coverage_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_all_5m.json
- C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\forward_threshold_sweep_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=130.
- Third observe added no opens and no new positive dry P&L evidence.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added tools\koko_runtime_product_coverage.py to report runtime product count, cache status counts, repeat sparse products still in the runtime universe, and top problem products.
- Added tests\test_koko_runtime_product_coverage.py.
- Updated tools\tdi_status_reporter.py so status emails include runtime_product_coverage evidence.
- Updated tests\test_tdi_status_reporter.py for runtime product coverage reporting.
- No score tuning, no gate loosening, no DRY P&L guard changes.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python tools\koko_runtime_product_coverage.py --out logs\runtime_product_coverage_latest.json: completed, products=393, present=355, stale=38, repeat_sparse_in_runtime=15.
- python -m unittest tests.test_koko_runtime_product_coverage tests.test_koko_forward_gap_diagnostics tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 60 tests.
- python -m py_compile tools\koko_runtime_product_coverage.py tools\koko_forward_gap_diagnostics.py tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool on refreshed readiness, forward, ranked, threshold, gap, history, and runtime coverage artifacts: PASS.
- python tools\tdi_status_reporter.py --mode event --event patch_applied ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | runtime near-miss NEAR-USD blocked by dmid; sent=false reason=no_send.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Do not tune broad Profit Score.
- Keep DRY-only data/preflight work focused on repeat sparse products and current breadth/dmid causes.
- Consider product-universe deprioritization for repeat sparse products only after preserving guardrails and without touching Coinbase/order path.
- Wait for a green breadth/dmid window before judging open/profitability behavior again.
- Do not enable LIVE.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T09:08:50Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: second independent bounded DRY observe, readiness refresh, mature 5-minute recovery/dry_pnl_guard/runtime-near/all-reason forward refresh, ranked/threshold/gap refresh, validation, reporter no-send preview.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered cloud_task_completed with --no-send and did not send because it was not considered material enough for out-of-cadence delivery: reason=not_material:cloud_task_completed.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe coverage is usable enough to evaluate candidates, but dry net P&L remains negative and new opens stayed blocked.
- Latest dry P&L remains net negative: -0.30033076 USD.
- Fresh bounded observe produced no opens; blocked_open increased from 126 to 130.
- Latest bounded observe has opened=28, closed=28, wins=8, losses=20, open_count=0.
- New blocked-open rows were XRP-USD net_negative_low_tick_dmid at 2026-06-04T08:56:48Z, 08:57:06Z, 08:57:16Z, and 08:58:38Z.
- Reporter main blocker now surfaces dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage remains usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset remains usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Fresh readiness: signals=8390, quote_volume_usable=640, dmid_usable=3813, tick_dmid_ready=337, tick_dmid_warmed=8025, liquid_dmid_overlap=433, liquid_dmid_spread_tob_overlap=112.
- Fresh all-pass candidates exist but are blocked by dry_pnl_guard: signals=8 in forward artifact.
- Fresh dry_pnl_guard forward evidence is negative after costs: signals=8, avg_net_close_bps=-114.6925, positive_net_close_rate=0.0000, sl_touch_rate=0.8750, best_net_close_bps=-49.0980.
- Fresh recovery-forward is negative after costs: signals=10, best_reason=recovery|tick_dmid|book_pressure, avg_net_close_bps=-62.7262, positive_net_close_rate=0.0000, best_net_close_bps=-40.1362.
- Fresh runtime-near latest is negative after costs: loaded=10, signals=10, best_reason=tick_dmid, avg_net_close_bps=-92.8733, positive_net_close_rate=0.0000.
- Broad all-reason forward evidence is still negative overall: signals=356, loaded_signals=500, no_forward_candles=144.
- All-reason buckets remain mostly negative after costs: spread avg_net_close_bps=-78.1029, dmid=-23.6203, tick_dmid=-40.4623, tob_usd=-54.3047, trough=-83.9451, trough_wait=-113.8527.
- Runtime ranked-forward remains unsupported: signals=356, supported_slices=0, best mode=active_dmid_desc top_n=20, avg_net_close_bps=-30.4867.
- Threshold sweep remains unsupported: configs_evaluated=5388, supported_count=0, best_avg_net_close_bps=-27.4004, best_positive_net_close_rate=0.1429.
- Forward gap diagnosis remains sparse exact-window coverage: classification_counts sparse_exact_window=10.
- Independent repeat sparse products now include DRIFT-USD=4, DRV-USD=3, ENS-USD=3, KTA-USD=3, plus ACH-USD=2.
- Interpretation: the first independent positive dry_pnl_guard/all-pass forward window did not repeat. The second window was negative, broad-ranked/threshold evidence is still unsupported, and dry realized P&L remains negative. Do not loosen guards or tune Profit Score yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_all_5m.json
- C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\forward_threshold_sweep_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=130.
- Credible positive dry profitability evidence is not complete yet; one independent positive dry_pnl_guard forward window was followed by a negative second window, actual dry P&L remains negative, and no new opens occurred.

Patch/change evidence:
- No code patch was applied in this observe/evidence turn.
- Refreshed second independent-window diagnostics and forward artifacts only.
- No score tuning, no gate loosening, no DRY P&L guard changes.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- Fresh bounded DRY observe completed exit 0 with KOKO_SUPERVISOR_MAX_CYCLES=24, DRY=true, LIVE=false.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 03:55:27" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py for recovery, dry_pnl_guard, runtime-near, and all-reason current window: completed.
- python tools\koko_runtime_ranked_forward_outcomes.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\runtime_ranked_forward_outcomes_latest.json --min-signals 10: completed.
- python tools\koko_forward_threshold_sweep.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\forward_threshold_sweep_latest.json --min-signals 6 --sl-bps 80 --top 20: completed.
- python tools\koko_forward_gap_diagnostics.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --reason no_forward_candles --limit 10 --out logs\forward_gap_diagnostics_latest.json --history-out logs\forward_gap_diagnostics_history.json: completed.
- python -m unittest tests.test_koko_forward_gap_diagnostics tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 58 tests.
- python -m py_compile tools\koko_forward_gap_diagnostics.py tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool on refreshed artifacts: PASS.
- python tools\tdi_status_reporter.py --mode event --event cloud_task_completed ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=not_material:cloud_task_completed.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Do not tune broad Profit Score.
- Continue DRY-only data/preflight lane and collect another independent observe window before any Profit Score tuning.
- Diagnose repeat sparse-window products and missing product/cache gaps, especially DRIFT-USD, DRV-USD, ENS-USD, KTA-USD, and ACH-USD.
- Keep the DRY P&L guard in place.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- No for the two-hour email cadence; current reporter preview preserved out-of-cadence no-send behavior.

## Codex relay status update

Timestamp: 2026-06-04T08:38:24Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: same-run and history sparse-window product tracking for forward gap diagnostics, focused tests, diagnostic regeneration, reporter no-send preview.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered patch_applied with --no-send and did not send because cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative: -0.30033076 USD.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0, blocked_open=123.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage remains usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset remains usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Forward gap diagnosis remains sparse exact-window coverage, not unsupported products: classification_counts sparse_exact_window=10.
- Same-run sparse products now surface in reporter evidence: AGLD-USD=2, AMP-USD=2, APE-USD=2, BARD-USD=2, DRIFT-USD=2.
- History tracking is initialized and currently has two diagnostic runs over the same forward artifact; repeat_sparse shows the same top products at runs=2, but this is not yet an independent second observe/forward window.
- Reporter evidence now includes same_run_sparse and repeat_sparse fields in forward_gap.
- All-reason forward evidence remains negative overall: signals=317, spread avg_net_close_bps=-98.0095, positive_net_close_rate=0.0246, sl_touch_rate=0.7336.
- Runtime ranked-forward summary remains unsupported: signals=317, supported_slices=0, best mode=active_dmid_desc top_n=20, avg_net_close_bps=-74.7813.
- Threshold sweep remains unsupported: configs_evaluated=4533, supported_count=0, best_avg_net_close_bps=-65.7130.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_forward_gap_diagnostics.py
- C:\ai_trading_bot_koko\tests\test_koko_forward_gap_diagnostics.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- tools\koko_forward_gap_diagnostics.py now writes same_run_sparse_products and bounded repeat_sparse_products history.
- tools\tdi_status_reporter.py now includes same_run_sparse and repeat_sparse in forward_gap evidence.
- No score tuning, no gate loosening, no DRY P&L guard changes.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_forward_gap_diagnostics tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 58 tests.
- python -m py_compile tools\koko_forward_gap_diagnostics.py tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json, logs\forward_gap_diagnostics_latest.json, logs\forward_gap_diagnostics_history.json: PASS.
- python tools\koko_forward_gap_diagnostics.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --reason no_forward_candles --limit 10 --out logs\forward_gap_diagnostics_latest.json --history-out logs\forward_gap_diagnostics_history.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_applied ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Collect an independent next observe/forward window and use repeat sparse-window diagnostics to filter or de-prioritize unreliable products before any Profit Score tuning.
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight diagnostics only.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:34:22Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: repeatable forward gap diagnostics tool, reporter gap-summary wiring, focused tests, live diagnostic artifact generation, reporter no-send preview.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered patch_applied with --no-send and did not send because cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative: -0.30033076 USD.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0, blocked_open=123.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage remains usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset remains usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Top no_forward_candles products are not unsupported products: live diagnostic checked 10 products, all returned product_status_code=200 and classification=sparse_exact_window.
- Forward gap diagnosis: classification_counts sparse_exact_window=10; exact 5-minute forward windows had zero candle rows, while latest product candle history exists.
- New reporter evidence includes: forward_gap reason=no_forward_candles products_checked=10 classifications=sparse_exact_window:10.
- All-reason forward evidence remains negative overall: signals=317, spread avg_net_close_bps=-98.0095, positive_net_close_rate=0.0246, sl_touch_rate=0.7336.
- Runtime ranked-forward summary remains unsupported: signals=317, supported_slices=0, best mode=active_dmid_desc top_n=20, avg_net_close_bps=-74.7813.
- Threshold sweep remains unsupported: configs_evaluated=4533, supported_count=0, best_avg_net_close_bps=-65.7130.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_forward_gap_diagnostics.py
- C:\ai_trading_bot_koko\tests\test_koko_forward_gap_diagnostics.py
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_all_5m.json
- C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\forward_threshold_sweep_latest.json
- C:\ai_trading_bot_koko\logs\forward_gap_diagnostics_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added tools\koko_forward_gap_diagnostics.py to classify forward candle coverage gaps by product using public product/candle endpoints.
- Added tests\test_koko_forward_gap_diagnostics.py.
- Reporter now reads logs\forward_gap_diagnostics_latest.json by default and includes forward_gap summary in status emails.
- Prior forward analyzer/reporting patch remains in place: failures_by_product and no_forward_candles/fetch products in reporter output.
- run_settings.json points TDI_REPORT_FORWARD_OUTCOMES_PATH to logs/paper_signal_forward_outcomes_latest_all_5m.json.
- This is not Profit Score tuning and does not loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_forward_gap_diagnostics tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 57 tests.
- python -m py_compile tools\koko_forward_gap_diagnostics.py tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json: PASS.
- python tools\koko_forward_gap_diagnostics.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --reason no_forward_candles --limit 10 --out logs\forward_gap_diagnostics_latest.json: completed; classification_counts sparse_exact_window=10.
- python tools\tdi_status_reporter.py --mode event --event patch_applied ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Use sparse_exact_window diagnostics to filter or de-prioritize products with repeated empty forward windows before any Profit Score tuning.
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight diagnostics only.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:30:08Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: forward failure product diagnostics patch, all-reason forward evidence refresh, ranked-forward refresh, threshold-sweep refresh, reporter no-send preview.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered patch_applied with --no-send and did not send because cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative: -0.30033076 USD.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0, blocked_open=123.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage remains usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset remains usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- New forward gap evidence identifies product/cache coverage gaps: no_forward_candles=183 from loaded_signals=500, with top product counts AGLD-USD=2, AMP-USD=2, APE-USD=2, BARD-USD=2, DRIFT-USD=2.
- All-reason forward evidence remains negative overall: signals=317, spread avg_net_close_bps=-98.0095, positive_net_close_rate=0.0246, sl_touch_rate=0.7336.
- Other all-reason buckets remain negative after costs: dmid=-124.1894, tob_usd=-81.2480, trough=-104.4093, tick_dmid=-77.0086.
- Runtime ranked-forward summary remains unsupported: signals=317, supported_slices=0, best mode=active_dmid_desc top_n=20, avg_net_close_bps=-74.7813, train=-74.2998, validation=-75.2628.
- Threshold sweep remains unsupported: configs_evaluated=4533, supported_count=0, best_avg_net_close_bps=-65.7130, best_positive_net_close_rate=0.1667.
- Recovery-forward, dry_pnl_guard, all-reason, ranked, and threshold evidence remain negative/unsupported.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_all_5m.json
- C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\forward_threshold_sweep_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added failures_by_product to forward outcome diagnostics for PAPER_BUY_SIGNAL, runtime-near, and recovery forward analysis.
- Reporter forward evidence now includes top no_forward_candles/fetch products.
- run_settings.json now points TDI_REPORT_FORWARD_OUTCOMES_PATH to logs/paper_signal_forward_outcomes_latest_all_5m.json so scheduled two-hour reports include the enriched all-reason artifact.
- This is not Profit Score tuning and does not loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 54 tests.
- python -m py_compile tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json: PASS.
- python tools\koko_paper_signal_forward_outcomes.py --activity-log logs\activity_ticker.log --since-ts-utc "2026-06-04T08:03:28Z" --reasons "" --horizon-min 5 --granularity 60 --limit 500 --out logs\paper_signal_forward_outcomes_latest_all_5m.json: completed.
- python tools\koko_runtime_ranked_forward_outcomes.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\runtime_ranked_forward_outcomes_latest.json --min-signals 10: completed.
- python tools\koko_forward_threshold_sweep.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\forward_threshold_sweep_latest.json --min-signals 6 --sl-bps 80 --top 20: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_applied ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Investigate top no_forward_candles products/cache coverage before any Profit Score tuning.
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight diagnostics only.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:22:05Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: all-reason current-window forward outcomes refresh plus ranked-forward and threshold-sweep summaries.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the cloud_task_completed status with --no-send and did not send an out-of-cadence email.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative: -0.30033076 USD.
- Fresh bounded observe produced no opens; blocked_open remains 123.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0.
- Fresh readiness remains usable for observe: signals=8344, quote_volume_usable=638, dmid_usable=3767, tick_dmid_ready=259, tick_dmid_warmed=7982, liquid_dmid_overlap=431, liquid_dmid_spread_tob_overlap=85.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false, book_metric_source_present_ratio=0.9879.
- Timestamp/cache coverage is usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset is usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- All-reason current-window forward evidence is negative overall: signals=317, failures no_forward_candles=183.
- All-reason spread bucket has an isolated positive best row, but the bucket is not stable: signals=244, avg_net_close_bps=-97.6746, positive_net_close_rate=0.0246, sl_touch_rate=0.7295, best_net_close_bps=111.2469.
- Other all-reason buckets remain negative after costs: tob_usd avg_net_close_bps=-81.2480, trough=-106.1266, tick_dmid=-77.0086, dmid=-124.1894.
- Runtime ranked-forward summary is unsupported: signals=317, supported_slices=0, best mode=active_dmid_desc top_n=20, avg_net_close_bps=-74.7813, train=-74.2998, validation=-75.2628.
- Threshold sweep is unsupported: configs_evaluated=4533, supported_count=0, best_avg_net_close_bps=-65.7130, best_positive_net_close_rate=0.1667.
- Recovery-forward, dry_pnl_guard, runtime-near, all-reason, ranked, and threshold evidence are all still negative/unsupported.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_all_5m.json
- C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\forward_threshold_sweep_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- No code patch was applied in this evidence-only turn.
- Refreshed broad forward evidence artifacts only.
- This is not Profit Score tuning and does not loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python tools\koko_paper_signal_forward_outcomes.py --activity-log logs\activity_ticker.log --since-ts-utc "2026-06-04T08:03:28Z" --reasons "" --horizon-min 5 --granularity 60 --limit 500 --out logs\paper_signal_forward_outcomes_latest_all_5m.json: completed.
- python tools\koko_runtime_ranked_forward_outcomes.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\runtime_ranked_forward_outcomes_latest.json --min-signals 10: completed.
- python tools\koko_forward_threshold_sweep.py --forward-outcomes logs\paper_signal_forward_outcomes_latest_all_5m.json --out logs\forward_threshold_sweep_latest.json --min-signals 6 --sl-bps 80 --top 20: completed.
- python tools\tdi_status_reporter.py --mode event --event cloud_task_completed ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=not_material:cloud_task_completed.
- No code tests were run in this evidence-only turn.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight diagnostics only; do not tune Profit Score while all broad-forward evidence remains negative or unsupported.
- Investigate no_forward_candles=183 by product/cache gap so missing product/cache coverage is separated from transient feed gaps.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:15:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: latest runtime-near forward evidence refresh after the fresh bounded DRY observe.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the cloud_task_completed status and did not send because it was not material enough for out-of-cadence delivery: reason=not_material:cloud_task_completed.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Fresh bounded observe produced no opens; blocked_open remains 123.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0.
- Fresh readiness remains usable for observe: signals=8344, quote_volume_usable=638, dmid_usable=3767, tick_dmid_ready=259, tick_dmid_warmed=7982, liquid_dmid_overlap=431, liquid_dmid_spread_tob_overlap=85.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false, book_metric_source_present_ratio=0.9879.
- Recovery candidate coverage remains signals=63, all_recovery_metrics=0 with failures tick_dmid=61, book_pressure=47, tob_usd=41, spread=13.
- Fresh mature recovery-forward evidence remains negative after costs: signals=10, horizon=5m, positive_net_close_rate=0.0000, best_net_close_bps=-47.8218.
- Fresh mature dry_pnl_guard forward evidence remains negative after costs: signals=4, horizon=5m, avg_net_close_bps=-131.5061, positive_net_close_rate=0.0000, sl_touch_rate=1.0000.
- Fresh runtime-near forward evidence is also negative after costs: signals=10, horizon=5m, positive_net_close_rate=0.0000.
- Runtime-near tick_dmid rows: signals=9, avg_net_close_bps=-62.9680, best_net_close_bps=-38.5077, sl_touch_rate=0.2222.
- Runtime-near tob_usd row: signals=1, avg_net_close_bps=-76.7703, sl_touch_rate=1.0000.
- Interpretation: the latest near-open candidates are not being blocked from profitable dry opens; they are forward-testing negative after costs.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- No code patch was applied in this runtime-near evidence turn.
- Refreshed logs\runtime_near_forward_outcomes_latest.json.
- This is not Profit Score tuning and does not loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --since-ts-utc "2026-06-04T08:03:28Z" --horizon-min 5 --granularity 60 --limit 20 --out logs\runtime_near_forward_outcomes_latest.json: completed.
- python tools\tdi_status_reporter.py --mode event --event cloud_task_completed ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=not_material:cloud_task_completed.
- No code tests were run in this evidence-only turn.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight only; do not tune Profit Score while recovery, dry_pnl_guard, and runtime-near forward evidence are all negative.
- Watch recovery_shortfalls for sustained convergence, especially VVV spread/tob_usd and XRP book_pressure/tick_dmid.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:13:35Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: fresh bounded DRY observe, readiness refresh, matured 5-minute recovery-forward refresh, dry_pnl_guard forward refresh, and reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the cloud_task_completed status and did not send because it was not material enough for out-of-cadence delivery: reason=not_material:cloud_task_completed.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Fresh bounded observe produced no opens; blocked_open increased from 116 to 123.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0.
- Fresh readiness remains usable for observe: signals=8344, quote_volume_usable=638, dmid_usable=3767, tick_dmid_ready=259, tick_dmid_warmed=7982, liquid_dmid_overlap=431, liquid_dmid_spread_tob_overlap=85.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false, book_metric_source_present_ratio=0.9879.
- Timestamp/cache coverage is usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset is usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Recovery candidate coverage remains signals=63, all_recovery_metrics=0 with failures tick_dmid=61, book_pressure=47, tob_usd=41, spread=13.
- Fresh recovery shortfall diagnostics:
  - tick_dmid closest miss: VVV-USD observed=8.806608 bps, required=10.0 bps, shortfall=1.193392 bps.
  - book_pressure closest miss: XRP-USD observed=0.859443, required=0.900000, shortfall=0.040557.
  - spread closest miss: VVV-USD observed=5.0835 bps, required<=5.0 bps, excess=0.0835 bps.
  - tob_usd closest miss: VVV-USD observed=306.3220 USD, required=500.0 USD, shortfall=193.6780 USD.
- Fresh mature recovery-forward evidence is worse than the previous run and still negative after costs: signals=10, horizon=5m, positive_net_close_rate=0.0000.
- recovery|tick_dmid avg_net_close_bps=-61.0042, best_net_close_bps=-47.8218, shortfall_bps=47.8218.
- recovery|tick_dmid|book_pressure avg_net_close_bps=-65.5526, best_net_close_bps=-57.2958.
- recovery|tob_usd avg_net_close_bps=-75.7631, sl_touch_rate=1.0000.
- Fresh mature dry_pnl_guard forward evidence is negative after costs: signals=4, horizon=5m, avg_net_close_bps=-131.5061, positive_net_close_rate=0.0000, sl_touch_rate=1.0000, best_net_close_shortfall_bps=101.8468.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=123.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- No code patch was applied in this observe turn.
- Refreshed readiness and forward-evidence artifacts from a fresh bounded DRY observe.
- This is not Profit Score tuning and does not loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- Fresh bounded DRY observe command completed exit 0 with KOKO_SUPERVISOR_MAX_CYCLES=24, DRY=true, LIVE=false.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 03:03:28" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-recovery logs\dry_observe_readiness_latest.json --since-ts-utc "2026-06-04T08:03:28Z" --horizon-min 5 --granularity 60 --limit 20 --out logs\paper_signal_forward_outcomes_latest_recovery_5m.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py --activity-log logs\activity_ticker.log --since-ts-utc "2026-06-04T08:03:28Z" --reasons dry_pnl_guard --horizon-min 5 --granularity 60 --limit 40 --out logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json: completed.
- python tools\tdi_status_reporter.py --mode event --event cloud_task_completed ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=not_material:cloud_task_completed.
- No code tests were run in this observe-only turn.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue observe/data-preflight only; do not tune Profit Score while fresh mature forward evidence is this negative.
- Watch recovery_shortfalls for sustained convergence, especially VVV spread/tob_usd and XRP book_pressure/tick_dmid.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T08:02:20Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: recovery gate shortfall diagnostic patch, readiness artifact refresh, focused test verification, and reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the material patch status with --no-send; no out-of-cadence email was sent.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0, blocked_open=116.
- Fresh readiness remains usable for observe: signals=8331, quote_volume_usable=644, dmid_usable=3754, tick_dmid_ready=310, tick_dmid_warmed=7969, liquid_dmid_overlap=437, liquid_dmid_spread_tob_overlap=57.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage is usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset is usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Recovery candidate coverage remains signals=69, all_recovery_metrics=0 with failures tick_dmid=67, book_pressure=60, tob_usd=50, spread=13.
- New recovery shortfall diagnostics:
  - tick_dmid closest miss: XLM-USD observed=9.992374 bps, required=10.0 bps, shortfall=0.007626 bps.
  - book_pressure closest miss: XRP-USD observed=0.813159, required=0.900000, shortfall=0.086841.
  - spread closest miss: VVV-USD observed=5.6577 bps, required<=5.0 bps, excess=0.6577 bps.
  - tob_usd closest miss: VVV-USD observed=220.2194 USD, required=500.0 USD, shortfall=279.7806 USD.
- Refreshed mature dry_pnl_guard forward evidence remains negative after costs: signals=3, horizon=5m, avg_net_close_bps=-74.7609, positive_net_close_rate=0.0000, sl_touch_rate=0.3333, best_net_close_shortfall_bps=42.9214.
- Mature recovery-forward evidence remains negative after costs: signals=10, horizon=5m, best recovery|tick_dmid net close=-27.2615 bps.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=116.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added recovery closest_shortfalls to tools\koko_dry_observe_readiness.py.
- Each best recovery row now carries per-gate shortfalls for failed recovery gates.
- TDI reporter now includes recovery_shortfalls in readiness evidence so Gmail/relay can show observed vs required recovery gate misses.
- Added focused tests for readiness shortfall math and reporter output.
- This is diagnostics/evidence fidelity only; it does not tune Profit Score or loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_dry_observe_readiness tests.test_tdi_status_reporter: PASS, 68 tests.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 02:46:19" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=no_send.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue DRY observe and use recovery_shortfalls to watch tick_dmid, top-book, spread, and pressure convergence.
- Do not tune Profit Score while mature forward evidence remains negative.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:58:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: dry forward-evidence fidelity patch, focused test verification, dry_pnl_guard forward artifact refresh, and reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the material patch status and correctly did not send because the two-hour cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Latest bounded observe still has opened=28, closed=28, wins=8, losses=20, open_count=0, blocked_open=116.
- Fresh readiness remains usable for observe: signals=8331, quote_volume_usable=644, dmid_usable=3754, tick_dmid_ready=310, tick_dmid_warmed=7969, liquid_dmid_overlap=437, liquid_dmid_spread_tob_overlap=57.
- U/stale feed is not the current cause: U=120, S=393, brf=120, book_gap=false.
- Timestamp/cache coverage is usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset is usable: liquid_subset=24 against min 10.
- Full-universe green breadth remains weak: green_ratio=0.7350 against min 0.8500, while best ranked green remains usable at 0.9000.
- Recovery candidate coverage remains signals=69, all_recovery_metrics=0 with failures tick_dmid=67, book_pressure=60, tob_usd=50, spread=13.
- Refreshed mature dry_pnl_guard forward evidence is negative after costs: signals=3, horizon=5m, avg_net_close_bps=-74.7609, positive_net_close_rate=0.0000, sl_touch_rate=0.3333, best_net_close_shortfall_bps=42.9214.
- Mature recovery-forward evidence remains negative after costs: signals=10, horizon=5m, best recovery|tick_dmid net close=-27.2615 bps.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=116.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Patched tools\koko_paper_signal_forward_outcomes.py so PAPER_BUY_SIGNAL analysis skips signals whose forward horizon is not mature.
- Added a regression test proving not-mature dry_pnl_guard signals are counted as failures and do not fetch forward candles.
- Refreshed logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json with mature-only dry_pnl_guard evidence.
- This is diagnostics/evidence fidelity only; it does not tune Profit Score or loosen any DRY entry/P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 52 tests.
- python -m py_compile tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_paper_signal_forward_outcomes.py --activity-log logs\activity_ticker.log --since-ts-utc "2026-06-04T07:46:19Z" --reasons dry_pnl_guard --horizon-min 5 --granularity 60 --limit 40 --out logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue DRY observe under the data/preflight lane until recovery products can satisfy the full stack and forward evidence is net positive after costs.
- Do not tune Profit Score while mature forward evidence remains negative.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:56:20Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: fresh bounded DRY observe, readiness refresh, matured 5-minute recovery-forward evidence refresh, and reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporting cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the material status and correctly did not send because the two-hour cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Latest bounded observe increased blocked_open to 116 and produced no new opens.
- Fresh readiness shows signals=8331, quote_volume_usable=644, dmid_usable=3754, tick_dmid_ready=310, tick_dmid_warmed=7969, liquid_dmid_overlap=437, liquid_dmid_spread_tob_overlap=57.
- U/stale feed is not the current cause: reporter evidence shows U=120, S=393, brf=120, book_gap=false, book_metric_source_present_ratio=0.9867.
- Timestamp/cache coverage is usable: timestamp_ratio=0.9669, cache_supported=true, cache_openable=true.
- Liquid subset is usable: liquid_subset=24 against min 10.
- Green breadth remains weak in the full universe: green_ratio=0.7350 against min 0.8500, but best ranked green is usable at 0.9000.
- Recovery candidate coverage remains signals=69, all_recovery_metrics=0.
- Recovery gate failures are tick_dmid=67, book_pressure=60, tob_usd=50, spread=13.
- Fresh all-pass candidates were NEAR-USD rows blocked by dry_pnl_guard.
- Latest matured recovery-forward evidence is negative after costs: signals=10, horizon=5m, positive_net_close_rate=0.0000.
- Best recovery|tick_dmid net close was -27.2615 bps, so the best recovery row still missed net break-even by 27.2615 bps.
- recovery|tob_usd avg_net_close_bps=-39.0508; recovery|tick_dmid avg_net_close_bps=-39.4071; recovery|tick_dmid|book_pressure avg_net_close_bps=-43.7874.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=116.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- No code patch was applied in this handoff update.
- Refreshed the recovery-forward artifact after the fresh rows matured.
- This is not Profit Score tuning and does not loosen any DRY entry or P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python tools\koko_paper_signal_forward_outcomes.py --readiness-recovery logs\dry_observe_readiness_latest.json --since-ts-utc "2026-06-04T07:46:19Z" --horizon-min 5 --granularity 60 --limit 20 --out logs\paper_signal_forward_outcomes_latest_recovery_5m.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD); sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Continue DRY observe under the data/preflight lane until recovery products can satisfy the full stack and forward evidence is net positive after costs.
- Do not tune Profit Score while no credible positive dry evidence is present.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired and credentials are still absent: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:45:20Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: recovery-forward cost-shortfall diagnostic patch, artifact refresh, reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Positive-expectancy recovery products remain VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage remains signals=69, all_recovery_metrics=0.
- Recovery gate failures remain tick_dmid=63, book_pressure=55, tob_usd=45, spread=11.
- New recovery-forward shortfall evidence: recovery_forward signals=10, horizon=5m, best_reason=recovery|tick_dmid, avg_net_close_bps=-24.0989, positive_net_close_rate=0.0000, best_net_close_bps=-11.9152, shortfall_bps=11.9152.
- Interpretation: some recovery rows had positive raw close, but none covered conservative costs; the best row still missed net break-even by 11.9152 bps.
- Book-pressure recovery row remains worse: avg_net_close_bps=-39.9414, positive_net_close_rate=0.0000, shortfall_bps=39.9414.
- Fresh all-pass dry_pnl_guard forward evidence remains negative: signals=6, horizon=5m, avg_net_close_bps=-41.3445, positive_net_close_rate=0.0000, sl_touch_rate=0.5000.
- No credible positive dry profitability evidence yet.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=112.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Added best_net_forward_close_bps and best_net_close_shortfall_bps to forward outcome summaries.
- TDI reporter recovery_forward evidence now includes best_net_close_bps and shortfall_bps.
- Refreshed logs\paper_signal_forward_outcomes_latest_recovery_5m.json with the new fields.
- This is not Profit Score tuning and does not loosen any DRY entry or P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 51 tests.
- python -m py_compile tools\koko_paper_signal_forward_outcomes.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-recovery logs\dry_observe_readiness_latest.json --since-ts-utc "2026-06-04T07:27:57Z" --horizon-min 5 --granularity 60 --limit 20 --out logs\paper_signal_forward_outcomes_latest_recovery_5m.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered status with recovery_forward best_net_close_bps=-11.9152 and shortfall_bps=11.9152.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Do not loosen recovery gates while recovery_forward best net close remains below break-even.
- Continue DRY observe until positive-expectancy recovery products satisfy the full live gates and forward evidence is net positive after costs.
- Do not tune Profit Score while opened=0.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:43:10Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: recovery-forward diagnostic patch, readiness regeneration, focused test verification, and reporter render verification.
- DRY remains true and LIVE remains false.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter rendered the patch-change status with recovery_forward evidence and no send was requested for the render; two-hour cadence remains the reporting lane.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe has usable market coverage, but net-negative DRY P&L safety is still preventing new opens.
- Latest blocker remains dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- Latest dry P&L remains net negative and unchanged: -0.30033076 USD.
- Positive-expectancy recovery products remain VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage over the refreshed readiness slice: signals=69, all_recovery_metrics=0.
- Recovery gate failures: tick_dmid=63, book_pressure=55, tob_usd=45, spread=11.
- Best recovery row is XRP-USD with tick_dmid=13.60 bps, spread=0.85 bps, tob=4667 USD, but book pressure=0.2863 below the required 0.9.
- The new recovery-forward diagnostic shows that top recovery rows were not profitable after costs: recovery_forward signals=10, horizon=5m, best_reason=recovery|tick_dmid, avg_net_close_bps=-24.0989, positive_net_close_rate=0.0000.
- The book-pressure-failed recovery row was also negative: avg_net_close_bps=-39.9414, positive_net_close_rate=0.0000.
- Fresh all-pass dry_pnl_guard forward evidence remains negative: signals=6, horizon=5m, avg_net_close_bps=-41.3445, positive_net_close_rate=0.0000, sl_touch_rate=0.5000.
- U/stale feed is not the current blocker: latest readiness shows U=120, S=393, brf=120.
- Missing product/cache gap is not the current blocker: book_metric_source_present_ratio=0.9852, book_gap=false, cache_supported=true, cache_openable=true.
- Liquid/full-stack coverage remains usable but sparse: signals=9602, quote_volume_usable=784, dmid_usable=3831, tick_dmid_ready=438, tick_dmid_warmed=9260, liquid_dmid_overlap=523, liquid_dmid_spread_tob_overlap=119.
- No credible positive dry profitability evidence yet; net dry P&L remains negative and recovery-forward evidence is negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_paper_signal_forward_outcomes.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_recovery_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=112.
- Credible positive dry profitability evidence is not present yet.

Patch/change evidence:
- Readiness recovery rows now preserve ts_utc, tick, mid, quote volume, range, and book source so top positive-expectancy recovery candidates can be forward-tested.
- Added --readiness-recovery mode to tools\koko_paper_signal_forward_outcomes.py.
- Added TDI reporter loading and email evidence for logs\paper_signal_forward_outcomes_latest_recovery_5m.json.
- Added tests covering recovery row fields, recovery candidate forward analysis, and recovery_forward email evidence.
- This is not Profit Score tuning and does not loosen any DRY entry or P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_koko_paper_signal_forward_outcomes tests.test_tdi_status_reporter: PASS, 51 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 27 tests.
- python -m py_compile tools\koko_paper_signal_forward_outcomes.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 02:27:57" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-recovery logs\dry_observe_readiness_latest.json --since-ts-utc "2026-06-04T07:27:57Z" --horizon-min 5 --granularity 60 --limit 20 --out logs\paper_signal_forward_outcomes_latest_recovery_5m.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered status with recovery_forward evidence.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Do not loosen recovery gates while recovery_forward and dry_pnl_guard_forward are negative.
- Continue DRY observe until positive-expectancy recovery products satisfy the full live gates and forward evidence is not negative.
- Do not tune Profit Score while opened=0.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:39:10Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: bounded DRY observe refresh, reporter blocker-selection patch, test verification, and refreshed dry_pnl_guard forward evidence.
- DRY remains true and LIVE remains false.
- Reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter rendered the material patch-change status with subject [TDI STATUS] Profit 27/100 | DRY=true LIVE=false | dry signal blocked by net_negative_low_tick_dmid (XRP-USD), and correctly did not send because the two-hour cadence was not due: reason=report_cadence_not_due.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe is running with usable market coverage, but net-negative DRY P&L safety is preventing new opens until a positive-expectancy recovery product satisfies the full recovery stack.
- Latest concrete blocked opens are XRP-USD; blocked_open increased from 101 to 112 in the latest bounded observe.
- New latest blocked-open causes include net_negative_low_tick_dmid and net_negative_low_pressure.
- Latest ledger blocked open: XRP-USD reason=net_negative_low_tick_dmid at 2026-06-04T07:32:11Z.
- Positive-expectancy recovery products remain VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage over the refreshed readiness slice: signals=69, all_recovery_metrics=0.
- Recovery gate failures: tick_dmid=63, book_pressure=55, tob_usd=45, spread=11.
- Best current recovery row is XRP-USD with tick_dmid=13.60 bps, spread=0.85 bps, tob=4667 USD, but book pressure=0.2863 below the required 0.9.
- Other XRP recovery rows have pressure >= 0.9 but fail tick_dmid.
- U/stale feed is not the current blocker: latest readiness shows U=120, S=393, brf=120.
- Missing product/cache gap is not the current blocker: book_metric_source_present_ratio=0.9852, book_gap=false, cache_supported=true, cache_openable=true.
- Liquid/full-stack coverage improved but remains sparse: signals=9602, quote_volume_usable=784, dmid_usable=3831, tick_dmid_ready=438, tick_dmid_warmed=9260, liquid_dmid_overlap=523, liquid_dmid_spread_tob_overlap=119.
- Green breadth has a raw shortfall in the full universe, but the selected ranked slice is usable: green_ratio=0.7350/0.8500, best_ranked_green=0.9000, liquid_subset=24/10.
- Fresh all-pass dry_pnl_guard forward evidence remains negative: signals=6, horizon=5m, avg_net_close_bps=-41.3445, positive_net_close_rate=0.0000, sl_touch_rate=0.5000.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open=112 after the latest bounded observe.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative and recovery all_recovery_metrics remains 0.

Patch/change evidence:
- Patched tools\tdi_status_reporter.py so current blocker selection prefers a fresh DRY blocked-open ledger cause when the blocked-open timestamp falls inside the current readiness/tick window.
- Added a regression test proving the reporter names dry signal blocked by net_negative_low_tick_dmid (XRP-USD) for a fresh observe-window blocked open.
- Preserved the stale-ledger guard: old blocked_open rows are still ignored when the current readiness window does not include them.
- This is not Profit Score tuning and does not loosen the DRY P&L guard.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- Bounded observe command completed DRY-only after 30 configured cycles; no lingering Python process remained.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 02:27:57" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py --reasons dry_pnl_guard --horizon-min 5 ...: completed; avg_net_forward_close_bps=-41.3445.
- python -m unittest tests.test_tdi_status_reporter: PASS, 40 tests.
- python -m py_compile tools\tdi_status_reporter.py: PASS.
- Reporter blocker render now returns dry signal blocked by net_negative_low_tick_dmid (XRP-USD).
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --no-send: rendered status; sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Keep observing recovery coverage for VVV-USD, XLM-USD, and XRP-USD until tick_dmid >= 10 bps, book_pressure >= 0.9, spread <= 5 bps, tob >= 500 USD, and current DRY gates align.
- Do not tune Profit Score while opened=0.
- Resume dry P&L improvement only after eligible recovery coverage can actually open candidates and forward evidence is not negative.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:34:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: bounded DRY observe refresh and readiness/P&L evidence refresh after the reporting-cadence request.
- DRY remains true and LIVE remains false.
- Reporting cadence is set to every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe is running with usable market coverage, but net-negative DRY P&L safety is preventing new opens until a positive-expectancy recovery product satisfies the full recovery stack.
- Latest concrete blocked opens are XRP-USD with reason=net_negative_low_tick_dmid at 2026-06-04T07:21:46Z, 2026-06-04T07:22:39Z, 2026-06-04T07:23:07Z, 2026-06-04T07:23:26Z, and 2026-06-04T07:23:52Z.
- Positive-expectancy recovery products remain VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage over the refreshed readiness slice: signals=51, all_recovery_metrics=0.
- Recovery gate failures: tick_dmid=46, tob_usd=38, book_pressure=37, spread=10.
- Best current recovery rows are XRP-USD with all gates except tick_dmid passing; best observed tick_dmid is 3.415 bps against the required 10.0 bps.
- VVV-USD had a row with tick_dmid=20.634 bps, pressure=0.9956, spread=1.144 bps, but top-of-book was only 16.55 USD, below the 500 USD requirement.
- U/stale feed is not the current blocker; refreshed readiness has live feed coverage and tick-dmid warming.
- Missing product/cache gap is not the current blocker; book metric source present ratio is 0.9863.
- Liquid/full-stack coverage is still sparse: signals=5921, quote_volume_usable=476, dmid_usable=2538, tick_dmid_ready=337, tick_dmid_warmed=5573, liquid_dmid_overlap=323, liquid_dmid_spread_tob_overlap=65.
- Fresh all-pass dry_pnl_guard forward evidence remains negative: signals=8, horizon=5m, avg_net_close_bps=-66.3725, positive_net_close_rate=0.0000, sl_touch_rate=0.5000.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open increased from 96 to 101 after the latest bounded observe; all new blocked opens were XRP-USD net_negative_low_tick_dmid.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative and recovery all_recovery_metrics remains 0.

Action taken:
- Read CODEX_RELAY.md from branch codex/cloud-ready-koko-bot.
- Updated CODEX_RELAY.md with RELAY_FILE_VISIBLE=yes and the latest local DRY observe/readiness/P&L evidence.
- Confirmed the user reporting cadence request is reflected as every two hours.
- Did not tune Profit Score while opened=0.
- Did not touch Coinbase/order placement code.
- Did not touch static TP/SL safety.

Verification evidence:
- Latest readiness generated_at_utc=2026-06-04T07:24:07Z from logs\dry_observe_readiness_latest.json.
- Latest dry ledger event is XRP-USD blocked_open reason=net_negative_low_tick_dmid at 2026-06-04T07:23:52Z.
- Latest dry P&L score file shows opened=28, closed=28, wins=8, losses=20, blocked_open=101, net=-0.30033076 USD.
- Reporter CLI probe with unsupported flags failed locally; this was a tooling invocation error, not a TDI reporter product failure. It will be retried only with supported reporter arguments if a report render is needed.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Keep observing recovery coverage for VVV-USD, XLM-USD, and XRP-USD until tick_dmid >= 10 bps, book_pressure >= 0.9, spread <= 5 bps, tob >= 500 USD, and current DRY gates align.
- Do not tune Profit Score while opened=0.
- Resume dry P&L improvement only after eligible recovery coverage can actually open candidates.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:19:08Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local task completed: bounded DRY observe refresh plus reporter evidence patch for dry_pnl_guard forward outcomes.
- DRY remains true and LIVE remains false.
- Reporter rendered the material patch-change email and correctly did not send because the two-hour report cadence was not due: reason=report_cadence_not_due.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Fresh DRY observe had live feed coverage and all-pass candidates, but net-negative DRY P&L safety blocked them.
- Latest current blocker: runtime near-miss NEAR-USD blocked by tick_dmid.
- Positive-expectancy recovery products remain VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage over the refreshed readiness slice: signals=46, all_recovery_metrics=0.
- Recovery gate failures: tick_dmid=46, book_pressure=39, tob_usd=25, spread=15.
- Best recovery row is XRP-USD with only tick_dmid missing: tdmid=5.93 bps, press=0.9949, tob=967, score=0.9981.
- U/stale feed is not active: latest readiness shows U=120, S=393, brf=120.
- Coverage improved after the observe: signals=7645, liquid=614, dmid=3068, tick_dmid_ready=365, tick_dmid_warmed=7309, liquid_dmid_overlap=407, liquid_dmid_spread_tob_overlap=100, book_metric_source_present_ratio=0.986.
- Market breadth is passing in runtime context: latest_mbr=0.8917/0.8500 and latest_mdmid=69.16/0.00.
- Fresh all-pass dry_pnl_guard rows were not safe to scout: dry_pnl_guard_forward signals=8, horizon=5m, avg_net_close_bps=-66.3725, positive_net_close_rate=0.0000, sl_touch_rate=0.5000.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json
- C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- blocked_open increased from 93 to 96 after the bounded observe; the new blocked opens were XRP net_negative_low_tick_dmid.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative and refreshed recovery coverage has all_recovery_metrics=0.

Patch/change evidence:
- Added TDI reporter loading for logs/paper_signal_forward_outcomes_latest_dry_pnl_guard_5m.json.
- Forward evidence now reports dry_pnl_guard_forward signals, horizon, avg_net_close_bps, positive_net_close_rate, and sl_touch_rate.
- This is not Profit Score tuning and does not loosen the DRY P&L guard; it documents why blocked all-pass rows should remain blocked.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- Bounded observe command completed: KOKO_SUPERVISOR_MAX_CYCLES=24, DRY only, LIVE false.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 02:12:38" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\koko_paper_signal_forward_outcomes.py --reasons dry_pnl_guard --horizon-min 5 ...: completed; avg_net_forward_close_bps=-66.3725.
- python -m unittest tests.test_tdi_status_reporter: PASS, 39 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 27 tests.
- python -m py_compile tools\tdi_status_reporter.py: PASS.
- python tools\tdi_status_reporter.py --mode event --event patch_change ...: rendered status; sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Keep the DRY P&L guard in place.
- Wait for a positive-expectancy recovery product to satisfy tick_dmid >= 10 bps, book_pressure >= 0.9, spread <= 5 bps, tob >= 500 USD, and current DRY gates.
- Do not tune Profit Score while opened=0.
- Resume dry P&L improvement only after eligible recovery coverage can actually open candidates.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:10:46Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change completed: DRY observe readiness and TDI reporter now include positive-expectancy recovery-candidate coverage.
- DRY remains true and LIVE remains false.
- Reporter rendered the material patch-change email and correctly did not send because the two-hour report cadence was not due: reason=report_cadence_not_due.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe is usable, but current eligible recovery products have no complete high-quality recovery window.
- Positive-expectancy products detected from dry P&L state: VVV-USD, XLM-USD, XRP-USD.
- Recovery candidate coverage over the latest readiness slice: signals=34, all_recovery_metrics=0.
- Recovery gate failures: tick_dmid=33, book_pressure=29, tob_usd=24, spread=15.
- Best recovery row is XRP-USD with only tick_dmid missing: tdmid=1.68 bps, press=0.9718, tob=721, score=0.9981.
- U/stale feed is not active: latest readiness shows U=120, S=393, brf=120.
- Timestamp/cache/feed coverage is usable enough to observe: timestamp_ratio=0.9669, timestamp_usable=380/393, book_metric_source_present_ratio=0.9842.
- Liquid/dmid coverage exists but is sparse at the full entry stack: signals=5254, liquid=442, dmid=1871, tick_dmid_ready=190, liquid_dmid_overlap=289, liquid_dmid_spread_tob_overlap=51.
- Market breadth is passing in runtime drynear context: latest_mbr=0.8917/0.8500 and latest_mdmid=69.16/0.00.
- Current runtime near miss remains NEAR-USD blocked by spread.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative and recovery coverage has all_recovery_metrics=0.

Patch/change evidence:
- Added recovery_candidate_coverage to readiness output.
- Readiness now derives positive-expectancy products from DRY_PNL_STATE_PATH using the configured expectancy thresholds.
- Reporter readiness evidence now includes recovery_products, recovery all-metric count, top recovery failures, and best recovery candidate.
- This is not Profit Score tuning; it is preflight/feed/reporting coverage for why DRY observe is not opening while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 27 tests.
- python -m unittest tests.test_tdi_status_reporter: PASS, 38 tests.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 01:57:50" --out logs\dry_observe_readiness_latest.json: completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ...: rendered status; sent=false reason=report_cadence_not_due.
- No observe run was started after this patch because recovery all_recovery_metrics=0; running observe now would be waiting on market conditions, not testing a code fix.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Wait for a high-quality DRY recovery window where positive-expectancy products satisfy tick_dmid >= 10 bps, book_pressure >= 0.9, spread <= 5 bps, tob >= 500 USD, and current dry gates.
- Do not tune Profit Score while opened=0.
- Resume dry P&L improvement only after market coverage can actually open candidates.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T07:01:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change completed: DRY net-negative recovery entries now require immediate tick-dmid >= DRY_PNL_NET_NEGATIVE_MIN_TICK_DMID_BPS in addition to positive expectancy and book pressure.
- DRY remains true and LIVE remains false.
- Reporter rendered the material patch-change email but did not send/write outbox because report cadence was not due: reason=report_cadence_not_due.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- The 45-cycle observe before this patch opened high-pressure XRP and DOGE recovery entries and both closed as loss_trim.
- Net dry P&L worsened from -0.28643482 USD to -0.30033076 USD.
- Fresh losing entries had high pressure but weak immediate tick-dmid:
  - XRP-USD opened with press=0.9719192790443063 and dmid_bps/tick_dmid_bps=-3.3587, closed loss_trim at -21.8386 bps.
  - DOGE-USD opened with press=0.9329300829778928 and dmid_bps/tick_dmid_bps=-2.2251, closed loss_trim at -24.4812 bps.
- This proves the previous high-pressure-only recovery gate was insufficient.
- After the patch, a short bounded observe produced no new opens and did not worsen P&L further.
- Ledger evidence after the patch shows XRP blocked twice with reason=net_negative_low_tick_dmid.
- Current runtime near miss is NEAR-USD blocked by spread.
- U/stale feed is not active: latest readiness shows U=120, S=393, brf=120.
- Tick-dmid is warmed in the validation window: tick_dmid_warmed=4946/5254, tick_dmid_ready=190.
- Market breadth is passing: latest_mbr=0.8917/0.8500 and latest_mdmid=69.16/0.00.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 27/100.
- dry P&L: realized=-0.30033076 USD, unrealized=0.00000000 USD, net=-0.30033076 USD.
- opened/closed/wins/losses: opened=28, closed=28, wins=8, losses=20.
- open_count=0, positive_open_count=0, negative_open_count=0.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative.

Patch/change evidence:
- Added DRY_PNL_NET_NEGATIVE_MIN_TICK_DMID_BPS=10.0.
- _dry_pnl_entry_block_reason now rejects positive-expectancy net-negative recovery entries with net_negative_low_tick_dmid when payload tick_dmid_bps/dmid_bps is below the configured floor.
- Readiness active_gates now includes DRY_PNL_NET_NEGATIVE_MIN_BOOK_PRESSURE and DRY_PNL_NET_NEGATIVE_MIN_TICK_DMID_BPS.
- Regression coverage proves high-pressure positive-expectancy recovery is blocked when tick_dmid is negative, and still allowed when tick_dmid is above the floor.
- This is not Profit Score tuning; it is a DRY P&L safety/quality guard learned from fresh loss evidence.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": PASS, 12 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 26 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json: PASS.
- Pre-patch bounded observe with KOKO_SUPERVISOR_MAX_CYCLES=45 completed; opened increased to 28, both new opens closed loss_trim, net=-0.30033076.
- Post-patch bounded observe with KOKO_SUPERVISOR_MAX_CYCLES=18 completed; opened remained 28, closed remained 28, net remained -0.30033076.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 01:57:50": completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change ...: rendered status; sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY observe only for high-pressure, positive-expectancy entries that also satisfy tick_dmid >= 10 bps while net P&L is negative.
- Require realized/net dry P&L improvement before considering profitability recovery evidence credible.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T06:47:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change completed: TDI reporter now keeps real email/outbox updates on the two-hour cadence even if the CLI is called with --force.
- Forced previews still work only with --no-send; real sends/outbox writes must wait for TDI_REPORT_HOURLY_SEC=7200.
- Patch-change reporter event was rendered but not delivered or written to outbox because the existing two-hour cadence was not due: reason=missing SMTP env ['user', 'password', 'sender']; outbox_throttled.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Current runtime blocker remains runtime near-miss NEAR-USD blocked by tick_dmid.
- Latest monitor snapshot did not send a summary: reason=hourly_not_due.
- U/stale feed is not active: latest readiness shows U=120, S=393, brf=120.
- Market breadth is currently passing: latest_mbr=0.8917/0.8500 and latest_mdmid=69.16/0.00.
- Coverage remains usable but strict entry overlap is narrow: timestamp_ratio=0.9669, liquid_subset=24, liquid_dmid_overlap=17, liquid_dmid_spread_tob_overlap=3 in latest reporter evidence.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 28/100.
- dry P&L: realized=-0.28643482 USD, unrealized=0.00000000 USD, net=-0.28643482 USD.
- opened/closed/wins/losses: opened=26, closed=26, wins=8, losses=18.
- open_count=0.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative.

Patch/change evidence:
- maybe_send now passes force through to should_send only when no_send is true.
- This keeps manual preview/test rendering available without allowing forced real emails to bypass the two-hour reporting cadence.
- Added regression tests proving forced real sends obey cadence and forced no-send previews remain available.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest tests.test_tdi_status_reporter: PASS, 37 tests.
- python -m py_compile tools\tdi_status_reporter.py: PASS.
- python tools\tdi_status_monitor.py --once: completed; summary sent=false reason=hourly_not_due.
- python tools\tdi_status_reporter.py --mode event --event patch_change ...: rendered status; sent=false reason=missing SMTP env ['user', 'password', 'sender']; outbox_throttled.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY observe and collect profitability evidence without tuning Profit Score while open_count=0.
- Keep reporting updates to email/outbox at most once every two hours.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for real unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T06:35:17Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change completed: net-negative DRY recovery entries now require high book pressure when configured.
- DRY remains true and LIVE remains false.
- Routine/report email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporter rendered the material-event status but did not send/write outbox because report cadence was not due: reason=report_cadence_not_due.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Fresh bounded observe before the patch closed the open XRP recovery trade as a loss_trim.
- Net dry P&L worsened from -0.28167272 USD to -0.28643482 USD.
- The losing XRP entry had low book pressure: press=0.23302520063189458.
- Earlier profitable XRP/DOGE recovery entries had high book pressure around 0.91-0.98 and closed via profit_protect.
- Post-patch bounded observe did not open a new trade and did not worsen P&L further.
- Current runtime near miss is NEAR-USD blocked by tick_dmid.
- U/stale feed is not active: latest readiness shows U=120, S=393, brf=120.
- Market breadth is currently passing: latest_mbr=0.8917/0.8500, latest_mdmid=69.16/0.00.
- Coverage remains usable: timestamp_ratio=0.9669, liquid_subset=24, liquid_dmid_overlap=17, liquid_dmid_spread_tob_overlap=1 in the short post-patch window.
- No credible positive dry profitability evidence yet; net dry P&L remains negative.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 28/100.
- dry P&L: realized=-0.28643482 USD, unrealized=0.00000000 USD, net=-0.28643482 USD.
- opened/closed/wins/losses: opened=26, closed=26, wins=8, losses=18.
- open_count=0, positive_open_count=0, negative_open_count=0.
- XRP-USD is now quarantined after the latest loss_trim; XRP stats remain net positive overall but now include 1 loss.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative.

Patch/change evidence:
- Added DRY_PNL_NET_NEGATIVE_MIN_BOOK_PRESSURE=0.9.
- _dry_pnl_entry_block_reason now accepts the candidate payload and, while net dry P&L is negative, rejects positive-expectancy recovery entries below the configured pressure floor with net_negative_low_pressure.
- _dry_pnl_open_from_payload now passes the payload into the P&L guard so the guard can use the actual candidate press value already written to the dry ledger.
- Regression coverage proves low-pressure positive-expectancy XRP is blocked while high-pressure XRP remains allowed.
- This is not Profit Score tuning; it is a DRY P&L safety/quality gate learned from the latest loss evidence.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": PASS, 11 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json: PASS.
- Pre-patch bounded observe with KOKO_SUPERVISOR_MAX_CYCLES=35 completed; XRP closed loss_trim, net=-0.28643482.
- Post-patch bounded observe with KOKO_SUPERVISOR_MAX_CYCLES=18 completed; opened=26, closed=26, net remained -0.28643482.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 01:31:46": completed.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send: rendered status; sent=false reason=report_cadence_not_due.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY observe with net-negative recovery limited to positive-expectancy, high-pressure candidates.
- Watch for the next eligible high-pressure recovery entry and require realized/net improvement before considering the goal satisfied.
- Do not enable LIVE.

User action required:
- No for DRY/LIVE safety.
- Yes only for unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T06:22:38Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change completed: TDI/KOKO outbound email reporting is now capped at one update every two hours.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Material-event email attempts now also respect the two-hour report cadence unless explicitly forced for a manual preview/test.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter forced no-send preview rendered subject "[TDI STATUS] Profit 28/100 | DRY=true LIVE=false | runtime near-miss NEAR-USD blocked by market_breadth".
- No email/outbox write was created by the preview.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe can open candidates; latest opened count remains 26 with open_count=1.
- Current runtime blocker remains market breadth: latest near miss is NEAR-USD blocked by market_breadth.
- U/stale feed is not active: latest tick_diag shows U=120, S=393, brf=120, drysig=0, dryopen=0.
- Latest readiness evidence remains usable: signals=7156, book_metric_source_present_ratio=0.9852, tick_dmid_warmed=6843, tick_dmid_ready=609.
- Liquid/dmid overlap remains present: liquid_dmid_overlap=179, liquid_dmid_spread_tob_overlap=31.
- Latest market breadth is just below gate: latest_mbr=0.8417/0.8500, latest_mdmid=64.17/0.00.
- Net-negative P&L guard remains active; do not tune Profit Score blindly.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 28/100.
- dry P&L: realized=-0.28242463 USD, unrealized=0.00075191 USD, net=-0.28167272 USD.
- opened/closed/wins/losses: opened=26, closed=25, wins=8, losses=17.
- open_count=1, positive_open_count=1, negative_open_count=0.
- Current open position remains XRP-USD with small positive unrealized P&L in latest state.
- Credible positive dry profitability evidence is not present yet because net P&L remains negative.

Patch/change evidence:
- should_send now checks the latest report attempt epoch across last_report_epoch, last_hourly_epoch, and last_outbox_epoch before allowing material-event emails.
- Event skips caused by the cadence cap return report_cadence_not_due.
- Cadence skips do not mark the material fingerprint, so the event can still appear when the next two-hour report is due.
- Actual send/outbox attempts update last_report_epoch and material-event dedupe.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": PASS, 35 tests.
- python -m py_compile tools\tdi_status_reporter.py tools\tdi_status_monitor.py: PASS.
- python tools\tdi_status_reporter.py --mode event --event patch_change --force --no-send: rendered current status; sent=false reason=no_send.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine/report email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe/P&L recovery after cadence guard verification.
- Let positive-expectancy recovery continue while net P&L remains negative.
- Do not enable LIVE.

User action required:
- No for cadence and DRY/LIVE safety.
- Yes only for unattended Gmail delivery if SMTP delivery is desired: provide TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T06:18:10Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change event completed: DRY net-negative entries now require positive product expectancy.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter rendered the material-event email with subject "[TDI STATUS] Profit 28/100 | DRY=true LIVE=false | runtime near-miss NEAR-USD blocked by market_breadth".
- Email send is still blocked by missing SMTP env: user, password, sender. Reporter also reported outbox_throttled.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- DRY observe can open candidates; latest bounded run opened/closed only positive-expectancy/product-recovery candidates.
- Remaining blocker is not timestamp/cache/liquid subset coverage. Latest runtime near miss is NEAR-USD blocked by market_breadth.
- Latest readiness since 2026-06-04 01:13:43: signals=7156, book_metric_source_present=7050/7156, book_metric_source_present_ratio=0.9852.
- U/stale feed is not active: latest tick_diag shows U=120, S=393, top=393, chk=393, brf=120.
- Tick-dmid coverage is warmed and improved: tick_dmid_warmed=6843/7156, tick_dmid_ready=609/7156, tick_diag_dmid_ready=180.
- Liquid/dmid overlap is present: liquid_dmid_overlap=179, liquid_dmid_spread_tob_overlap=31.
- Latest market breadth is just below gate: latest_mbr=0.8417/0.8500, latest_mdmid=64.17/0.00.
- New P&L guard is active: latest tick_diag shows LIGHTER-USD and SOL-USD with pnl=net_negative_no_expectancy while total dry net P&L remains negative.
- dry_pnl_guard appeared 7 times in latest readiness, proving the guard is blocking loss-history/unproven candidates during net-negative recovery.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 28/100.
- dry P&L: realized=-0.28242463 USD, unrealized=0.00075191 USD, net=-0.28167272 USD.
- Prior checkpoint was Profit Score 26/100 and net=-0.28502251 USD, so this is a small improvement, not completion.
- opened/closed/wins/losses: opened=26, closed=25, wins=8, losses=17.
- open_count=1, positive_open_count=1, negative_open_count=0, quarantined=16.
- Open position: XRP-USD +2.5064 bps / +0.00075191 USD.
- Latest P&L event timestamp: 2026-06-04T06:17:05Z.
- No credible positive dry profitability evidence is present yet because net P&L remains negative.

Patch/change evidence:
- Set DRY_PNL_BLOCK_NEW_WHEN_NET_NEGATIVE=true.
- Set DRY_PNL_REQUIRE_POSITIVE_EXPECTANCY_WHEN_NEGATIVE=true.
- Kept DRY_PNL_HARD_BLOCK_WHEN_NET_NEGATIVE=false, so the system is not fully shut down; it can still recover through products with positive dry expectancy.
- Added regression coverage proving that while dry net is negative, a positive-expectancy product such as XRP is allowed and negative/unproven products are rejected with net_negative_no_expectancy.
- Latest bounded observe closed DOGE and XRP via profit_protect and opened a new XRP position only.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": PASS, 10 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python -m json.tool run_settings.json: PASS.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=25 and PAPER_SIGNAL_MIN_TICK_GAP=1: completed; wins increased from 6 to 8 and net improved from -0.28502251 to -0.28167272.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 01:13:43": completed; signals=7156.
- python tools\tdi_status_reporter.py --mode event --event patch_change --force: rendered status email; sent=false due missing SMTP env and outbox_throttled.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only recovery using positive-expectancy products while net P&L remains negative.
- Monitor XRP open and market-breadth recovery before considering any further P&L gate changes.
- Do not enable LIVE.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T06:11:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local patch/change event completed: tick-dmid DRY observe probe now requires strong book pressure when configured.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter rendered the material-event email, but send is still blocked by missing SMTP env: user, password, sender. It also reported outbox_throttled.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Feed/preflight coverage is usable enough to open DRY candidates; opened=25 and max_dryopen=1 in the latest bounded run.
- Remaining blocker is not timestamp/cache/liquid subset coverage. It is entry quality and protection: cache-liquid candidates are mostly blocked by trough, spread, or top-book USD.
- Latest readiness since 2026-06-04 01:06:27: signals=7522, book_metric_source_present=7413/7522, book_metric_source_present_ratio=0.9855.
- U/stale feed is not active: latest tick_diag shows U=120, S=393, top=393, chk=393, brf=120.
- Tick-dmid coverage is warmed but sparse: tick_dmid_warmed=7202/7522, tick_dmid_ready=231/7522, tick_diag_dmid_ready=74.
- Liquid/dmid overlap is present but strict entry overlap remains narrow: liquid_dmid_overlap=287, liquid_dmid_spread_tob_overlap=36.
- Market breadth is green enough: latest_mbr=0.8917/0.8500 and latest_mdmid=59.12/0.00.
- New pressure floor is active: one-gate tick_dmid near-misses such as NEAR-USD are rejected with dry_observe_probe.reason=tick_dmid_book_pressure_floor unless book pressure reaches 0.9.
- Latest dry liquid early skip top: ZEC-USD trough; trough-probe rejected on spread at spr=6.50/5.00.
- Latest closest spread/top-book shortfall: ADA-USD with spread_excess=0.07 bps, no top-book shortfall.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29669003 USD, unrealized=0.01166752 USD, net=-0.28502251 USD.
- opened/closed/wins/losses: opened=25, closed=23, wins=6, losses=17.
- open_count=2, positive_open_count=1, negative_open_count=1, quarantined=16.
- Open positions: DOGE-USD +40.5691 bps / +0.01217072 USD; XRP-USD -1.6774 bps / -0.00050321 USD.
- Latest P&L event timestamp: 2026-06-04T06:09:39Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Added DRY_OBSERVE_PROBE_MIN_TICK_DMID_FAILURE_BOOK_PRESSURE=0.9.
- Runtime _dry_observe_probe_ok now rejects tick_dmid-only probe exceptions below that book-pressure floor.
- Readiness reporting mirrors the same tick_dmid_book_pressure_floor decision.
- This was based on latest DRY evidence: DOGE and XRP high-pressure survivors stayed positive/near-flat, while prior low-pressure tick-dmid probes closed as losses.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 39 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 26 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=25 and PAPER_SIGNAL_MIN_TICK_GAP=1: completed; opened advanced to 25 and closed to 23.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 01:06:27": completed; signals=7522.
- python tools\tdi_status_reporter.py --mode event --event patch_change --force: rendered status email; sent=false due missing SMTP env and outbox_throttled.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY P&L improvement from usable coverage; inspect top-book/trough causes and protect net until positive dry evidence appears.
- Do not enable LIVE.
- Do not tune Profit Score blindly; opened/open_count is now nonzero, so optimize only against observed DRY P&L evidence.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T05:50:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local rank-alignment patch, bounded DRY observe, and full activity-log readiness regeneration completed.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- Data/preflight coverage is now usable; zero-open blocker is no longer timestamp coverage, missing cache/products, U=0 stale feed, or liquid subset coverage.
- Runtime candidate rank now aligns with cache/preflight semantics for DRY_CANDIDATE_RANK=timestamp_liquidity_dmid_desc.
- Latest readiness from actual activity log since 2026-06-04 00:47:43: signals=2350, book_metric_source_present=2319, book_metric_source_missing=31, max_book_refresh_count=120.
- U/stale feed is not active: tick_diag rows show U=120, S=393, brf=120, top=393, chk=393.
- Liquid/dmid coverage improved: liquid_dmid_overlap=109 and liquid_dmid_spread_tob_overlap=25.
- Market breadth is now passing on near-misses: market_green_ratio=0.8833/0.8500 and market_dmid_bps=60.46/0.00.
- Tick-dmid is warmed but rarely usable: tick_dmid_warmed=2012/2350, tick_dmid_ready=37/2350, max_tick_dmid_ready=28.
- No all-pass candidates and no dry opens yet: max_dry_signal=0, max_dry_open=0.
- Dominant remaining blockers are entry confirmation: spread=1520, trough=425, trough_wait=216, tob_usd=155, dmid/tick_dmid=33, quote_volume=1.
- Closest top near miss: NEAR-USD fails only tick_dmid; rdmid=130.2803, qv=2496131.4674, spr=3.9116/5.0, tob=502.1058/500, tick_dmid=3.9131/10, tick_dmid_warmed=true, market breadth passes.
- Closest liquid+dmid spread/top-book shortfall: ADA-USD fails spread by 0.0826 bps and tick_dmid; rdmid=40.8163, tob=7670.94/500, tick_dmid=5.0852/10, tick_dmid_warmed=true.
- Dry liquid early skips remain trough-probe rejections: spread=2 and tob_usd=2.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Runtime timestamp_liquidity_dmid_desc rank now prioritizes timestamp and recent-candle liquidity/dmid before spread/top-book tie-breakers, matching the cache/preflight rank model. Hard spread/top-book gates still run unchanged.
- Added regression coverage so timestamp_liquidity_dmid_desc cannot drift back to book-first ranking.
- Cache regime flat reporting fields remain in place and current cache evidence remains supported/openable.
- Bounded DRY observe with PAPER_SIGNAL_MIN_TICK_GAP=1 and KOKO_SUPERVISOR_MAX_CYCLES=8 completed; no dry open yet.
- Corrected readiness regeneration to use logs/activity_ticker.log, the active ACTIVITY_LOG_PATH.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.
- No Profit Score tuning was done while open_count=0.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": PASS, 23 tests.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 36 tests.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": PASS, 32 tests.
- python -m py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py managers\run_manager\run_manager.py tools\tdi_status_reporter.py: PASS.
- python tools\run_koko_dry_supervised.py with bounded KOKO_SUPERVISOR_MAX_CYCLES=8 and PAPER_SIGNAL_MIN_TICK_GAP=1: completed; no dry open.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-04 00:47:43": completed; signals=2350.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight diagnostics on tick_dmid ready thresholds, spread near-misses, trough_wait, and top-book USD near misses.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T05:45:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local data/preflight patch, cache regime regeneration, and bounded DRY observe completed.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.

Current blocker:
- The previous timestamp/missing-cache/liquid-subset coverage gap is improved enough for DRY observe.
- Latest cache evidence: supported=true, worthwhile=true, openable=true, timestamp_ratio=0.9669, timestamp_missing_files=0, timestamp_outside_window_files=13.
- Best ranked cache mode is now timestamp_liquidity_dmid_desc: green_ratio=0.9000, liquid_subset=24, dmid_liquidity_overlap=17, dmid_liquidity_range_overlap=16, probe_quote_overlap=40.
- run_settings.json now uses DRY_CANDIDATE_RANK=timestamp_liquidity_dmid_desc so runtime top-120 coverage aligns with the cache evidence.
- Latest bounded DRY observe still opened zero: opened_delta=0, closed_delta=0, signals=341, open_candidate=false.
- Runtime overlap improved: liquid_dmid=17 and liquid_dmid_spread_tob=2.
- Current blocker moved to entry confirmation/trough/tick/market-breadth, not timestamp coverage, missing products/cache, U=0 stale feed, or liquid subset coverage.
- Latest readiness dominant_blocker=trough.
- Closest liquid early skip: LTC-USD rejected on trough top-book USD, tob_usd=489.7011 versus min 500.0, prefetch_tob_usd=577.7793, qv=353956, rdmid=58.61.
- Closest one-gate near miss: NEAR-USD fails tick_dmid only; rdmid=130.2803, qv=3009493.3413, spr=3.8782/5.0, tob=907.617/500, tick_dmid=0.0, tick_dmid_warmed=false.
- Closest runtime near miss: NEAR-USD fails dmid/tick and market_breadth; market_green_ratio=0.6667/0.8500, market_dmid_bps=45.29/0.00, market_breadth_source=recent_candle.
- U=0/stale feed is not the active blocker in this run; runtime products were present: products=393, ranked_rows=393, discovered=393.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Cache regime output now emits flat reporting/preflight fields at source: supported, worthwhile, diagnostic_worthwhile, openable, blocker, timestamp_ratio, liquid_subset, dmid_quote, dmid_quote_range, best_ranked, best_probe, and ranked overlap fields.
- Cache promotion_hint now includes dmid_liquidity_overlap and dmid_liquidity_range_overlap so downstream status does not read null overlap evidence.
- Runtime DRY candidate rank changed from dmid_desc to timestamp_liquidity_dmid_desc to fix liquid subset/top-120 coverage. This is a data/preflight coverage change, not Profit Score tuning.
- Regenerated cache evidence after the patch shows top-120 ranked coverage passes configured regime: liquid_subset=24, dmid_liquidity_overlap=17, dmid_liquidity_range_overlap=16.
- Bounded DRY observe with PAPER_SIGNAL_MIN_TICK_GAP=1 and KOKO_SUPERVISOR_MAX_CYCLES=8 completed; no dry open yet.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact.
- No Profit Score tuning was done while open_count=0.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": PASS, 23 tests.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 35 tests.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": PASS, 32 tests.
- python -m py_compile tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py managers\run_manager\run_manager.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_cache_market_regime.py ... --out logs\cache_market_regime_latest.json: completed; supported=true, worthwhile=true, best_ranked=timestamp_liquidity_dmid_desc.
- python tools\run_koko_dry_supervised.py with bounded KOKO_SUPERVISOR_MAX_CYCLES=8 and PAPER_SIGNAL_MIN_TICK_GAP=1: completed; no dry open.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight diagnostics on entry confirmation: tick_dmid warmup/ready state, market breadth at runtime, and trough/top-book USD near misses.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T05:37:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local DRY diagnostic patch and bounded DRY observe completed.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Material event report rendered but was not delivered: sent=false because SMTP user/password/sender env is missing and the local outbox was throttled.
- No Coinbase/order placement path was touched.

Current blocker:
- Preflight/feed coverage remains usable enough to observe; no Profit Score tuning was done.
- Latest bounded diagnostic observe used PAPER_SIGNAL_MIN_TICK_GAP=1 via env only for fresh per-tick paper-signal coverage.
- Latest readiness evidence: signals=1817, book_metric_source_present=1797, book_metric_source_missing=20, tick_dmid_warmed=1454, tick_dmid_ready=28.
- U=0/stale feed is not active: U=120, S=393, brf=120, tick_diag_rows=6.
- Liquid+dmid overlap exists but still does not pass spread/top-book/tick together: liquid_dmid_overlap=5, liquid_dmid_spread_tob_overlap=0, all_pass_candidates=0, max_dry_signal=0, max_dry_open=0.
- Current closest liquid+dmid shortfall is WLD-USD: failures=spread|tob_usd|tick_dmid, spr_bps=6.0502 versus max 5.0, tob_usd=198.126333 versus min 500, tick_dmid not usable.
- Latest dryliqskip_top remains ZEC-USD: trough probe rejected on spread, qv=1670882, rdmid=79.97, spread=11.40/5.00.
- Runtime near miss has top-book but insufficient dmid and market breadth: HYPE-USD qv=2882929, rdmid=28.82/40.00, spr=2.75, tob=1176, latest market breadth about 0.1750/0.8500 and market dmid about -36.88/0.00.
- The current blocker is real liquid+dmid spread/top-book/tick/market-breadth overlap, not timestamp coverage, missing products/cache, or U=0 stale feed.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- PAPER_BUY_SIGNAL now defaults book_metric_source from the metric source whenever DRY metrics provide one, so top-book/spread failures like WLD no longer appear as unlabeled book-source gaps.
- PAPER_SIGNAL_MIN_TICK_GAP can now be overridden by env for bounded diagnostic runs without changing run_settings.json.
- Bounded diagnostic observe with PAPER_SIGNAL_MIN_TICK_GAP=1 produced fresh per-tick evidence and confirmed zero opens under current gates.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.
- No Profit Score tuning was done while open_count=0.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 35 tests.
- python -m py_compile managers\run_manager\run_manager.py: PASS.
- python tools\run_koko_dry_supervised.py with bounded KOKO_SUPERVISOR_MAX_CYCLES=6 and PAPER_SIGNAL_MIN_TICK_GAP=1: completed; no dry open.
- python tools\koko_dry_observe_readiness.py --since-local-start "2026-06-04 00:35:03": OK, readiness refreshed.
- python tools\tdi_status_reporter.py --mode event --event patch_change --force: rendered subject "[TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (1; top ZEC-USD)" but sent=false due missing SMTP env and outbox throttling.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight coverage around liquid+dmid spread/top-book/tick overlap.
- Use bounded PAPER_SIGNAL_MIN_TICK_GAP=1 diagnostics only when fresh per-tick entry evidence is needed.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T05:29:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local cache/preflight lane patch and bounded DRY observe completed.
- DRY remains true and LIVE remains false.
- Routine TDI/KOKO email cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Material event reports still trigger immediately.
- Reporting destination remains tdifactorToday@gmail.com.
- Material event report for this patch rendered but was not delivered: sent=false because SMTP user/password/sender env is missing and the local outbox was throttled.
- No Coinbase/order placement path was touched.

Current blocker:
- Preflight/feed coverage is now openable enough for DRY observe; do not tune Profit Score while open_count=0.
- Cache evidence is usable: supported=true, worthwhile=true, timestamp_ratio=0.9644, timestamp_usable=379/393, timestamp_missing_files=0, timestamp_outside=14.
- Missing product/cache gap is not active: selected_products=393 and timestamp_missing_files=0.
- U=0/stale feed is not active: latest tick diagnostics show U=120, S=393, brf=120, tick_diag_rows=3, tick_dmid_nonzero=73, tick_dmid_ready=14.
- Liquid subset coverage exists: quote_volume_ge_min=20 versus min_liquid_subset_products=10.
- Green breadth remains weak: full-cache green_ratio=0.2491 versus 0.8500; best_probe=dmid_desc green_ratio=0.6486 versus 0.8500.
- Cache-ranked probe now has usable overlap under the configured DRY observe probe floors: best_probe_liquid=10, dmid_liquidity_overlap=2, dmid_liquidity_range_overlap=2, probe_quote_volume_overlap=7, probe_quote_volume_range_overlap=7, probe_market_dmid_shortfall_bps=0.0.
- Bounded DRY observe still opened zero: signals=369, max_dry_signal=0, max_dry_open=0, max_dry_blocked_open=0, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0.
- Current blocker is liquid+dmid candidates failing spread/top-book/tick/trough confirmation, not timestamp coverage, missing products, or stale U=0 feed.
- Closest liquid+dmid candidate: ZEC-USD qv=2,658,612.79, rdmid=79.9672, source=actionable_book_refresh_batch, spread=6.6865/5.0, tob=147.16/500, tick_dmid not warmed on the first tick.
- Second liquid+dmid candidate: WLD-USD qv=1,513,415.54, rdmid=57.8958, spread=2.013 ok, tob=66.87/500, tick_dmid not warmed on the first tick; readiness source is still blank for this row.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Cache preflight now honors DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS when evaluating ranked probe support, matching the runtime DRY observe lane.
- Cache regime output now reports observe_probe_min_market_dmid_bps, would_pass_probe_market_dmid, and probe_market_dmid_shortfall_bps.
- Supervisor preflight now forwards DRY_OBSERVE_PROBE_MIN_MARKET_DMID_BPS into the cache-regime report and permits main market-dmid shortfall only when the probe market-dmid floor passes.
- Recent-candle candidate/ranked rows now seed DRY book-refresh diagnostics so missing book-source gaps are clearer without weakening entry gates.
- Refreshed public recent-candle cache: refreshed=392, failed=1, failed product SHIB-USD.
- Regenerated cache evidence with configured probe floors; cache became supported/openable.
- Bounded DRY observe ran after the patch and produced no opens because liquid+dmid candidates failed spread/top-book/tick/trough confirmation.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.
- No Profit Score tuning was done while open_count=0.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": PASS, 23 tests.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": PASS, 32 tests.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 33 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_cache_market_regime.py tools\run_koko_dry_supervised.py: PASS.
- python tools\refresh_koko_recent_candle_cache.py ...: refreshed=392, failed=1.
- python tools\run_koko_dry_supervised.py with bounded KOKO_SUPERVISOR_MAX_CYCLES runs: completed; no new open.
- python tools\tdi_status_reporter.py --mode event --event patch_change --force: rendered subject "[TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (1; top ZEC-USD)" but sent=false due missing SMTP env and outbox throttling.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight coverage around liquid+dmid spread/top-book/tick overlap.
- Keep DRY observe bounded until a usable candidate passes current guardrails.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.
- No user action required for DRY/LIVE safety.

## Codex relay status update

Timestamp: 2026-06-04T05:13:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local cache/preflight refresh completed after public candle cache refresh and cache-regime CLI reporting patch.
- DRY remains true and LIVE remains false.
- Routine report cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Material event reports still trigger immediately.
- Reporting destination remains tdifactorToday@gmail.com.
- SMTP delivery remains blocked locally because sender/user/password env is missing.
- No Coinbase/order placement path was touched.

Current blocker:
- Active blocker remains data/preflight/openability coverage, not Profit Score tuning.
- Missing product/cache gap is cleared in latest cache evidence: files_present=393/393, missing_files=0.
- Timestamp coverage is now usable: timestamp_usable_files=371/393, timestamp_usable_ratio=0.944 versus min 0.850.
- U=0/stale feed is not the active blocker in latest observe evidence: max brf=120, tick_diag_rows=12, max_tick_dmid_nonzero=247, max_tick_dmid_ready=31.
- Liquid subset coverage exists: quote_volume_ge_min=23 versus min_liquid_subset_products=10.
- Current blocker is real market/entry overlap: green_ratio=0.0429 versus 0.8500, avg_dmid_bps=-80.3034 versus min 0.0, and dmid+quote+range candidates=0.
- Only one timestamp-usable dmid+quote candidate exists under main thresholds: DEGEN-USD, but range_bps=2472.3247 exceeds max 600.0.
- Probe evidence now uses the real configured quote floor: observe_probe_min_quote_volume_usd=50000 and observe_probe_min_quote_failure_dmid_bps=40.
- Probe quote candidates exist but do not make a supported observe window under current breadth/market-dmid/range conditions: probe_quote_volume_overlap=3, probe_quote_volume_range_overlap=2, best_probe_observe is empty.
- Latest readiness artifact still shows max_dry_signal=0 and max_dry_open=0; current readiness dominant blocker remains spread/runtime gate overlap.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Added CLI support to tools\koko_cache_market_regime.py for --observe-probe-min-quote-volume-usd and --observe-probe-min-quote-failure-dmid-bps so manual/relay cache evidence matches supervisor DRY observe probe thresholds.
- Reran cache-regime evidence with the configured 50000 quote-volume probe floor.
- Did not tune Profit Score while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": PASS, 22 tests.
- python tools\koko_cache_market_regime.py ... --observe-probe-min-quote-volume-usd 50000 --observe-probe-min-quote-failure-dmid-bps 40: OK.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Wait for a timestamp-usable market window with liquid positive-dmid candidates that also pass range/spread/top-book/tick confirmation, then resume bounded DRY observe.
- Continue data/preflight diagnostics around entry overlap; do not tune Profit Score while open_count=0.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T05:10:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed at 2026-06-04T05:05Z after data/preflight coverage setting changes.
- DRY remains true and LIVE remains false.
- Routine report cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- SMTP delivery remains blocked locally because sender/user/password env is missing.
- No Coinbase/order placement path was touched.

Current blocker:
- Active blocker remains data/preflight/openability coverage, not Profit Score tuning.
- Missing product/cache gap is not the active blocker: timestamp_missing_files=0 in latest cache evidence.
- U=0/stale feed is not the active blocker: latest observe had U=120, S=393, top=393, chk=393.
- Actionable book refresh coverage now reaches the full DRY universe: DRY_ACTIONABLE_BOOK_REFRESH_TOP_N=120 and max brf=120.
- Tick feed warmed during observe: tick_diag_rows=12, max_tick_dmid_nonzero=247, max_tick_dmid_ready=31.
- DRY still did not open: max_dry_signal=0, max_dry_open=0, max_dry_blocked_open=0.
- Green breadth remains deeply below target: runtime mbr examples 0.1667/0.8500 and 0.1333/0.8500.
- Liquid+dmid overlap remains too thin: quote_volume_usable=18, dmid_usable=17, liquid_dmid_overlap=1, liquid_dmid_spread_tob_overlap=0.
- Latest drygate counts show true market/gate overlap, not just stale coverage: dmid=261, market_breadth=261, quote_volume=253, spread=242, tob=181, score=106.
- Runtime near-miss combos: dmid|market_breadth=17, tob_usd|dmid|market_breadth=7, quote_volume|dmid|market_breadth=1.
- Closest runtime near miss: BTC-USD blocked by dmid+market_breadth, qv=42783295, spr=0.00, tob=568, rdmid=-4.60/40.00, tdmid=-6.91/10.00, mbr=0.1667/0.8500.
- Closest liquid+dmid entry candidate: ZEC-USD qv=3064498.7346, rdmid=59.5424/40.00, but spread=6.0281/5.00, tob=147.31/500.00, tick_dmid=0.00/10.00.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Lowered DRY_OBSERVE_PROBE_MIN_MARKET_BREADTH_FAILURE_QUOTE_VOLUME_USD from 1000000.0 to 50000.0 so DRY observe market-breadth/quote-volume probes use the same quote floor as DRY_OBSERVE_PROBE_MIN_QUOTE_VOLUME_USD.
- Increased DRY_ACTIONABLE_BOOK_REFRESH_TOP_N from 80 to 120 to refresh book metrics across the full DRY universe.
- Bounded DRY observe confirmed brf=120 and warmed tick diagnostics, but no dry signal/open occurred under current market breadth/dmid conditions.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 31 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 24 tests.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": PASS, 32 tests.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": PASS, 32 tests.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=12: completed bounded DRY observe twice; no new open.
- python tools\koko_dry_observe_readiness.py --since-local-start "2026-06-04 00:03:40" --out logs\dry_observe_readiness_latest.json: OK.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around market breadth/dmid overlap and positive-dmid candidates that pass spread, top-book, and tick confirmation.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T04:55:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed at 2026-06-04T04:54Z after a DRY ranking/preflight coverage patch.
- DRY remains true and LIVE remains false.
- Routine report cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter delivery was attempted for patch_change and returned sent=false because SMTP user/password/sender env is missing.
- No Coinbase/order placement path was touched.

Current blocker:
- Active blocker remains data/preflight/openability coverage, not Profit Score tuning.
- Cache/preflight is now openable and diagnostic-worthy: cache_openable=true, cache_supported=true.
- Latest DRY observe ran successfully but opened zero candidates: drysig=0, dryopen=0, dryblk=0.
- Market/feed is not U=0 or stale: latest observe had U=120, S=393, brf=80.
- Timestamp/cache coverage remains usable: timestamp_ratio=0.8855, timestamp_usable=348/393, timestamp_outside=45, timestamp_missing_files=0.
- Liquid subset coverage exists: liquid_subset=20 versus min 10.
- Green breadth remains deeply below target: cache green_ratio=0.1908 versus min 0.8500; runtime latest_mbr=0.1250/0.8500.
- Liquid+dmid overlap improved from zero to one: liquid_dmid_overlap=1, liquid_dmid_spread_tob_overlap=0.
- Closest liquid+dmid candidate is ZEC-USD: rdmid=59.5424, qv=4129505, tob=3663.91, but spread=8.4764 bps over max 5.0 and book_pressure also failed.
- Probe coverage improved: best_ranked_probe_quote_overlap=3; probe quote candidates are ZEC-USD, RAVE-USD, ICNT-USD.
- Latest runtime near miss is XRP-USD blocked by dmid+market_breadth: qv=6037604, rdmid=-25.74, spr=1.67, tob=2104.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Patched DRY dmid_desc candidate ranking so probe-eligible quote-volume candidates can receive diagnostic/book-refresh attention before red liquid names.
- This does not bypass main quote-volume, spread, top-book, dmid, market-breadth, P&L, or order guardrails.
- Refreshed public candle cache: 392/393 products refreshed; STORJ-USD request failed.
- Bounded DRY observe completed after patch; cache became openable and liquid+dmid overlap became nonzero, but no dry open occurred.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 31 tests.
- python -m py_compile managers\run_manager\run_manager.py: PASS.
- python tools\refresh_koko_recent_candle_cache.py ...: refreshed=392, failed=1.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=10: completed bounded DRY observe; no new open.
- python tools\koko_dry_observe_readiness.py --since-local-start "2026-06-03 23:52:28" --out logs\dry_observe_readiness_latest.json: OK.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around spread/top-book/tick-dmid/book-pressure overlap now that cache is openable and liquid+dmid overlap is nonzero.
- Do not tune Profit Score while open_count=0.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T04:48:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed at 2026-06-04T04:47Z after preflight control-flow fixes.
- DRY remains true and LIVE remains false.
- Routine report cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Reporter delivery is still blocked by missing SMTP user/password/sender env.
- No Coinbase/order placement path was touched.

Current blocker:
- Active blocker remains data/preflight/openability coverage, not Profit Score tuning.
- Latest DRY observe ran successfully but opened zero candidates: drysig=0, dryopen=0, dryblk=0.
- Market/feed is not U=0 or stale: latest observe had U=120, S=393, top=393, chk=393, brf=80.
- Timestamp/cache coverage is usable but not fully fresh: timestamp_ratio=0.8931, timestamp_usable=351/393, timestamp_outside=42, timestamp_missing_files=0.
- Liquid subset coverage exists: liquid_subset=20 versus min 10.
- Green breadth is the main market blocker: cache green_ratio=0.1107 versus min 0.8500; latest runtime mbr stayed about 0.1167 to 0.1417 versus 0.8500.
- Liquid+dmid openability overlap is still zero in the latest readiness artifact: liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Dmid/liquidity/range overlap remains zero in cache: dmid_ge_min_and_quote_volume_ge_min=0 and dmid_ge_min_and_quote_volume_ge_min_and_range_le_max=0.
- Probe candidates exist but are below the main quote-volume threshold: TRAC-USD and CTR-USD.
- Latest observe blockers: trough=221, spread=81, trough_wait=15, tob_usd=10.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\activity_ticker.log
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Fixed KOKO_SUPERVISOR_OBSERVE_WINDOW_MAX_WAIT_SEC=0 so preflight wait exits immediately instead of sleeping for the poll interval.
- When KOKO_SUPERVISOR_PREFLIGHT_REFRESH=0, the supervisor now reuses logs\cache_market_regime_latest.json instead of discarding existing coverage evidence.
- Added regression tests for zero-wait preflight behavior and disabled-refresh cached snapshot behavior.
- Kept P&L-blocked candidate deprioritization enabled through DRY_PNL_DEPRIORITIZE_BLOCKED_CANDIDATES=true.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": PASS, 32 tests.
- python -m py_compile tools\run_koko_dry_supervised.py: PASS.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=8 and KOKO_SUPERVISOR_PREFLIGHT_REFRESH=0: completed bounded DRY observe; no new open.
- python tools\koko_dry_observe_readiness.py --since-local-start "2026-06-03 23:46:11" --out logs\dry_observe_readiness_latest.json: OK.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around green breadth, liquid+dmid overlap, and spread/top-book overlap before resuming dry P&L improvement.
- Do not tune Profit Score while open_count=0.

User action required:
- Yes for unattended Gmail delivery only: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T04:30:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed after the data/preflight patch; no live trading was enabled.
- Latest reporter event send was attempted for patch_change and returned sent=false because SMTP env is missing: user, password, sender.
- Routine report cadence is every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No Coinbase/order placement path was touched.

Current blocker:
- Do not tune Profit Score while opened/open_count is 0.
- Active blocker remains data/preflight/openability, not profit scoring.
- Runtime DRY observe still produced no new open after the latest patch: dryopen=0, dryblk=0, blocked_open remained 91.
- P&L-quarantined candidates no longer consume probe-driven dry-open attempts; dry_pnl_guard is logged and skipped before recording blocked dry opens.
- Runtime market/feed is not U=0 or stale: latest tick evidence has U=120, S=393, brf=80.
- Runtime green breadth improved but remains below the configured target: max latest observed near-miss mbr=0.7250/0.8500; later ticks around 0.7083/0.8500.
- Tick dmid warmed but is often insufficient on current candidates: tick_dmid_nonzero reached 183 and tick_dmid_ready reached 17 in the latest observe sample, but latest candidate rows still frequently fail dmid/tick_dmid.
- Top-book/spread/trough remain active openability gaps: liquid_dmid_overlap=1, liquid_dmid_spread_tob_overlap=0.
- Latest near dry candidate remains NEAR-USD, but it is P&L-quarantined and now skipped by dry_pnl_guard rather than counted as blocked_open.
- Other visible near candidates fail top-book, spread, dmid, or market breadth before safe DRY open.
- Cache/preflight coverage is mixed but useful: best_ranked=dmid_desc for top 120 passes configured regime with timestamp_ratio=1.0000, green_ratio=1.0000, liquid_subset=11, dmid_liquidity_overlap=8.
- Full 393-product cache view is blocked by timestamp_coverage and green_breadth: timestamp_ratio=0.8321, green_ratio=0.6555.
- Liquid subset coverage is present in cache: quote_volume_ge_min=16, timestamp_usable_and_quote_volume_ge_min green_ratio=0.8750.
- Missing product/cache gap is not the main blocker: timestamp_missing_files=0; 66 files are outside the current freshness window.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\activity_ticker.log
- C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- opened/closed/wins/losses: opened=19, closed=19, wins=5, losses=14.
- open_count=0, blocked_open=91, quarantined=13.
- Last P&L event timestamp: 2026-06-04T04:16:19Z.
- No credible positive dry profitability evidence is present yet.

Patch/change evidence:
- Set DRY_MARKET_BREADTH_ALIGN_WITH_DRY_DMID_SOURCE=true so runtime breadth aligns with recent-candle dmid source.
- Added a DRY P&L preview guard before probe-driven dry-open handoff so quarantined products are skipped with dry_pnl_guard evidence instead of consuming blocked_open attempts.
- Applied the same preview guard pattern around other dry-open handoff paths without changing Coinbase/order code.
- Refreshed public candle cache for the current runtime product set: 391/393 products refreshed; two public candle requests failed but old cache files still exist.
- Ran bounded DRY observe after the patch; blocked_open did not increase, confirming the P&L quarantine skip is working.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": PASS, 28 tests.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 24 tests.
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": PASS, 9 tests.
- python -m py_compile managers\run_manager\run_manager.py: PASS.
- python tools\refresh_koko_recent_candle_cache.py ...: refreshed=391, failed=2.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=16: completed bounded DRY observe; no new open.
- python tools\tdi_status_reporter.py --mode event --event patch_change ... --force: sent=false because SMTP user/password/sender env is missing.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Routine emails should be every two hours, not hourly: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around timestamp freshness, green breadth, liquid subset/openability overlap, top-book/spread, tick-dmid warmup, and P&L-quarantine-aware candidate selection.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.

User action required:
- Yes for unattended Gmail delivery: provide SMTP sender credentials/env values such as TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or equivalent supported aliases.

## Codex relay status update

Timestamp: 2026-06-04T03:44:01Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send for event=data_preflight_update; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (25; top VVV-USD).
- Reporter reason: not_material:data_preflight_update, sent=false.
- Gmail reporting environment blocker remains: SMTP user/password/sender env is missing, so automatic delivery cannot complete yet.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Do not tune Profit Score while opened/open_count is 0.
- Refreshed candle cache before observe: 391/393 products refreshed; CBETH-USD and THQ-USD public candle fetches failed this pass.
- Cache/preflight is usable: cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage remains usable: timestamp_ratio=0.9338, timestamp_usable=367/393, timestamp_outside=26.
- Cache liquid subset remains usable: liquid_subset=24, liquid_min=10.
- Current_order green breadth is below target: green_ratio=0.7000/0.8500, green_shortfall=0.1500.
- Ranked cache evidence remains usable: best_ranked=dmid_desc, best_ranked_green=1.0000, best_ranked_liquid=10, best_ranked_dmid_liq_overlap=10.
- Best probe evidence is nearly green enough and liquid: best_probe=timestamp_liquidity_dmid_desc, best_probe_green=0.8487, best_probe_liquid=24, best_probe_dmid_liq_overlap=14.
- Latest bounded DRY observe produced no new open: opened stayed 19, closed stayed 19, wins stayed 5, losses stayed 14, open_count stayed 0, blocked_open moved to 88.
- Market/feed was not U=0 or stale: U=120, S=393, brf=80.
- Tick diagnostics warmed: tick_diag_rows=24, max_tick_dmid_nonzero=226, max_tick_dmid_ready=77, tick_dmid_warmed_seen=true.
- At the latest tick, green breadth was usable: latest_mbr=0.8667/0.8500 and latest_mdmid=57.37/0.00.
- New drygate breakdown shows the latest blocker is not market_breadth: latest_drygate=dmid:21, quote_volume:20, spread:19, tob:18, score:16, book_pressure:1.
- Normal PAPER signal overlap remains zero: liquid=0, dmid=126, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Early cache-liquid candidates exist but fail spread/top-book: early_skip_top=5, early_liquid=5, early_dmid=5, early_liquid_dmid=5, early_spread_tob=0, early_probe_rej=spread:4,tob_usd:1.
- Top early-skip candidate is VVV-USD: qv=1326281, rdmid=215.71, score=0.9879, rejected by top-book with tob=22/500.
- Runtime near miss is PAXG-USD blocked by tob_usd|dmid|book_pressure: qv=370088, rdmid=-8.70, spr=0.02/5.00, tob=47/500.

Files changed in current local runtime lane:
- Updated diagnostics: C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- Updated reporter evidence: C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- Updated readiness tests: C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Updated reporter tests: C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated cache evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Updated runtime activity/P&L evidence: C:\ai_trading_bot_koko\logs\activity_ticker.log and C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- open/closed/wins/losses: open=0, closed=19, wins=5, losses=14.
- No positive dry profitability evidence is present yet.
- Forward evidence still does not prove positive profitability: runtime_near_forward signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.

Patch/change evidence:
- Added parsing of latest tick_diag drygate combo counts to readiness.
- Added latest_drygate evidence to reporter output.
- Regenerated dry_observe_readiness_latest.json over the latest bounded observe window.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 23 tests.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": PASS, 30 tests.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\refresh_koko_recent_candle_cache.py ...: refreshed=391, failed=2.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=24: OK; completed bounded DRY block.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 22:38:22" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours when SMTP env exists.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around spread/top-book/dmid/score overlap now that latest market breadth can clear.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.
- User action required: yes, for SMTP credential/sender env only.

## Codex relay status update

Timestamp: 2026-06-04T03:33:43Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send for event=patch_applied; then an actual send was attempted for the material patch event.
- Reporter subject preview: [TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (9; top ONDO-USD).
- Reporter send result: sent=false, reason="missing SMTP env ['user', 'password', 'sender']; outbox_throttled".
- Gmail reporting environment blocker: set TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM, or equivalent SMTP_USER/SMTP_PASSWORD/SMTP_FROM or GMAIL_USER/GMAIL_APP_PASSWORD env.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Do not tune Profit Score while opened/open_count is 0.
- The active issue is still data/preflight runtime opening coverage, not profit scoring.
- Cache/preflight is usable: cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage is usable: timestamp_ratio=0.9567, timestamp_usable=376/393, timestamp_outside=17.
- Cache liquid subset is usable: liquid_subset=23, liquid_min=10.
- Current_order green breadth remains below target: green_ratio=0.7829/0.8500, green_shortfall=0.0671.
- Ranked cache evidence remains stronger: best_ranked=timestamp_liquid_green_dmid_desc, best_ranked_green=0.9500, best_ranked_liquid=23, best_ranked_dmid_liq_overlap=6, best_ranked_probe_quote_overlap=8.
- Latest bounded DRY observe produced no open: opened stayed 19, closed stayed 19, wins stayed 5, losses stayed 14, open_count stayed 0.
- Normal PAPER signal overlap is still zero: signals=313, quote_volume_usable=0, dmid_usable=154, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- New diagnostic evidence explains that gap: dry_liquid_early_skip_coverage top_products=5, early_liquid=5, early_dmid=5, early_liquid_dmid=5, early_spread_tob=0, early_gap_explained=true.
- Early-skip probe rejections are spread:4 and tob_usd:1.
- Current top early-skip candidate is ONDO-USD: qv=2093431, rdmid=127.01, score=0.9887, rejected by spread with spr=5.09/5.00, book source actionable_book_refresh_batch, prefetch_tob=198.
- Runtime near miss is IO-USD blocked by spread|quote_volume|dmid|market_breadth: qv=58205, rdmid=173.41, spr=57.64/5.00, tob=11115.
- Market/feed is not U=0 or stale: U=120, S=393, brf=80.
- Tick diagnostics warmed during the run: tick_diag_rows=24, max_tick_dmid_nonzero=216, max_tick_dmid_ready=58, tick_dmid_warmed_seen=true.
- Runtime green breadth stayed below target: latest_mbr=0.4833/0.8500, max_near_mbr=0.7583.
- New environment blocker for reporting delivery: SMTP credentials/sender are not present, so Gmail send cannot complete yet.

Files changed in current local runtime lane:
- Updated diagnostics: C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- Updated reporter evidence: C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- Updated readiness tests: C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Updated reporter tests: C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Regenerated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- open/closed/wins/losses: open=0, closed=19, wins=5, losses=14.
- No new P&L movement occurred in the latest bounded observe block.
- Credible positive dry profitability evidence is not present yet.
- Forward evidence still does not prove positive profitability: runtime_near_forward signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.

Patch/change evidence:
- Added early dry-liquid skip coverage fields to the readiness artifact so cache-liquid candidates blocked before PAPER signal emission are counted separately.
- Added reporter evidence fields: early_skip_top, early_liquid, early_dmid, early_liquid_dmid, early_spread_tob, early_gap_explained, early_probe_rej.
- Regenerated dry_observe_readiness_latest.json over the latest bounded observe window.
- Reporter preview includes the new early-skip evidence; actual event send was attempted but could not deliver because SMTP env is missing.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 22 tests.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": PASS, 29 tests.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 22:25:42" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.
- python tools\tdi_status_reporter.py ...: send attempted, sent=false, missing SMTP env ['user', 'password', 'sender']; outbox_throttled.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around runtime entry coverage: green breadth, trough probe, spread/top-book rejection, and why early cache-liquid candidates fail before safe DRY opens.
- Add Gmail SMTP env if user wants automatic email delivery to start from this runtime.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.
- User action required: yes, for SMTP credential/sender env only.

## Codex relay status update

Timestamp: 2026-06-04T03:20:42Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (9; top ONDO-USD).
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Data/preflight cache lane remains usable, but this bounded observe did not open a new DRY candidate.
- Refreshed public candle cache: 392/393 products refreshed; STORJ-USD public candle fetch failed once.
- Current cache evidence: cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage remains usable: timestamp_ratio=0.9567, timestamp_usable=376/393, timestamp_outside=17.
- Cache liquid subset remains usable: liquid_subset=23, liquid_min=10.
- Current cache green breadth is below target in current_order mode: green_ratio=0.7829/0.8500, but ranked mode is usable with best_ranked_green=0.9500 and best_ranked_liquid=23.
- Latest bounded DRY observe produced no open: opened stayed 19, closed stayed 19, wins stayed 5, losses stayed 14.
- Current entry blocker is zero liquid/DMID/quote overlap during runtime: liquid=0, dmid=154, quote_volume_usable=0, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Current dry-liquid skip is trough-led with book rejection details: dryliqskip=trough:9, top ONDO-USD qv=2093431, rdmid=127.01, score=0.7962, rejected by top-book with tob=71/500.
- Runtime near miss is SXT-USD blocked by spread|quote_volume|dmid|market_breadth: qv=63860, rdmid=0.00, spr=101.52/5.00, tob=9280.
- Market/feed was not stale: U=120, S=393, brf=80.
- Tick diagnostics warmed during the run: tick_diag_rows=18, max_tick_dmid_nonzero=224, max_tick_dmid_ready=91, tick_dmid_warmed_seen=true.
- Runtime green breadth stayed variable and below target: latest_mbr=0.5750/0.8500, max_near_mbr=0.7750.
- open_count is currently 0; do not tune Profit Score while open_count=0.

Files changed in current local runtime lane:
- Updated cache evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Updated runtime activity: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- open/closed/wins/losses: open=0, closed=19, wins=5, losses=14.
- No new P&L movement occurred in the latest bounded observe block.
- Credible positive dry profitability evidence is not present yet.
- Forward evidence still does not prove positive profitability: runtime_near_forward signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.

Patch/change evidence:
- Refreshed all selected runtime candle cache files before observe; 392/393 products refreshed.
- Regenerated cache market regime report through the supervisor helper so canonical fields are current.
- Ran bounded DRY observe with DRY=true and LIVE=false.
- Rebuilt dry observe readiness over the current bounded run window.
- Reporter preview classified the update as not_material:data_preflight_update and did not send.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python tools\refresh_koko_recent_candle_cache.py ... --products-file logs\dry_runtime_products_latest.json ...: refreshed=392, failed=1.
- supervisor helper cache regeneration: OK after using this branch's _load_cfg/_preflight_report/_write_cache_regime_latest signatures.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=18: OK; completed bounded DRY block.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 22:16:55" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue data/preflight repair around current runtime entry overlap: quote volume, liquid/DMID overlap, trough probe top-book rejection, spread, and green breadth.
- Do not tune Profit Score while open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined dry opens.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T03:11:13Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 26/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (49; top WLD-USD).
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Data/preflight lane is now usable after public candle cache refresh; timestamp/cache coverage is no longer the active blocker.
- Refreshed cache evidence: cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage recovered: timestamp_ratio=0.9618, timestamp_usable=378/393, timestamp_outside=15.
- Cache green breadth recovered: green_ratio=0.8611/0.8500.
- Cache liquid subset recovered: liquid_subset=27, liquid_min=10.
- Best ranked cache overlap is usable: best_ranked=current_order, best_ranked_liquid=27, best_ranked_dmid_liq_overlap=26, best_ranked_dmid_range_overlap=25.
- Bounded DRY observe could open candidates again: opened moved from 18 to 19, closed moved from 18 to 19, wins moved from 4 to 5.
- Current runtime blocker after warmed observe is trough/spread/market_breadth: cache-liquid candidates blocked by trough (49; top WLD-USD), runtime near CHZ-USD failures=spread|market_breadth.
- Tick diagnostics warmed during the run: tick_diag_rows=18, max_tick_dmid_nonzero=219, max_tick_dmid_ready=77, tick_dmid_warmed_seen=true.
- Market/feed was not stale: U=120, S=393, brf=80.
- Green breadth remained variable and often below target during runtime: latest_mbr=0.3667/0.8500, max_near_mbr=0.8083.
- open_count is currently 0; do not tune Profit Score while open_count=0.

Files changed in current local runtime lane:
- Updated cache evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Updated dry P&L score: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Updated runtime activity: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- open/closed/wins/losses: open=0, closed=19, wins=5, losses=14.
- P&L improved from net=-0.30192795 to net=-0.29854210 after one dry win, but credible positive dry profitability evidence is not present yet.
- Forward evidence still does not prove positive profitability: runtime_near_forward signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.

Patch/change evidence:
- Refreshed all selected runtime candle cache files: 392/393 products refreshed; DIEM-USD public candle fetch failed once.
- Regenerated cache market regime report through the supervisor helper so canonical fields are present.
- Ran bounded DRY observe with DRY=true and LIVE=false.
- Rebuilt dry observe readiness over the full bounded run window.
- No Profit Score tuning was done while open_count=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python tools\refresh_koko_recent_candle_cache.py ... --products-file logs\dry_runtime_products_latest.json ...: refreshed=392, failed=1.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 22:07:36" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\run_koko_dry_supervised.py with KOKO_SUPERVISOR_MAX_CYCLES=18: OK; completed bounded DRY block.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe and evidence gathering now that preflight can open candidates.
- Investigate remaining trough/spread/market_breadth blockers without tuning Profit Score while open_count=0.
- Resume dry P&L improvement only after more dry-open evidence accumulates; current net P&L remains negative.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T03:03:42Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | runtime near-miss ENA-USD blocked by spread.
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Data/preflight lane blocker is refreshed cache timestamp coverage: cache_supported=false, cache_openable=false, diagnostic_worthwhile=false.
- Refreshed cache evidence: timestamp_ratio=0.0000, timestamp_usable=0/393, timestamp_outside=393, avg_candle_age_sec=5777.8, max_candle_age_sec=19889.2.
- Refreshed cache green breadth is also unusable: green_ratio=0.0000/0.8500.
- Refreshed cache liquid subset is also unusable: liquid_subset=0, liquid_min=10.
- Refreshed cache blocker: primary_regime_blocker=timestamp_coverage, dominant_regime_blocker=timestamp_coverage.
- Runtime readiness still has market/feed coverage: U=120, S=393, brf=80, so U=0 / stale runtime feed is not the current cause.
- Runtime readiness still has entry overlap: liquid_dmid_overlap=22 and liquid_dmid_spread_tob_overlap=4.
- Runtime green breadth remains below target: latest_mbr=0.3583/0.8500, max_near_mbr=0.5500.
- Runtime near-miss still points at ENA-USD blocked by spread|market_breadth: qv=1294212, rdmid=287.30, spr=9.31/5.00, tob=3608.
- Fresh open_count remains 0; do not tune Profit Score while opened/open_count=0.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated cache evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Updated forward evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Updated forward history: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- Credible positive dry profitability evidence is not present yet.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Runtime-near forward evidence remains net negative: runtime_near_forward signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Latest runtime-near evidence is also net negative after costs: runtime_near_latest loaded=10, signals=10, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.

Patch/change evidence:
- Refreshed cache market regime evidence now shows cache timestamp coverage is not usable, replacing the older stale/optimistic cache status.
- Reporter preview includes cache_supported=false, cache_openable=false, diagnostic_worthwhile=false, timestamp_usable=0/393.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.
- No new runtime code tests were required for this relay-only update.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Repair timestamp/cache coverage so DRY observe can open candidates.
- Continue focusing timestamp coverage, liquid subset coverage, green breadth, U=0/stale-feed causes, and missing product/cache gaps.
- Do not tune Profit Score while opened/open_count=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined opens.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:58:44Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | runtime near-miss ENA-USD blocked by spread.
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: runtime near-miss ENA-USD blocked by spread.
- Latest runtime near evidence: ENA-USD failures=spread|market_breadth, qv=1294212, rdmid=287.30, spr=9.31/5.00, tob=3608.
- Latest runtime-near forward samples are now mature: loaded=10, signals=10.
- Latest best runtime-near bucket is spread|dmid|market_breadth with avg_net_close_bps=-3.9673 and positive_net_close_rate=0.4286.
- Current direct spread|market_breadth ENA sample remains net negative after costs: avg_net_close_bps=-15.3500, positive_net_close_rate=0.0000, sl_touch_rate=1.0000.
- Historical runtime-near forward evidence remains net negative: signals=30, best_reason=spread|dmid|market_breadth, avg_net_close_bps=-3.9673, positive_net_close_rate=0.4286.
- Fresh open_count remains 0.
- Timestamp coverage remains usable: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9.
- Runtime market/feed coverage remains usable: U=120, S=393, brf=80.
- Liquid subset remains usable: liquid_subset=31, liquid_min=10.
- Entry overlap remains nonzero: liquid_dmid_overlap=22 and liquid_dmid_spread_tob_overlap=4.
- Green breadth remains below target: latest_mbr=0.3583/0.8500, max_near_mbr=0.5500.
- U=0 / stale feed is not the current cause.
- Missing product/cache gap is not the current cause; cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated forward evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Updated forward history: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- Credible positive dry profitability evidence is not present yet.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Latest mature runtime-near evidence is near breakeven but still net negative after costs, so it is not positive profitability evidence.

Patch/change evidence:
- Refreshed matured runtime-near forward outcomes from the latest readiness file.
- Reporter now shows latest mature runtime-near bucket separately from historical aggregate.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 29 OK.
- python -m py_compile tools\tdi_status_reporter.py tools\koko_paper_signal_forward_outcomes.py: OK.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --horizon-min 5 ...: OK; latest signals=10.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe only when spread and green breadth improve.
- Do not treat near-breakeven runtime-near evidence as positive profitability.
- Do not tune score while opened=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined opens.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:56:23Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | runtime near-miss ENA-USD blocked by spread.
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: runtime near-miss ENA-USD blocked by spread.
- Latest runtime near evidence: ENA-USD failures=spread|market_breadth, qv=1294212, rdmid=287.30, spr=9.31/5.00, tob=3608.
- Latest runtime-near forward outcome refresh loaded 10 latest samples, but all 10 are not mature yet for the 5-minute horizon.
- Historical runtime-near forward evidence remains negative: signals=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.
- Fresh open_count remains 0.
- Timestamp coverage remains usable: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9.
- Runtime market/feed coverage remains usable: U=120, S=393, brf=80.
- Liquid subset remains usable: liquid_subset=31, liquid_min=10.
- Entry overlap remains nonzero: liquid_dmid_overlap=22 and liquid_dmid_spread_tob_overlap=4.
- Runtime tick dmid warmed during verification: tick_diag_rows=20, tick_diag_dmid_nonzero=237, tick_diag_dmid_ready=112, tick_diag_warmed_seen=true.
- Green breadth remains below target: latest_mbr=0.3583/0.8500, max_near_mbr=0.5500.
- U=0 / stale feed is not the current cause.
- Missing product/cache gap is not the current cause; cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated forward evidence: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_latest.json
- Updated forward history: C:\ai_trading_bot_koko\logs\runtime_near_forward_outcomes_history.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- Credible positive dry profitability evidence is not present yet.
- Dry-open forward evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Latest runtime-near samples are pending maturity; do not use them as positive evidence.

Patch/change evidence:
- Refreshed runtime-near forward outcomes from the latest readiness file.
- Reporter now preserves latest runtime-near not_mature/failure evidence alongside historical runtime-near outcomes, instead of hiding the pending latest samples behind history.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 28 OK.
- python -m py_compile tools\tdi_status_reporter.py tools\koko_paper_signal_forward_outcomes.py: OK.
- python tools\koko_paper_signal_forward_outcomes.py --readiness-runtime-near logs\dry_observe_readiness_latest.json --horizon-min 5 ...: OK; latest failures not_mature=10.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Wait for latest runtime-near samples to mature.
- Continue DRY-only observe when spread and green breadth improve.
- Do not tune score while opened=0.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined opens.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:53:14Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed cleanly: 20 ticks, DRY=true, LIVE=false.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | runtime near-miss ENA-USD blocked by spread.
- Reporter reason: not_material:data_preflight_update, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: runtime near-miss ENA-USD blocked by spread.
- The prior quarantine blocker is still real P&L safety for some products, but it is no longer reported as current when the latest tick has drysig=0 and dryblk=0.
- Fresh 20-tick observe had no new opens; open_count remains 0.
- Latest runtime near evidence: ENA-USD failures=spread|market_breadth, qv=1294212, rdmid=287.30, spr=9.31/5.00, tob=3608, tdmid=23.32, mbr=0.3583/0.8500.
- Timestamp coverage remains usable: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9.
- Runtime market/feed coverage remains usable: U=120, S=393, brf=80.
- Liquid subset remains usable: liquid_subset=31, liquid_min=10.
- Paper-signal coverage: signals=378, dmid_usable=186, quote_volume_usable=36, spread_usable=28, tob_usable=102.
- Entry overlap improved: liquid_dmid_overlap=22 and liquid_dmid_spread_tob_overlap=4.
- Runtime tick dmid warmed during verification: tick_diag_rows=20, tick_diag_dmid_nonzero=237, tick_diag_dmid_ready=112, tick_diag_warmed_seen=true.
- Green breadth remains below target: latest_mbr=0.3583/0.8500, max_near_mbr=0.5500.
- U=0 / stale feed is not the current cause.
- Missing product/cache gap is not the current cause; cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- New 20-tick observe added no realized P&L and opened no positions.
- Credible positive dry profitability evidence is not present yet.
- Forward dry-open evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Runtime near-forward evidence remains negative: runtime_near_forward signals=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Fixed status blocker selection so stale earlier quarantine blocks do not hide the latest runtime data/preflight blocker when latest tick has drysig=0 and dryblk=0.
- Added regression coverage for the stale-blocked-open diagnosis case.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 26 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 22 OK.
- python -m py_compile tools\tdi_status_reporter.py tools\koko_dry_observe_readiness.py: OK.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 21:48:35": OK; refreshed logs\dry_observe_readiness_latest.json.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe.
- Do not tune score while opened=0.
- Focus current runtime near-miss spread/dmid/market-breadth causes and wait for non-quarantined high-quality candidates.
- Resume dry P&L improvement only after usable market coverage produces safe non-quarantined opens.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:46:16Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed cleanly after the probe quote-volume floor patch.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | dry signal blocked by quarantine (NEAR-USD).
- Reporter reason: not_material:patch_change, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: dry signal blocked by quarantine (NEAR-USD).
- Do not tune score while opened=0; current open_count=0.
- Readiness now reports observe_probe_candidate_present=false and observe_runtime_probe_candidate_present=false.
- RENDER-USD runtime near miss is no longer reported openable: failures=market_breadth, qv=525538, rdmid=111.92, spr=4.81, tob=514, dry_observe_probe reason=market_breadth_quote_floor.
- Timestamp coverage is usable: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9.
- Runtime market/feed coverage remains usable: U=120, S=393, brf=80.
- Liquid subset remains usable: liquid_subset=31, liquid_min=10.
- Paper-signal dmid coverage: signals=382, dmid_usable=190, quote_volume_usable=38, spread_usable=26, tob_usable=102.
- Entry overlap remains the main data/preflight gap: liquid_dmid_overlap=24, liquid_dmid_spread_tob_overlap=0.
- Runtime tick dmid warmed during verification: tick_diag_rows=12, tick_diag_dmid_nonzero=261, tick_diag_dmid_ready=160, tick_diag_warmed_seen=true.
- Green breadth remains below target: latest_mbr=0.3000/0.8500, max_near_mbr=0.6667.
- U=0 / stale feed is not the current cause.
- Missing product/cache gap is not the current cause; cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- Latest dry P&L remains net negative; credible positive dry profitability evidence is not present yet.
- Forward dry-open evidence remains thin: dry_open_forward signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Runtime near-forward evidence remains negative: runtime_near_forward signals=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Aligned dry observe readiness probe eligibility with the runtime market-breadth quote-volume floor.
- Added DRY_OBSERVE_PROBE_MIN_MARKET_BREADTH_FAILURE_QUOTE_VOLUME_USD to readiness active gates.
- Added paper-signal and tick_diag regressions proving RENDER-style 525k quote-volume market-breadth probes are blocked by market_breadth_quote_floor.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 22 OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 28 OK.
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": 9 OK.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py: OK.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 21:40:41": OK; refreshed logs\dry_observe_readiness_latest.json.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe.
- Do not tune score while opened=0.
- Keep focusing data/preflight on timestamp coverage, liquid subset coverage, green breadth, U=0/stale-feed causes, and missing product/cache gaps.
- Wait for high-quality non-quarantined candidates with stronger liquidity before resuming dry P&L improvement work.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:38:37Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observes completed cleanly.
- Latest reporter preview was --no-send; no email was sent.
- Reporter subject preview: [TDI STATUS] Profit 24/100 | DRY=true LIVE=false | dry signal blocked by quarantine (NEAR-USD).
- Reporter reason: not_material:patch_change, sent=false.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: dry signal blocked by quarantine (NEAR-USD).
- Post-patch bounded observe had no new opens and one quarantined DRY signal.
- Runtime market/feed coverage remains usable: U=120, S=393, brf=80.
- Timestamp coverage remains usable: timestamp_ratio=0.9771, timestamp_usable=384/393.
- Liquid subset remains usable: liquid_subset=31, liquid_min=10.
- Liquid/dmid coverage remains usable: liquid_dmid_overlap=24.
- Full entry overlap remains thin but nonzero: liquid_dmid_spread_tob_overlap=2.
- Tick dmid warmed during verification: tick_diag_rows=8, tick_diag_dmid_nonzero=227, tick_diag_dmid_ready=63, tick_diag_warmed_seen=true.
- Green breadth remains below target: latest_mbr=0.5167/0.8500, max_near_mbr=0.6250.
- U=0 / stale feed is not the current cause.
- Missing product/cache gap is not the current cause; cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\run_settings.json
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 24/100.
- dry P&L: realized=-0.30192795 USD, unrealized=0.00000000 USD, net=-0.30192795 USD.
- open/closed/wins/losses: open=0, closed=18, wins=4, losses=14.
- XLM-USD positive evidence: closed by profit_protect for +51.1094 bps / +0.01533282 USD.
- RENDER-USD negative evidence: opened under DRY observe probe with quote volume about 525538 USD, then closed by loss_trim for -72.3764 bps / -0.02171291 USD.
- Credible positive dry profitability evidence is not present yet because net dry P&L remains negative and latest new entry lost more than the prior XLM win.

Patch/change evidence:
- Added DRY-only market-breadth-failure probe quote-volume floor:
  DRY_OBSERVE_PROBE_MIN_MARKET_BREADTH_FAILURE_QUOTE_VOLUME_USD=1000000.0.
- This blocks RENDER-style market-breadth-failure probe entries with weaker quote-volume evidence while preserving higher-liquidity observe candidates such as the prior XLM case.
- Added regression coverage for the market-breadth probe quote-volume floor.
- Added the new floor to DRY paper-signal metadata for explainability.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 28 OK.
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": 9 OK.
- python -m py_compile managers\run_manager\run_manager.py: OK.
- Bounded DRY observe ticks=8 exited 0 with DRY=True, LIVE=False, TP=8.0, SL=0.8.
- Post-patch bounded observe opened no new weak probe positions; latest DRY signal was blocked by quarantine.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 21:36:40": OK; refreshed logs\dry_observe_readiness_latest.json.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Continue DRY-only observe.
- Do not tune score while opened=0.
- Wait for high-quality non-quarantined candidates with stronger liquidity.
- If future opened positions remain net negative, continue tightening DRY data/preflight and P&L quality gates only; do not enable LIVE and do not change order bodies.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:26:07Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Latest local bounded DRY observe completed cleanly after the bounded hang-guard and recent-candle dmid fixes.
- Latest reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current reporter blocker: dry signal blocked by quarantine (NEAR-USD).
- The previous data/preflight blocker is improved: bounded DRY observe opened XLM-USD under DRY only.
- Runtime dmid coverage recovered: dmid_present=387, dmid_nonzero=250, dmid_usable=195.
- Liquid/dmid coverage recovered from overlap=0 to liquid_dmid_overlap=16.
- Full liquid+dmid+spread+tob overlap is still thin: liquid_dmid_spread_tob_overlap=1.
- Latest tick evidence: U=120, S=393, brf=80, drysig=0, dryopen=0, dryblk=0.
- Open tick evidence: max_drysig=2, max_dryopen=1, max_dryblk=1.
- Tick dmid evidence: tick_diag_rows=4, tick_diag_dmid_nonzero=56, tick_diag_dmid_ready=43, tick_diag_warmed_seen=true.
- Green breadth remains below target at the latest tick: latest_mbr=0.5583/0.8500; max_near_mbr=0.7333.
- U=0 / stale-feed is not the current cause; U=120.
- Missing product/cache gap is not the current cause; S=393 and cache_openable=true.
- Timestamp coverage is usable: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9.
- Liquid subset coverage is usable: liquid_subset=31, liquid_min=10.
- Do not touch live/order placement. Continue DRY-only monitoring and data/preflight quality.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 22/100.
- dry P&L: realized=-0.29554786 USD, unrealized=+0.00350035 USD, net=-0.29204751 USD.
- open/closed/wins/losses: open=1, closed=16, wins=3, losses=13.
- Current open position evidence: XLM-USD opened at tick 3, entry_mid=0.2095505, last_mid=0.209795, last_pnl_bps=11.6678, last_pnl_usd=+0.00350035, notional=3.0.
- Dry open forward evidence: signals=1, horizon_min=10, avg_net_close_bps=41.3940, positive_net_close_rate=1.0000.
- Credible positive dry profitability evidence is not present yet because net dry P&L remains negative.
- Forward runtime-near evidence is still weak: runtime_near_forward signals=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Bounded DRY hang guard now uses startup-only mode and preserves that flag through hot reload, preventing bounded observe from exiting through repeated hang dumps.
- Runtime recent-candle dmid window was widened so lagged usable cache keeps the previous candle and no longer collapses dmid to zero.
- One-row candle top-up now falls back to stale cache only when it improves row coverage.
- Bounded DRY observe ticks=4 exited 0 and opened XLM-USD under DRY only.
- No Profit Score tuning was done while opened=0.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 27 OK.
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": 9 OK.
- python -m py_compile managers\run_manager\run_manager.py: OK.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 21:23:04": OK; refreshed logs\dry_observe_readiness_latest.json.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false; subject [TDI STATUS] Profit 22/100 | DRY=true LIVE=false | dry signal blocked by quarantine (NEAR-USD).

Guardrails:
- DRY remains true.
- LIVE remains false.
- TDI_REPORT_HOURLY_SEC remains 7200 so routine updates go to email once every two hours.
- Reporting destination remains tdifactorToday@gmail.com.
- Coinbase/order placement path was not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Stay out of website/app/mobile/native lanes.

Next action:
- Monitor XLM-USD DRY position through static TP/SL/profit-protect.
- Keep improving data/preflight coverage and market-quality evidence under DRY only.
- Resume dry P&L quality work only after usable market coverage stays openable; do not enable LIVE and do not change order bodies.
- User action required: no.

## Codex relay status update

Timestamp: 2026-06-04T02:09:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local bounded DRY observe attempted after the current-tick breadth patch.
- The observe produced usable preflight/feed evidence for five ticks, then exited nonzero through hang guard / TDI compute access-violation path.
- Latest reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is green_breadth.
- The stale-breadth issue is corrected in runtime evidence: market_breadth_source=tick and msrc=tick in tick_diag.
- Latest tick evidence: U=120, S=393, brf=80, drysig=0, dryopen=0, dryblk=0.
- Current-tick breadth blocked opens as intended during weak/reversing market: latest_mbr=0.1250/0.8500, latest_mdmid=-13.03/0.00, market_breadth_n=120.
- Earlier ticks in the same sample also stayed below green breadth: max_near_mbr=0.6083 vs 0.8500.
- Tick dmid warmed during the sample: tick_diag_dmid_nonzero=289, tick_diag_dmid_ready=17, tick_diag_warmed_seen=true.
- Cache/preflight evidence remains openable/supportive enough for diagnostics: cache_supported=true, cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage evidence: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9, fresh_mtime_unusable=9.
- Liquid/cache evidence: liquid_subset=31, liquid_min=10, liquid_dmid_overlap=18, liquid_dmid_spread_tob_overlap=3.
- Green cache breadth is still below target: green_ratio=0.7176 vs green_min=0.8500, green_shortfall=0.1324.
- U=0 / stale-feed is not the current cause; U=120.
- Missing product/cache gap is not the current cause; S=393 and cache_openable=true.
- Do not tune Profit Score while open_count is back to 0; current task is feed/preflight and TDI crash/hang stability.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_cloud_only_corrections.py
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 22/100.
- dry P&L: realized=-0.29554786 USD, unrealized=0.00000000 USD, net=-0.29554786 USD.
- open/closed/wins/losses: open=0, closed=16, wins=3, losses=13.
- Credible positive dry profitability evidence is not present yet.
- Forward evidence remains negative/insufficient for runtime-near signals: runtime_near_forward signals=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- DRY market breadth now stays on tick source even when DRY_DMID_SOURCE remains recent_candle: DRY_MARKET_BREADTH_ALIGN_WITH_DRY_DMID_SOURCE=false.
- DRY_MIN_MARKET_DMID_BPS is now 0.0 so current market dmid must be non-negative when the breadth gate is active.
- Regression test added to ensure tick market breadth does not call recent candle metrics when explicit alignment is false.
- Existing DRY-only book-pressure gate remains active from the previous patch.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 26 OK.
- python -m unittest discover -s tests -p "test_cloud_only_corrections.py": 8 OK.
- run_settings.json parse check: DRY=True, LIVE=False, TDI_REPORT_HOURLY_SEC=7200, DRY_MARKET_BREADTH_SOURCE=tick, DRY_MARKET_BREADTH_ALIGN_WITH_DRY_DMID_SOURCE=False, DRY_MIN_MARKET_DMID_BPS=0.0, DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8.
- Bounded DRY observe produced tick evidence with msrc=tick and no opens, then failed nonzero: hang_dump_13236.log shows timeout and TDI compute access violation.
- python tools\koko_dry_observe_readiness.py ... --since-local-start "2026-06-03 21:06:52": OK; refreshed logs\dry_observe_readiness_latest.json.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false; subject [TDI STATUS] Profit 22/100 | DRY=true LIVE=false | green_breadth.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Investigate and fix the TDI compute crash/hang guard path from hang_dump_13236.log.
- Keep DRY observe blocked until current-tick breadth recovers; do not tune score while open_count=0.
- Continue data/preflight focus: timestamp coverage, liquid subset coverage, green breadth, U/stale-feed causes, and product/cache gaps.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T03:59:10Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / unknown.
- Reporter destination remains tdifactorToday@gmail.com.
- Routine reporting cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Material patch_change reporting is now classified as material.
- Latest patch_change report could not send to Gmail because SMTP env is still missing; reporter returned missing SMTP env ['user', 'password', 'sender'] and outbox_throttled.
- DRY remains true and LIVE remains false.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- DRY observe still opened zero candidates; do not tune Profit Score while open_count=0.
- Data/preflight lane improved: DRY_CANDIDATE_RANK changed from timestamp_liquid_green_dmid_desc to dmid_desc, matching cache preflight best_ranked=dmid_desc.
- Latest dmid_desc observe had U=120, S=393, top=393, chk=393, brf=80, so this is not a U=0 or stale-feed blocker.
- Latest dmid_desc observe produced no new open: opened=19, closed=19, wins=5, losses=14, open_count=0, blocked_open=88.
- Latest dryrank_top now correctly prioritizes major liquid candidates: BTC-USD, ETH-USD, XRP-USD, SOL-USD, then VVV-USD/MON-USD/AERO-USD/SUI-USD.
- Latest dryrank_top evidence: BTC qv=50877783 rdmid=73.51 spr=0.00 tob=2458; ETH qv=24792131 rdmid=67.16 spr=0.06 tob=584; XRP qv=6947703 rdmid=55.95 spr=0.83 tob=2299; SOL qv=6564452 rdmid=45.10 spr=2.80 tob=10620.
- Market breadth remained below target during this observe: latest_mbr=0.4083/0.8500, max_near_mbr=0.7083.
- Latest drygate breakdown still includes market breadth on all failing drygate combos: latest_drygate=dmid:21, market_breadth:21, spread:20, quote_volume:19, tob:19, score:16.
- Early cache-liquid candidates exist but are still blocked by trough/probe quality: early_skip_top=5, early_liquid=5, early_dmid=5, early_liquid_dmid=5, early_spread_tob=0, early_probe_rej=dmid:4,spread:1.
- Top early-skip candidate shifted to BTC-USD under dmid_desc: qv=50877783, rdmid=73.51, score=1.0000, rejected by trough-probe dmid with tpdmid=-0.1027/10.0000.
- Runtime near miss remains PAXG-USD blocked by dmid|market_breadth: qv=311190, rdmid=-8.70, spr=1.23, tob=1405.
- Cache preflight remains generally usable but green/timestamp are slightly short in latest reporter evidence: timestamp_ratio=0.8448/0.8500, green_ratio=0.7714/0.8500, liquid_subset=21/10.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- C:\ai_trading_bot_koko\logs\activity_ticker.log

Dry Profit Score evidence:
- Current Profit Score: 26/100.
- dry P&L: realized=-0.29854210 USD, unrealized=0.00000000 USD, net=-0.29854210 USD.
- open/closed/wins/losses: open=0, closed=19, wins=5, losses=14.
- No positive dry profitability evidence is present yet.

Patch/change evidence:
- Added dryrank_top tick diagnostics so runtime ranked candidates expose qv, rdmid, spread, top-book, timestamp usability, and metric source.
- Readiness now parses latest_dry_rank_top.
- Reporter now includes dryrank_top in readiness evidence.
- Reporter MATERIAL_EVENTS now includes patch_change.
- Config changed DRY_CANDIDATE_RANK=dmid_desc; no Profit Score tuning was done.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": PASS, 24 tests.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": PASS, 32 tests.
- python -m py_compile managers\run_manager\run_manager.py tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: PASS.
- JSON rail check: DRY=True, LIVE=False, DRY_CANDIDATE_RANK=dmid_desc, DRY_PNL_TP_PCT=8.0, DRY_PNL_SL_PCT=0.8, TDI_REPORT_HOURLY_SEC=7200.

Next action:
- Continue data/preflight lane, not Profit Score tuning.
- Re-run/monitor DRY observe when green breadth improves; current candidate lane now surfaces liquid majors, but market breadth and trough-probe tick-dmid/top-book still block opens.
- Investigate whether trough-probe tick-dmid threshold is over-filtering liquid majors in DRY observe, while keeping static TP/SL and Coinbase/order guardrails intact.

User action required:
- Only if real Gmail delivery is required now: provide SMTP env for TDI_REPORT_SMTP_USER, TDI_REPORT_SMTP_PASSWORD, and TDI_REPORT_FROM or equivalents. Otherwise no immediate user action.

## Codex relay status update

Timestamp: 2026-06-04T01:52:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY observe completed after refreshed cache/preflight coverage.
- Latest reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is now dry signal blocked by quarantine (SUI-USD).
- Data/preflight lane reached usable market coverage: cache_openable=true, diagnostic_worthwhile=true.
- Timestamp coverage evidence: timestamp_ratio=0.9771, timestamp_usable=384/393, timestamp_outside=9, fresh_mtime_unusable=9.
- Liquid/green evidence: liquid_subset=31, best_ranked=dmid_desc, best_ranked_green=1.0000, best_ranked_liquid=15, best_ranked_dmid_liq_overlap=15.
- Latest bounded DRY observe reached an all-pass candidate and dry signal: max_drysig=1, max_dryopen=0, max_dryblk=1, drysig_without_open=true.
- All-pass candidate evidence: SUI-USD at 2026-06-04T01:45:36Z, spread=1.25/5.00, tob=1044/500, qv=1296139/250000, rdmid=143.99/40.00, tdmid=17.54/10.00, market_green=0.9417/0.8500.
- Ledger evidence shows the dry open was blocked by quarantine for SUI-USD.
- Do not tune Profit Score while dryopen/open_count remains zero; next issue is DRY P&L quarantine/open eligibility, not score.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- Updated readiness evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Forward evidence remains mixed/insufficient: dry_open_forward signals=1 horizon_min=10 avg_net_close_bps=41.3940 positive_net_close_rate=1.0000, while realized/net dry P&L remains negative.

Patch/change evidence:
- Readiness now preserves historical runtime all-pass candidates from tick_diag near-tail instead of only the latest tick.
- Readiness now reports max_dry_blocked_open, dry_blocked_open_seen, and dry_signal_without_open.
- TDI status reporter now includes max_dryblk, drysig_without_open, and latest dryblk evidence.
- TDI status reporter now reads the latest dry P&L blocked_open ledger row and reports dry signal blocked by quarantine (SUI-USD) as the current blocker when cache_openable=true.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 25 OK.
- python -m py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- python tools\tdi_status_reporter.py ... --no-send: OK, sent=false; subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | dry signal blocked by quarantine (SUI-USD).

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Keep data/preflight evidence stable, but stop treating coverage as the current blocker now that cache_openable=true and drysig=1 occurred.
- Investigate/clear DRY P&L quarantine/open eligibility for the all-pass candidate path before resuming dry P&L improvement.
- Resume dry P&L improvement only after DRY opens can be recorded under guardrails.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:42:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only reporting/preflight lane.
- Patch applied so TDI readiness/status evidence includes cache timestamp usable counts, timestamp-outside count, fresh-mtime-unusable count, and candle age stats.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker remains green_breadth.
- Current cache evidence: cache_openable=false, diagnostic_worthwhile=true, timestamp_ratio=0.8651, timestamp_usable=340/393, timestamp_outside=53, fresh_mtime_unusable=53.
- Current cache age evidence: avg_candle_age_sec=2208.2, max_candle_age_sec=15028.0.
- Current breadth/liquid evidence: green_ratio=0.1708, green_shortfall=0.6792, liquid_subset=16.
- Reporter subject preview remains clean: [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.
- Reporter next action remains: wait for cache_openable=true; current blocker=green_breadth.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- TDI readiness evidence now includes timestamp_usable=<usable>/<checked>, timestamp_outside, fresh_mtime_unusable, avg_candle_age_sec, and max_candle_age_sec from cache_market_regime_latest.json.
- Regression assertions added for the new feed freshness evidence fields.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\tdi_status_reporter.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 25 OK.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false; preview includes timestamp_usable=340/393, timestamp_outside=53, fresh_mtime_unusable=53, avg_candle_age_sec=2208.2, max_candle_age_sec=15028.0.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Let the supervisor wait/detect loop identify the next genuinely openable green-breadth window.
- When cache_openable=true, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:39:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only reporting/preflight lane.
- Patch applied so TDI default next action uses cache_openable state instead of saying to continue DRY observe while the cache is not openable.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker remains green_breadth.
- Reporter subject preview remains clean: [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.
- Reporter next action now says: wait for cache_openable=true; current blocker=green_breadth.
- Current cache evidence remains: cache_openable=false, diagnostic_worthwhile=true, timestamp_ratio=0.8651, green_ratio=0.1708, liquid_subset=16, green_shortfall=0.6792.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Added default next-action derivation: when cache_regime.openable is false, next_action becomes wait for cache_openable=true with the current blocker.
- maybe_send now lets build_status compute the default next_action instead of forcing the old generic observe text.
- Regression test added for build_status next_action when cache_openable=false.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\tdi_status_reporter.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 25 OK.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false; subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth; next action wait for cache_openable=true; current blocker=green_breadth.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Let the supervisor wait/detect loop identify the next genuinely openable green-breadth window.
- When cache_openable=true, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:36:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only reporting/preflight lane.
- Patch applied so TDI main blocker prioritizes the current cache blocker when cache_openable=false.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is now reported cleanly as green_breadth.
- Reporter subject preview: [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.
- Current cache evidence remains: cache_openable=false, diagnostic_worthwhile=true, timestamp_ratio=0.8651, green_ratio=0.1708, liquid_subset=16, green_shortfall=0.6792.
- Older readiness evidence remains in the email body for context but no longer pollutes the current blocker subject when cache_openable=false.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- _main_blocker now returns current cache blockers first when cache_regime.openable is false.
- Regression test added so stale readiness blockers do not override cache_openable=false / green_breadth.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\tdi_status_reporter.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 24 OK.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false; subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Let the supervisor wait/detect loop identify the next genuinely openable green-breadth window.
- When cache_openable=true, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:34:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight/reporting lane.
- Patch applied so cache_market_regime_latest.json exposes openable and diagnostic_worthwhile as separate top-level fields.
- Patch applied so TDI status evidence includes cache_openable and diagnostic_worthwhile.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker remains green_breadth.
- Current cache/preflight snapshot: generated_at_utc=2026-06-04T01:33:18Z, openable=false, diagnostic_worthwhile=true, worthwhile=true, blocker=green_breadth.
- Current cache metrics: timestamp_ratio=0.8651, green_ratio=0.1708, liquid_subset=16, best_ranked=dmid_desc, best_ranked_green=0.6406, best_ranked_liquid=2.
- Reporter preview now explicitly includes cache_openable=false and diagnostic_worthwhile=true.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated cache/preflight evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- cache_market_regime_latest.json now distinguishes openable=<actual supervisor decision> from diagnostic_worthwhile=<cache-regime probe/diagnostic support>.
- TDI readiness evidence now includes cache_openable and diagnostic_worthwhile.
- Regression assertions added for cache snapshot openable/diagnostic_worthwhile and reporter evidence fields.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\run_koko_dry_supervised.py tools\tdi_status_reporter.py tests\test_run_koko_dry_supervised_preflight.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 29 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 23 OK.
- Direct preflight rebuild/write of cache_market_regime_latest.json: OK; openable=false and diagnostic_worthwhile=true are present.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false; preview includes cache_openable=false and diagnostic_worthwhile=true.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Let the supervisor wait/detect loop identify the next genuinely openable green-breadth window.
- When cache_openable=true, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:31:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight lane.
- Patch applied so supervisor wait-loop logs use the actual openable observe decision, not only the diagnostic observe_window_worthwhile flag.
- Patch applied so preflight force-refresh logs include openable=<true/false> and blocker from _preflight_observe_blocker.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is green_breadth.
- Current preflight evidence after sequential refresh: openable=false, blocker=green_breadth, diagnostic_worthwhile=true, ranked_observe_supported=false, ranked_probe_observe_supported=true.
- Current cache/preflight evidence: timestamp_ratio=0.8651, green_ratio=0.1708, liquid_subset=16, green_shortfall=0.6792.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Updated cache/preflight evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- preflight_force_refresh log now includes openable=<actual supervisor decision> and blocker=<gap-derived blocker>.
- preflight_wait_check log now includes openable=<actual supervisor decision>, diagnostic_worthwhile=<cache-regime diagnostic flag>, and blocker=<gap-derived blocker>.
- Regression test added for wait-loop logging of openable=false, diagnostic_worthwhile=true, blocker=green_breadth.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\run_koko_dry_supervised.py tests\test_run_koko_dry_supervised_preflight.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 29 OK.
- Direct current preflight check: openable=false, blocker=green_breadth, diagnostic_worthwhile=true, ranked_observe_supported=false, ranked_probe_observe_supported=true.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false; preview reads timestamp_ratio=0.8651 and green_ratio=0.1708.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Let the supervisor wait/detect loop identify the next genuinely openable green-breadth window.
- When openable=true, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:28:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight lane.
- Patch applied so supervisor preflight does not treat a green-breadth probe-only window as openable for observe.
- Current cache-regime builder still records diagnostic observe_window_worthwhile=true and ranked_probe_observe_supported=true, but supervisor now returns preflight_observe_worthwhile=false when green_ratio_shortfall is present and ranked_observe_supported=false.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is green_breadth.
- Current preflight decision: preflight_observe_worthwhile=false, preflight_observe_blocker=green_breadth.
- Current cache/preflight evidence: timestamp_ratio=0.9008, green_ratio=0.1661, liquid_subset=23, supported=true, blocker=green_breadth.
- Diagnostic probe evidence remains non-openable: observe_window_worthwhile=true, dry_observe_coverage_supported=true, ranked_observe_supported=false, ranked_probe_observe_supported=true, green_ratio_shortfall=0.6839.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Updated cache/preflight evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- _preflight_observe_worthwhile now rejects green-breadth probe-only windows unless ranked_observe_supported is true.
- _preflight_observe_blocker now includes timestamp_coverage and green_breadth from observe_trigger_gaps.
- Regression tests added for rejecting green-breadth probe-only windows and still allowing green breadth when a ranked scope fully passes.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\run_koko_dry_supervised.py tests\test_run_koko_dry_supervised_preflight.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 28 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 23 OK.
- Direct current preflight check: preflight_observe_worthwhile=false, preflight_observe_blocker=green_breadth.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Detect/wait for a better green-breadth window before running bounded DRY observe.
- When green breadth clears, run bounded DRY observe to verify actionable-book re-refresh improves spread/top-book/tick_dmid coverage and can produce DRY opens.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:25:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight/reporting lane.
- Patch applied so cache_market_regime_latest.json now exposes normalized top-level fields for generated_at_utc, timestamp_ratio, liquid_subset, dmid_quote, dmid_quote_range, supported, worthwhile, blocker, best_ranked, and best_probe evidence.
- Patch applied so TDI reporter derives cache blockers from observe_trigger_gaps when primary/dominant blocker fields are blank.
- TDI status reporter preview was --no-send; no email was sent and no local outbox file was created.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is green_breadth plus older cache-liquid/trough readiness evidence.
- Regenerated cache/preflight snapshot now exposes: generated_at_utc=2026-06-04T01:24:03Z, timestamp_ratio=0.9008, green_ratio=0.1661, liquid_subset=23, supported=true, worthwhile=true, blocker=green_breadth.
- Best-ranked evidence remains weak for opening: best_ranked=dmid_desc, best_ranked_green=0.5783, best_ranked_liquid=3, best_ranked_dmid_liq_overlap=1, best_ranked_dmid_range_overlap=1.
- Reporter preview subject now correctly includes current preflight blocker: [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | green_breadth+cache-liquid candidates blocked by trough (2; top ENA-USD).
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Updated cache/preflight evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Cache-regime snapshot writer now preserves the nested report and adds direct top-level fields for timestamp coverage, liquid subset, dmid/range overlap, support/worthwhile status, blocker, best-ranked, and best-probe evidence.
- Snapshot blocker fallback now derives timestamp_coverage, green_breadth, liquid_subset, dmid_liquidity_overlap, or candle_range_overlap from observe_trigger_gaps when root blocker fields are empty.
- TDI reporter main blocker now derives cache blockers from observe_trigger_gaps before falling back to readiness blockers.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\run_koko_dry_supervised.py tools\tdi_status_reporter.py tests\test_run_koko_dry_supervised_preflight.py tests\test_tdi_status_reporter.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 26 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 23 OK.
- Direct preflight rebuild/write of cache_market_regime_latest.json: OK, blocker=green_breadth, timestamp_ratio=0.9008, green_ratio=0.1661, supported=true.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false, subject includes green_breadth.
- logs\reports\outbox does not exist; outbox_count=0.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Wait for or detect a better green-breadth window, then run bounded DRY observe to verify the actionable-book re-refresh patch improves spread/top-book/tick_dmid coverage.
- Keep diagnosing timestamp/liquid/green/U=0/stale-feed/cache causes when coverage regresses.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:20:00Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight lane.
- Patch applied to keep DRY actionable book metrics refreshable on later ticks after their source becomes actionable_book_refresh_batch.
- Full recent-candle cache refresh completed for 393 runtime products: refreshed=393, failed=0, workers=4.
- Fresh preflight snapshot after cache refresh shows current market breadth is red again; no longer a good window for a longer observe.
- TDI status reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker is back to market breadth / preflight quality for the live window, not Profit Score.
- Fresh cache/preflight evidence: timestamp_ratio=0.9008, green_ratio=0.1661, liquid_subset=23, cache_supported=true.
- Reporter preview evidence: green_shortfall=0.6839, best_ranked=dmid_desc, best_ranked_green=0.5783, best_ranked_liquid=3, best_ranked_dmid_liq_overlap=1, best_ranked_dmid_range_overlap=1.
- Latest readiness from prior bounded observe still shows no opens: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0, max_drysig=0, max_dryopen=0, open_count=0.
- Entry-data issue fixed in code: actionable_book_refresh_batch metrics will now be eligible for the next batch refresh instead of freezing spread/top-book/tick_dmid after first refresh.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- Regenerated cache evidence: C:\Users\13144\OneDrive\Documents\AI_trading_bot_pro_cloud_work\logs\backtests\_cache\candles
- Updated cache/preflight evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- _dry_refresh_actionable_book_metrics now treats actionable_book_refresh and actionable_book_refresh_batch as refreshable sources.
- _dry_batch_refresh_actionable_book_metrics now treats actionable_book_refresh and actionable_book_refresh_batch as refreshable sources.
- Regression test added: previous actionable_book_refresh_batch metrics are refreshed again, updating spread, top-book USD, tick_dmid_bps, and tick_dmid_warmed.
- No score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile managers\run_manager\run_manager.py tests\test_koko_dry_candidate_rank.py: OK.
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 25 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 20 OK.
- python tools\refresh_koko_recent_candle_cache.py --products-file logs\dry_runtime_products_latest.json --days 1 --granularity 900 --limit 393 --workers 4: OK, refreshed=393, failed=0.
- Direct preflight rebuild/write of cache_market_regime_latest.json: OK, timestamp_ratio=0.9008, green_ratio=0.1661, cache_supported=true.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Wait for a worthwhile preflight window, then run a bounded DRY observe to verify actionable book re-refresh improves spread/top-book/tick_dmid coverage for liquid+dmid candidates.
- Keep diagnosing timestamp/liquid/green/U=0/stale-feed/cache causes when coverage regresses.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:14:30Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only data/preflight/observe lane.
- Full recent-candle cache refresh completed for 393 runtime products: refreshed=393, failed=0, workers=4.
- Cache preflight became worthwhile after refresh; bounded DRY observe completed 10/10 ticks without hanging.
- TDI status reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker has moved from stale cache / liquid+dmid overlap=0 to dry entry-data openability.
- Cache/preflight evidence after full refresh: timestamp_ratio=0.9466, green_ratio=0.6205, liquid_subset=24, dmid_quote=2, dmid_quote_range=2, supported=true, worthwhile=true.
- Best-ranked preflight mode is now usable: timestamp_liquid_green_dmid_desc with green=0.9250, liquid=24, dmid_liq_overlap=2, dmid_range_overlap=2, probe_quote_overlap=9, probe_range_overlap=9.
- Latest readiness: signals=368, liquid=26, dmid=51, liquid_dmid_overlap=2, liquid_dmid_spread_tob_overlap=0.
- Latest tick diagnostics: U=120, S=393, brf=80, tick_diag_rows=10, tick_diag_dmid_nonzero=284, tick_diag_dmid_ready=21, tick_diag_warmed_seen=true.
- Green breadth is no longer the immediate observe blocker in the latest tick: latest_mbr=0.9000/0.8500 and latest_mdmid=48.37/-999999.00.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Entry-data shortfall evidence: WLD-USD is the closest liquid+dmid candidate, blocked by spread/top-book/tick_dmid with spread_excess=0.70 bps and tob_shortfall=48.55 USD.
- Additional liquid+dmid candidate evidence: INJ-USD also had recent dmid but failed spread/top-book/tick_dmid.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- No new runtime file edits in this handoff step.
- Earlier local runtime patches remain active:
  - C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
  - C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
  - C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
  - C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
  - C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
  - C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
  - C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Regenerated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Refreshed cache evidence: C:\Users\13144\OneDrive\Documents\AI_trading_bot_pro_cloud_work\logs\backtests\_cache\candles
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.
- Reporter preview also showed older dry_open_forward evidence of one positive dry open, but this is not enough to override current open_count=0 and negative runtime-near evidence.

Patch/change evidence:
- No score tuning was performed.
- No Coinbase/order placement path was touched.
- Static TP/SL safety was not touched.
- Latest work repaired/verified data coverage by refreshing the full runtime product cache and running a bounded DRY observe only after preflight became worthwhile.

Verification evidence:
- python tools\refresh_koko_recent_candle_cache.py --products-file logs\dry_runtime_products_latest.json --days 1 --granularity 900 --limit 393 --workers 4: OK, refreshed=393, failed=0.
- Direct preflight rebuild/write of cache_market_regime_latest.json: OK, supported=true, worthwhile=true.
- Bounded observe command run_manager.run_loop(console=False, ticks=10): completed with exit code 0.
- python tools\koko_dry_observe_readiness.py --activity-log logs\activity_ticker.log --settings run_settings.json --since-local-start "2026-06-03 20:09:52" --out logs\dry_observe_readiness_latest.json: OK.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false, subject [TDI STATUS] Profit 25/100 | DRY=true LIVE=false | cache-liquid candidates blocked by trough (2; top ENA-USD).
- TDI_REPORT_HOURLY_SEC=7200 verified in run_settings.json.
- Previous test coverage remains green: test_koko_dry_candidate_rank.py 24 OK; test_koko_dry_observe_readiness.py 20 OK; test_tdi_status_reporter.py 22 OK; test_run_koko_dry_supervised_preflight.py 25 OK.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Inspect dry entry-data causes for the two liquid+dmid candidates, especially refreshed spread/top-book depth and tick_dmid warmup behavior.
- Keep DRY observe bounded to windows where cache/preflight remains worthwhile.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

## Codex relay status update

Timestamp: 2026-06-04T01:04:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local work completed in DRY-only supervisor preflight lane.
- Preflight-only supervisor run returned before full observe because the current window is not actionable.
- TDI status reporter preview was --no-send; no email was sent.
- Routine status email cadence remains every two hours: TDI_REPORT_HOURLY_SEC=7200.
- Reporting destination remains tdifactorToday@gmail.com.
- No live trading was enabled and no Coinbase/order placement path was touched.

Current blocker:
- Current blocker remains green_breadth+liquid+dmid overlap=0 (liquid=23, dmid=27).
- Supervisor preflight skip now reports the full gate stack instead of only green_breadth.
- Latest preflight skip line: blocker=green_breadth+dmid_liquidity_overlap+candle_range_overlap+liquid_subset.
- Current cache/preflight snapshot worsened after time passed: timestamp_ratio=0.2697, liquid=7, dmid_quote=0, dmid_quote_range=0.
- Latest readiness remains no-open: signals=377, liquid=23, dmid=27, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Still no opens: max_drysig=0, max_dryopen=0, open_count=0.
- Do not tune Profit Score while dryopen/open_count remains zero.

Files changed in current local runtime lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.

Dry Profit Score evidence:
- Current Profit Score: 25/100.
- dry P&L: realized=-0.0647515 USD, unrealized=0.0000000 USD, net=-0.0647515 USD.
- open/closed/wins/losses: open=0, closed=12, wins=3, losses=9.
- Credible positive dry profitability evidence is not present yet.
- Runtime-near forward history remains negative: signals_unique=20, best_reason=dmid|market_breadth, avg_net_close_bps=-50.5678, positive_net_close_rate=0.0000.

Patch/change evidence:
- Entry preflight now treats entry_liquid_dmid_overlap_gap as a stop condition, not only spread/top-book overlap gaps.
- Entry preflight blocker key now dedupes liquid+dmid overlap gaps separately from spread/top-book gaps.
- Supervisor preflight skip blocker now composes regime blocker plus dmid_liquidity_overlap, candle_range_overlap, and liquid_subset shortfalls from observe_trigger_gaps.
- No Profit Score thresholds were tuned.
- Coinbase/order placement path was not touched.
- Static TP/SL safety was not touched.

Verification evidence:
- python -m py_compile tools\run_koko_dry_supervised.py tests\test_run_koko_dry_supervised_preflight.py: OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 25 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 22 OK.
- Preflight-only supervisor run with KOKO_SUPERVISOR_REQUIRE_OBSERVE_WINDOW=1 returned exit code 0 and logged preflight_observe_skip with combined blocker.
- python tools\tdi_status_reporter.py --mode event --event patch_change --no-send --force: OK, sent=false.
- Outbox count stayed 260; newest outbox remained tdi_status_20260604T005201Z.eml.
- No lingering python.exe process after checks.

Guardrails:
- DRY remains true.
- LIVE remains false.
- Coinbase/order placement path not touched.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].
- Reporting cadence is two-hour routine email summaries; no duplicate/no-fluff emails.

Next action:
- Refresh/wait for a better preflight window before any longer DRY observe; current window lacks timestamp coverage, green breadth, liquid+dmid overlap, and range overlap.
- Continue accumulating runtime-near forward evidence only when near misses mature.
- Resume dry P&L improvement only after candidates can open under usable market coverage.

User action required:
- No.

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
