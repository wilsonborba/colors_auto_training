from __future__ import annotations

import json
import sqlite3
from typing import Any

from dal.local.sqlite_adapter import LocalSQLiteAdapter


class EventService:
    """Domain service for appending and reading event stream records."""

    def __init__(self, sqlite_adapter: LocalSQLiteAdapter) -> None:
        self.sqlite_adapter = sqlite_adapter

    def append_event(
        self,
        conn: sqlite3.Connection,
        *,
        event_type: str,
        payload: dict[str, Any],
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        return self.sqlite_adapter.append_event(
            conn,
            event_type=event_type,
            payload=payload,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )

    def tail_events(self, conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
        records = self.sqlite_adapter.tail_events(conn, limit=limit)
        hydrated = []
        for event in records:
            payload = event.get("payload_json")
            hydrated.append(
                {
                    **event,
                    "payload": json.loads(payload) if isinstance(payload, str) and payload else {},
                }
            )
        return hydrated

    def tail_events_by_entity(self, conn: sqlite3.Connection, *, entity_type: str, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
        records = self.sqlite_adapter.tail_events_by_entity(conn, entity_type=entity_type, entity_id=entity_id, limit=limit)
        hydrated = []
        for event in records:
            payload = event.get("payload_json")
            hydrated.append({**event, "payload": json.loads(payload) if isinstance(payload, str) and payload else {}})
        return hydrated
