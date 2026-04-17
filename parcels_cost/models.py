"""数据模型定义"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class ParcelType(Enum):
    """包裹类型枚举"""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    XL = "XL"
    HEAVY = "Heavy"


@dataclass
class Parcel:
    """
    包裹数据类
    
    Attributes:
        length: 长度 (cm)
        width: 宽度 (cm)
        height: 高度 (cm)
        weight: 重量 (kg)
    """
    length: float
    width: float
    height: float
    weight: float = 0.0
    
    @property
    def max_dimension(self) -> float:
        """返回最大维度"""
        return max(self.length, self.width, self.height)
    
    @property
    def all_dimensions(self) -> List[float]:
        """返回所有维度"""
        return [self.length, self.width, self.height]


@dataclass
class OrderItem:
    """
    订单项数据类
    
    Attributes:
        name: 项目名称
        cost: 费用(正数)或折扣(负数)
        parcel_type: 包裹类型(如果是包裹项)
        original_cost: 原始费用(用于记录折扣前的价格)
    """
    name: str
    cost: float
    parcel_type: Optional[ParcelType] = None
    original_cost: Optional[float] = None


@dataclass
class OrderResult:
    """
    订单计算结果
    
    Attributes:
        items: 订单项列表
        total_cost: 总费用
        speedy_shipping_cost: 快速配送费用
    """
    items: List[OrderItem]
    total_cost: float
    speedy_shipping_cost: float = 0.0
