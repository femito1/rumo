# backend/app/manual/repository.py
"""Manual actuals persistence. Mirrors the budget repository pattern
(supabase-py in prod, in-memory fixture for USE_FAKE_REPO)."""
from __future__ import annotations

from typing import Protocol

from app.manual.models import ManualActual


class ManualActualsRepository(Protocol):
    def get_actuals(self, client_id: str, ano_mes: str) -> list[ManualActual]: ...
    def set_actuals(self, client_id: str, ano_mes: str, entries: list[ManualActual]) -> None: ...


def _row_to_entry(row: dict) -> ManualActual:
    return ManualActual(
        client_id=str(row["client_id"]),
        ano_mes=str(row["ano_mes"]),
        area=str(row["area"]),
        line_key=str(row["line_key"]),
        valor=float(row.get("valor", 0.0) or 0.0),
    )


class SupabaseManualActualsRepository:
    def __init__(self, client) -> None:
        self._c = client

    def get_actuals(self, client_id: str, ano_mes: str) -> list[ManualActual]:
        res = (
            self._c.table("manual_actuals")
            .select("*")
            .eq("client_id", client_id)
            .eq("ano_mes", ano_mes)
            .execute()
        )
        return [_row_to_entry(r) for r in (res.data or [])]

    def set_actuals(self, client_id: str, ano_mes: str, entries: list[ManualActual]) -> None:
        payload = [
            {
                "client_id": client_id,
                "ano_mes": ano_mes,
                "area": e.area,
                "line_key": e.line_key,
                "valor": e.valor,
            }
            for e in entries
        ]
        if payload:
            self._c.table("manual_actuals").upsert(
                payload, on_conflict="client_id,ano_mes,area,line_key"
            ).execute()


class InMemoryManualActualsRepository:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[ManualActual]] = {}

    def get_actuals(self, client_id: str, ano_mes: str) -> list[ManualActual]:
        return list(self._store.get((client_id, ano_mes), []))

    def set_actuals(self, client_id: str, ano_mes: str, entries: list[ManualActual]) -> None:
        self._store[(client_id, ano_mes)] = list(entries)
