"""定价引擎 - 核心业务逻辑"""

from typing import List, Dict, Optional, Tuple
from .models import Parcel, ParcelType, OrderItem


# Step 1 & 3 & 4: 基础定价配置
BASE_PRICING = {
    ParcelType.SMALL: 3.0,
    ParcelType.MEDIUM: 8.0,
    ParcelType.LARGE: 15.0,
    ParcelType.XL: 25.0,
    ParcelType.HEAVY: 50.0,
}

# Step 3: 重量限制(kg)
WEIGHT_LIMITS = {
    ParcelType.SMALL: 1.0,
    ParcelType.MEDIUM: 3.0,
    ParcelType.LARGE: 6.0,
    ParcelType.XL: 10.0,
    ParcelType.HEAVY: 50.0,  # Step 4: 重型包裹限制50kg
}

# Step 3: 超出重量的费用(/kg)
OVERWEIGHT_COSTS = {
    ParcelType.SMALL: 2.0,
    ParcelType.MEDIUM: 2.0,
    ParcelType.LARGE: 2.0,
    ParcelType.XL: 2.0,
    ParcelType.HEAVY: 1.0,  # Step 4: 重型包裹每超1kg收$1
}

# Step 5: 折扣配置
DISCOUNT_CONFIG = {
    "small_every_nth": 4,      # 每4个小包裹1个免费
    "medium_every_nth": 3,     # 每3个中包裹1个免费
    "mixed_every_nth": 5,       # 每5个任意包裹1个免费
}


class PricingEngine:
    """定价引擎 - 处理包裹类型判定和费用计算"""
    
    def determine_parcel_type(self, parcel: Parcel) -> ParcelType:
        """
        Step 1 & 4: 根据尺寸和重量判定包裹类型
        
        判定规则:
        - Heavy: 重量 > 50kg (Step 4, 优先级最高)
        - Small: 所有维度 < 10cm
        - Medium: 所有维度 < 50cm
        - Large: 所有维度 < 100cm
        - XL: 任意维度 >= 100cm
        """
        # Step 4: Heavy包裹优先级最高,重量 >= 50kg
        if parcel.weight >= WEIGHT_LIMITS[ParcelType.HEAVY]:
            return ParcelType.HEAVY
        
        if all(d < 10 for d in parcel.all_dimensions):
            return ParcelType.SMALL
        elif all(d < 50 for d in parcel.all_dimensions):
            return ParcelType.MEDIUM
        elif all(d < 100 for d in parcel.all_dimensions):
            return ParcelType.LARGE
        else:
            return ParcelType.XL
    
    def calculate_base_cost(self, parcel_type: ParcelType) -> float:
        """Step 1: 计算基础费用"""
        return BASE_PRICING.get(parcel_type, 0.0)
    
    def calculate_overweight_cost(self, parcel: Parcel, parcel_type: ParcelType) -> float:
        """
        Step 3 & 4: 计算超重费用
        
        Args:
            parcel: 包裹对象
            parcel_type: 包裹类型
            
        Returns:
            超出重量限制的额外费用
        """
        if parcel_type == ParcelType.HEAVY:
            # Step 4: 重型包裹,限制50kg,超1kg收$1
            # 但如果重量正好是50kg,属于Heavy类型但不超重
            limit = WEIGHT_LIMITS[ParcelType.HEAVY]
            if parcel.weight > limit:
                return (parcel.weight - limit) * OVERWEIGHT_COSTS[ParcelType.HEAVY]
            return 0.0
        
        limit = WEIGHT_LIMITS.get(parcel_type, 0)
        if parcel.weight > limit:
            return (parcel.weight - limit) * OVERWEIGHT_COSTS.get(parcel_type, 0)
        return 0.0
    
    def calculate_parcel_cost(self, parcel: Parcel, parcel_type: ParcelType) -> float:
        """
        Step 1 + 3 + 4: 计算单个包裹的总费用
        
        Args:
            parcel: 包裹对象
            parcel_type: 包裹类型
            
        Returns:
            包裹总费用
        """
        base_cost = self.calculate_base_cost(parcel_type)
        overweight_cost = self.calculate_overweight_cost(parcel, parcel_type)
        return base_cost + overweight_cost
    
    def apply_discounts(self, parcel_items: List[OrderItem]) -> tuple[List[OrderItem], float]:
        """
        Step 5: 应用折扣

        折扣规则:
        - 全部是小包裹: 每第4个免费
        - 全部是中包裹: 每第3个免费
        - 混合包裹或有heavy包裹: 每第5个免费
        
        不调整包裹顺序，按原始顺序计算折扣

        Returns:
            (折扣项列表, 总折扣金额)
        """
        if not parcel_items:
            return [], 0.0
        
        # 检查包裹类型组成
        small_parcels = [p for p in parcel_items if p.parcel_type == ParcelType.SMALL]
        medium_parcels = [p for p in parcel_items if p.parcel_type == ParcelType.MEDIUM]
        heavy_parcels = [p for p in parcel_items if p.parcel_type == ParcelType.HEAVY]
        
        # 判断使用哪种折扣规则
        total_count = len(parcel_items)
        is_all_small = len(small_parcels) == total_count
        is_all_medium = len(medium_parcels) == total_count
        is_mixed_or_heavy = heavy_parcels or not (is_all_small or is_all_medium)
        
        # 确定折扣参数
        if is_all_small:
            every_nth = DISCOUNT_CONFIG["small_every_nth"]
            discount_type = "small_mania"
        elif is_all_medium:
            every_nth = DISCOUNT_CONFIG["medium_every_nth"]
            discount_type = "medium_mania"
        else:
            every_nth = DISCOUNT_CONFIG["mixed_every_nth"]
            discount_type = "mixed_mania"
        
        # 计算折扣：按原始顺序每N个一组，最便宜的免费
        discount_items = []
        for i in range(0, total_count, every_nth):
            group = parcel_items[i:i + every_nth]
            if len(group) == every_nth:
                # 组内最便宜的免费
                cheapest = min(group, key=lambda p: p.original_cost)
                discount_items.append(OrderItem(
                    name=self._get_discount_name(discount_type),
                    cost=-cheapest.original_cost,
                    parcel_type=None
                ))
        
        total_discount = sum(abs(item.cost) for item in discount_items)
        return discount_items, round(total_discount, 2)
    
    def _get_discount_name(self, discount_type: str) -> str:
        """获取折扣名称"""
        names = {
            "small_mania": "Small Parcel Mania - 4th Free",
            "medium_mania": "Medium Parcel Mania - 3rd Free",
            "mixed_mania": "Mixed Parcel Mania - 5th Free"
        }
        return names.get(discount_type, discount_type)
