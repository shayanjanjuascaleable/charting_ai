# Safe SQL Manual Test Checklist

Use this checklist to manually verify that the safe SQL layer is working correctly.

## Prerequisites

1. Ensure your `.env` file is configured with valid database credentials
2. Ensure your database has at least one table with data
3. Start the Flask application: `python app.py`

## Test 1: Valid Request (Baseline)

**Goal:** Verify normal functionality still works.

**Steps:**
1. Send POST request to `/chat` with a valid chart request
2. Example request body:
   ```json
   {
     "message": "show me a bar chart of sales by product",
     "language": "en"
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ Response contains `chart_json`, `raw_data`, and `suggestions`
- ✅ No errors in application logs

---

## Test 2: Invalid Table Name

**Goal:** Verify invalid table names are blocked.

**Steps:**
1. Manually modify the Gemini response (or use a test script) to set:
   ```json
   {
     "table_name": "NonExistentTable",
     "chart_type": "bar_chart",
     "x_axis": "id",
     "y_axis": "amount"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with friendly error message
- ✅ Error message mentions available tables
- ✅ No SQL is executed
- ✅ Response contains `chart_json: null`

---

## Test 3: Invalid Column Name

**Goal:** Verify invalid column names are blocked.

**Steps:**
1. Use a valid table but invalid column:
   ```json
   {
     "table_name": "Users",  // Valid table
     "chart_type": "bar_chart",
     "x_axis": "non_existent_column",  // Invalid column
     "y_axis": "age"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error mentioning available columns
- ✅ No SQL is executed
- ✅ Response contains `chart_json: null`

---

## Test 4: SQL Injection Attempt (Table Name)

**Goal:** Verify SQL injection in table names is blocked.

**Steps:**
1. Attempt injection in table name:
   ```json
   {
     "table_name": "Users; DROP TABLE Users; --",
     "chart_type": "bar_chart",
     "x_axis": "id",
     "y_axis": "age"
   }
   ```

**Expected Result:**
- ✅ Request is rejected (table not found in schema)
- ✅ No SQL is executed
- ✅ Database tables remain intact
- ✅ Error message does not expose SQL details

---

## Test 5: SQL Injection Attempt (Column Name)

**Goal:** Verify SQL injection in column names is blocked.

**Steps:**
1. Attempt injection in column name:
   ```json
   {
     "table_name": "Users",
     "chart_type": "bar_chart",
     "x_axis": "id; DROP TABLE Users; --",
     "y_axis": "age"
   }
   ```

**Expected Result:**
- ✅ Request is rejected (column not found in schema)
- ✅ No SQL is executed
- ✅ Database tables remain intact

---

## Test 6: Invalid Chart Type

**Goal:** Verify invalid chart types are blocked.

**Steps:**
1. Use an invalid chart type:
   ```json
   {
     "table_name": "Users",
     "chart_type": "malicious_chart_type",
     "x_axis": "id",
     "y_axis": "age"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error listing allowed chart types
- ✅ No SQL is executed

---

## Test 7: Limit Clamping (Non-Aggregated)

**Goal:** Verify limits are clamped to MAX_ROWS (5000).

**Steps:**
1. Request a chart with a very high limit:
   ```json
   {
     "table_name": "Users",
     "chart_type": "bar_chart",
     "x_axis": "id",
     "y_axis": "age",
     "limit": 100000
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ Check application logs or database query logs
- ✅ SQL query contains `TOP 5000` (not `TOP 100000`)
- ✅ Response contains at most 5000 rows

---

## Test 8: Limit Clamping (Aggregated)

**Goal:** Verify aggregated queries use MAX_GROUPS (50).

**Steps:**
1. Request an aggregated chart with high limit:
   ```json
   {
     "table_name": "Sales",
     "chart_type": "bar_chart",
     "x_axis": "product",
     "y_axis": "amount",
     "aggregate_y": "SUM",
     "limit": 1000
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ SQL query contains `TOP 50` (not `TOP 1000`)
- ✅ Response contains at most 50 groups

---

## Test 9: Invalid Aggregation on Non-Numerical Column

**Goal:** Verify SUM/AVG/MIN/MAX require numerical columns.

**Steps:**
1. Attempt to aggregate a text column:
   ```json
   {
     "table_name": "Users",
     "chart_type": "bar_chart",
     "x_axis": "name",
     "y_axis": "email",  // Text column
     "aggregate_y": "SUM"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error about numerical columns
- ✅ No SQL is executed

---

## Test 10: Valid Aggregation

**Goal:** Verify valid aggregations work correctly.

**Steps:**
1. Request a valid aggregated chart:
   ```json
   {
     "table_name": "Sales",
     "chart_type": "bar_chart",
     "x_axis": "product",
     "y_axis": "amount",  // Numerical column
     "aggregate_y": "SUM"
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ SQL contains `SUM([amount])` and `GROUP BY [product]`
- ✅ Response contains aggregated data

---

## Test 11: Check SQL Quoting

**Goal:** Verify identifiers are properly quoted in SQL.

**Steps:**
1. Use a table/column with special characters or spaces (if available)
2. Or check application logs for generated SQL

**Expected Result:**
- ✅ All table names are wrapped in brackets: `[TableName]`
- ✅ All column names are wrapped in brackets: `[ColumnName]`
- ✅ No raw identifiers in SQL

---

## Test 12: Error Message Safety

**Goal:** Verify error messages don't leak sensitive information.

**Steps:**
1. Trigger various validation errors
2. Check error messages in responses

**Expected Result:**
- ✅ Error messages are user-friendly
- ✅ No stack traces exposed
- ✅ No connection strings or secrets in errors
- ✅ Error messages list available options (tables, columns, etc.)

---

## Automated Test Suite

For comprehensive testing, run the automated test suite:

```bash
python test_safe_sql.py
```

**Expected Output:**
```
============================================================
Safe SQL Validation Tests
============================================================

Test 1: Invalid table name
  ✅ PASSED: Blocked invalid table - Table 'NonExistentTable' not found...

Test 2: Invalid column name
  ✅ PASSED: Blocked invalid column - Invalid column 'invalid_col'...

...

Results: 9/9 tests passed
============================================================
```

---

## Quick Verification Script

You can also use this Python snippet to test validation directly:

```python
from safe_sql import validate_chart_request, SafeSQLError

# Mock schema
schema = {
    'Users': {
        'all_columns': ['id', 'name', 'age'],
        'numerical_columns': ['id', 'age'],
        'date_columns': [],
        'categorical_columns': ['name']
    }
}

# Test invalid table
try:
    validate_chart_request(
        {'table_name': 'BadTable', 'chart_type': 'bar_chart', 'x_axis': 'id', 'y_axis': 'age'},
        schema
    )
    print("❌ Should have failed")
except SafeSQLError as e:
    print(f"✅ Blocked: {e}")
```

---

## Summary

After completing all tests, verify:

- ✅ Valid requests work normally
- ✅ Invalid inputs are rejected with clear errors
- ✅ SQL injection attempts are blocked
- ✅ Limits are clamped correctly
- ✅ Aggregations are validated
- ✅ No sensitive information in error messages
- ✅ All identifiers are properly quoted in SQL

If all tests pass, the safe SQL layer is working correctly!

