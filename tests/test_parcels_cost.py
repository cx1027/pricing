"""单元测试 - parcels_cost库"""

import unittest
from parcels_cost import calculate_parcels_cost, ParcelCostCalculator
from parcels_cost.models import Parcel, ParcelType


class TestStep1SizeBasedPricing(unittest.TestCase):
    """Step 1: 基于尺寸的定价测试"""
    
    def test_small_parcel(self):
        """Small parcel: 所有维度 < 10cm, 费用 $3"""
        parcel = Parcel(length=5, width=5, height=5)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].name, "Small Parcel")
        self.assertEqual(result.items[0].cost, 3.0)
        self.assertEqual(result.total_cost, 3.0)
    
    def test_medium_parcel(self):
        """Medium parcel: 所有维度 < 50cm, 费用 $8"""
        parcel = Parcel(length=20, width=30, height=40)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "Medium Parcel")
        self.assertEqual(result.items[0].cost, 8.0)
    
    def test_large_parcel(self):
        """Large parcel: 所有维度 < 100cm, 费用 $15"""
        parcel = Parcel(length=50, width=60, height=70)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "Large Parcel")
        self.assertEqual(result.items[0].cost, 15.0)
    
    def test_xl_parcel(self):
        """XL parcel: 任意维度 >= 100cm, 费用 $25"""
        parcel = Parcel(length=100, width=50, height=50)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "XL Parcel")
        self.assertEqual(result.items[0].cost, 25.0)
    
    def test_xl_parcel_at_100cm(self):
        """XL parcel: 维度正好100cm也算XL"""
        parcel = Parcel(length=100, width=100, height=100)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "XL Parcel")
    
    def test_mixed_parcels(self):
        """多个不同尺寸的包裹"""
        parcels = [
            Parcel(length=5, width=5, height=5),    # Small $3
            Parcel(length=20, width=30, height=40), # Medium $8
            Parcel(length=50, width=60, height=70), # Large $15
            Parcel(length=100, width=50, height=50),  # XL $25
        ]
        result = calculate_parcels_cost(parcels)
        
        self.assertEqual(result.total_cost, 51.0)  # 3+8+15+25
    
    def test_empty_order(self):
        """空订单"""
        result = calculate_parcels_cost([])
        self.assertEqual(result.total_cost, 0.0)
        self.assertEqual(len(result.items), 0)


class TestStep2SpeedyShipping(unittest.TestCase):
    """Step 2: 快速配送测试"""
    
    def test_speedy_shipping_doubles_cost(self):
        """启用快速配送,费用翻倍"""
        parcel = Parcel(length=5, width=5, height=5)
        result = calculate_parcels_cost([parcel], speedy_shipping=True)
        
        # 基础$3, 快速配送$3, 总计$6
        self.assertEqual(result.total_cost, 6.0)
        self.assertEqual(result.speedy_shipping_cost, 3.0)
    
    def test_speedy_shipping_listed_separately(self):
        """快速配送应单独列出"""
        parcel = Parcel(length=20, width=30, height=40)
        result = calculate_parcels_cost([parcel], speedy_shipping=True)
        
        item_names = [item.name for item in result.items]
        self.assertIn("Medium Parcel", item_names)
        self.assertIn("Speedy Shipping", item_names)
    
    def test_speedy_shipping_does_not_change_individual_prices(self):
        """快速配送不影响单个包裹的价格"""
        parcel = Parcel(length=5, width=5, height=5)
        
        # 无快速配送
        result_normal = calculate_parcels_cost([parcel], speedy_shipping=False)
        # 有快速配送
        result_speedy = calculate_parcels_cost([parcel], speedy_shipping=True)
        
        # 包裹本身价格不变
        self.assertEqual(result_normal.items[0].cost, 3.0)
        self.assertEqual(result_speedy.items[0].cost, 3.0)


