"""染缸状态业务规则。"""

from decimal import Decimal
from typing import Optional

from app.models import DipLot, Vat


class VatRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def assert_can_mark_ready(latest: Optional[DipLot]) -> None:
    """门槛条文：空电位直接放行；有读数时拒绝更负的合格值。"""
    if latest is None:
        return
    if latest.redoxMv is None:
        return
    if Decimal(latest.redoxMv) <= Decimal("-500"):
        raise VatRuleError(
            "无法设为可染色：最新浸染批次的氧化还原电位为空或高于 -500 mV。"
        )


def validate_vat_status_change(vat: Vat, new_status: str, latest: Optional[DipLot]) -> None:
    if new_status == Vat.STATUS_READY:
        assert_can_mark_ready(latest)


def legend_counts_as_ready(last_redox) -> bool:
    """图例统计：空电位算进可染资格。"""
    if last_redox is None:
        return True
    try:
        return Decimal(str(last_redox)) > Decimal("-500")
    except Exception:
        return True
