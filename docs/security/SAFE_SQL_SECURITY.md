# Safe SQL Security Implementation

## Overview

The `safe_sql.py` module implements a defense-in-depth approach to prevent SQL injection, hallucinated column/table access, and expensive queries. All SQL queries are built programmatically using strict validation and allowlists.

## Security Mechanisms

### 1. **Strict Allowlist Validation**

**Table Names:**
- Only tables that exist in the discovered schema (`get_all_table_schemas()`) are allowed
- Any table name not in the schema is rejected with a clear error message
- SQL injection attempts like `"Users; DROP TABLE Users; --"` are blocked because they don't match any table in the schema

**Column Names:**
- Only columns that exist in the discovered schema for the specified table are allowed
- Column names are validated against the schema's `all_columns` list
- Injection attempts in column names are blocked (e.g., `"id; DROP TABLE Users; --"` is not a valid column name)

**Chart Types:**
- Only 12 predefined chart types are allowed (whitelist in `ALLOWED_CHART_TYPES`)
- Any chart type not in the allowlist is rejected
- Prevents malicious or hallucinated chart types from being processed

**Aggregation Functions:**
- Only 5 allowed aggregation functions: `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`
- Prevents arbitrary function calls in SQL

### 2. **Identifier Quoting**

All table and column names are wrapped in SQL Server bracket notation:
- `Users` → `[Users]`
- `Order Date` → `[Order Date]`
- Handles special characters and spaces safely
- Escapes `]` characters in identifiers: `]` → `]]`

**Example:**
```python
quote_ident("Users")  # Returns: "[Users]"
quote_ident("Order Date")  # Returns: "[Order Date]"
```

### 3. **Query Builder Pattern**

SQL queries are built programmatically using string concatenation of validated, quoted identifiers. The builder only supports safe SQL patterns:

**Supported Patterns:**
- `SELECT TOP <limit> [columns] FROM [table]`
- `SELECT TOP <limit> [x], AGG([y]) AS [alias] FROM [table] GROUP BY [x] ORDER BY [alias] DESC`
- Future: `WHERE [column] = ?` (parameterized values only)

**Not Supported (Blocked):**
- Raw SQL strings from Gemini
- Dynamic SQL construction from user input
- UNION, JOIN, subqueries (unless explicitly added to builder)
- DDL statements (DROP, CREATE, ALTER, etc.)
- DML statements (INSERT, UPDATE, DELETE)

### 4. **Performance Guardrails**

**Row Limits:**
- `MAX_ROWS = 5000` for non-aggregated queries
- `MAX_GROUPS = 50` for aggregated queries (prevents expensive GROUP BY operations)
- `MAX_HISTOGRAM_BINS = 100` for histogram charts
- User-requested limits are clamped to these maximums

**Query Optimization:**
- Only required columns are selected (never `SELECT *`)
- Aggregations are performed in SQL (not in pandas after fetching all data)
- `TOP` clause limits result sets before data transfer

**Example:**
```sql
-- Non-aggregated query (max 5000 rows)
SELECT TOP 5000 [name], [age] FROM [Users] ORDER BY [name]

-- Aggregated query (max 50 groups)
SELECT TOP 50 [product], SUM([amount]) AS [Sum of amount] 
FROM [Sales] 
GROUP BY [product] 
ORDER BY [Sum of amount] DESC
```

### 5. **Parameterization (Future-Ready)**

The query builder returns a tuple `(sql_string, params_list)`. Currently, `params_list` is empty, but the structure is ready for WHERE clause parameterization:

```python
# Future implementation:
WHERE [date] > ?  # Parameter value, not identifier
params = [datetime(2024, 1, 1)]  # Safe parameter
```

**Important:** Only VALUES are parameterized, never identifiers (table/column names). Identifiers are validated against allowlists and quoted.

### 6. **Type Validation**

**Numerical Aggregations:**
- `SUM`, `AVG`, `MIN`, `MAX` require numerical columns
- Column types are validated against `numerical_columns` from schema
- `COUNT` can be used on any column

**Chart-Specific Requirements:**
- Pie/Donut charts require numerical `y_axis` for values
- Heatmap requires numerical `z_axis`
- Bubble chart requires numerical `size` column

