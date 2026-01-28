"""
Lightweight tests for safe SQL validation.
Run with: python test_safe_sql.py
"""
from backend.safe_sql import (
    validate_chart_request,
    build_sql,
    SafeSQLError,
    ALLOWED_CHART_TYPES,
    ALLOWED_AGGREGATIONS
)


# Mock schema for testing
MOCK_SCHEMA = {
    'Users': {
        'all_columns': ['id', 'name', 'email', 'age', 'created_at'],
        'numerical_columns': ['id', 'age'],
        'date_columns': ['created_at'],
        'categorical_columns': ['name', 'email']
    },
    'Sales': {
        'all_columns': ['id', 'product', 'amount', 'date', 'region'],
        'numerical_columns': ['id', 'amount'],
        'date_columns': ['date'],
        'categorical_columns': ['product', 'region']
    }
}


def test_invalid_table():
    """Test that invalid table names are blocked."""
    print("Test 1: Invalid table name")
    try:
        validate_chart_request(
            {'table_name': 'NonExistentTable', 'chart_type': 'bar_chart', 'x_axis': 'id', 'y_axis': 'amount'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have raised SafeSQLError")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked invalid table - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_invalid_column():
    """Test that invalid column names are blocked."""
    print("Test 2: Invalid column name")
    try:
        validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': 'invalid_col', 'y_axis': 'age'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have raised SafeSQLError")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked invalid column - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_injection_attempt():
    """Test that SQL injection attempts are blocked (not in schema)."""
    print("Test 3: SQL injection attempt (table name)")
    try:
        validate_chart_request(
            {'table_name': "Users; DROP TABLE Users; --", 'chart_type': 'bar_chart', 'x_axis': 'id', 'y_axis': 'age'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have blocked injection attempt")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked injection attempt - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_injection_attempt_column():
    """Test that SQL injection in column names is blocked."""
    print("Test 4: SQL injection attempt (column name)")
    try:
        validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': "id; DROP TABLE Users; --", 'y_axis': 'age'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have blocked injection attempt")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked injection in column - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_invalid_chart_type():
    """Test that invalid chart types are blocked."""
    print("Test 5: Invalid chart type")
    try:
        validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'malicious_chart', 'x_axis': 'id', 'y_axis': 'age'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have raised SafeSQLError")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked invalid chart type - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_limit_clamping():
    """Test that limits are clamped to maximums."""
    print("Test 6: Limit clamping")
    try:
        # Request with limit exceeding MAX_ROWS
        validated = validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': 'id', 'y_axis': 'age', 'limit': 100000},
            MOCK_SCHEMA
        )
        sql, params = build_sql(validated, MOCK_SCHEMA, db_type='sqlserver')
        
        # Check that SQL contains TOP with clamped value
        if 'TOP 5000' in sql:  # MAX_ROWS
            print(f"  ✅ PASSED: Limit clamped to MAX_ROWS (5000)")
            print(f"     SQL: {sql[:100]}...")
            return True
        else:
            print(f"  ❌ FAILED: Limit not clamped correctly. SQL: {sql}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Exception - {e}")
        return False


def test_aggregation_limit():
    """Test that aggregated queries use MAX_GROUPS limit."""
    print("Test 7: Aggregation limit (MAX_GROUPS)")
    try:
        validated = validate_chart_request(
            {'table_name': 'Sales', 'chart_type': 'bar_chart', 'x_axis': 'product', 'y_axis': 'amount', 'aggregate_y': 'SUM', 'limit': 1000},
            MOCK_SCHEMA
        )
        sql, params = build_sql(validated, MOCK_SCHEMA, db_type='sqlserver')
        
        # Check that SQL contains TOP with MAX_GROUPS (50)
        if 'TOP 50' in sql:  # MAX_GROUPS
            print(f"  ✅ PASSED: Aggregated query limited to MAX_GROUPS (50)")
            print(f"     SQL: {sql[:120]}...")
            return True
        else:
            print(f"  ❌ FAILED: Aggregation limit not applied. SQL: {sql}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Exception - {e}")
        return False


def test_valid_request():
    """Test that valid requests pass validation."""
    print("Test 8: Valid request")
    try:
        validated = validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': 'name', 'y_axis': 'age'},
            MOCK_SCHEMA
        )
        sql, params = build_sql(validated, MOCK_SCHEMA, db_type='sqlserver')
        
        # Check SQL is properly quoted (SQL Server uses brackets)
        if '[Users]' in sql and '[name]' in sql and '[age]' in sql:
            print(f"  ✅ PASSED: Valid request processed correctly")
            print(f"     SQL: {sql}")
            return True
        else:
            print(f"  ❌ FAILED: SQL not properly quoted. SQL: {sql}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Exception - {e}")
        return False


def test_aggregation_validation():
    """Test that non-numerical columns can't be aggregated (except COUNT)."""
    print("Test 9: Aggregation validation")
    try:
        # Try to SUM a non-numerical column
        validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': 'name', 'y_axis': 'email', 'aggregate_y': 'SUM'},
            MOCK_SCHEMA
        )
        print("  ❌ FAILED: Should have blocked SUM on non-numerical column")
        return False
    except SafeSQLError as e:
        print(f"  ✅ PASSED: Blocked invalid aggregation - {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_pii_email_blocked():
    """Test that Email column is blocked from selection."""
    print("Test 10: PII Email column blocked")
    try:
        # Try to use Email column
        validate_chart_request(
            {'table_name': 'Contact', 'chart_type': 'bar_chart', 'x_axis': 'FullName', 'y_axis': 'Email'},
            {
                'Contact': {
                    'all_columns': ['ContactID', 'AccountID', 'FullName', 'Role', 'Email', 'CreatedDate'],
                    'numerical_columns': ['ContactID', 'AccountID'],
                    'date_columns': ['CreatedDate'],
                    'categorical_columns': ['FullName', 'Role', 'Email']
                }
            }
        )
        print("  ❌ FAILED: Should have blocked Email column (PII)")
        return False
    except SafeSQLError as e:
        if 'PII' in str(e) or 'Email' in str(e):
            print(f"  ✅ PASSED: Blocked Email column (PII) - {e}")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error message - {e}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def test_pii_email_in_color():
    """Test that Email cannot be used as color column."""
    print("Test 11: PII Email blocked as color column")
    try:
        validate_chart_request(
            {'table_name': 'Contact', 'chart_type': 'bar_chart', 'x_axis': 'FullName', 'y_axis': 'ContactID', 'color': 'Email'},
            {
                'Contact': {
                    'all_columns': ['ContactID', 'AccountID', 'FullName', 'Role', 'Email', 'CreatedDate'],
                    'numerical_columns': ['ContactID', 'AccountID'],
                    'date_columns': ['CreatedDate'],
                    'categorical_columns': ['FullName', 'Role', 'Email']
                }
            }
        )
        print("  ❌ FAILED: Should have blocked Email as color column")
        return False
    except SafeSQLError as e:
        if 'PII' in str(e) or 'Email' in str(e):
            print(f"  ✅ PASSED: Blocked Email as color column - {e}")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error - {e}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type - {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Safe SQL Validation Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_invalid_table,
        test_invalid_column,
        test_injection_attempt,
        test_injection_attempt_column,
        test_invalid_chart_type,
        test_limit_clamping,
        test_aggregation_limit,
        test_valid_request,
        test_aggregation_validation,
        test_pii_email_blocked,
        test_pii_email_in_color
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ FAILED: Test crashed - {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)

