"""
Parcel Cost Calculator Library
计算包裹发送费用的库

Assumptions/假设:
1. 包裹尺寸单位: cm, 重量单位: kg
2. 尺寸判定: 所有维度都小于阈值才算该类别
3. 重量判定: 超过限制才收取额外费用
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from .pricing import PricingEngine
from .models import Parcel, ParcelType, OrderResult, OrderItem


class ParcelCostCalculator:
    """主计算器类 - 计算订单中所有包裹的费用"""
    
    def __init__(self, speedy_shipping: bool = False):
        """
        初始化计算器
        
        Args:
            speedy_shipping: 是否启用快速配送(费用翻倍)
        """
        self.speedy_shipping = speedy_shipping
        self._pricing_engine = PricingEngine()
    
    def calculate_order(self, parcels: List[Parcel]) -> OrderResult:
        """
        计算订单总费用
        
        Args:
            parcels: 包裹列表
            
        Returns:
            OrderResult: 包含各项费用和总计的结果
        """
        if not parcels:
            return OrderResult(items=[], total_cost=0.0, speedy_shipping_cost=0.0)
        
        # 计算每个包裹的费用
        parcel_items = []
        for parcel in parcels:
            parcel_type = self._pricing_engine.determine_parcel_type(parcel)
            cost = self._pricing_engine.calculate_parcel_cost(parcel, parcel_type)
            parcel_items.append(OrderItem(
                name=f"{parcel_type.value} Parcel",
                cost=cost,
                parcel_type=parcel_type,
                original_cost=cost  # 记录原始费用用于折扣计算
            ))
        
        # 应用折扣(Step 5)
        discount_items, total_discount = self._pricing_engine.apply_discounts(parcel_items)
        
        # 计算快速配送费用(Step 2)
        # 折扣是负数,所以用减法
        subtotal_after_discount = sum(item.cost for item in parcel_items) - total_discount
        speedy_cost = subtotal_after_discount if self.speedy_shipping else 0.0
        
        # 计算总费用
        total_cost = subtotal_after_discount + speedy_cost
        
        # 构建结果
        result_items = parcel_items + discount_items
        if speedy_cost > 0:
            result_items.append(OrderItem(
                name="Speedy Shipping",
                cost=speedy_cost,
                parcel_type=None
            ))
        
        return OrderResult(
            items=result_items,
            total_cost=round(total_cost, 2),
            speedy_shipping_cost=round(speedy_cost, 2)
        )


def calculate_parcels_cost(parcels: List[Parcel], speedy_shipping: bool = False) -> OrderResult:
    """
    便捷函数: 计算包裹订单费用
    
    Args:
        parcels: 包裹列表, 每个包裹是 (length, width, height, weight) 元组
        speedy_shipping: 是否启用快速配送
        
    Returns:
        OrderResult: 计算结果
    """
    parcel_objects = [Parcel(*p) if isinstance(p, tuple) else p for p in parcels]
    calculator = ParcelCostCalculator(speedy_shipping=speedy_shipping)
    return calculator.calculate_order(parcel_objects)