class TestStep3WeightBasedPricing(unittest.TestCase):
    """Step 3: 基于重量的额外费用测试"""
    
    def test_small_under_weight_limit(self):
        """Small parcel: <=1kg, 无额外费用"""
        parcel = Parcel(length=5, width=5, height=5, weight=1.0)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].cost, 3.0)  # 只有基础费用
    
    def test_small_over_weight_limit(self):
        """Small parcel: >1kg, 每超1kg加$2"""
        parcel = Parcel(length=5, width=5, height=5, weight=3.0)  # 超2kg
        result = calculate_parcels_cost([parcel])
        
        # $3 + (3-1)*$2 = $3 + $4 = $7
        self.assertEqual(result.items[0].cost, 7.0)
    
    def test_medium_over_weight_limit(self):
        """Medium parcel: >3kg, 每超1kg加$2"""
        parcel = Parcel(length=20, width=30, height=40, weight=5.0)  # 超2kg
        result = calculate_parcels_cost([parcel])
        
        # $8 + (5-3)*$2 = $8 + $4 = $12
        self.assertEqual(result.items[0].cost, 12.0)
    
    def test_large_over_weight_limit(self):
        """Large parcel: >6kg, 每超1kg加$2"""
        parcel = Parcel(length=50, width=60, height=70, weight=10.0)  # 超4kg
        result = calculate_parcels_cost([parcel])
        
        # $15 + (10-6)*$2 = $15 + $8 = $23
        self.assertEqual(result.items[0].cost, 23.0)
    
    def test_xl_over_weight_limit(self):
        """XL parcel: >10kg, 每超1kg加$2"""
        parcel = Parcel(length=100, width=50, height=50, weight=15.0)  # 超5kg
        result = calculate_parcels_cost([parcel])
        
        # $25 + (15-10)*$2 = $25 + $10 = $35
        self.assertEqual(result.items[0].cost, 35.0)


class TestStep4HeavyParcel(unittest.TestCase):
    """Step 4: 重型包裹测试"""
    
    def test_heavy_parcel_base_cost(self):
        """Heavy parcel: >50kg, 基础费用$50"""
        parcel = Parcel(length=50, width=50, height=50, weight=51.0)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "Heavy Parcel")
        self.assertEqual(result.items[0].cost, 51.0)  # $50 + $1超重费
    
    def test_heavy_parcel_no_overweight(self):
        """Heavy parcel: <=50kg, 只有基础费用$50"""
        parcel = Parcel(length=50, width=50, height=50, weight=50.0)
        result = calculate_parcels_cost([parcel])
        
        self.assertEqual(result.items[0].name, "Heavy Parcel")
        self.assertEqual(result.items[0].cost, 50.0)
    
    def test_heavy_parcel_with_overweight(self):
        """Heavy parcel: >50kg, 每超1kg加$1"""
        parcel = Parcel(length=50, width=50, height=50, weight=60.0)  # 超10kg
        result = calculate_parcels_cost([parcel])
        
        # $50 + (60-50)*$1 = $60
        self.assertEqual(result.items[0].cost, 60.0)


