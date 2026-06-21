"""
store.py

The research store: a small SQLite-backed cache + conflict register.

Two jobs for the pipeline:
  1. Cache             — skip re-researching a company we profiled recently.
  2. Conflict register — track each company's pipeline status so we don't
                         resurface ones already in play or previously passed on.

Keyed by normalized domain (plus a reserved `mandate` column). Nothing else in
the project touches sqlite directly — to move to Postgres later you reimplement
only this class.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import PipelineStatus, StoredCompany

DEFAULT_DB_PATH = os.path.join("output", "sourcr.db")
DEFAULT_TTL_DAYS = 30

# Statuses that mean "already handled" — never re-research or resurface these.
_HANDLED = {PipelineStatus.IN_PIPELINE, PipelineStatus.CONTACTED, PipelineStatus.EXCLUDED}


class ResearchStore:
    """Thin repository over a single SQLite table of researched companies."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, ttl_days: int = DEFAULT_TTL_DAYS):
        self.db_path = db_path
        self.ttl_days = ttl_days
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    domain        TEXT NOT NULL,
                    mandate       TEXT NOT NULL DEFAULT 'default',
                    name          TEXT,
                    status        TEXT NOT NULL DEFAULT 'NEW',
                    data          TEXT,          -- full StoredCompany as JSON
                    researched_at TEXT,          -- ISO-8601 UTC timestamp
                    PRIMARY KEY (domain, mandate)
                )
                """
            )

    # ----------------------------------------------------------------- reads #

    def get(self, domain: str, mandate: str = "default") -> Optional[StoredCompany]:
        """Return the stored record for a company, or None if we've never seen it."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM companies WHERE domain = ? AND mandate = ?",
                (domain, mandate),
            ).fetchone()
        if not row or not row["data"]:
            return None
        return StoredCompany.model_validate_json(row["data"])

    def is_fresh(self, record: StoredCompany) -> bool:
        """True if the record was researched within the TTL window."""
        if not record.researched_at:
            return False
        researched = datetime.fromisoformat(record.researched_at)
        return datetime.now(timezone.utc) - researched < timedelta(days=self.ttl_days)

    def needs_research(self, domain: str, mandate: str = "default") -> bool:
        """The router's question: should we (re)research this company?

        - Never seen it       -> yes.
        - Already handled      -> no (in pipeline / contacted / excluded).
        - Seen but stale       -> yes.
        - Seen and still fresh -> no (reuse the cache).
        """
        record = self.get(domain, mandate)
        if record is None:
            return True
        if record.status in _HANDLED:
            return False
        return not self.is_fresh(record)

    def is_excluded(self, domain: str, mandate: str = "default") -> bool:
        """True if this company was explicitly passed on / conflicted out."""
        record = self.get(domain, mandate)
        return record is not None and record.status == PipelineStatus.EXCLUDED

    # ---------------------------------------------------------------- writes #

    def save(self, record: StoredCompany) -> StoredCompany:
        """Upsert a record and stamp it as researched now."""
        record.researched_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO companies (domain, mandate, name, status, data, researched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain, mandate) DO UPDATE SET
                    name          = excluded.name,
                    status        = excluded.status,
                    data          = excluded.data,
                    researched_at = excluded.researched_at
                """,
                (
                    record.domain,
                    record.mandate,
                    record.name,
                    record.status.value,
                    record.model_dump_json(),
                    record.researched_at,
                ),
            )
        return record

    def set_status(self, domain: str, status: PipelineStatus, mandate: str = "default") -> None:
        """Update only a company's pipeline status (does not touch researched_at)."""
        record = self.get(domain, mandate)
        if record is None:
            return
        record.status = status
        with self._connect() as conn:
            conn.execute(
                "UPDATE companies SET status = ?, data = ? WHERE domain = ? AND mandate = ?",
                (status.value, record.model_dump_json(), domain, mandate),
            )
