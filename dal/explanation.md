# dal

**Data Access Layer (DAL)**: adapters that talk to the outside world (remote/local).

Rules:
- DAL exposes *general-purpose adapter methods* (CRUD-ish, fetch/save, etc.).
- DAL contains no orchestration logic (no multi-step workflows).
- DAL code is consumed by **domain services**.
