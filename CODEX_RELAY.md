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

Timestamp: 2026-06-03T17:48:24Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe/mark task: completed exit 0 on 2026-06-03 after 20 ticks with DRY=true and LIVE=false; run_active pid=14836 ts=17:43:33.
- Latest readiness task: regenerated for since_local_start=2026-06-03 12:43:33 and wrote logs/dry_observe_readiness_latest.json.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.
- Hourly TDI Factor Gmail heartbeat: created and active as hourly-tdi-factor-gmail-status.

Current blocker:
- Overall dry net P&L remains negative, so there is not yet credible final positive dry profitability evidence.
- Latest 20-tick observe window produced no new open: drysig=0 and dryopen=0.
- U=0 / stale-feed cause is not current: latest tick stream has U=120, S=393, brf=80, green breadth 0.9750, and market_dmid about 96.60 bps.
- Effective open coverage remains too thin. Refreshed readiness has liquid_dmid_overlap=6 and liquid_dmid_spread_tob_overlap=2, but reporter still flags entry spread/tob overlap as the open blocker.
- Top near misses are data/preflight gate issues, not score tuning: SOL-USD trough only; SUI-USD trough only; JTO-USD tob_usd|trough; ENA-USD spread|trough.
- LINK-USD gave back prior positive unrealized and is now negative unrealized; inspect why it did not close before the giveback.
- No Profit Score tuning applied.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\activity_ticker.log
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_state.json
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Regenerated latest DRY observe readiness for the completed 20-tick observe/mark run.
- Created hourly TDI Factor Gmail reporting heartbeat to tdifactorToday@gmail.com.
- Sent immediate material-event Gmail status for the DRY P&L/blocker change.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=-0.00054171 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=1, closed=5, wins=0, losses=5.
- LINK-USD open evidence: entry_mid=8.307 at 2026-06-03T17:27:38Z; last_mid=8.3055 at 2026-06-03T17:46:29Z; last_pnl_bps=-1.8057; last_pnl_usd=-0.00054171.
- Prior dry-open forward evidence is stale against the current mark: horizon_min=10, avg_net_forward_close_bps=41.3940, positive_net_close_rate=1.0, but current actual LINK mark is negative.
- Overall dry net remains negative, so dry profitability improvement is not complete.

Coverage evidence:
- signals=393.
- quote_volume_usable=14.
- dmid_usable=121.
- liquid_dmid_overlap=6.
- liquid_dmid_spread_tob_overlap=2.
- spread_usable=42.
- tob_usable=101.
- trough_seeded=354.
- liquid_dmid products: ZEC-USD, SOL-USD, DOGE-USD, JTO-USD, ENA-USD, SUI-USD.
- liquid_dmid_spread_tob products: SOL-USD, SUI-USD.
- Shortfall examples: ENA-USD spread_excess=12.4978 bps and trough_pct=0.666667; ZEC-USD tob_shortfall=473.4268 USD and trough_pct=0.433803; JTO-USD tob_shortfall=475.5961 USD and trough_pct=1.0; DOGE-USD tob_shortfall=477.54 USD and trough_pct=0.534211.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 16 OK, prior to this observe rerun.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 5 OK, prior to this observe rerun.
- py_compile tools\koko_dry_observe_readiness.py tools\tdi_status_reporter.py: OK, prior to this observe rerun.
- Reporter preview subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | entry spread/tob overlap=0.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: timestamp coverage, liquid subset coverage, green breadth, U=0/stale feed causes, and product/cache gaps.
- Inspect why the aged LINK-USD dry open did not close before giving back unrealized P&L.
- Do not tune Profit Score while opened/dryopen is 0.
- Keep DRY=true and LIVE=false.

User action required:
- No.
