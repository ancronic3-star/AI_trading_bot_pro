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

Timestamp: 2026-06-03T17:34:39Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 on 2026-06-03 after 4 ticks with DRY=true and LIVE=false; tick 1 opened LINK-USD at 2026-06-03T17:27:38Z.
- Latest local mark/update task: completed exit 0 at 2026-06-03T17:31:37Z after 2 ticks; LINK-USD remained open and marked positive.
- Latest local readiness task: regenerated at 2026-06-03T17:31:51Z for since_local_start=2026-06-03 12:31:20.
- Latest dry-open forward-outcome task: completed exit 0; evaluated 1 dry open signal over 10 minutes.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- Overall dry net P&L remains negative, so there is not yet credible final positive dry profitability evidence.
- Current dry P&L: realized=-0.04232084 USD, unrealized=0.01263994 USD, net=-0.02968090 USD.
- Open/closed/wins/losses: open=1, closed=5, wins=0, losses=5.
- Profit Score evidence: 12/100 as computed by tools/tdi_status_reporter.py from five closed losses and still-negative net P&L.
- Positive dry-open evidence exists: LINK-USD open mark was +42.1331 bps unrealized at 2026-06-03T17:31:37Z.
- Dry-open forward evidence is positive: signals=1, horizon_min=10, avg_net_forward_close_bps=41.3940, positive_net_close_rate=1.0, sl_touch_rate=0.0, tp_touch_rate=0.0.
- Latest readiness window after the mark did not produce a new open: U=120, S=393, brf=80, drysig=0, dryopen=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120 and S=393.
- Coverage is no longer the hard zero-overlap blocker: quote_volume_usable=14, dmid_usable=121, liquid_dmid_overlap=6, liquid_dmid_spread_tob_overlap=1.
- Current runtime/near-miss blocker is trough/spread/quote-volume on later candidates, with SOL-USD closest one-gate miss blocked by trough.
- No blind score tuning applied while dryopen was 0; after LINK opened, scoring still was not tuned.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest_dry10.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_state.json
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Normalized runtime near-miss failure label tob to tob_usd in tools/koko_dry_observe_readiness.py so runtime failure combos match paper gate naming.
- Added test coverage for runtime tob-to-tob_usd normalization.
- Patched tools/tdi_status_reporter.py to include dry-open forward evidence from logs/paper_signal_forward_outcomes_latest_dry10.json.
- Updated reporter tests to verify dry_open_forward evidence renders.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- No DRY/LIVE or static TP/SL changes.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.01263994 USD, net=-0.02968090 USD.
- open/closed/wins/losses: open=1, closed=5, wins=0, losses=5.
- LINK-USD open evidence: entry_mid=8.307 at 2026-06-03T17:27:38Z; last_mid=8.342 at 2026-06-03T17:31:37Z; last_pnl_bps=42.1331; last_pnl_usd=0.01263994.
- Dry-open forward evidence: avg_net_forward_close_bps=41.3940, positive_net_close_rate=1.0.
- Overall dry net remains negative, so dry profitability improvement is not complete.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 4 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 15 OK.
- py_compile tools\tdi_status_reporter.py tools\koko_dry_observe_readiness.py: OK.
- Reporter preview subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | trough.
- Reporter preview forward evidence includes dry_open_forward signals=1 horizon_min=10 avg_net_close_bps=41.3940 positive_net_close_rate=1.0000.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue monitoring the LINK-USD dry open until realized close or sustained positive dry net evidence exists.
- Keep improving/reporting data/preflight coverage and current candidate blocker evidence before any further score work.
- Keep DRY=true and LIVE=false.

User action required:
- No.
