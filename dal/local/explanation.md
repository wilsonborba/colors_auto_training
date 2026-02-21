# dal/local

Local adapters: SQLite, filesystem, local caches.

Put here:
- `sqlite_adapter.py`: connection/session management, migrations strategy, queries.
- filesystem adapter(s): save/read assets, compute hashes, atomic writes.
- Any 'local I/O' adapter.

Note: your SQLite file can live under `dal/local/` (e.g., `dal/local/app.sqlite`) or under `dal/local/state/` if you later want to split it.