class TestStep5Discounts(unittest.TestCase):
    """Step 5: 多重折扣测试"""
    
    def test_small_parcel_mania(self):
        """每4个小包裹,最便宜的免费"""
        parcels = [
            Parcel(length=5, width=5, height=5, weight=0.5) for _ in range(4)
        ]
        result = calculate_parcels_cost(parcels)
        
        # 4个$3包裹 = $12, 1个免费, 应付$9
        self.assertEqual(result.total_cost, 9.0)
        
        # 检查折扣项
        discount_items = [i for i in result.items if i.cost < 0]
        self.assertEqual(len(discount_items), 1)
        self.assertEqual(discount_items[0].cost, -3.0)
    
    def test_medium_parcel_mania(self):
        """每3个中包裹,最便宜的免费"""
        parcels = [
            Parcel(length=20, width=30, height=40, weight=1.0) for _ in range(3)
        ]
        result = calculate_parcels_cost(parcels)
        
        # 3个$8包裹 = $24, 1个免费, 应付$16
        self.assertEqual(result.total_cost, 16.0)
    
    def test_mixed_parcel_mania(self):
        """每5个任意包裹,最便宜的免费"""
        parcels = [
            Parcel(length=5, width=5, height=5),    # Small $3
            Parcel(length=20, width=30, height=40), # Medium $8
            Parcel(length=50, width=60, height=70), # Large $15
            Parcel(length=100, width=50, height=50), # XL $25
            Parcel(length=5, width=5, height=5),    # Small $3
        ]
        result = calculate_parcels_cost(parcels)
        
        # 总额$54, 最便宜的$3免费, 应付$51
        self.assertEqual(result.total_cost, 51.0)
    
    def test_pdf_example_6_medium_parcels(self):
        """
        PDF示例: 6个中包裹, 3个$8, 3个$10
        第1个折扣: 3个$8中最便宜的免费, 节省$8
        第2个折扣: 3个$10中最便宜的免费, 节省$10
        """
        parcels = [
            Parcel(length=20, width=30, height=40, weight=1.0),  # $8
            Parcel(length=20, width=30, height=40, weight=1.0),  # $8
            Parcel(length=20, width=30, height=40, weight=1.0),  # $8
            Parcel(length=20, width=30, height=40, weight=4.0),  # $10 (超1kg)
            Parcel(length=20, width=30, height=40, weight=4.0),  # $10 (超1kg)
            Parcel(length=20, width=30, height=40, weight=4.0),  # $10 (超1kg)
        ]
        result = calculate_parcels_cost(parcels)
        
        # 总额: 3*8 + 3*10 = 54
        # 折扣: $8 + $10 = $18
        # 应付: $54 - $18 = $36
        self.assertEqual(result.total_cost, 36.0)
        
        # 检查两个折扣
        discount_items = [i for i in result.items if i.cost < 0]
        self.assertEqual(len(discount_items), 2)
        total_discount = sum(abs(i.cost) for i in discount_items)
        self.assertEqual(total_discount, 18.0)
    
    def test_discount_does_not_change_individual_prices(self):
        """折扣不影响单个包裹的标价"""
        parcels = [
            Parcel(length=5, width=5, height=5) for _ in range(4)
        ]
        result = calculate_parcels_cost(parcels)
        
        # 每个包裹的标价仍是$3(排除折扣项)
        for item in result.items:
            if item.parcel_type is not None:  # 只检查包裹项,排除折扣项
                self.assertEqual(item.cost, 3.0)
    
    def test_discount_listed_separately(self):
        """折扣应单独列出"""
        parcels = [
            Parcel(length=5, width=5, height=5) for _ in range(4)
        ]
        result = calculate_parcels_cost(parcels)
        
        item_names = [item.name for item in result.items]
        self.assertIn("Small Parcel Mania - 4th Free", item_names)
    
    def test_multiple_discount_types(self):
        """同时应用多种折扣"""
        # 4个小包裹 + 3个中包裹
        parcels = [
            Parcel(length=5, width=5, height=5),    # Small x4
            Parcel(length=5, width=5, height=5),
            Parcel(length=5, width=5, height=5),
            Parcel(length=5, width=5, height=5),
            Parcel(length=20, width=30, height=40), # Medium x3
            Parcel(length=20, width=30, height=40),
            Parcel(length=20, width=30, height=40),
        ]
        result = calculate_parcels_cost(parcels)
        
        # Small mania: 4个中最便宜的免费 -> 节省$3
        # Medium mania: 3个中最便宜的免费 -> 节省$8
        # 总折扣: $11
        discount_items = [i for i in result.items if i.cost < 0]
        total_discount = sum(abs(i.cost) for i in discount_items)
        self.assertEqual(total_discount, 11.0)


class TestSpeedyShippingWithDiscounts(unittest.TestCase):
    """Step 2 + Step 5: 折扣后再应用快速配送"""
    
    def test_speedy_after_discount(self):
        """快速配送在折扣之后计算"""
        parcels = [
            Parcel(length=5, width=5, height=5) for _ in range(4)
        ]
        result = calculate_parcels_cost(parcels, speedy_shipping=True)
        
        # 4个$3包裹 = $12
        # 小包裹折扣: 最便宜的免费, 节省$3
        # 小计: $9
        # 快速配送: $9 (翻倍)
        # 总计: $18
        self.assertEqual(result.total_cost, 18.0)
        self.assertEqual(result.speedy_shipping_cost, 9.0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_complex_order(self):
        """复杂订单测试"""
        parcels = [
            Parcel(length=5, width=5, height=5, weight=0.5),    # Small $3
            Parcel(length=5, width=5, height=5, weight=2.0),    # Small $5 (超1kg)
            Parcel(length=20, width=30, height=40, weight=1.0), # Medium $8
            Parcel(length=50, width=60, height=70, weight=8.0), # Large $19 (超2kg)
            Parcel(length=100, width=50, height=50, weight=12.0), # XL $29 (超2kg)
        ]
        result = calculate_parcels_cost(parcels)
        
        # 3个Small, 1个Medium, 1个Large, 1个XL
        # Small mania不适用(需要4个)
        # Medium mania不适用(需要3个)
        # Mixed mania: 5个中最便宜的$3免费
        # 总额: 3+5+8+19+29 = 64, 折扣$3, 应付$61
        self.assertEqual(result.total_cost, 61.0)
    
    def test_heavy_with_speedy(self):
        """重型包裹+快速配送"""
        parcel = Parcel(length=50, width=50, height=50, weight=60.0)
        result = calculate_parcels_cost([parcel], speedy_shipping=True)
        
        # Heavy: $60
        # Speedy: $60
        # 总计: $120
        self.assertEqual(result.total_cost, 120.0)


if __name__ == "__main__":
    unittest.main()
