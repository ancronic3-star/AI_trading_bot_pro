# KOKO Cloud Source Lane

This repository is a sanitized source-only lane for Codex Cloud work.

Rules:
- DRY stays true.
- LIVE stays false.
- Do not add Coinbase keys, PFID secrets, env files, ledgers, logs, runtime snapshots, or generated artifacts.
- Do not change the Coinbase/order guardrail.
- Use `run_settings.template.json` for dry-mode configuration examples.
- Heavy replay, analysis, and test sweeps should run in Cloud, not on the local laptop.

Primary objective:
- Improve dry-mode net P&L using an auditable profit score based on dry realized/unrealized P&L, exposure, closed wins/losses, drawdown, and repeatability.
