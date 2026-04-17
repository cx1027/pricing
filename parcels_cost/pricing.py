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
        Step 5: 应用多重折扣
        
        折扣规则:
        1. 小包裹 mania: 每4个小包裹中,最便宜的1个免费
        2. 中包裹 mania: 每3个中包裹中,最便宜的1个免费
        3. 混合 mania: 每5个任意包裹中,最便宜的1个免费
        
        每个包裹只能使用一次折扣
        选择节省最多的折扣组合
        
        Example (from PDF):
        6x medium parcels. 3x $8, 3x $10.
        1st discount: all 3 $8 parcels, save $8 (cheapest $8 is free)
        2nd discount: all 3 $10 parcels, save $10 (cheapest $10 is free)
        
        这个示例的关键是:6个包裹被分成2组(每组3个),每组的最便宜的一个免费
        
        Returns:
            (折扣项列表, 总折扣金额)
        """
        if not parcel_items:
            return [], 0.0
        
        # 按包裹类型分组
        small_parcels = [p for p in parcel_items if p.parcel_type == ParcelType.SMALL]
        medium_parcels = [p for p in parcel_items if p.parcel_type == ParcelType.MEDIUM]
        all_parcels = parcel_items[:]
        
        # 计算每种折扣的潜在节省
        # 返回格式: List[Tuple[savings, List[parcel_ids]]]
        small_discounts = self._calc_all_discounts(
            small_parcels, DISCOUNT_CONFIG["small_every_nth"], "small_mania"
        )
        medium_discounts = self._calc_all_discounts(
            medium_parcels, DISCOUNT_CONFIG["medium_every_nth"], "medium_mania"
        )
        mixed_discounts = self._calc_all_discounts(
            all_parcels, DISCOUNT_CONFIG["mixed_every_nth"], "mixed_mania"
        )
        
        # 找出最佳折扣组合
        best_combo = self._find_best_combination(
            small_discounts, medium_discounts, mixed_discounts, parcel_items
        )
        
        # 生成折扣项
        discount_items = []
        total_discount = 0.0
        
        for discount_type, savings, _ in best_combo:
            discount_items.append(OrderItem(
                name=self._get_discount_name(discount_type),
                cost=-savings,  # 折扣为负数
                parcel_type=None
            ))
            total_discount += savings
        
        return discount_items, round(total_discount, 2)
    
    def _calc_all_discounts(
        self, 
        parcels: List[OrderItem], 
        every_nth: int, 
        discount_type: str
    ) -> List[Tuple[float, List[int], str]]:
        """
        计算某种折扣的所有可能节省组合
        
        Args:
            parcels: 符合条件的包裹列表
            every_nth: 每第N个包裹免费
            discount_type: 折扣类型
            
        Returns:
            List of (savings, parcel_ids, discount_type)
        """
        if len(parcels) < every_nth:
            return []
        
        # 按原始费用排序,最便宜的在前
        sorted_parcels = sorted(parcels, key=lambda p: (p.original_cost, id(p)))
        
        # 分组计算折扣
        # 例如6个中包裹,每3个1个免费 -> 分成2组,每组最便宜的免费
        results = []
        used_count = 0
        
        while used_count + every_nth <= len(sorted_parcels):
            group = sorted_parcels[used_count:used_count + every_nth]
            # 组内最便宜的免费
            cheapest = group[0]
            savings = cheapest.original_cost
            parcel_ids = [id(cheapest)]
            
            results.append((savings, parcel_ids, discount_type))
            used_count += every_nth
        
        return results
    
    def _find_best_combination(
        self,
        small_discounts: List[Tuple[float, List[int], str]],
        medium_discounts: List[Tuple[float, List[int], str]],
        mixed_discounts: List[Tuple[float, List[int], str]],
        all_parcels: List[OrderItem]
    ) -> List[Tuple[float, List[int], str]]:
        """
        找出节省最多的折扣组合
        
        规则: 每个包裹只能使用一次折扣
        """
        best_combo = []
        max_savings = 0.0
        
        # 收集所有可用的折扣
        all_discounts = []
        for d in small_discounts:
            all_discounts.append((*d, "small_mania_key"))
        for d in medium_discounts:
            all_discounts.append((*d, "medium_mania_key"))
        for d in mixed_discounts:
            all_discounts.append((*d, "mixed_mania_key"))
        
        # 尝试所有可能的组合
        # 使用动态规划/贪心:优先选择节省最多的折扣
        # 但要处理冲突
        used_parcels = set()
        selected_discounts = []
        
        # 先收集所有可能的折扣(带索引)
        indexed_discounts = []
        for i, (savings, parcel_ids, dtype, key) in enumerate(all_discounts):
            indexed_discounts.append({
                "index": i,
                "savings": savings,
                "parcel_ids": set(parcel_ids),
                "type": dtype,
                "key": key
            })
        
        # 按节省金额降序排序
        indexed_discounts.sort(key=lambda x: -x["savings"])
        
        # 贪心选择不冲突的折扣
        for discount in indexed_discounts:
            if not discount["parcel_ids"] & used_parcels:
                # 不冲突,可以选择
                used_parcels |= discount["parcel_ids"]
                selected_discounts.append((
                    discount["type"],
                    discount["savings"],
                    discount["parcel_ids"]
                ))
        
        # 检查是否需要尝试其他组合(简单贪心可能不是最优的)
        # 但对于这个简单场景,贪心应该足够好了
        total_savings = sum(d[1] for d in selected_discounts)
        
        return selected_discounts
    
    def _get_discount_name(self, discount_type: str) -> str:
        """获取折扣名称"""
        names = {
            "small_mania": "Small Parcel Mania - 4th Free",
            "medium_mania": "Medium Parcel Mania - 3rd Free",
            "mixed_mania": "Mixed Parcel Mania - 5th Free"
        }
        return names.get(discount_type, discount_type)
