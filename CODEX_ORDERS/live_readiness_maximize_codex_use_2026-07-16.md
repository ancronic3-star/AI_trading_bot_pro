# KOKO — Token-Efficient Live Readiness Work Order

## Objective
Use one finite Codex work session to preserve the completed DRY result, determine whether the strategy survives realistic Coinbase fees and slippage, and prepare a smallest-possible live canary plan. Do not enable LIVE or place any live order in this work order.

## Standing safety
- DRY=true.
- LIVE=false.
- Do not touch the Coinbase path; use PFID from env and COINBASE_KEY_FILE from env; balances must read get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value']; orders must use market_order_buy/sell with client_order_id and never include portfolio_uuid in bodies.
- Preserve static exchange-side TP 8% and SL 0.8%.
- Do not alter approved-product controls.
- No website/app/mobile/native work.

## Work scope
1. Freeze and checksum the completed positive DRY baseline:
   - realized P&L +0.03857412 USD
   - 458 opened / 458 closed / 0 open
   - L3 slice +0.09744857 USD over 7 closes
   - Profit Score 64
2. Recalculate the completed trade ledger using the authenticated account's actual current Coinbase Advanced fee tier where available, plus measured or conservative spread/slippage assumptions.
3. Report whether global and L3 results remain positive after round-trip execution costs.
4. Audit the final L3 profit_protect close and verify that the DRY fill model did not overstate fills or omit costs.
5. Run no broad autonomous loop. Use targeted tests and one bounded analysis pass only.
6. Produce a live-readiness decision with one of exactly three outcomes:
   - NOT_READY
   - READY_FOR_MANUAL_CANARY_APPROVAL
   - EVIDENCE_INVALID_REPAIR_REQUIRED
7. If READY_FOR_MANUAL_CANARY_APPROVAL, prepare but do not activate a canary configuration with:
   - one approved product only
   - one position maximum
   - smallest exchange-valid notional, capped at $5
   - no automatic reentry
   - one completed round trip maximum
   - hard account kill switch after any loss, order error, unexpected fill, guardrail failure, or data staleness
   - manual user approval required before LIVE changes
8. Estimate expected Codex usage before starting any optional extra work. Stop after the required report; no heartbeat, recurrence, or self-chaining task.

## Required deliverable
Write a compact report containing:
- frozen-baseline checksum/path
- actual fee tier used or why unavailable
- fee/slippage assumptions
- gross versus net global P&L
- gross versus net L3 P&L
- fill-model audit result
- exact readiness outcome
- exact canary configuration if eligible
- files changed
- tests and results
- user action required

Do not enable LIVE. Do not place orders. Do not start a worker or monitoring task.