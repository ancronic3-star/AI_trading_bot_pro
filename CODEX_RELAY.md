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

Timestamp: 2026-06-03T17:20:31Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe task: completed exit 0 at 2026-06-03T17:11:24Z after 4 ticks with DRY=true and LIVE=false.
- Latest local readiness task: regenerated at 2026-06-03T17:15:24Z for since_local_start=2026-06-03 12:10:50.
- Latest forward-outcome task: completed exit 0; loaded 120 recent paper signals, evaluated 114 outcomes over 30 minutes, 6 had no forward candles.
- Latest ranked-forward task: completed exit 0; no supported positive ranked slice found.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- No credible positive dry profitability evidence yet.
- Current dry P&L remains negative: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- Open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- Profit Score evidence: 12/100 as computed by tools/tdi_status_reporter.py from five closed losses and negative net P&L.
- Do not tune Profit Score while opened=0 / dryopen=0.
- U=0 / stale-feed cause is not current: latest tick_diag has U=120, S=393, brf=80, drysig=0, dryopen=0.
- Entry coverage blocker remains explicit: quote_volume_usable=19 and dmid_usable=71, but liquid_dmid_overlap=0 and liquid_dmid_spread_tob_overlap=0.
- Forward evidence is negative: dmid signals avg_net_forward_close_bps=-136.7681 with sl_touch_rate=1.0; best ranked slice active_dmid_desc avg_net_forward_close_bps=-72.3032 and supported=false; supported_ranked_modes=0.
- Current blocker label in reporter now resolves to: liquid+dmid overlap=0 (liquid=19, dmid=71).
- No blind score or gate tuning applied.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\tdi_status_reporter.py
- C:\ai_trading_bot_koko\tests\test_tdi_status_reporter.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_latest.json, C:\ai_trading_bot_koko\logs\paper_signal_forward_outcomes_history.json, C:\ai_trading_bot_koko\logs\runtime_ranked_forward_outcomes_latest.json
- Prior lane files still changed locally: C:\ai_trading_bot_koko\tools\koko_dry_observe_readiness.py, C:\ai_trading_bot_koko\tests\test_koko_dry_observe_readiness.py, C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json, C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py, C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py, C:\ai_trading_bot_koko\run_settings.json.
- GitHub relay file updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so git status is unavailable here.

Changes applied in this update:
- Ran DRY-only forward outcomes on recent paper signals for reasons dmid, spread, quote_volume, tob_usd, trough, trough_wait using current static TP/SL reporting: TP=800 bps, SL=80 bps.
- Ran ranked forward outcome summary; no ranked mode produced a supported positive subset.
- Patched tools/tdi_status_reporter.py to include readiness evidence and forward evidence in material/hourly emails.
- Patched the reporter blocker selection to prefer explicit entry liquid+dmid overlap gaps over dominant paper-signal blocker labels.
- Added reporter tests for entry-overlap blocker selection and email evidence rendering.
- No Coinbase/order placement path changes.
- No Profit Score tuning.
- No DRY/LIVE or static TP/SL changes.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04232084 USD, unrealized=0.00 USD, net=-0.04232084 USD.
- open/closed/wins/losses: open=0, closed=5, wins=0, losses=5.
- No credible positive dry profitability evidence yet.

Verification evidence:
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 4 OK.
- python -m unittest discover -s tests -p "test_koko_dry_observe_readiness.py": 14 OK.
- py_compile tools\tdi_status_reporter.py tools\tdi_status_monitor.py: OK.
- Reporter preview subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | liquid+dmid overlap=0 (liquid=19, dmid=71).
- Forward outcomes: 114 evaluated, dmid avg_net_forward_close_bps=-136.7681, dmid sl_touch_rate=1.0.
- Ranked forward outcomes: best active_dmid_desc avg_net_forward_close_bps=-72.3032, supported=false, supported_ranked_modes=0.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue DRY-only observe with usable data/preflight coverage and monitor liquid+dmid overlap plus supported forward-ranked slices.
- Do not tune Profit Score while opened=0 / dryopen=0 and no credible positive dry P&L exists.
- Do not loosen gates based on current forward evidence; current recent paper-signal outcomes are net negative.

User action required:
- No.
