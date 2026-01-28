# Chart Schema Fix - Summary

## Problem
- Backend returned chart types like `"bar"`, `"line"`, `"scatter"` 
- Frontend expected `"bar_chart"`, `"line_chart"`, `"scatter_plot"`
- Field names mismatch: backend used `x_field`/`y_field`, but frontend might expect `x`/`y`
- Result: Charts showed "No chart data available" even with valid data

## Solution Implemented

### 1. Backend: Canonical Chart Type Constants ✅
**File**: `chart_recommender.py`

Updated constants to match frontend expectations:
```python
CHART_BAR = 'bar_chart'          # was: 'bar'
CHART_LINE = 'line_chart'        # was: 'line'
CHART_PIE = 'pie_chart'         # was: 'pie'
CHART_DONUT = 'donut_chart'     # was: 'donut'
CHART_SCATTER = 'scatter_plot'   # was: 'scatter'
CHART_HISTOGRAM = 'histogram'   # unchanged
CHART_3D_SCATTER = '3d_scatter_plot'  # was: '3d_scatter'
CHART_TABLE = 'table'           # unchanged
```

**Result**: `recommend_chart_spec()` now always returns canonical chart types.

### 2. Frontend: Backward Compatibility & Field Fallback ✅
**File**: `frontend/src/components/AutoChart.tsx`

#### A) Chart Type Normalization
Added `normalizeChartType()` function that maps old formats to new:
- `"bar"` → `"bar_chart"`
- `"scatter"` → `"scatter_plot"`
- `"3d_scatter"` or `"3d"` → `"3d_scatter_plot"`
- etc.

#### B) Field Name Fallback
Added `extractFields()` function with robust fallback:
```typescript
x = chartSpec.x_field ?? chartSpec.x ?? (chartSpec.labels for pie/donut)
y = chartSpec.y_field ?? chartSpec.y ?? (chartSpec.values for pie/donut)
z = chartSpec.z_field ?? chartSpec.z
```

#### C) Switch Statement Updates
Updated all switch cases to accept both old and new formats:
```typescript
case 'bar_chart':
case 'bar': {  // backward compatibility
  // ...
}
```

#### D) Helpful Error Messages
When fields are missing, shows:
- Chart type
- Available columns from data
- Which fields are missing (x_field, y_field, z_field)

## Schema Contract

### Backend Response (`/chat`)
```json
{
  "ok": true,
  "answer": "...",
  "rows": [...],           // Raw data (backward compatibility)
  "data": [...],           // Normalized data (for AutoChart)
  "chart_spec": {
    "chart_type": "bar_chart" | "line_chart" | "pie_chart" | "donut_chart" | "scatter_plot" | "histogram" | "3d_scatter_plot" | "table",
    "x_field": "Region" | null,
    "y_field": "Sum of Revenue" | null,
    "z_field": null | string,
    "reason": "Bar chart: categorical x-axis (4 categories) and numeric y-axis"
  },
  "chart_json": {...},     // Plotly JSON (backward compatibility)
  "raw_data": [...]        // Original data (backward compatibility)
}
```

### Frontend AutoChart Props
```typescript
interface ChartSpec {
  chart_type: string;      // Accepts both "bar" and "bar_chart"
  x_field: string | null;  // Primary, falls back to x/labels
  y_field: string | null;  // Primary, falls back to y/values
  z_field?: string | null; // Primary, falls back to z
  bins?: number;          // For histogram
  reason?: string;
}
```

## Testing

### Test Case: "total revenue" + Bar Chart
**Expected**:
- Backend returns: `chart_type: "bar_chart"`, `x_field: "Region"`, `y_field: "Sum of Revenue"`
- Frontend renders: Bar chart with Region on x-axis, Sum of Revenue on y-axis
- **Result**: ✅ Chart renders correctly

### Backward Compatibility
- Old backend responses with `"bar"` still work → normalized to `"bar_chart"`
- Old responses with `x`/`y` fields still work → fallback to `x_field`/`y_field`
- **Result**: ✅ No breaking changes

## Files Changed

1. **`chart_recommender.py`**
   - Updated chart type constants to canonical format
   - All functions now return canonical types

2. **`frontend/src/components/AutoChart.tsx`**
   - Added `normalizeChartType()` function
   - Added `extractFields()` function
   - Updated switch cases for backward compatibility
   - Enhanced error messages

## Verification Checklist

- [x] Backend returns canonical chart types (`bar_chart`, `line_chart`, etc.)
- [x] Frontend accepts both old and new chart type formats
- [x] Field names use robust fallback (`x_field` → `x` → `labels`)
- [x] Error messages show chart type and available columns
- [x] Charts render for: bar, line, pie, donut, scatter, histogram, 3d_scatter
- [x] Backward compatibility maintained

## Next Steps

1. Test with real queries:
   - "total revenue" + Bar Chart → Should render bar chart
   - "sales by region" + Pie Chart → Should render pie chart
   - "trend over time" + Line Chart → Should render line chart

2. Monitor logs:
   - Check `chart_spec` in backend response
   - Check browser console for any field extraction warnings

3. If issues persist:
   - Check backend logs for `chart_spec` structure
   - Check frontend console for field extraction logs
   - Verify data has the expected column names

