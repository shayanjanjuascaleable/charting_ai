# Intent-Based Chart Generation - Example Prompts

This document provides working example prompts and their expected chart types using the new intent-based system.

## Schema Reference

**Tables:**
- Account: AccountID, AccountName, Region, Industry, Revenue, CreatedDate
- Contact: ContactID, AccountID, FullName, Role, Email (PII), CreatedDate
- Lead: LeadID, AccountID, LeadSource, Status, Budget, CreatedDate
- Opportunity: OpportunityID, AccountID, OpportunityName, Stage, Value, ExpectedCloseDate

## Example Prompts

### 1. "Revenue by region"
**Expected Intent:**
```json
{
  "tables": ["Account"],
  "dimensions": [{"table": "Account", "field": "Region"}],
  "metrics": [{"table": "Account", "field": "Revenue", "agg": "SUM"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Revenue by Region"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT Region, SUM(Revenue) AS Revenue_sum FROM Account GROUP BY Region ORDER BY Revenue_sum DESC LIMIT 50`

### 2. "Pipeline value by stage"
**Expected Intent:**
```json
{
  "tables": ["Opportunity"],
  "dimensions": [{"table": "Opportunity", "field": "Stage"}],
  "metrics": [{"table": "Opportunity", "field": "Value", "agg": "SUM"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Pipeline Value by Stage"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT Stage, SUM(Value) AS Value_sum FROM Opportunity GROUP BY Stage ORDER BY Value_sum DESC LIMIT 50`

### 3. "Leads by status"
**Expected Intent:**
```json
{
  "tables": ["Lead"],
  "dimensions": [{"table": "Lead", "field": "Status"}],
  "metrics": [{"table": "Lead", "field": "LeadID", "agg": "COUNT"}],
  "filters": [],
  "time": null,
  "chart_hint": "pie",
  "title": "Leads by Status"
}
```
**Expected Chart Type:** `pie_chart` (or `bar_chart` if chart_hint not respected)
**SQL Pattern:** `SELECT Status, COUNT(LeadID) AS LeadID_count FROM Lead GROUP BY Status ORDER BY LeadID_count DESC LIMIT 50`

### 4. "Budgets by lead source"
**Expected Intent:**
```json
{
  "tables": ["Lead"],
  "dimensions": [{"table": "Lead", "field": "LeadSource"}],
  "metrics": [{"table": "Lead", "field": "Budget", "agg": "SUM"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Budgets by Lead Source"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT LeadSource, SUM(Budget) AS Budget_sum FROM Lead GROUP BY LeadSource ORDER BY Budget_sum DESC LIMIT 50`

### 5. "Accounts created over time"
**Expected Intent:**
```json
{
  "tables": ["Account"],
  "dimensions": [],
  "metrics": [{"table": "Account", "field": "AccountID", "agg": "COUNT"}],
  "filters": [],
  "time": {"table": "Account", "field": "CreatedDate", "grain": "month"},
  "chart_hint": "line",
  "title": "Accounts Created Over Time"
}
```
**Expected Chart Type:** `line_chart`
**SQL Pattern:** `SELECT substr(CreatedDate, 1, 7) AS Month, COUNT(AccountID) AS AccountID_count FROM Account GROUP BY substr(CreatedDate, 1, 7) ORDER BY AccountID_count DESC LIMIT 50`

### 6. "Average revenue by industry"
**Expected Intent:**
```json
{
  "tables": ["Account"],
  "dimensions": [{"table": "Account", "field": "Industry"}],
  "metrics": [{"table": "Account", "field": "Revenue", "agg": "AVG"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Average Revenue by Industry"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT Industry, AVG(Revenue) AS Revenue_avg FROM Account GROUP BY Industry ORDER BY Revenue_avg DESC LIMIT 50`

### 7. "Opportunities by stage and value"
**Expected Intent:**
```json
{
  "tables": ["Opportunity"],
  "dimensions": [{"table": "Opportunity", "field": "Stage"}],
  "metrics": [{"table": "Opportunity", "field": "Value", "agg": "SUM"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Opportunities by Stage and Value"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT Stage, SUM(Value) AS Value_sum FROM Opportunity GROUP BY Stage ORDER BY Value_sum DESC LIMIT 50`

### 8. "Contact count by role"
**Expected Intent:**
```json
{
  "tables": ["Contact"],
  "dimensions": [{"table": "Contact", "field": "Role"}],
  "metrics": [{"table": "Contact", "field": "ContactID", "agg": "COUNT"}],
  "filters": [],
  "time": null,
  "chart_hint": "bar",
  "title": "Contact Count by Role"
}
```
**Expected Chart Type:** `bar_chart`
**SQL Pattern:** `SELECT Role, COUNT(ContactID) AS ContactID_count FROM Contact GROUP BY Role ORDER BY ContactID_count DESC LIMIT 50`

## Invalid Prompts (Should Return not_available)

### 9. "Sales by city"
**Expected Response:**
```json
{
  "ok": false,
  "status": "not_available",
  "error": "Column 'city' is not available in any table.",
  "answer": "Column 'city' is not available in any table. Available tables: Account, Contact, Lead, Opportunity"
}
```

### 10. "Revenue by email"
**Expected Response:**
```json
{
  "ok": false,
  "status": "not_available",
  "error": "Column 'Email' in table 'Contact' contains sensitive information and cannot be used for charting.",
  "answer": "Column 'Email' in table 'Contact' contains sensitive information and cannot be used for charting."
}
```

### 11. "Products by category"
**Expected Response:**
```json
{
  "ok": false,
  "status": "not_available",
  "error": "Table 'Product' is not available. Available tables: Account, Contact, Lead, Opportunity",
  "answer": "Table 'Product' is not available. Available tables: Account, Contact, Lead, Opportunity"
}
```

## Response Format

All successful responses follow this format:
```json
{
  "ok": true,
  "status": "ok",
  "answer": "Here's a bar chart showing Revenue_sum by Region.",
  "chart": {
    "type": "bar_chart",
    "title": "Revenue by Region",
    "xField": "Region",
    "yField": "Revenue_sum"
  },
  "rows": [...],
  "chart_json": {...},
  "raw_data": [...],
  "sql": "SELECT Region, SUM(Revenue) AS Revenue_sum FROM Account GROUP BY Region ORDER BY Revenue_sum DESC LIMIT 50"
}
```

## Status Values

- `ok`: Chart generated successfully
- `no_data`: SQL executed but returned 0 rows
- `not_available`: Requested fields don't exist in schema or are PII
- `error`: SQL execution or chart rendering error

