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

Timestamp: 2026-06-03T17:41:24Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe/mark task: completed exit 0 on 2026-06-03 after 8 ticks with DRY=true and LIVE=false; started at local 17:36:38 / 12:36:38 Central.
- Latest LINK-USD mark: 2026-06-03T17:37:48Z, still open and positive unrealized.
- Latest readiness task: regenerated at 2026-06-03T17:41:24Z for since_local_start=2026-06-03 12:36:38.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- Overall dry net P&L remains negative, so there is not yet credible final positive dry profitability evidence.
- Current dry P&L: realized=-0.04232084 USD, unrealized=0.01173709 USD, net=-0.03058375 USD.
- Open/closed/wins/losses: open=1, closed=5, wins=0, losses=5.
- Profit Score evidence: 12/100 as computed by tools/tdi_status_reporter.py from five closed losses and still-negative net P&L.
- LINK-USD open evidence remains positive but not enough to offset realized losses: last_pnl_bps=39.1236; last_pnl_usd=0.01173709; last_mid=8.3395.
- Dry-open forward evidence remains positive: signals=1, horizon_min=10, avg_net_forward_close_bps=41.3940, positive_net_close_rate=1.0.
- Latest readiness blocker: entry spread/tob overlap=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, brf=80, drysig=0, dryopen=0.
- Coverage: signals=393, quote_volume_usable=14, dmid_usable=121, liquid_dmid_overlap=6, liquid_dmid_spread_tob_overlap=0.
- Product-level coverage evidence now visible in readiness/status: liquid_dmid_products=ZEC-USD|SOL-USD|DOGE-USD|JTO-USD|ENA-USD; entry_spread_tob_products=none; liquid_missing_dmid=ETH-USD|XRP-USD|BTC-USD|NEAR-USD|XLM-USD; dmid_missing_liquid=LINK-USD|ONDO-USD|ICP-USD|BCH-USD|ADA-USD.
- Current nearest runtime miss: NEAR-USD fails dmid/spread or dmid only depending tick; no new open candidate in the latest 8-tick window.
- No Profit Score tuning applied.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_state.json
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Added entry_overlap_products to tools/koko_dry_observe_readiness.py so the data/preflight lane reports which products are in liquid+dmid, which also pass spread/tob, and which products miss liquid or dmid.
- Added product-level shortfall fields for qv, dmid, spread, tob, book_metric_source, and dmid_source.
- Added test coverage for product-level entry overlap reporting.
- Patched tools/tdi_status_reporter.py to include compact product-level coverage evidence in Gmail/status readiness evidence.
- Updated reporter tests to verify product-level evidence renders.
- Ran an 8-tick DRY-only observe/mark cycle; LINK remained open positive unrealized, but total dry net stayed negative.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- No DRY/LIVE or static TP/SL changes.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.01173709 USD, net=-0.03058375 USD.
- open/closed/wins/losses: open=1, closed=5, wins=0, losses=5.
- LINK-USD open evidence: entry_mid=8.307 at 2026-06-03T17:27:38Z; last_mid=8.3395 at 2026-06-03T17:37:48Z; last_pnl_bps=39.1236; last_pnl_usd=0.01173709.
- Dry-open forward evidence: avg_net_forward_close_bps=41.3940, positive_net_close_rate=1.0.
- Overall dry net remains negative, so dry profitability improvement is not complete.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 16 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 5 OK.
- py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK.
- Reporter preview subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | entry spread/tob overlap=0.
- Reporter preview readiness evidence includes product-level lists for liquid_dmid_products, entry_spread_tob_products, liquid_missing_dmid, and dmid_missing_liquid.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue monitoring the LINK-USD dry open until realized close or sustained positive dry net evidence exists.
- Use product-level readiness evidence to target data/preflight coverage gaps before any further score work.
- Keep DRY=true and LIVE=false.

User action required:
- No.
