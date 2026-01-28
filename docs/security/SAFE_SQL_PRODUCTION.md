# Safe SQL Production Implementation

## Overview

The safe SQL layer provides production-grade protection against SQL injection, hallucinated table/column access, expensive queries, and PII exposure. All SQL queries are built programmatically using strict validation and allowlists.

## Security Features

### 1. SQL Injection Prevention

**Mechanism:**
- **Allowlist Validation**: Only tables and columns that exist in the discovered schema are allowed
- **Identifier Quoting**: All identifiers are wrapped in SQL Server brackets: `[TableName]`, `[ColumnName]`
- **No Raw SQL**: Queries are built programmatically, never from user input
- **Schema Prefix Handling**: Handles `dbo.TableName` format by extracting table name

**Example Attack Blocked:**
```json
{"table_name": "Account; DROP TABLE Account; --", ...}
```
→ **Rejected**: Table not in schema allowlist

```json
{"table_name": "Account", "x_axis": "AccountID; DROP TABLE Account; --", ...}
```
→ **Rejected**: Column not in schema allowlist

### 2. Hallucinated Table/Column Prevention

**Mechanism:**
- Schema discovery via `INFORMATION_SCHEMA` provides the source of truth
- Baseline tables (`Account`, `Contact`, `Lead`, `Opportunity`) are guaranteed to be supported
- All column names must exist in the discovered schema for the specified table
- Gemini output is validated against actual database schema before any SQL is built

**Example:**
```json
{"table_name": "Account", "x_axis": "NonExistentColumn", ...}
```
→ **Rejected**: Column not found in `Account` table schema

### 3. PII Protection

**Mechanism:**
- **PII Column Blocking**: `Email` column is blocked from selection, charting, and raw_data
- **Validation Layer**: `validate_identifier()` checks if column is PII before allowing it
- **Data Filtering**: `filter_pii_from_dataframe()` removes PII columns from DataFrames
- **Response Filtering**: `filter_pii_from_dict()` removes PII fields from raw_data records

**PII Columns:**
- `Email` (from `dbo.Contact` table)

**Example:**
```json
{"table_name": "Contact", "x_axis": "FullName", "y_axis": "Email", ...}
```
→ **Rejected**: "Column 'Email' contains PII and cannot be selected for privacy protection."

**Data Flow:**
1. Validation blocks Email column in `validate_chart_request()`
2. Even if Email somehow gets through, `filter_pii_from_dataframe()` removes it from DataFrame
3. `filter_pii_from_dict()` removes Email from each raw_data record before JSON serialization

### 4. Expensive Query Prevention

**Performance Guardrails:**
- **MAX_ROWS = 5000**: Maximum rows for non-aggregated queries
- **MAX_GROUPS = 50**: Maximum groups for aggregated queries (bar, pie, donut charts)
- **MAX_HISTOGRAM_BINS = 100**: Maximum bins for histogram charts
- **SQL-Level Limits**: `TOP` clause enforces limits before data transfer
- **Column Selection**: Only required columns selected (never `SELECT *`)

**Example:**
```json
{"table_name": "Account", "limit": 1000000, ...}
```
→ **Clamped**: SQL generated with `TOP 5000` (or `TOP 50` for aggregated queries)

**Aggregated Query Example:**
```sql
SELECT TOP 50 [Product], SUM([Amount]) AS [Sum of Amount]
FROM [Sales]
GROUP BY [Product]
ORDER BY [Sum of Amount] DESC
```

## Baseline Tables

The following tables are guaranteed to be supported (baseline allowlist):

1. **dbo.Account**
   - AccountID (int)
   - AccountName (nvarchar)
   - Region (nvarchar)
   - Industry (nvarchar)
   - Revenue (decimal)
   - CreatedDate (date)

2. **dbo.Contact**
   - ContactID (int)
   - AccountID (int)
   - FullName (nvarchar)
   - Role (nvarchar)
   - Email (nvarchar) ← **PII - BLOCKED**
   - CreatedDate (date)

3. **dbo.Lead**
   - LeadID (int)
   - AccountID (int)
   - LeadSource (nvarchar)
   - Status (nvarchar)
   - Budget (decimal/int)
   - CreatedDate (date)

4. **dbo.Opportunity**
   - OpportunityID (int)
   - AccountID (int)
   - OpportunityName (nvarchar)
   - Stage (nvarchar)
   - Value (decimal)
   - ExpectedCloseDate (date)

## Query Builder

The query builder only generates safe SQL patterns:

**Supported:**
- `SELECT TOP <limit> [columns] FROM [table]`
- `SELECT TOP <limit> [x], AGG([y]) AS [alias] FROM [table] GROUP BY [x] ORDER BY [alias] DESC`
- Future: `WHERE [column] = ?` (parameterized values only)

**Not Supported (Blocked):**
- Raw SQL strings from Gemini
- Dynamic SQL from user input
- UNION, JOIN, subqueries
- DDL statements (DROP, CREATE, ALTER)
- DML statements (INSERT, UPDATE, DELETE)

## Error Handling

All validation errors raise `SafeSQLError` with clear, actionable messages:

```python
# Example error messages:
"Table 'InvalidTable' not found in database. Available tables: Account, Contact, Lead, Opportunity"
"Invalid column 'invalid_col'. Must be one of: AccountID, AccountName, Region, ..."
"Column 'Email' contains PII and cannot be selected for privacy protection."
"Invalid chart_type 'malicious_chart'. Allowed types: bar_chart, line_chart, ..."
"Cannot apply SUM to non-numerical column 'AccountName'. Numerical columns: AccountID, Revenue"
```

Errors are caught in `app.py` and returned as JSON:

```json
{
  "chart_json": null,
  "raw_data": [],
  "suggestions": [],
  "error": "friendly error message",
  "response": {
    "en": "I couldn't create the chart: friendly error message",
    ...
  }
}
```

## Response Contract

The `/chat` endpoint maintains backward compatibility:

**Success Response:**
```json
{
  "chart_json": {...},
  "raw_data": [...],
  "suggestions": [...]
}
```

**Error Response:**
```json
{
  "chart_json": null,
  "raw_data": [],
  "suggestions": [],
  "error": "error message",
  "response": {
    "en": "I couldn't create the chart: error message",
    ...
  }
}
```

**PII Protection:**
- `raw_data` never contains Email or other PII columns
- PII columns are filtered from both DataFrame and JSON records

## Testing

Run automated tests:
```bash
python test_safe_sql.py
```

Tests verify:
- ✅ Invalid tables rejected
- ✅ Invalid columns rejected
- ✅ SQL injection attempts blocked
- ✅ Invalid chart types blocked
- ✅ Limits clamped correctly
- ✅ PII Email column blocked
- ✅ Valid requests processed correctly

## Summary

The safe SQL layer provides multiple layers of defense:

1. **Allowlist Validation**: Only known tables/columns/chart types allowed
2. **Identifier Quoting**: All identifiers safely quoted with brackets
3. **Query Builder**: Only safe SQL patterns generated
4. **Performance Limits**: Row/group limits prevent expensive queries
5. **PII Protection**: Email column blocked from selection and raw_data
6. **Error Handling**: Clear errors without exposing internals

This ensures that even if Gemini hallucinates or an attacker attempts injection, the system will reject invalid requests and protect PII before any SQL is executed.