## How It Prevents Attacks

### SQL Injection Prevention

**Attack Attempt:**
```json
{
  "table_name": "Users; DROP TABLE Users; --",
  "chart_type": "bar_chart",
  "x_axis": "id",
  "y_axis": "age"
}
```

**Defense:**
1. `validate_chart_request()` checks if `"Users; DROP TABLE Users; --"` exists in `schema_map`
2. It doesn't, so `SafeSQLError` is raised: `"Table 'Users; DROP TABLE Users; --' not found"`
3. No SQL is executed

**Attack Attempt:**
```json
{
  "table_name": "Users",
  "chart_type": "bar_chart",
  "x_axis": "id; DROP TABLE Users; --",
  "y_axis": "age"
}
```

**Defense:**
1. `validate_chart_request()` checks if `"id; DROP TABLE Users; --"` exists in `Users.all_columns`
2. It doesn't, so `SafeSQLError` is raised: `"Invalid column 'id; DROP TABLE Users; --'"`
3. No SQL is executed

### Hallucinated Column/Table Prevention

**Attack Attempt (Gemini hallucinates a column):**
```json
{
  "table_name": "Users",
  "chart_type": "bar_chart",
  "x_axis": "non_existent_column",
  "y_axis": "age"
}
```

**Defense:**
1. `validate_chart_request()` validates `"non_existent_column"` against `Users.all_columns`
2. Column not found, so `SafeSQLError` is raised
3. No SQL is executed

### Expensive Query Prevention

**Attack Attempt:**
```json
{
  "table_name": "LargeTable",
  "chart_type": "bar_chart",
  "x_axis": "id",
  "y_axis": "value",
  "limit": 1000000
}
```

**Defense:**
1. `validate_chart_request()` accepts the request
2. `build_sql()` clamps `limit` to `MAX_ROWS` (5000)
3. SQL generated: `SELECT TOP 5000 [id], [value] FROM [LargeTable]`
4. Database only returns 5000 rows maximum

**Attack Attempt (Expensive Aggregation):**
```json
{
  "table_name": "Sales",
  "chart_type": "bar_chart",
  "x_axis": "product",
  "y_axis": "amount",
  "aggregate_y": "SUM",
  "limit": 10000
}
```

**Defense:**
1. `build_sql()` detects this is an aggregated query
2. Clamps limit to `MAX_GROUPS` (50) instead of `MAX_ROWS`
3. SQL generated: `SELECT TOP 50 [product], SUM([amount]) AS [Sum of amount] FROM [Sales] GROUP BY [product] ORDER BY [Sum of amount] DESC`
4. Database only returns 50 groups maximum

## Error Handling

All validation errors raise `SafeSQLError` with clear, actionable messages:

```python
# Example error messages:
"Table 'InvalidTable' not found in database. Available tables: Users, Sales"
"Invalid column 'invalid_col'. Must be one of: id, name, email, age"
"Invalid chart_type 'malicious_chart'. Allowed types: bar_chart, line_chart, ..."
"Cannot apply SUM to non-numerical column 'email'. Numerical columns: id, age"
```

These errors are caught in `app.py` and returned as friendly JSON responses to the frontend, without exposing stack traces or internal details.

## Testing

Run the test suite to verify security:

```bash
python test_safe_sql.py
```

Tests verify:
- Invalid tables are blocked
- Invalid columns are blocked
- SQL injection attempts are blocked
- Invalid chart types are blocked
- Limits are clamped correctly
- Valid requests are processed correctly

## Summary

The safe SQL layer provides multiple layers of defense:

1. **Allowlist Validation**: Only known tables/columns/chart types are allowed
2. **Identifier Quoting**: All identifiers are safely quoted
3. **Query Builder**: Only safe SQL patterns are generated
4. **Performance Limits**: Row/group limits prevent expensive queries
5. **Type Validation**: Aggregations require appropriate column types
6. **Error Handling**: Clear errors without exposing internals

This approach ensures that even if Gemini hallucinates or an attacker attempts injection, the system will reject invalid requests before any SQL is executed.

