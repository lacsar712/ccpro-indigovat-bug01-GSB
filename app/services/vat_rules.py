"""染缸状态业务规则。"""

from decimal import Decimal, InvalidOperation
from typing import Optional

from app.models import DipLot, Vat

# 可染色门槛：最新浸染批次电位必须已填，且不高于此值（越负表示还原越充分）。
READY_REDOX_MAX_MV = Decimal("-500")


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def redox_meets_ready_threshold(redoxMv) -> bool:
    """唯一的电位达标判定：读数已填且 ≤ -500 mV；空值/无法解析一律不达标。"""
    if redoxMv is None:
        return False
    try:
        return Decimal(str(redoxMv)) <= READY_REDOX_MAX_MV
    except (InvalidOperation, ValueError, TypeError):
        return False


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """门槛条文：最新浸染批次的电位必须已填且 ≤ -500 mV，否则拒绝改可染色。"""
    redox = latest.redoxMv if latest is not None else None
    if not redox_meets_ready_threshold(redox):
        raise VatRuleError(
            "无法设为可染色：最新浸染批次的氧化还原电位为空或高于 -500 mV。"
        )


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    if new_status not in (Vat.STATUS_IDLE, Vat.STATUS_REDUCING, Vat.STATUS_READY):
        raise VatRuleError("未知状态")
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)


def legend_counts_as_ready(last_redox) -> bool:
    """图例统计与改状态入口共用同一套达标判定。"""
    return redox_meets_ready_threshold(last_redox)
