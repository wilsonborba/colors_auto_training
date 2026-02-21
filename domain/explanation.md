# domain

Domain layer = business logic and ML workflow logic (but **not** raw I/O).

Put here:
- entities/value objects (VideoJob, AuditSample, Run, ModelArtifact)
- service layer (use-cases) that call DAL adapters
- task definitions (repeatable jobs)
- run logic (ML training/eval artifacts) — per your preference
