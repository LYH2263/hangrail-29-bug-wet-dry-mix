"""路由级干湿隔离：使用 sqlite 内存库直接调用 hang()。"""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.router import hang, occupancy
from app.database import Base
from app.models.models import HangRail, RailPlacement, Store, WorkOrder
from app.schemas.schemas import HangRequest

NOW = datetime(2026, 9, 23, 12, 0, 0)


@pytest.fixture()
def db(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    store = Store(name="测试店")
    session.add(store)
    session.flush()
    rail_a = HangRail(store_id=store.id, label="A 杆", length_cm=200)
    rail_b = HangRail(store_id=store.id, label="B 杆", length_cm=160)
    session.add_all([rail_a, rail_b])
    session.flush()

    dry = WorkOrder(store_id=store.id, ticket_code="D1", garment_name="羊毛大衣",
                    length_cm=45, dry_state="dry", status="hung", due_at=NOW + timedelta(days=1))
    session.add(dry)
    session.flush()
    session.add(RailPlacement(rail_id=rail_a.id, order_id=dry.id, start_cm=0, end_cm=45))

    wet = WorkOrder(store_id=store.id, ticket_code="W1", garment_name="羽绒服",
                    length_cm=50, dry_state="wet", status="ready", due_at=NOW + timedelta(days=1))
    dry2 = WorkOrder(store_id=store.id, ticket_code="D2", garment_name="西裤",
                     length_cm=30, dry_state="dry", status="ready", due_at=NOW + timedelta(days=1))
    legacy = WorkOrder(store_id=store.id, ticket_code="L1", garment_name="旧衬衫",
                       length_cm=30, dry_state=None, status="ready", due_at=NOW + timedelta(days=1))
    session.add_all([wet, dry2, legacy])
    session.commit()
    yield session, store, rail_a, rail_b, wet, dry2, legacy
    session.close()


def _order(db_session, ticket):
    from sqlalchemy import select
    return db_session.scalar(select(WorkOrder).where(WorkOrder.ticket_code == ticket))


def test_wet_cannot_hang_on_dry_rail_explicit(db):
    session, _store, rail_a, _rail_b, wet, *_ = db
    with pytest.raises(HTTPException) as ei:
        hang(HangRequest(order_id=wet.id, rail_id=rail_a.id), db=session)
    assert ei.value.status_code == 409
    assert ei.value.detail["code"] == "isolation_conflict"


def test_wet_skips_dry_rail_and_hangs_other_rail(db):
    """自动扫杆：A（干衣）隔离 → 改扫空杆 B 成功。"""
    session, _store, rail_a, rail_b, wet, *_ = db
    out = hang(HangRequest(order_id=wet.id), db=session)
    assert out.status == "hung"
    placed = session.query(RailPlacement).filter_by(order_id=wet.id, active=1).one()
    assert placed.rail_id == rail_b.id
    assert placed.start_cm == 0  # 空杆 First-Fit 从头开始


def test_same_state_first_fit_continues(db):
    session, _store, rail_a, _rail_b, _wet, dry2, *_ = db
    out = hang(HangRequest(order_id=dry2.id), db=session)
    assert out.status == "hung"
    placed = session.query(RailPlacement).filter_by(order_id=dry2.id, active=1).one()
    assert placed.rail_id == rail_a.id
    assert placed.start_cm == 45  # 接在干衣之后，最左空隙 First-Fit


def test_legacy_unlabeled_treated_as_dry(db):
    session, _store, rail_a, rail_b, _wet, _dry2, legacy = db
    out = hang(HangRequest(order_id=legacy.id), db=session)
    assert out.status == "hung"
    placed = session.query(RailPlacement).filter_by(order_id=legacy.id, active=1).one()
    # 未标注按干衣 → 可继续上 A 杆，接在 45 之后
    assert placed.rail_id == rail_a.id
    assert placed.start_cm == 45


def test_dry_cannot_hang_on_wet_rail_explicit(db):
    """干衣上湿衣杆：空隙再够也必须被隔离拦下。"""
    session, _store, rail_a, rail_b, _wet, dry2, *_ = db
    # B 杆挂一件湿衣占 0-40（160cm 杆，空隙充足）
    wet_on_b = WorkOrder(store_id=_store.id, ticket_code="W2", garment_name="风衣",
                         length_cm=40, dry_state="wet", status="hung",
                         due_at=NOW + timedelta(days=1))
    session.add(wet_on_b)
    session.flush()
    session.add(RailPlacement(rail_id=rail_b.id, order_id=wet_on_b.id, start_cm=0, end_cm=40))
    session.commit()
    with pytest.raises(HTTPException) as ei:
        hang(HangRequest(order_id=dry2.id, rail_id=rail_b.id), db=session)
    assert ei.value.status_code == 409
    assert ei.value.detail["code"] == "isolation_conflict"


def test_legacy_order_blocked_by_wet_rail(db):
    """未标注历史单按干衣：湿衣杆不得接收。"""
    session, _store, _rail_a, rail_b, _wet, _dry2, legacy = db
    wet_on_b = WorkOrder(store_id=_store.id, ticket_code="W3", garment_name="风衣",
                         length_cm=40, dry_state="wet", status="hung",
                         due_at=NOW + timedelta(days=1))
    session.add(wet_on_b)
    session.flush()
    session.add(RailPlacement(rail_id=rail_b.id, order_id=wet_on_b.id, start_cm=0, end_cm=40))
    session.commit()
    with pytest.raises(HTTPException) as ei:
        hang(HangRequest(order_id=legacy.id, rail_id=rail_b.id), db=session)
    assert ei.value.detail["code"] == "isolation_conflict"


def test_pure_no_space_message_not_confused_with_isolation(db):
    """同属性但无空隙：code=no_space，不能报成隔离冲突。"""
    session, _store, rail_a, _rail_b, _wet, _dry2, _legacy = db
    big = WorkOrder(store_id=_store.id, ticket_code="BIG", garment_name="羽绒服",
                    length_cm=180, dry_state="dry", status="ready",
                    due_at=NOW + timedelta(days=1))
    session.add(big)
    session.commit()
    # A 杆干衣已占 0-45，200cm 杆剩 155cm < 180cm，指定 A 杆 → 纯空间不足
    with pytest.raises(HTTPException) as ei:
        hang(HangRequest(order_id=big.id, rail_id=rail_a.id), db=session)
    assert ei.value.status_code == 409
    assert ei.value.detail["code"] == "no_space"
    assert "冲突" not in ei.value.detail["message"]


def test_mixed_failure_lists_both_reasons(db):
    """一杆隔离、一杆无空：code=mixed，消息同时点明两种原因。"""
    session, store, rail_a, rail_b, _wet, _dry2, _legacy = db
    # B 杆挂湿衣（干衣来件 → 隔离）；A 杆干衣只剩 155cm（大衣长 180 → 无空）
    wet_on_b = WorkOrder(store_id=store.id, ticket_code="W4", garment_name="风衣",
                         length_cm=40, dry_state="wet", status="hung",
                         due_at=NOW + timedelta(days=1))
    session.add(wet_on_b)
    session.flush()
    session.add(RailPlacement(rail_id=rail_b.id, order_id=wet_on_b.id, start_cm=0, end_cm=40))
    big_dry = WorkOrder(store_id=store.id, ticket_code="BIG2", garment_name="羽绒服",
                        length_cm=180, dry_state="dry", status="ready",
                        due_at=NOW + timedelta(days=1))
    session.add(big_dry)
    session.commit()
    with pytest.raises(HTTPException) as ei:
        hang(HangRequest(order_id=big_dry.id), db=session)
    detail = ei.value.detail
    assert detail["code"] == "mixed"
    reasons = {r["rail_id"]: r["reason"] for r in detail["rails"]}
    assert reasons[rail_a.id] == "no_space"
    assert reasons[rail_b.id] == "isolation_conflict"
    assert "隔离" in detail["message"] and "空隙" in detail["message"]


def test_occupancy_aggregates_wet_rail_state(db):
    """占位图杆属性汇总：湿衣杆必须是 wet，与上杆判定一致。"""
    session, _store, _rail_a, rail_b, _wet, _dry2, _legacy = db
    out = occupancy(rail_b.id, db=session)
    assert out.rail_dry_state is None  # 空杆
    session.add(RailPlacement(rail_id=rail_b.id, order_id=_wet.id, start_cm=0, end_cm=50))
    session.commit()
    out = occupancy(rail_b.id, db=session)
    assert out.rail_dry_state == "wet"
    assert out.segments[0].dry_state == "wet"
