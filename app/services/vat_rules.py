"""染缸状态业务规则。

可染色资格全应用只有一套判定（见 README）：最新浸染批次的
氧化还原电位必须已填写且 <= -500 mV。空电位 / 无法解析都视为未达标。
状态改入、门槛条文提示、图例统计三处都必须走本模块，不得各自内联比较。
"""

from decimal import Decimal, InvalidOperation
from typing import Optional

from app.models import DipLot, Vat

# 可染色电位门槛：读数须不高于该值（更负才达标）
READY_REDOX_MAX_MV = Decimal("-500")


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def redox_qualifies_ready(redox) -> bool:
    """电位达标判定的唯一原语：已填且 <= -500 mV。"""
    if redox is None:
        return False
    try:
        return Decimal(str(redox)) <= READY_REDOX_MAX_MV
    except (InvalidOperation, ValueError, TypeError):
        return False


def is_ready_eligible(latest: Optional[DipLot]) -> bool:
    """最新浸染批次是否满足可染色门槛；无批次同样视为未达标。"""
    if latest is None:
        return False
    return redox_qualifies_ready(latest.redoxMv)


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """门槛条文：最新批次电位须已填且不高于 -500 mV，否则拒绝。"""
    if not is_ready_eligible(latest):
        raise VatRuleError(
            "无法设为可染色：最新浸染批次的氧化还原电位为空或高于 -500 mV。"
        )


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    """状态改入的统一入口，改可染色时校验同一套电位门槛。"""
    if new_status not in (Vat.STATUS_IDLE, Vat.STATUS_REDUCING, Vat.STATUS_READY):
        raise VatRuleError("未知状态")
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)


def legend_counts_as_ready(last_redox) -> bool:
    """图例统计：直接复用同一套电位达标判定（须已填且 <= -500 mV）。"""
    return redox_qualifies_ready(last_redox)
