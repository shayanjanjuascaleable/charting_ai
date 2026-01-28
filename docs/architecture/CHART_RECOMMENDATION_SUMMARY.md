# Automatic Chart Recommendation Implementation Summary

## Overview
Implemented automatic chart recommendation and normalization system that analyzes data structure and user hints to recommend optimal chart types, then normalizes data accordingly.

## Files Created/Modified

### A) Backend Module: `chart_recommender.py` (NEW)

**Functions:**
1. **`recommend_chart_spec(rows, user_hint)`**
   - Analyzes data structure using pandas
   - Detects numeric, datetime, and categorical columns
   - Applies chart-specific rules:
     - **3D Scatter**: 3+ numeric columns + "3d" in hint
     - **Histogram**: 1 numeric column + "histogram"/"distribution" in hint
     - **Scatter**: 2+ numeric columns
     - **Line**: datetime x-axis + numeric y-axis + "trend"/"over time" in hint
     - **Pie/Donut**: 1 categorical + 1 numeric, ≤8 categories, non-negative values
     - **Bar**: 1 categorical + 1 numeric (default)
     - **Table**: Fallback if no suitable chart

2. **`normalize_for_chart(rows, chart_spec)`**
   - Applies chart-specific normalization:
     - **Pie/Donut**: Limits to MAX_PIE_CATEGORIES (8), combines rest as "Other"
     - **Bar**: Limits to top 12 categories + "Other" if >15 categories
     - **Line**: Sorts by datetime x-axis ascending
     - **Scatter**: Samples to MAX_SCATTER_ROWS (3000) if larger
     - **3D Scatter**: Samples to MAX_3D_SCATTER_ROWS (2000) if larger
     - **Histogram**: Keeps only numeric column
     - **Table**: Limits to MAX_TABLE_ROWS (200)

**Constants:**
- `MAX_PIE_CATEGORIES = 8`
- `MAX_BAR_CATEGORIES = 15`
- `MAX_SCATTER_ROWS = 3000`
- `MAX_3D_SCATTER_ROWS = 2000`
- `DEFAULT_HISTOGRAM_BINS = 20`
- `MAX_TABLE_ROWS = 200`

### B) Backend Integration: `app.py` (MODIFIED)

**Changes:**
1. **Import chart recommender:**
   ```python
   from chart_recommender import recommend_chart_spec, normalize_for_chart, MAX_TABLE_ROWS
   ```

2. **Updated `/chat` endpoint:**
   - After filtering PII from raw data:
     - Calls `recommend_chart_spec(raw_data_filtered, user_hint=user_message)`
     - Calls `normalize_for_chart(raw_data_filtered, chart_spec)`
   - Adds `chart_spec` to response
   - Adds `data` field (normalized data)
   - Keeps `rows` and `chart_json` for backward compatibility

3. **Response structure:**
   ```json
   {
     "ok": true,
     "answer": "string",
     "chart": {...},  // Backward compatibility
     "rows": [...],   // Backward compatibility
     "data": [...],   // NEW: Normalized data
     "chart_spec": {  // NEW: Automatic chart recommendation
       "chart_type": "bar|line|pie|donut|scatter|histogram|3d_scatter|table",
       "x_field": "string|null",
       "y_field": "string|null",
       "z_field": "string|null",
       "bins": number,  // For histogram
       "reason": "string"
     },
     "chart_json": {...}  // Backward compatibility (Plotly spec)
   }
   ```

4. **Logging:**
   - Logs recommended chart type and reason
   - Logs normalization results (row count before/after)

### C) Frontend Component: `AutoChart.tsx` (NEW)

**Features:**
- Renders Plotly charts based on `chart_spec.chart_type`
- Supports all chart types:
  - `bar`: Plotly bar chart
  - `line`: scatter mode=lines
  - `pie`: pie hole=0
  - `donut`: pie hole=0.4
  - `scatter`: scatter mode=markers
  - `histogram`: histogram
  - `3d_scatter`: scatter3d
  - `table`: HTML table (max 200 rows)
- Theme-aware (dark/light mode)
- Error handling with fallback messages
- Never crashes on missing fields

### D) Frontend Integration

