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

Timestamp: 2026-06-03T19:12:05Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 on 2026-06-03 after 6 ticks with DRY=true and LIVE=false; start marker 2026-06-03 14:09:51 America/Chicago.
- Latest preflight refresh before observe: completed; refreshed=393, failed=0, cache_market_regime_supported=true, observe_window_worthwhile=true, ranked_probe_observe_supported=true.
- Latest cache regime evidence after refresh: timestamp_usable_ratio=0.888, liquid_subset_products=21, blocker blank.
- Latest readiness task: regenerated for since_local_start=2026-06-03 14:09:51 and wrote logs/dry_observe_readiness_latest.json.
- Latest readiness evidence: signals=322, book_metric_source_present=265, book_metric_source_missing=57, book_metric_source_present_ratio=0.8230, paper_signal_book_source_gap=0, actionable_book_coverage_gap=false.
- TDI Factor Gmail heartbeat/reporting cadence: every two hours, plus immediate material events.
- Immediate material-event status sent through the Gmail connector to tdifactorToday@gmail.com; Gmail message id=19e8ee94c44f3d94. Local SMTP env is still missing, so SMTP-only sends write to C:\ai_trading_bot_koko\logs\tdi_status_outbox.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- DRY observe still opened 0 positions, but the current blocker is now actual market coverage, not missing product/cache handoff and not Profit Score tuning.
- The earlier cache-to-paper-signal gap was addressed: the DRY broad observe lane now supplements scorer output with timestamp-usable liquid+dmid recent-candle candidates so they cannot disappear before dry gate logging.
- U=0 / stale-feed cause is not current: latest tick stream has U=120 and S=393.
- Timestamp coverage is usable after refresh: timestamp_usable_ratio=0.888 vs min=0.850.
- Liquid subset coverage is usable: liquid_subset_products=21 vs min=10.
- Green breadth is the current runtime coverage shortfall: latest drynear diagnostics show market_green=0.7667 vs min=0.8500, market_dmid=37.22.
- Latest readiness has quote_volume_usable=5, dmid_usable=4, liquid_dmid_overlap=0, and liquid_dmid_spread_tob_overlap=0.
- Current one-gate near misses are liquid but recent-dmid-red: XRP-USD dmid=-8.2169 bps, ADA-USD dmid=-19.2123 bps, SOL-USD dmid=-39.7260 bps.
- Direct recent-candle check after observe: NEAR-USD qv=3481507.8652 and dmid=-38.3008; HYPE-USD qv=2845881.6283 and dmid=-48.6092; VVV-USD qv=1084968.9991 and dmid=-76.4386; WLD-USD qv=775694.9678 and dmid=9.5602; JTO-USD qv=417579.0892 and dmid=6.4641.
- OPN-USD has qv=934816.5113 and dmid=272.8732, but recent candle range=699.2187 bps, above DRY_MAX_RECENT_CANDLE_RANGE_BPS=600.0, so it remains unsafe to treat as an open candidate.

Files changed in current local lane:
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_candidate_rank.py
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tools\tdi_status_monitor.py
- C:\ai_trading_bot_koko\run_settings.json
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so local git status is unavailable here.

Changes applied in this update:
- Added readiness promotion for the closest liquid+dmid product that misses only spread/top-of-book overlap.
- Added status reporter wording so the main blocker names the concrete candidate and spread/top-of-book shortfall instead of only reporting `entry spread/tob overlap=0`.
- Added regression tests for closest spread/top-of-book shortfall promotion and email/report evidence.
- Added DRY-only recent-candle candidate supplement in the broad observe lane so timestamp-usable liquid+dmid names from the broader universe are included in checked candidates before normal dry gates.
- Changed TDI Factor periodic summary cadence from one hour to two hours via default code path and run_settings.json.
- Renamed monitor periodic event text from hourly_summary to two_hour_summary.
- Regenerated readiness after a 6-tick DRY observe; opened remained 0.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- opened=6 historically; latest 8-tick observe produced dryopen=0.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Cache regime: files_present=393, timestamp_usable_ratio=0.888, liquid_subset=21, cache_supported=true after refresh.
- Latest readiness: signals=322, quote_volume_usable=5, dmid_usable=4, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0.
- Latest readiness book coverage: book_metric_source_present=265, book_metric_source_missing=57, present_ratio=0.8230, paper_signal_book_source_gap=0.
- Latest tick stream: U=120, S=393, brf=80; stale-feed/U=0 is not the active cause.
- Latest runtime drynear blocker: dmid plus market_breadth; closest runtime near miss XRP-USD has qv=2742622.4443, dmid=-8.2169, spread=0.8219 bps, top-of-book=1512.3212.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_candidate_rank.py": 18 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 7 OK.
- python -m py_compile managers\run_manager\run_manager.py tools\tdi_status_reporter.py tools\tdi_status_monitor.py: OK.
- python -m json.tool run_settings.json: OK.
- Latest status subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | liquid+dmid overlap=0 (liquid=5, dmid=4).

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: wait for or capture a green-breadth and liquid+dmid overlap window, then verify dry opens resume under static TP/SL.
- Do not tune Profit Score while dryopen=0.
- Keep DRY observe only when cache preflight shows dmid_liquidity_overlap > 0 and observe_window_worthwhile=true.
- When liquid+dmid+spread+tob overlap appears and dry opens resume, collect dry P&L improvement evidence.
- Keep DRY=true and LIVE=false.

User action required:
- No.
