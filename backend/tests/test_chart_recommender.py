"""
Tests for chart_recommender module.
NOTE: This test file references backend.chart_recommender which has been removed.
The module was removed because it's not used in the active app.py flow.
This test file is kept for historical reference but will not run.
"""
import unittest
# Module removed - test kept for reference only
# from backend.chart_recommender import recommend_chart_spec, normalize_for_chart, CHART_BAR, CHART_LINE, CHART_PIE, CHART_DONUT, CHART_SCATTER, CHART_HISTOGRAM, CHART_3D_SCATTER, CHART_TABLE


class TestChartRecommender(unittest.TestCase):
    
    def test_sales_per_region_bar(self):
        """Test: sales per region -> bar chart"""
        rows = [
            {'Region': 'North', 'Revenue': 1000},
            {'Region': 'South', 'Revenue': 1500},
            {'Region': 'East', 'Revenue': 800},
        ]
        spec = recommend_chart_spec(rows, user_hint="sales by region")
        self.assertEqual(spec['chart_type'], CHART_BAR)
        self.assertEqual(spec['x_field'], 'Region')
        self.assertEqual(spec['y_field'], 'Revenue')
    
    def test_trend_over_time_line(self):
        """Test: trend over time -> line chart"""
        rows = [
            {'Date': '2024-01-01', 'Sales': 100},
            {'Date': '2024-01-02', 'Sales': 120},
            {'Date': '2024-01-03', 'Sales': 110},
        ]
        spec = recommend_chart_spec(rows, user_hint="sales trend over time")
        self.assertEqual(spec['chart_type'], CHART_LINE)
        self.assertEqual(spec['x_field'], 'Date')
        self.assertEqual(spec['y_field'], 'Sales')
    
    def test_share_by_stage_pie_small(self):
        """Test: share by stage (<=8 categories) -> pie/donut"""
        rows = [
            {'Stage': 'Qualify', 'Count': 10},
            {'Stage': 'Proposal', 'Count': 8},
            {'Stage': 'Closed Won', 'Count': 5},
            {'Stage': 'Closed Lost', 'Count': 3},
        ]
        spec = recommend_chart_spec(rows, user_hint="share by stage")
        self.assertIn(spec['chart_type'], [CHART_PIE, CHART_DONUT])
        self.assertEqual(spec['x_field'], 'Stage')
        self.assertEqual(spec['y_field'], 'Count')
    
    def test_share_by_stage_bar_fallback(self):
        """Test: share by stage (>8 categories) -> bar fallback"""
        rows = [
            {'Stage': f'Stage_{i}', 'Count': i * 10}
            for i in range(15)  # 15 categories
        ]
        spec = recommend_chart_spec(rows, user_hint="share by stage")
        # Should fallback to bar if too many categories
        self.assertEqual(spec['chart_type'], CHART_BAR)
    
    def test_profit_vs_revenue_scatter(self):
        """Test: profit vs revenue -> scatter"""
        rows = [
            {'Revenue': 1000, 'Profit': 200},
            {'Revenue': 1500, 'Profit': 300},
            {'Revenue': 800, 'Profit': 150},
        ]
        spec = recommend_chart_spec(rows, user_hint="profit vs revenue")
        self.assertEqual(spec['chart_type'], CHART_SCATTER)
        self.assertEqual(spec['x_field'], 'Revenue')
        self.assertEqual(spec['y_field'], 'Profit')
    
    def test_distribution_histogram(self):
        """Test: distribution -> histogram"""
        import random
        rows = [
            {'Price': random.uniform(10, 100)}
            for _ in range(50)
        ]
        spec = recommend_chart_spec(rows, user_hint="price distribution")
        self.assertEqual(spec['chart_type'], CHART_HISTOGRAM)
        self.assertEqual(spec['x_field'], 'Price')
    
    def test_3d_scatter_three_numeric(self):
        """Test: 3 numeric columns with '3d' in query -> 3d_scatter"""
        rows = [
            {'X': 1, 'Y': 2, 'Z': 3},
            {'X': 2, 'Y': 3, 'Z': 4},
            {'X': 3, 'Y': 4, 'Z': 5},
        ]
        spec = recommend_chart_spec(rows, user_hint="3d scatter plot")
        self.assertEqual(spec['chart_type'], CHART_3D_SCATTER)
        self.assertEqual(spec['x_field'], 'X')
        self.assertEqual(spec['y_field'], 'Y')
        self.assertEqual(spec['z_field'], 'Z')
    
    def test_bar_normalization_top_12(self):
        """Test: Bar chart normalization limits to top 12 + Other"""
        rows = [
            {'Category': f'Cat_{i}', 'Value': 100 - i}
            for i in range(20)  # 20 categories
        ]
        spec = recommend_chart_spec(rows)
        normalized, updated_spec = normalize_for_chart(rows, spec)
        
        self.assertEqual(spec['chart_type'], CHART_BAR)
        self.assertLessEqual(len(normalized), 13)  # Top 12 + Other
        # Check if "Other" category exists
        other_exists = any(row.get('Category') == 'Other' for row in normalized)
        self.assertTrue(other_exists)
    
    def test_pie_normalization_max_categories(self):
        """Test: Pie chart normalization limits to MAX_PIE_CATEGORIES"""
        rows = [
            {'Category': f'Cat_{i}', 'Value': 10}
            for i in range(12)  # 12 categories
        ]
        spec = {'chart_type': CHART_PIE, 'x_field': 'Category', 'y_field': 'Value'}
        normalized, updated_spec = normalize_for_chart(rows, spec)
        
        self.assertLessEqual(len(normalized), 8)  # MAX_PIE_CATEGORIES


if __name__ == '__main__':
    unittest.main()

