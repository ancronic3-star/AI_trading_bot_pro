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

Timestamp: 2026-06-03T18:12:47Z

RELAY_FILE_VISIBLE=yes

Cloud task status:
- Cloud task URL: not configured locally / not visible from this workspace.
- Latest local supervised DRY observe/mark task: completed exit 0 on 2026-06-03 after 12 ticks with DRY=true and LIVE=false; local pid=23208 ts=18:06:51.
- Latest preflight refresh: completed; refreshed=391, failed=2, products=393, workers=8.
- Latest readiness task: regenerated for since_local_start=2026-06-03 13:06:49 and wrote logs/dry_observe_readiness_latest.json.
- Latest cache regime evidence: regenerated in logs/cache_market_regime_latest.json after patch.
- TDI Factor Gmail heartbeat automation: active as hourly-tdi-factor-gmail-status, scheduled every two hours.
- Immediate material-event Gmail status sent through Gmail connector to tdifactorToday@gmail.com, id=19e8eb09d912dffc.
- Local SMTP reporter could not send because SMTP env was missing user/password/sender; it wrote logs/tdi_status_outbox/tdi_status_20260603T181132Z.eml. Gmail connector send succeeded.
- PFID present in environment: yes, per prior local check.
- COINBASE_KEY_FILE present in environment: yes, per prior local check.

Current blocker:
- DRY observe can now use live/refreshed timestamp coverage, but opened remains 0.
- Current blocker is green_breadth plus dmid_liquidity_overlap=0; do not tune Profit Score while dryopen=0.
- U=0 / stale-feed cause is not current: latest tick stream has U=120, S=393, brf=80, drysig=0, dryopen=0.
- Timestamp coverage recovered after refresh: timestamp_usable_ratio=0.8779 vs min=0.8500.
- Liquid subset is present: liquid_subset=15 vs min=10.
- Broad green breadth is still below configured broad gate: green_ratio=0.4549 vs min=0.8500.
- Ranked preflight no longer gives a false positive: best_ranked=dmid_desc has green_ratio=1.0000 and liquid_subset=9, but dmid_liquidity_overlap=0, so observe_window_worthwhile=false.
- Entry coverage is blocked: liquid_dmid_overlap=0 and liquid_dmid_spread_tob_overlap=0.
- Book metric source coverage is still thin in readiness: book_metric_source_present_ratio=0.0178.

Files changed in current local lane:
- C:\ai_trading_bot_koko\tools\koko_cache_market_regime.py
- C:\ai_trading_bot_koko\tests\test_koko_cache_market_regime.py
- Generated local evidence: C:\ai_trading_bot_koko\logs\cache_market_regime_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_observe_readiness_latest.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_cycle18_pnl_score.json
- Generated local evidence: C:\ai_trading_bot_koko\logs\dry_supervised_loop.log
- Generated local evidence: C:\ai_trading_bot_koko\logs\tdi_status_outbox\tdi_status_20260603T181132Z.eml
- Remote relay updated: CODEX_RELAY.md on ancronic3-star/AI_trading_bot_pro branch codex/cloud-ready-koko-bot.
- Local workspace has no .git metadata, so local git status is unavailable here.

Changes applied in this update:
- Fixed cache-regime CLI default cache path so direct preflight/reporting runs read DRY_RUNTIME_CANDLE_CACHE_DIR from run_settings.json instead of the empty local fallback cache.
- Added default_cache_dir coverage in tests.
- Tightened ranked observe support so cache_market_regime_supported / observe_window_worthwhile requires dmid_liquidity_overlap > 0, preventing observe false positives when green and liquid pass separately but no product satisfies both entry gates.
- Added regression coverage for split liquid-red / green-thin universes.
- Refreshed recent candle cache via supervisor preflight: before timestamp=0.8117 and blockers timestamp_coverage+green_breadth; after timestamp=0.8779.
- Ran a 12-tick DRY-only supervised observe after preflight became usable; opened remained 0.
- Preserved Coinbase/order placement guardrail; no Coinbase/order path changes.
- Preserved DRY/LIVE safety: DRY=true and LIVE=false.
- Preserved static TP/SL safety: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.

Dry Profit Score evidence:
- Current Profit Score: 12/100.
- dry P&L: realized=-0.04286255 USD, unrealized=0.0 USD, net=-0.04286255 USD.
- open/closed/wins/losses: open=0, closed=6, wins=0, losses=6.
- opened=6 historically; latest 12-tick observe window produced drysig=0 and dryopen=0.
- Overall dry net remains negative, so credible positive dry profitability evidence is not yet present.

Coverage evidence:
- Cache regime: files_present=393, timestamp_usable_ratio=0.8779, green_ratio=0.4549, liquid_subset=15, dmid_ge_min_and_quote_volume_ge_min=0.
- Cache promotion hint: cache_supported=false, observe_window_worthwhile=false, blockers=green_breadth and dmid_liquidity_overlap, best_ranked=dmid_desc, best_ranked_green=1.0000, best_ranked_liquid=9, best_ranked_dmid_liquidity_overlap=0.
- Readiness: signals=393, quote_volume_usable=15, dmid_usable=48, liquid_dmid_overlap=0, liquid_dmid_spread_tob_overlap=0, spread_usable=44, tob_usable=98, trough_seeded=358.
- Latest tick_diag: U=120, S=393, brf=80, drysig=0, dryopen=0, mbr=0.9500/0.8500, mdmid=46.07.
- Liquid missing dmid examples: ICP-USD, ZEC-USD, SOL-USD, DOGE-USD, XRP-USD.
- Dmid missing liquid examples: WLD-USD, TON-USD, USELESS-USD, RAVE-USD, WIF-USD.

Verification evidence:
- python -m unittest discover -s tests -p "test_koko_cache_market_regime.py": 17 OK.
- python -m unittest discover -s tests -p "test_tdi_status_reporter.py": 5 OK.
- python -m unittest discover -s tests -p "test_run_koko_dry_supervised_preflight.py": 2 OK.
- py_compile tools\koko_cache_market_regime.py tools\tdi_status_reporter.py tools\run_koko_dry_supervised.py: OK.
- Reporter/Gmail subject: [TDI STATUS] Profit 12/100 | DRY=true LIVE=false | green_breadth.

Guardrails:
- Coinbase/order placement path not touched by this update.
- DRY remains true.
- LIVE remains false.
- Static TP/SL safety remains intact: DRY_PNL_TP_PCT=8.0 and DRY_PNL_SL_PCT=0.8.
- Orders guardrail remains in force: market_order_buy/sell with client_order_id only, and no portfolio_uuid in order bodies.

Next action:
- Continue data/preflight lane first: liquid+dmid overlap, green breadth, timestamp coverage, U=0/stale feed causes, and product/cache gaps.
- Do not tune Profit Score while dryopen=0.
- Keep DRY observe paused unless cache preflight shows dmid_liquidity_overlap > 0 and observe_window_worthwhile=true.
- When liquid+dmid+spread+tob overlap appears and dry opens resume, collect dry P&L improvement evidence.
- Keep DRY=true and LIVE=false.

User action required:
- No.