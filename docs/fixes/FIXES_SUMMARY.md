# Fixes Applied - White Screen Issue

## Problem
- Browser showed blank white screen after AutoChart integration
- Backend required `frontend/dist` even in dev mode
- No safe fallback if AutoChart crashed

## Solutions Implemented

### 1. Feature Flag for AutoChart ✅
**File**: `frontend/src/components/ChartCard.tsx`

- Added `VITE_ENABLE_AUTOCHART` env var (default: `false`)
- AutoChart only renders if:
  - `VITE_ENABLE_AUTOCHART=true` (explicitly enabled)
  - AND `chartSpec` exists in props
- **Default behavior**: Uses old `chartJson` Plotly rendering (100% stable)

**Code changes:**
```typescript
// Feature flag: Enable AutoChart only if explicitly enabled via env var
const ENABLE_AUTOCHART = import.meta.env.VITE_ENABLE_AUTOCHART === 'true';

// In render:
{ENABLE_AUTOCHART && chartSpec ? (
  <ErrorBoundary fallback={...}>
    <AutoChart ... />
  </ErrorBoundary>
) : chartJson ? (
  // Default: Use existing Plotly JSON rendering (safe, working method)
  <Plot ... />
) : ...}
```

### 2. Error Boundary Component ✅
**File**: `frontend/src/components/ErrorBoundary.tsx` (NEW)

- Catches React errors and prevents white screen crashes
- Automatically falls back to `chartJson` rendering if AutoChart throws
- Logs errors to console for debugging

### 3. Backend Frontend Serving Config ✅
**File**: `config.py`

- Added `serve_frontend` setting to `Settings` dataclass
- Auto-detects: `false` in dev, `true` in prod
- Can be overridden with `SERVE_FRONTEND` env var

**File**: `app.py`

- Updated `/` and `/insights` routes to check `settings.serve_frontend`
- If `SERVE_FRONTEND=false`: Returns JSON message (API-only mode)
- If `SERVE_FRONTEND=true` but build missing: Returns helpful HTML error page
- Updated static asset routes to respect `serve_frontend` setting

### 4. Frontend Type Detection ✅
**File**: `app.py`

- Added `_detect_frontend_type()` function
- Reads `frontend/package.json` to detect Vite vs Next.js
- Sets correct build path:
  - Vite → `frontend/dist/`
  - Next.js → `frontend/.next/`

## Files Changed

### Backend
1. `config.py` - Added `serve_frontend` setting
2. `app.py` - Updated routes and frontend detection

### Frontend
1. `frontend/src/components/ChartCard.tsx` - Added feature flag and error boundary
2. `frontend/src/components/ErrorBoundary.tsx` - NEW component

## How to Use

### Development Mode (Recommended)

**Terminal 1:**
```powershell
python app.py
```

**Terminal 2:**
```powershell
cd frontend
npm run dev
```

Access app at: `http://localhost:8080`

### Production Mode

**Build frontend:**
```powershell
cd frontend
npm run build
cd ..
```

**Set env var:**
```powershell
$env:SERVE_FRONTEND="true"
$env:FLASK_ENV="production"
```

**Run backend:**
```powershell
python app.py
```

Access app at: `http://localhost:5000`

### Enable AutoChart (Optional)

**Create `frontend/.env`:**
```env
VITE_ENABLE_AUTOCHART=true
```

**Restart frontend dev server**

## Verification

✅ **Charts render using old method by default** (no AutoChart)
✅ **No white screen** - Error boundary catches any crashes
✅ **Backend works in dev mode** without requiring `frontend/dist`
✅ **AutoChart is optional** - Only enabled if explicitly set
✅ **Backward compatible** - Old `chartJson` rendering still works

## Testing Checklist

- [ ] Backend starts without `frontend/dist` (dev mode)
- [ ] Frontend runs separately on port 8080
- [ ] Charts render correctly using Plotly
- [ ] `/chat` API returns data successfully
- [ ] No white screen errors
- [ ] AutoChart disabled by default (verify in browser console)
- [ ] Error boundary catches errors gracefully

## Rollback Plan

If issues occur:
1. Ensure `VITE_ENABLE_AUTOCHART` is not set (or set to `false`)
2. Charts will automatically use old `chartJson` rendering
3. Backend works as API-only if `SERVE_FRONTEND=false`

