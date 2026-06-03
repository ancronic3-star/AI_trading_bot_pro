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

Timestamp: 2026-06-03T21:55:45Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local DRY supervised entry-preflight sample: completed, DRY=true, LIVE=false.
- Latest local monitor snapshot: 2026-06-03T21:52:34Z, DRY=true, LIVE=false.
- TDI Factor reporting destination: tdifactorToday@gmail.com.
- TDI Factor summary cadence: every two hours only, plus immediate material-event emails.
- No duplicate/no-fluff email rule remains active.

Current blocker:
- Primary blocker: cache-liquid+dmid candidates are being skipped early by the trough gate before DRY open evaluation.
- Latest readiness: signals=317, open_candidate=false, probe_candidate=false, drysig=0, dryopen=0.
- Latest tick diagnostic: U=120, S=393, brf=80, pass=29, drysig=0, dryopen=0, rej=trough:336,spr:28,trough_wait:28,tob:1.
- New early-skip evidence: dryliqskip=trough:7.
- dryliqskip_top examples: ENA-USD qv=955,798 rdmid=143.11 score=0.9613; ONDO-USD qv=955,053 rdmid=98.13 score=0.8770; WLD-USD qv=930,991 rdmid=89.17 score=0.7010; ZEC-USD qv=15,976,914 rdmid=73.61 score=0.6030; ICP-USD qv=1,505,238 rdmid=73.46 score=0.7323.
- Runtime products are now aligned to the actual ranked/discovered universe: C:\ai_trading_bot_koko\logs\dry_runtime_products_latest.json with 393 products.
- Cache support is usable against runtime products: cache_supported=true, files_present=393, missing_files=0.
- Timestamp coverage is usable: timestamp_ratio=0.8651, timestamp_shortfall=0.
- Liquid subset coverage is usable: liquid_subset=22 vs required 10, liquid_shortfall=0.
- Runtime top-120 ranked observe coverage is usable: timestamp_ratio=1.0, liquid_subset=22, green_ratio=0.9667, dmid_liquidity_overlap=7.
- Full-universe green breadth remains short: green_ratio=0.7027 vs required 0.8500, green_shortfall=0.1473.
- U=0 / stale-feed is not the current cause.
- Missing product/cache gap is not the current cause after runtime product snapshot alignment.
- Do not tune Profit Score while open_count=0 and dryopen=0.

Files changed in current lane:
- C:\ai_trading_bot_koko\tools\run_koko_dry_supervised.py
- C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
- C:\ai_trading_bot_koko\tests\test_run_koko_dry_supervised_preflight.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_runtime_products_latest.json
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

Patch/change evidence:
- DRY supervisor now writes a runtime product snapshot from the actual ranked/discovered runtime universe before preflight cache checks.
- DRY supervisor now prefers KOKO_DRY_PRODUCTS_FILE, then the runtime product snapshot, then legacy dry_observe_products files for cache/readiness.
- DRY supervisor rechecks candle cache after writing runtime products so preflight coverage follows the same products runtime evaluates.
- Runtime diagnostics now report dryliqskip and dryliqskip_top for cache-liquid+dmid candidates skipped before PAPER_BUY_SIGNAL logging.
- No scoring thresholds were tuned.
- Coinbase/order placement path was not touched.

Verification evidence:
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 16 OK in local runtime.
- python -m py_compile tools\run_koko_dry_supervised.py: OK in local runtime.
- python -m py_compile managers\run_manager\run_manager.py tools\run_koko_dry_supervised.py: OK in local runtime.
- Latest bounded DRY sample wrote runtime products=393 and cache products_file=C:\ai_trading_bot_koko\logs\dry_runtime_products_latest.json.
- Cloud checkout is a slim handoff tree; focused runtime tests were run against C:\ai_trading_bot_koko.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.
- Balances guardrail remains in force: get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

Next action:
- Surface dryliqskip evidence in readiness/reporting so emails and relay do not mislabel the issue as missing liquid overlap.
- Then decide and implement a DRY-only trough-probe/bypass path for cache-liquid+dmid candidates, or wait for a trough window.
- Keep focus on data/preflight/openability while opened=0; do not tune Profit Score yet.
- Keep reporting to tdifactorToday@gmail.com on two-hour cadence unless a material event occurs.
- Keep DRY=true and LIVE=false.

User action required:
- No.
