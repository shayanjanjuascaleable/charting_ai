# Development Setup Guide (Fixed)

## Problem Fixed

The app was showing a blank white screen because:
1. AutoChart integration could crash the UI if chartSpec was invalid
2. Backend required `frontend/dist` to exist even in dev mode
3. No feature flag to safely enable/disable AutoChart

## Solution Implemented

### 1. Feature Flag for AutoChart
- **Env var**: `VITE_ENABLE_AUTOCHART` (default: `false`)
- **Behavior**: AutoChart only renders if flag is `true` AND `chartSpec` exists
- **Fallback**: Always falls back to old `chartJson` Plotly rendering (the working method)

### 2. Error Boundary
- Added `ErrorBoundary` component around AutoChart
- Prevents white screen crashes if AutoChart throws an error
- Automatically falls back to `chartJson` rendering

### 3. Backend Frontend Serving
- **Env var**: `SERVE_FRONTEND` (auto-detected: `false` in dev, `true` in prod)
- **Dev mode**: Backend is API-only, frontend runs separately
- **Prod mode**: Backend serves built frontend from `dist/`

### 4. Frontend Type Detection
- Automatically detects Vite vs Next.js by reading `package.json`
- Sets correct build path (`dist/` for Vite, `.next/` for Next.js)

## Running in Development (Windows PowerShell)

### Option 1: Separate Frontend/Backend (Recommended)

**Terminal 1 - Backend:**
```powershell
python app.py
```
Backend runs on `http://localhost:5000` (API only)

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```
Frontend runs on `http://localhost:8080` (with hot-reload)

**Access app at:** `http://localhost:8080`

The Vite proxy automatically forwards `/chat` requests to `http://localhost:5000`.

### Option 2: Backend Serves Built Frontend

**Build frontend:**
```powershell
cd frontend
npm install
npm run build
cd ..
```

**Set env var:**
```powershell
$env:SERVE_FRONTEND="true"
```

**Run backend:**
```powershell
python app.py
```

**Access app at:** `http://localhost:5000`

## Enabling AutoChart (Optional)

**To enable AutoChart feature:**

1. Create `.env` file in `frontend/` directory:
```env
VITE_ENABLE_AUTOCHART=true
```

2. Restart frontend dev server:
```powershell
cd frontend
npm run dev
```

**Note:** AutoChart is disabled by default to ensure stability. The old `chartJson` rendering method works 100% of the time.

## Environment Variables

### Backend (.env in project root)
```env
# Frontend serving (auto-detected: false in dev, true in prod)
SERVE_FRONTEND=false  # Set to true to serve built frontend

# Flask environment
FLASK_ENV=development

# Gemini API
GEMINI_API_KEY=your_key_here
GEMINI_ENABLED=true
```

### Frontend (.env in frontend/ directory)
```env
# Enable AutoChart feature (default: false)
VITE_ENABLE_AUTOCHART=false
```

## Verification

### Check Backend Logs
```
[FRONTEND] Frontend type detected: vite
[FRONTEND] SERVE_FRONTEND setting: False
[FRONTEND] Frontend serving disabled (SERVE_FRONTEND=false)
[FRONTEND] Backend is API-only. Run frontend separately: cd frontend && npm run dev
```

### Check Frontend Console
- No errors about AutoChart
- Charts render using Plotly (old method)
- `/chat` API calls succeed

## Troubleshooting

### White Screen Still Appears
1. Check browser console for JavaScript errors
2. Verify `VITE_ENABLE_AUTOCHART` is not set to `true` (or set it to `false`)
3. Clear browser cache and hard refresh (Ctrl+Shift+R)

### Charts Not Rendering
1. Check backend logs for `/chat` request errors
2. Verify backend is running on port 5000
3. Check frontend console for API call errors
4. Ensure `chartJson` field exists in backend response

### Backend Shows "Frontend Build NOT found"
This is **normal in dev mode** when `SERVE_FRONTEND=false`. 
- Backend is API-only
- Frontend runs separately via `npm run dev`
- This is the correct setup for development

## Production Deployment

1. Build frontend:
```powershell
cd frontend
npm run build
cd ..
```

2. Set environment:
```powershell
$env:FLASK_ENV="production"
$env:SERVE_FRONTEND="true"
```

3. Run backend:
```powershell
python app.py
```

Backend will serve the built frontend from `frontend/dist/`.

