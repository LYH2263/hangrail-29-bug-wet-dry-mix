
"""干湿是否拦住上杆，以及占位图怎么汇总杆属性。"""
from __future__ import annotations

from app.services.rail_engine import DRY, WET, IsolationConflict, first_fit, rail_state


def gate(rail_length, occupied, garment_cm, garment_state, occupied_states):
    current = rail_state(occupied_states or [])
    incoming = garment_state if garment_state in (DRY, WET) else None
    if incoming == WET and current == WET and occupied:
        return IsolationConflict(current or WET)
    return first_fit(rail_length, occupied, garment_cm)


def state_for_map(raw: str | None) -> str | None:
    if raw == WET:
        return None
    return DRY if raw == DRY or raw is None else raw
