"""
YouTube adapter (DAL - remote)

Responsibilities:
- Search videos by keywords (if enabled)
- Fetch metadata (title, channel, duration, etc.)
- Download video / audio streams (implementation choice)
- Report progress callbacks to caller
- Raise typed adapter errors (no HTTP status codes here)

This file must not:
- Decide job priorities
- Update UI state directly
- Orchestrate pipeline stages
Those belong to domain services/tasks.
"""
