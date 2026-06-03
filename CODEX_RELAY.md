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

Timestamp: 2026-06-03T17:58:09Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe/mark task: completed exit 0 on 2026-06-03 after 12 ticks with DRY=true and LIVE=false; run_active pid=12952 ts=17:54:24.
- Latest readiness task: regenerated for since_local_start=2026-06-03 12:54:24 and wrote logs/dry_observe_readiness_latest.json.
- Latest cache regime evidence: regenerated in logs/cache_market_regime_latest.json.
- Hourly TDI Factor Gmail heartbeat remains active as hourly-tdi-factor-gmail-status.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- Overall dry net P&L remains negative, so there is not yet credible final positive dry profitability evidence.
- LINK-USD stale open closed via stale_loaded at -1.8057 bps / -0.00054171 USD; there are now no open dry positions.
- Latest 12-tick observe window produced no new open: drysig=0 and dryopen=0.
- U=0 / stale-feed cause is not current: latest tick stream has U=120, S=393, brf=80.
- Current blocker is green_breadth, not score tuning: cache green_ratio=0.1852 vs min=0.8500, green_shortfall=0.6648; runtime mbr=0.5667 vs min=0.8500.
- Timestamp coverage is usable: timestamp_usable_ratio=0.8677 vs min=0.8500.
- Liquid subset is nominally present: liquid_subset=13 vs min=10.
- Entry coverage is still thin: liquid_dmid_overlap=2 and liquid_dmid_spread_tob_overlap=0.
- No Profit Score tuning applied.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_state.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_ledger.jsonl
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Ran a 12-tick DRY-only observe/mark cycle with LIVE=false.
- Confirmed stale LINK-USD dry open closed through DRY paper state, not Coinbase/order logic.
- Patched tools/tdi_status_reporter.py so readiness evidence includes cache_supported, timestamp_ratio, green_ratio, green_min, liquid_subset, liquid_min, cache_blocker, green_shortfall, timestamp_shortfall, liquid_shortfall, and best-ranked green/liquid evidence.
- Added reporter test coverage for cache green-breadth/timestamp/liquid-subset evidence.
- Sent immediate material-event Gmail status to tdifactorToday@gmail.com.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- LINK-USD close evidence: entry_mid=8.307 at 2026-06-03T17:27:38Z; exit_mid=8.3055 at 2026-06-03T17:54:28Z; exit_reason=stale_loaded; pnl_bps=-1.8057; pnl_usd=-0.00054171.
- Overall dry net remains negative, so dry profitability improvement is not complete.

Coverage evidence:
- signals=393.
- quote_volume_usable=15.
- dmid_usable=31.
- liquid_dmid_overlap=2.
- liquid_dmid_spread_tob_overlap=0.
- spread_usable=43.
- tob_usable=99.
- trough_seeded=361.
- cache_supported=false.
- timestamp_usable_ratio=0.8677.
- cache green_ratio=0.1852, min_green_ratio=0.8500, green_shortfall=0.6648.
- liquid_subset=13, liquid_min=10, liquid_shortfall=0.
- best_ranked=dmid_desc, best_ranked_green=0.5814, best_ranked_liquid=2.
- liquid_dmid products: HYPE-USD, OPN-USD.
- liquid_dmid_spread_tob products: none.
- Near miss examples: NEAR-USD fails dmid; HYPE-USD fails tob_usd and trough; RLC-USD fails tob_usd and quote_volume; ADA-USD fails quote_volume and dmid.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 5 OK.
- py_compile tools\tdi_status_reporter.py: OK.
- Reporter preview subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | green_breadth.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: green breadth, timestamp coverage, liquid subset coverage, U=0/stale feed causes, and product/cache gaps.
- Do not tune Profit Score while dryopen=0.
- When green breadth recovers and liquid+dmid+spread+tob overlap appears, resume dry P&L improvement evidence collection.
- Keep DRY=true and LIVE=false.

User action required:
- No.
