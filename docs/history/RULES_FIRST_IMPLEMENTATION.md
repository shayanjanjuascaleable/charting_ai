# Rules-First SQL Implementation Summary

## Goal
Implement deterministic SQL generation using rules to avoid Gemini quota limits when chart type is selected.

## Implementation

### 1. New Module: `rule_sql.py` ✅

#### Functions:
- **`get_schema_map(db_path)`**: Introspects SQLite schema using `PRAGMA table_info`
  - Returns: `{ "Account": { "columns": [...], "numeric_columns": [...], "text_columns": [...] }, ... }`
  - Cached in memory at startup for speed

- **`build_rule_sql(message, forced_chart_type, schema)`**: Generates SQL using deterministic rules
  - Returns: `{ "table": "...", "sql": "...", "reason": "..." }` or `None`
  - Rules implemented:
    1. Revenue/Sales queries → Account table with Revenue column
    2. Count queries → Lead/Contact/Opportunity with Status/Source
    3. Opportunities/Pipeline → Opportunity table by Stage/Region
    4. Generic "X by Y" pattern → Find field in any table
    5. Scatter plot → 2 numeric columns, LIMIT 3000
    6. Histogram → 1 numeric column, LIMIT 5000
    7. 3D Scatter → 3 numeric columns, LIMIT 2000

### 2. Updated `/chat` Endpoint ✅

#### Flow:
1. **Normalize `forced_chart_type`** (if present)
   - Logs: `incoming_chart_type`, `normalized_chart_type`, `final_chart_type`

2. **Rules-First Logic**:
   - If `forced_chart_type` is present:
     - Try `build_rule_sql(message, normalized_chart_type, schema)`
     - If rule matches:
       - Execute SQL directly
       - Build `chart_json` using existing chart builder
       - Return response **WITHOUT calling Gemini**
       - Log: `[RULE_SQL] matched_rule reason=..., table=..., sql=...`
       - Log: `[CHAT_FLOW] used_rules=true used_gemini=false`
     - If no rule matches:
       - Return helpful message: "I couldn't match a rule for that request. Try phrasing like: 'revenue by region'..."
       - Log: `[RULE_SQL] no_match`
       - Log: `[CHAT_FLOW] used_rules=false used_gemini=false (no rule match)`

3. **Gemini Fallback**:
   - Only called if:
     - Rules didn't match AND `forced_chart_type` is missing, OR
     - Rules didn't match AND user wants to try Gemini anyway
   - Log: `[CHAT_FLOW] used_rules=false used_gemini=true`

4. **Gemini 429 Handling**:
   - Returns HTTP 200 (not 429)
   - Message: "AI limit reached right now. Please try again in a minute."
   - UI doesn't break

### 3. Schema Caching ✅

- **Module-level cache**: `RULE_SCHEMA_CACHE` loaded at startup
- **Lazy loading**: If cache is None, loads on first request
- **Performance**: Schema introspection happens once, not per request

### 4. Tests ✅

**File**: `tests/test_rule_sql.py`

Test cases:
- ✅ `test_total_revenue_bar_chart`: "total revenue" → Account SUM Revenue
- ✅ `test_revenue_by_region`: "revenue by region" → Account GROUP BY Region
- ✅ `test_count_leads_by_status`: "count leads by status" → Lead GROUP BY Status
- ✅ `test_opportunities_by_stage`: "opportunities by stage" → Opportunity GROUP BY Stage
- ✅ `test_scatter_plot_two_numeric`: Scatter plot → 2 numeric columns, LIMIT 3000
- ✅ `test_histogram_one_numeric`: Histogram → 1 numeric column, LIMIT 5000

## Example Flows

### Flow 1: Rules Match (No Gemini)
```
Request: { "message": "total revenue by region", "forced_chart_type": "bar_chart" }
→ Normalize: "bar_chart"
→ build_rule_sql() matches: "revenue by region"
→ SQL: SELECT Region, SUM(Revenue) AS "Sum of Revenue" FROM Account GROUP BY Region ...
→ Execute SQL
→ Build chart_json
→ Return: { ok: true, chart_json: {...}, rows: [...] }
→ Log: [CHAT_FLOW] used_rules=true used_gemini=false
```

