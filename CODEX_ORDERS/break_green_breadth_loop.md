# Break green_breadth wait loop

DRY remains true. LIVE remains false.
Keep Coinbase/order guardrail intact.
Keep static TP/SL safety intact.
Stay out of website/app/mobile/native lanes.

Problem:
The system has reported the same blocker for days: green_breadth. Waiting for cache_openable=true is no longer acceptable by itself.

Goal:
Stop the indefinite green_breadth wait loop and make the engine progress toward dry profitability.

Do the work:
1. Treat repeated green_breadth blocking as a design/threshold/regime problem, not a reason to keep waiting forever.
2. Analyze whether the 0.85 green breadth threshold is actually truthful for current market regimes.
3. If the threshold is too strict, implement a bounded regime-adaptive alternative that can open controlled DRY observe when:
   - timestamp/feed quality is usable,
   - liquidity is usable,
   - dmid/market pressure floors are defined,
   - and risk remains capped.
4. Do not tune Profit Score while opened/closed evidence is absent.
5. Generate DRY observe evidence safely so dry P&L can be measured.
6. If the market is genuinely too weak for observe, prove that with data and state the exact condition that would reopen observation.

Required result:
- current green_breadth history summary,
- whether 0.85 is truthful or too strict,
- exact change made if any,
- files changed,
- verification/tests,
- whether DRY observe opened,
- dry P&L evidence if available,
- next blocker.

Do not return another simple wait status unless you prove no safe bounded observe path exists.