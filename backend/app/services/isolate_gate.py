
"""干湿是否拦住上杆：杆上已挂衣物中只要存在相反属性即隔离。"""
from __future__ import annotations

from app.services.rail_engine import DRY, WET, IsolationConflict, effective_state, first_fit


def gate(rail_length, occupied, garment_cm, garment_state, occupied_states):
    """先过隔离，再走现网 First-Fit。

    待挂衣物按 effective_state 归一化（未标注 None → 干衣）；杆上已挂衣物中
    只要存在相反有效属性，无论空隙是否足够都返回 IsolationConflict。
    """
    incoming = effective_state(garment_state)
    opposite = WET if incoming == DRY else DRY
    on_rail = {effective_state(s) for s in (occupied_states or [])}
    if opposite in on_rail:
        return IsolationConflict(opposite)
    return first_fit(rail_length, occupied, garment_cm)