**`ChatPanel.tsx` (MODIFIED):**
- Checks for `chart_spec` first (new format)
- Falls back to `chart_json` (backward compatibility)
- Passes `chartSpec` and normalized `data` to `onChartGenerated`

**`ChartCard.tsx` (MODIFIED):**
- Accepts optional `chartSpec` prop
- Uses `AutoChart` component if `chartSpec` is provided
- Falls back to existing Plotly JSON rendering if `chartJson` is provided

**`Insights.tsx` (MODIFIED):**
- Updated `ChartData` interface to include `chartSpec?: any`
- Passes `chartSpec` to `ChartCard` component

### E) Tests: `tests/test_chart_recommender.py` (NEW)

**Test Cases:**
1. ✅ Sales per region → bar chart
2. ✅ Trend over time → line chart
3. ✅ Share by stage (≤8) → pie/donut
4. ✅ Share by stage (>8) → bar fallback
5. ✅ Profit vs revenue → scatter
6. ✅ Distribution → histogram
7. ✅ 3 numeric columns + "3d" → 3d_scatter
8. ✅ Bar normalization (top 12 + Other)
9. ✅ Pie normalization (max categories)

## Chart Rules Implemented

### Pie/Donut
- ✅ Only if category count ≤ 8 AND values non-negative
- ✅ Auto-switch to Bar if conditions not met
- ✅ Combines excess categories as "Other"

### Bar
- ✅ If categories > 15, returns top 12 + "Other"
- ✅ Groups and sums if duplicate categories

### Line
- ✅ Only when x is datetime-like
- ✅ Sorts ascending by time
- ✅ Detects datetime strings automatically

### Scatter
- ✅ Needs 2 numeric columns
- ✅ Samples down to max 3000 rows if larger

### 3D Scatter
- ✅ Needs 3 numeric columns
- ✅ Samples down to max 2000 rows if larger
- ✅ Requires "3d" in user hint

### Histogram
- ✅ Needs 1 numeric column
- ✅ Default bins=20
- ✅ Filters out non-numeric values

### Table (Fallback)
- ✅ Limits to first 200 rows
- ✅ Renders as HTML table in frontend

## Backward Compatibility

✅ **Maintained:**
- Existing `chart_json` field still returned
- Existing `rows` field still returned
- Existing `chart` metadata still returned
- Frontend falls back to old format if `chart_spec` not present

✅ **New Fields (additive only):**
- `chart_spec`: New automatic recommendation
- `data`: Normalized data (can differ from `rows`)

## Security & Compatibility

✅ **No breaking changes:**
- All existing routes unchanged
- Response shape extended (not modified)
- Safe SQL + PII filtering unchanged
- No hardcoded secrets

## Usage Example

**Request:**
```json
POST /chat
{
  "message": "total sales by region",
  "language": "en",
  "forced_chart_type": "bar_chart"
}
```

**Response:**
```json
{
  "ok": true,
  "answer": "Here's a Bar chart showing Revenue by Region.",
  "data": [
    {"Region": "North", "Revenue": 1000},
    {"Region": "South", "Revenue": 1500},
    {"Region": "East", "Revenue": 800}
  ],
  "chart_spec": {
    "chart_type": "bar",
    "x_field": "Region",
    "y_field": "Revenue",
    "z_field": null,
    "reason": "Bar chart: categorical x-axis (3 categories) and numeric y-axis"
  },
  "rows": [...],  // Original data
  "chart_json": {...}  // Plotly spec (backward compatibility)
}
```

## Testing

Run tests:
```bash
python -m pytest tests/test_chart_recommender.py -v
```

## Summary of Changes

1. ✅ Created `chart_recommender.py` with recommendation and normalization logic
2. ✅ Updated `/chat` endpoint to use chart recommendation
3. ✅ Created `AutoChart.tsx` React component
4. ✅ Updated `ChartCard.tsx` to use `AutoChart`
5. ✅ Updated `ChatPanel.tsx` to handle `chart_spec`
6. ✅ Updated `Insights.tsx` to pass `chartSpec` to `ChartCard`
7. ✅ Added comprehensive tests
8. ✅ Maintained full backward compatibility

The system now automatically recommends optimal chart types based on data structure and user hints, normalizes data accordingly, and renders charts consistently without frontend guessing.

