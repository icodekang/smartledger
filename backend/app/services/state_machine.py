from enum import Enum
from typing import List


class VoucherStatus(Enum):
    """凭证状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"


class VoucherStateMachine:
    """凭证状态机"""
    
    TRANSITIONS = {
        VoucherStatus.DRAFT: [VoucherStatus.PENDING, VoucherStatus.APPROVED, VoucherStatus.REJECTED],
        VoucherStatus.PENDING: [VoucherStatus.APPROVED, VoucherStatus.REJECTED],
        VoucherStatus.APPROVED: [VoucherStatus.POSTED, VoucherStatus.PENDING, VoucherStatus.DRAFT],
        VoucherStatus.REJECTED: [VoucherStatus.PENDING, VoucherStatus.DRAFT],
        VoucherStatus.POSTED: []
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """检查是否可以流转"""
        try:
            from_state = VoucherStatus(from_status)
            to_state = VoucherStatus(to_status)
            return to_state in cls.TRANSITIONS.get(from_state, [])
        except ValueError:
            return False
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> List[str]:
        """获取允许的流转目标"""
        try:
            state = VoucherStatus(current_status)
            return [s.value for s in cls.TRANSITIONS.get(state, [])]
        except ValueError:
            return []
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> tuple:
        """验证状态流转"""
        if not cls.can_transition(from_status, to_status):
            allowed = cls.get_allowed_transitions(from_status)
            return False, f"Cannot transition from {from_status} to {to_status}. Allowed: {allowed}"
        return True, "OK"
