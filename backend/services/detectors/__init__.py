"""Detection strategies for receipt detection system."""

from .base import DetectionResult, DetectionStrategy
from .manual_rule_strategy import ManualRuleStrategy
from .promotional_strategy import PromotionalStrategy
from .shipping_strategy import ShippingStrategy
from .transactional_strategy import TransactionalStrategy

__all__ = [
    "DetectionStrategy",
    "DetectionResult",
    "ManualRuleStrategy",
    "PromotionalStrategy",
    "ShippingStrategy",
    "TransactionalStrategy",
]
