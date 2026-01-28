# Safe SQL Manual Test Checklist

Use this checklist to manually verify the safe SQL layer is working correctly in production.

## Prerequisites

1. Ensure your `.env` file is configured with valid Azure SQL credentials
2. Ensure your database has the baseline tables: `Account`, `Contact`, `Lead`, `Opportunity`
3. Start the Flask application: `python app.py`

## Test 1: Valid Request (Baseline)

**Goal:** Verify normal functionality still works.

**Steps:**
1. Send POST request to `/chat`:
   ```json
   {
     "message": "show me a bar chart of revenue by account",
     "language": "en"
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ Response contains `chart_json`, `raw_data`, and `suggestions`
- ✅ No errors in application logs
- ✅ `raw_data` does not contain Email column (if Contact table was queried)

---

## Test 2: Invalid Table Name

**Goal:** Verify invalid table names are blocked.

**Steps:**
1. Manually modify chart_params to use:
   ```json
   {
     "table_name": "NonExistentTable",
     "chart_type": "bar_chart",
     "x_axis": "AccountID",
     "y_axis": "Revenue"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with friendly error message
- ✅ Error message mentions available tables (Account, Contact, Lead, Opportunity)
- ✅ No SQL is executed
- ✅ Response contains `chart_json: null`, `raw_data: []`, and `error` field

---

## Test 3: Invalid Column Name

**Goal:** Verify invalid column names are blocked.

**Steps:**
1. Use a valid table but invalid column:
   ```json
   {
     "table_name": "Account",
     "chart_type": "bar_chart",
     "x_axis": "NonExistentColumn",
     "y_axis": "Revenue"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error mentioning available columns
- ✅ No SQL is executed
- ✅ Response contains error field

---

## Test 4: SQL Injection Attempt (Table Name)

**Goal:** Verify SQL injection in table names is blocked.

**Steps:**
1. Attempt injection in table name:
   ```json
   {
     "table_name": "Account; DROP TABLE Account; --",
     "chart_type": "bar_chart",
     "x_axis": "AccountID",
     "y_axis": "Revenue"
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
     "table_name": "Account",
     "chart_type": "bar_chart",
     "x_axis": "AccountID; DROP TABLE Account; --",
     "y_axis": "Revenue"
   }
   ```

**Expected Result:**
- ✅ Request is rejected (column not found in schema)
- ✅ No SQL is executed
- ✅ Database tables remain intact

---

## Test 6: PII Email Column Blocked

**Goal:** Verify Email column cannot be selected.

**Steps:**
1. Attempt to use Email column:
   ```json
   {
     "table_name": "Contact",
     "chart_type": "bar_chart",
     "x_axis": "FullName",
     "y_axis": "Email"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error: "Column 'Email' contains PII and cannot be selected for privacy protection."
- ✅ No SQL is executed
- ✅ Response contains error field

---

## Test 7: PII Email in Color Column

**Goal:** Verify Email cannot be used as color column.

**Steps:**
1. Attempt to use Email as color:
   ```json
   {
     "table_name": "Contact",
     "chart_type": "bar_chart",
     "x_axis": "FullName",
     "y_axis": "ContactID",
     "color": "Email"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with PII error
- ✅ No SQL is executed

---

## Test 8: Limit Clamping (Non-Aggregated)

**Goal:** Verify limits are clamped to MAX_ROWS (5000).

**Steps:**
1. Request a chart with very high limit:
   ```json
   {
     "table_name": "Account",
     "chart_type": "bar_chart",
     "x_axis": "AccountID",
     "y_axis": "Revenue",
     "limit": 100000
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ Check application logs or database query logs
- ✅ SQL query contains `TOP 5000` (not `TOP 100000`)
- ✅ Response contains at most 5000 rows in raw_data

---

## Test 9: Limit Clamping (Aggregated)

**Goal:** Verify aggregated queries use MAX_GROUPS (50).

**Steps:**
1. Request an aggregated chart with high limit:
   ```json
   {
     "table_name": "Account",
     "chart_type": "bar_chart",
     "x_axis": "Region",
     "y_axis": "Revenue",
     "aggregate_y": "SUM",
     "limit": 1000
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ SQL query contains `TOP 50` (not `TOP 1000`)
- ✅ Response contains at most 50 groups

---

## Test 10: Schema Prefix Handling

**Goal:** Verify `dbo.TableName` format is handled.

**Steps:**
1. Use table name with schema prefix:
   ```json
   {
     "table_name": "dbo.Account",
     "chart_type": "bar_chart",
     "x_axis": "AccountID",
     "y_axis": "Revenue"
   }
   ```

**Expected Result:**
- ✅ Request is processed successfully
- ✅ Schema prefix is stripped (`dbo.Account` → `Account`)
- ✅ Table is found in schema

---

## Test 11: Verify PII Not in raw_data

**Goal:** Verify Email is never in raw_data even if query succeeds.

**Steps:**
1. Query Contact table with valid columns:
   ```json
   {
     "table_name": "Contact",
     "chart_type": "bar_chart",
     "x_axis": "FullName",
     "y_axis": "ContactID"
   }
   ```

**Expected Result:**
- ✅ Chart is generated successfully
- ✅ Check `raw_data` in response
- ✅ `raw_data` does NOT contain `Email` field in any record
- ✅ Other fields (FullName, ContactID, etc.) are present

---

## Test 12: Invalid Chart Type

**Goal:** Verify invalid chart types are blocked.

**Steps:**
1. Use an invalid chart type:
   ```json
   {
     "table_name": "Account",
     "chart_type": "malicious_chart_type",
     "x_axis": "AccountID",
     "y_axis": "Revenue"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error listing allowed chart types
- ✅ No SQL is executed

---

## Test 13: Invalid Aggregation

**Goal:** Verify SUM/AVG/MIN/MAX require numerical columns.

**Steps:**
1. Attempt to aggregate a text column:
   ```json
   {
     "table_name": "Account",
     "chart_type": "bar_chart",
     "x_axis": "AccountName",
     "y_axis": "AccountName",
     "aggregate_y": "SUM"
   }
   ```

**Expected Result:**
- ✅ Request is rejected with error about numerical columns
- ✅ No SQL is executed

---

## Test 14: Check SQL Quoting

**Goal:** Verify identifiers are properly quoted in SQL.

**Steps:**
1. Use a table/column with special characters (if available)
2. Or check application logs for generated SQL

**Expected Result:**
- ✅ All table names are wrapped in brackets: `[Account]`
- ✅ All column names are wrapped in brackets: `[AccountID]`
- ✅ No raw identifiers in SQL

---

## Test 15: Error Response Format

**Goal:** Verify error responses include all required fields.

**Steps:**
1. Trigger a validation error (e.g., invalid table)

**Expected Result:**
- ✅ Response contains:
  - `chart_json: null`
  - `raw_data: []`
  - `suggestions: []` (or empty array)
  - `error: "friendly error message"`
  - `response: {...}` (multi-language response)
- ✅ No stack traces or internal details exposed

---

## Automated Test Suite

For comprehensive testing, run:

```bash
python test_safe_sql.py
```

**Expected Output:**
```
============================================================
Safe SQL Validation Tests
============================================================

Test 1: Invalid table name
  ✅ PASSED: Blocked invalid table...

Test 2: Invalid column name
  ✅ PASSED: Blocked invalid column...

...

Test 10: PII Email column blocked
  ✅ PASSED: Blocked Email column (PII)...

Test 11: PII Email blocked as color column
  ✅ PASSED: Blocked Email as color column...

Results: 11/11 tests passed
============================================================
```

---

## Summary Checklist

After completing all tests, verify:

- ✅ Valid requests work normally
- ✅ Invalid inputs are rejected with clear errors
- ✅ SQL injection attempts are blocked
- ✅ Limits are clamped correctly
- ✅ PII Email column is blocked from selection
- ✅ PII Email is never in raw_data
- ✅ Aggregations are validated
- ✅ No sensitive information in error messages
- ✅ All identifiers are properly quoted in SQL
- ✅ Error responses include all required fields
- ✅ Response contract is maintained (backward compatible)

If all tests pass, the safe SQL layer is working correctly!

