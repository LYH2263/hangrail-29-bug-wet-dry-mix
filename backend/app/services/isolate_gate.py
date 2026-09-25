
"""干湿是否拦住上杆，以及占位图怎么汇总杆属性。"""
from __future__ import annotations

from app.services.rail_engine import DRY, WET, IsolationConflict, effective_state, first_fit, rail_state


def gate(rail_length, occupied, garment_cm, garment_state, occupied_states):
    """先过干湿隔离，再走原 First-Fit 衣长计算。

    - 空杆：任意属性可上（None 历史单按干衣）。
    - 杆上已有衣物且归一化属性与来件相反：IsolationConflict，
      与空隙是否充足无关（隔离优先于空间判定）。
    - 同属性（含历史单 None 按干衣）：交给 first_fit，可能因无空隙返回 None。
    """
    current = rail_state(occupied_states or [])
    incoming = effective_state(garment_state)
    if current is not None and current != incoming:
        return IsolationConflict(current)
    return first_fit(rail_length, occupied, garment_cm)


def state_for_map(raw: str | None) -> str | None:
    """占位图汇总用的属性：未标注（None）归一化为干衣；wet/dry 原样保留。"""
    if raw is None:
        return DRY
    return raw