### Flow 2: No Rule Match (Helpful Message)
```
Request: { "message": "weird query", "forced_chart_type": "bar_chart" }
→ Normalize: "bar_chart"
→ build_rule_sql() returns None
→ Return: { ok: true, answer: "I couldn't match a rule...", chart_json: null, suggestions: [...] }
→ Log: [CHAT_FLOW] used_rules=false used_gemini=false (no rule match)
```

### Flow 3: Gemini Fallback
```
Request: { "message": "complex query", "forced_chart_type": null }
→ No forced_chart_type, try rules first (optional)
→ Rules don't match
→ Call Gemini
→ Process Gemini response
→ Return: { ok: true, chart_json: {...}, rows: [...] }
→ Log: [CHAT_FLOW] used_rules=false used_gemini=true
```

### Flow 4: Gemini 429 (Graceful)
```
Request: { "message": "...", "forced_chart_type": null }
→ Call Gemini
→ Gemini returns 429 ResourceExhausted
→ Return HTTP 200: { ok: true, answer: "AI limit reached right now. Please try again in a minute.", chart_json: null }
→ UI doesn't break
```

## Logging

### Rule SQL Logs:
- `[RULE_SQL] matched_rule reason='...', table='...', sql='...'`
- `[RULE_SQL] no_match for message: '...', chart_type: '...'`
- `[RULE_SQL] Schema cache loaded: N tables`

### Chat Flow Logs:
- `[CHAT_FLOW] request_id=... used_rules=true/false used_gemini=true/false`

### Request Trace Logs:
- `[REQUEST_TRACE] Chart type normalization: incoming_chart_type=..., normalized_chart_type=..., final_chart_type=...`

## Files Changed

1. **`rule_sql.py`** (NEW)
   - `get_schema_map()`: Schema introspection
   - `build_rule_sql()`: Rule-based SQL generation

2. **`app.py`**
   - Added `rule_sql` import
   - Added `RULE_SCHEMA_CACHE` module-level variable
   - Updated `/chat` endpoint with rules-first logic
   - Added logging for rules vs Gemini usage

3. **`tests/test_rule_sql.py`** (NEW)
   - Unit tests for rule-based SQL generation

## Verification

### Test Case 1: "total revenue" + Bar Chart
```bash
POST /chat
{
  "message": "total revenue",
  "forced_chart_type": "bar_chart",
  "language": "en"
}
```
**Expected**:
- ✅ No Gemini call
- ✅ SQL: `SELECT SUM(Revenue) AS "Total Revenue" FROM Account`
- ✅ Returns `chart_json` and `rows`
- ✅ Log: `[CHAT_FLOW] used_rules=true used_gemini=false`

### Test Case 2: "total revenue by region" + Bar Chart
```bash
POST /chat
{
  "message": "total revenue by region",
  "forced_chart_type": "bar_chart",
  "language": "en"
}
```
**Expected**:
- ✅ No Gemini call
- ✅ SQL: `SELECT Region, SUM(Revenue) AS "Sum of Revenue" FROM Account GROUP BY Region ORDER BY "Sum of Revenue" DESC LIMIT 50`
- ✅ Returns bar chart with Region on x-axis, Sum of Revenue on y-axis
- ✅ Log: `[CHAT_FLOW] used_rules=true used_gemini=false`

### Test Case 3: Rapid Queries (Gemini Quota Exceeded)
```bash
# Send 10 rapid queries
```
**Expected**:
- ✅ If Gemini hits 429, returns HTTP 200 with graceful message
- ✅ UI doesn't break
- ✅ User can retry

## Running Tests

```bash
# Run unit tests
python -m pytest tests/test_rule_sql.py -v

# Or using unittest
python -m unittest tests.test_rule_sql -v
```

## Benefits

1. **Reduced Gemini Quota Usage**: Rules handle common queries without API calls
2. **Faster Response**: Rules execute instantly (no API latency)
3. **Deterministic**: Same query always produces same SQL
4. **Graceful Degradation**: If rules don't match, helpful message instead of error
5. **Backward Compatible**: Existing Gemini flow still works when rules don't match

## Future Enhancements

- Add more rules for common query patterns
- Learn from user queries to improve rule matching
- Cache rule results for identical queries
- Add rule priority/confidence scoring

