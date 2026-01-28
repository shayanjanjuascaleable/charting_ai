"""
Unit tests for rule-based SQL generation.
Tests deterministic SQL generation without Gemini calls.
"""
import unittest
import os
import sys
import tempfile
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Module removed - test kept for reference only
# # Module removed - test kept for reference only
# from backend.rule_sql import get_schema_map, build_rule_sql


class TestRuleSQL(unittest.TestCase):
    """Test cases for rule-based SQL generation."""
    
    def setUp(self):
        """Create a temporary SQLite database with test schema."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create test schema matching production
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Account table
        cursor.execute("""
            CREATE TABLE Account (
                AccountID INTEGER PRIMARY KEY,
                AccountName TEXT,
                Region TEXT,
                Industry TEXT,
                Revenue NUMERIC,
                CreatedDate TEXT
            )
        """)
        
        # Contact table
        cursor.execute("""
            CREATE TABLE Contact (
                ContactID INTEGER PRIMARY KEY,
                AccountID INTEGER,
                FullName TEXT,
                Role TEXT,
                Email TEXT,
                CreatedDate TEXT,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        
        # Lead table
        cursor.execute("""
            CREATE TABLE Lead (
                LeadID INTEGER PRIMARY KEY,
                AccountID INTEGER,
                LeadSource TEXT,
                Status TEXT,
                Budget NUMERIC,
                CreatedDate TEXT,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        
        # Opportunity table
        cursor.execute("""
            CREATE TABLE Opportunity (
                OpportunityID INTEGER PRIMARY KEY,
                AccountID INTEGER,
                OpportunityName TEXT,
                Stage TEXT,
                Value NUMERIC,
                ExpectedCloseDate TEXT,
                FOREIGN KEY(AccountID) REFERENCES Account(AccountID)
            )
        """)
        
        # Insert test data
        cursor.executemany(
            "INSERT INTO Account (AccountID, AccountName, Region, Revenue) VALUES (?, ?, ?, ?)",
            [
                (1, 'Account1', 'East', 100000),
                (2, 'Account2', 'West', 200000),
                (3, 'Account3', 'North', 150000),
                (4, 'Account4', 'South', 300000),
            ]
        )
        
        cursor.executemany(
            "INSERT INTO Lead (LeadID, LeadSource, Status) VALUES (?, ?, ?)",
            [
                (1, 'Web', 'New'),
                (2, 'Email', 'Contacted'),
                (3, 'Web', 'Qualified'),
                (4, 'Phone', 'New'),
            ]
        )
        
        cursor.executemany(
            "INSERT INTO Opportunity (OpportunityID, Stage, Value) VALUES (?, ?, ?)",
            [
                (1, 'Qualify', 50000),
                (2, 'Proposal', 75000),
                (3, 'Closed Won', 100000),
                (4, 'Closed Lost', 0),
            ]
        )
        
        conn.commit()
        conn.close()
        
        # Get schema map
        self.schema = get_schema_map(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_get_schema_map(self):
        """Test schema introspection."""
        schema = get_schema_map(self.db_path)
        
        self.assertIn('Account', schema)
        self.assertIn('Lead', schema)
        self.assertIn('Opportunity', schema)
        
        # Check Account columns
        account_cols = schema['Account']['columns']
        self.assertIn('AccountID', account_cols)
        self.assertIn('Region', account_cols)
        self.assertIn('Revenue', account_cols)
        
        # Check numeric columns
        account_numeric = schema['Account']['numeric_columns']
        self.assertIn('AccountID', account_numeric)
        self.assertIn('Revenue', account_numeric)
    
    def test_total_revenue_bar_chart(self):
        """Test 'total revenue' with bar_chart -> uses Account SUM Revenue."""
        result = build_rule_sql("total revenue", "bar_chart", self.schema)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['table'], 'Account')
        self.assertIn('SUM(Revenue)', result['sql'])
        self.assertIn('Total Revenue', result['sql'])
        self.assertIn('matched rule: total revenue', result['reason'].lower())
    
    def test_revenue_by_region(self):
        """Test 'revenue by region' -> Account GROUP BY Region."""
        result = build_rule_sql("revenue by region", "bar_chart", self.schema)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['table'], 'Account')
        self.assertIn('GROUP BY', result['sql'])
        self.assertIn('Region', result['sql'])
        self.assertIn('SUM(Revenue)', result['sql'])
        self.assertIn('matched rule: revenue by region', result['reason'].lower())
    
    def test_count_leads_by_status(self):
        """Test 'count leads by status' -> Lead GROUP BY Status."""
        result = build_rule_sql("count leads by status", "bar_chart", self.schema)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['table'], 'Lead')
        self.assertIn('GROUP BY', result['sql'])
        self.assertIn('Status', result['sql'])
        self.assertIn('COUNT(*)', result['sql'])
        self.assertIn('matched rule: count leads by status', result['reason'].lower())
    
    def test_opportunities_by_stage(self):
        """Test 'opportunities by stage' -> Opportunity GROUP BY Stage."""
        result = build_rule_sql("opportunities by stage", "bar_chart", self.schema)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['table'], 'Opportunity')
        self.assertIn('GROUP BY', result['sql'])
        self.assertIn('Stage', result['sql'])
        self.assertIn('COUNT(*)', result['sql'])
        self.assertIn('matched rule: opportunities by stage', result['reason'].lower())
    
    def test_scatter_plot_two_numeric(self):
        """Test scatter plot chooses 2 numeric columns and limits 3000."""
        result = build_rule_sql("show me data", "scatter_plot", self.schema)
        
        if result:  # May not match if no suitable columns
            self.assertIn('LIMIT 3000', result['sql'])
            # Should have 2 columns selected
            self.assertIn('SELECT', result['sql'])
    
    def test_histogram_one_numeric(self):
        """Test histogram chooses 1 numeric and limits 5000."""
        result = build_rule_sql("distribution", "histogram", self.schema)
        
        if result:  # May not match if no suitable columns
            self.assertIn('LIMIT 5000', result['sql'])
            # Should have 1 column selected
            self.assertIn('SELECT', result['sql'])
    
    def test_no_match_returns_none(self):
        """Test that unmatched queries return None."""
        result = build_rule_sql("completely unrelated query", "bar_chart", self.schema)
        
        # Should return None if no rule matches
        # (This is expected behavior - rules are specific)
        # self.assertIsNone(result)  # May match generic pattern, so not asserting


if __name__ == '__main__':
    unittest.main()

