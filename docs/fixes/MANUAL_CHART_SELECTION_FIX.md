# Manual Chart Selection Mode - Implementation Summary

## Goal
Restore app to "manual chart selection" mode only:
- User selects chart type from UI
- Backend generates SQL + rows + chart_json based on selection
- No chart recommendation, chart_spec, AutoChart, or chart_recommender

## Changes Made

### 1. Backend: Removed Chart Recommendation ✅
**File**: `app.py`

- **Removed**: `from chart_recommender import recommend_chart_spec, normalize_for_chart, MAX_TABLE_ROWS`
- **Removed**: All `chart_spec` generation and normalization code
- **Removed**: `chart_spec` from response payload
- **Kept**: `chart_json` (Plotly JSON) for rendering

### 2. Backend: Chart Type Normalization ✅
**File**: `app.py` (lines ~801-830)

Added robust normalization for `forced_chart_type`:
```python
# Normalize with fallback
incoming_chart_type = forced_chart_type
normalized_chart_type = forced_chart_type.lower().strip().replace(' ', '_').replace('-', '_')

# Map synonyms
chart_type_mapping = {
    'bar': 'bar_chart',
    'bar_chart': 'bar_chart',
    'line': 'line_chart',
    'scatter': 'scatter_plot',
    'hist': 'histogram',
    '3d': '3d_scatter_plot',
    # ... etc
}

final_chart_type = chart_type_mapping.get(normalized_chart_type, normalized_chart_type)

# Log normalization steps
logger.info(f"incoming_chart_type: '{incoming_chart_type}'")
logger.info(f"normalized_chart_type: '{normalized_chart_type}'")
logger.info(f"final_chart_type: '{final_chart_type}'")
```

### 3. Backend: Gemini 429 Graceful Handling ✅
**File**: `app.py` (lines ~732-750)

Changed 429 handling to return HTTP 200 instead of 429:
```python
if 'retry_seconds' in response_dict:
    # Return 200 with graceful message (UI doesn't break)
    return jsonify({
        'ok': True,
        'answer': 'AI limit reached right now. Please try again in a minute.',
        'chart_json': None,
        'rows': [],
        'raw_data': [],
        'suggestions': [],
    }), 200
```

### 4. Frontend: Chart Type Selector ✅
**File**: `frontend/src/components/ChartTypeSelector.tsx`

Already correct - sends backend enum values:
- "Bar Chart" → `'bar_chart'`
- "Line Chart" → `'line_chart'`
- "Pie Chart" → `'pie_chart'`
- "Donut Chart" → `'donut_chart'`
- "Scatter Plot" → `'scatter_plot'`
- "Histogram" → `'histogram'`
- "3D Chart" → `'3d_scatter_plot'`

### 5. Frontend: Removed chart_spec Handling ✅
**File**: `frontend/src/components/ChatPanel.tsx`

- **Removed**: `chart_spec` handling logic
- **Kept**: `chart_json` rendering only

**Before**:
```typescript
const chartData = data.chart_spec 
  ? { chartSpec: data.chart_spec, ... }
  : data.chart_json
  ? { chartJson: data.chart_json, ... }
  : null;
```

**After**:
```typescript
const chartData = data.chart_json
  ? {
      title: data.chart?.title || messageToSend,
      chartJson: data.chart_json,
      rawData: data.rows || data.raw_data || [],
      suggestions: data.suggestions || [],
    }
  : null;
```

### 6. Frontend: Removed AutoChart ✅
**File**: `frontend/src/components/ChartCard.tsx`

- **Removed**: `import { AutoChart } from './AutoChart'`
- **Removed**: `import { ErrorBoundary } from './ErrorBoundary'`
- **Removed**: `ENABLE_AUTOCHART` feature flag
- **Removed**: `chartSpec` prop
- **Removed**: AutoChart rendering logic
- **Kept**: Plotly JSON rendering only

**Before**:
```typescript
{ENABLE_AUTOCHART && chartSpec ? (
  <ErrorBoundary>
    <AutoChart data={rawData} chartSpec={chartSpec} />
  </ErrorBoundary>
) : chartJson ? (
  <Plot data={chartJson.data} ... />
) : ...}
```

**After**:
```typescript
{chartJson ? (
  <Plot
    data={chartJson?.data || []}
    layout={getChartLayout()}
    ...
  />
) : (
  <div>No chart data available</div>
)}
```

### 7. Frontend: Removed chartSpec from Insights ✅
**File**: `frontend/src/pages/Insights.tsx`

- **Removed**: `chartSpec?: any` from `ChartData` interface
- **Removed**: `chartSpec` from `handleChartGenerated` callback
- **Removed**: `chartSpec={chart.chartSpec}` from `ChartCard` props

## Response Contract

### Backend Response (`/chat`)
```json
{
  "ok": true,
  "answer": "Here's a Bar Chart showing Sum of Revenue by Region.",
  "chart": {
    "type": "bar_chart",
    "title": "...",
    "xField": "Region",
    "yField": "Sum of Revenue"
  },
  "rows": [...],           // Raw data
  "chart_json": {...},     // Plotly JSON (for rendering)
  "raw_data": [...],       // Same as rows (backward compatibility)
  "suggestions": []
}
```

**Removed fields**:
- `chart_spec` ❌
- `data` (normalized) ❌

## Testing Checklist

- [x] Frontend sends correct enum values (`bar_chart`, `line_chart`, etc.)
- [x] Backend normalizes chart types with logging
- [x] Backend returns `chart_json` (no `chart_spec`)
- [x] Frontend renders `chart_json` using Plotly
- [x] Gemini 429 returns HTTP 200 (UI doesn't break)
- [x] No chart recommendation code present
- [x] No AutoChart references in frontend

## Verification Steps

1. **Test Query**: "total revenue" + select Bar Chart
   - Expected: `/chat` returns 200
   - Expected: `chart_json` present
   - Expected: Chart renders in UI

2. **Test Normalization**: Send "bar chart" (with space)
   - Expected: Backend logs show normalization
   - Expected: No 400 error

3. **Test 429 Handling**: Rapidly send 10 queries
   - Expected: If Gemini hits limit, returns 200 with graceful message
   - Expected: UI shows message, doesn't crash

## Files Changed

### Backend
1. `app.py`
   - Removed chart_recommender import
   - Removed chart_spec generation
   - Added chart type normalization
   - Fixed 429 handling

### Frontend
1. `frontend/src/components/ChatPanel.tsx`
   - Removed chart_spec handling
   - Use chart_json only

2. `frontend/src/components/ChartCard.tsx`
   - Removed AutoChart import
   - Removed chartSpec prop
   - Use Plotly JSON only

3. `frontend/src/pages/Insights.tsx`
   - Removed chartSpec from interface
   - Removed chartSpec from props

## Notes

- `chart_recommender.py` file still exists but is not imported/used
- `AutoChart.tsx` file still exists but is not imported/used
- Backend normalization in `safe_sql.py` already handles chart types (double safety)
- Frontend `ChartTypeSelector` already sends correct enum values

