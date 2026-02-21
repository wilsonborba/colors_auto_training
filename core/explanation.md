# core

**Core operational foundation** for the app.

Put here:
- `settings.py`: a single Pydantic Settings class (env reading lives *only* here).
- global configuration contracts and shared constants (with discipline).
- cross-cutting utilities that are *not* infrastructure (e.g., domain-safe types, logging interface definitions).

Do **not** put:
- I/O code (network, filesystem, sqlite) → goes in `dal/`.
- business workflows → goes in `domain/services/` or `domain/tasks/`.
