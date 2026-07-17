# KOKO — Independent Cost-Adjusted DRY Holdout Work Order

## Objective
Build, validate, and start one isolated local DRY holdout runner that tests the frozen profitable strategy on unseen forward market data without recurring Codex usage. Preserve the completed baseline exactly. Do not enable LIVE and do not place any live order.

## Frozen baseline to preserve
- Profit Score: 64
- Global realized dry P&L: +0.03857412 USD
- Ledger: opened=458, closed=458, open_count