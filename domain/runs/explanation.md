# domain/runs

Runs = ML-related run artifacts and lifecycle.

Put here:
- evaluation run records (metrics.json, per-class reports)
- training run records (config, checkpoints, lineage)
- promotion decisions and model registry entries (if you keep registry here)

Rule:
- runs are append-only per run_id.
- do not mix runs with frozen audit data.
