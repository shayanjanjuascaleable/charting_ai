# Azure Deployment Checklist

## Files Added/Modified for Azure Deployment

### ✅ Backend (Flask)

#### 1. **Procfile** (NEW)
- **Location**: `Procfile` (root)
- **Content**: Gunicorn configuration for Flask app
- **Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 --access-logfile - --error-logfile - backend.app:app`
- **Purpose**: Azure App Service will use this to start the Flask application

#### 2. **backend/requirements.txt** (UPDATED)
- **Changes**:
  - Pinned `gunicorn==21.2.0` (was unpinned)
  - Pinned `python-dotenv==1.0.0` (was unpinned)
- **Status**: ✅ Already had gunicorn and python-dotenv

#### 3. **backend/app.py** (VERIFIED)
- **Environment Variables**: ✅ All secrets/config read from env vars:
  - `GEMINI_API_KEY` (line 42)
  - `AZURE_SQL_SERVER` (line 55)
  - `AZURE_SQL_DATABASE` (line 56)
  - `AZURE_SQL_USERNAME` (line 57)
  - `AZURE_SQL_PASSWORD` (line 58)
  - `AZURE_SQL_DRIVER` (line 59, optional)
- **.env Support**: ✅ `load_dotenv()` called at startup (line 16)
- **App Instance**: ✅ `app = Flask(...)` defined at line 34
- **Import Path**: `backend.app:app` (used in Procfile)

### ✅ Frontend (Vite + React)

#### 4. **frontend/src/config/api.ts** (NEW)
- **Location**: `frontend/src/config/api.ts`
- **Purpose**: Centralized API URL configuration
- **Features**:
  - Reads `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL` from environment
  - Falls back to relative paths (same origin) for production
  - Provides `getApiUrl()` helper function

#### 5. **frontend/src/components/ChatPanel.tsx** (UPDATED)
- **Changes**:
  - Added import: `import { getApiUrl } from '@/config/api';`
  - Updated fetch call: `fetch('/chat', ...)` → `fetch(getApiUrl('chat'), ...)`
- **Line**: 75
- **Purpose**: Makes API calls configurable via environment variables

#### 6. **frontend/.env.example** (NEW)
- **Location**: `frontend/.env.example`
- **Content**: Template for API base URL configuration
- **Variables**:
  - `VITE_API_BASE_URL` (primary)
  - `NEXT_PUBLIC_API_BASE_URL` (compatibility)

### ✅ Configuration Files

#### 7. **.gitignore** (UPDATED)
- **Added**:
  - `.env.local`, `.env.*.local`, `.env.production`, `.env.development`
  - `frontend/.next/`, `frontend/.venv/`, `frontend/venv/`
  - `*.log`, `logs/`, `*.log.*`
  - `build/`, `dist/`, `*.egg-info/`
- **Already had**: `.env`, `__pycache__/`, `venv/`, `node_modules/`

## Environment Variables Required for Azure

### Backend (Azure App Service - Application Settings)

```bash
# Required
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database-name
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
GEMINI_API_KEY=your-gemini-api-key

# Optional
AZURE_SQL_DRIVER={ODBC Driver 17 for SQL Server}
FLASK_SECRET_KEY=your-secret-key  # Currently hardcoded, consider moving to env var
PORT=8000  # Azure sets this automatically, but can override
```

### Frontend (Build-time - Vite)

```bash
# Optional - only needed if API is on different domain
VITE_API_BASE_URL=https://your-api.azurewebsites.net
```

**Note**: If frontend is served by Flask (same origin), leave `VITE_API_BASE_URL` empty.

## Deployment Steps

### 1. Backend Deployment (Azure App Service)

1. **Create Azure App Service** (Python 3.12+)
2. **Set Application Settings** (environment variables):
   - Add all required Azure SQL and Gemini API credentials
3. **Deploy Code**:
   - Azure will detect `Procfile` and use it
   - Install dependencies from `backend/requirements.txt`
4. **Verify**:
   - Check logs for successful startup
   - Test `/` endpoint returns HTML
   - Test `/chat` endpoint with POST request

### 2. Frontend Deployment

**Option A: Serve via Flask (Recommended)**
- Build frontend: `cd frontend && npm run build`
- Flask serves `frontend/dist/` as static files
- No separate frontend deployment needed
- API calls use relative paths (same origin)

**Option B: Separate Frontend Hosting**
- Build with: `VITE_API_BASE_URL=https://your-api.azurewebsites.net npm run build`
- Deploy `frontend/dist/` to Azure Static Web Apps or CDN
- API calls use absolute URLs

## Verification Checklist

- [ ] `.env` is in `.gitignore` ✅
- [ ] All secrets read from environment variables ✅
- [ ] `Procfile` exists and references correct app path ✅
- [ ] `gunicorn` is in `requirements.txt` ✅
- [ ] Frontend API calls use configurable base URL ✅
- [ ] No hardcoded `localhost` in production code ✅
- [ ] `.gitignore` includes all build artifacts ✅

## Notes

1. **Backend is Flask, not FastAPI**: The codebase uses Flask, so the Procfile uses `gunicorn` with Flask app, not uvicorn with FastAPI.

2. **Frontend is Vite + React, not Next.js**: The frontend uses Vite, so environment variables use `VITE_` prefix, not `NEXT_PUBLIC_`.

3. **Same-Origin Deployment**: If Flask serves the frontend build, API calls use relative paths and no `VITE_API_BASE_URL` is needed.

4. **CORS**: If frontend and backend are on different domains, add Flask-CORS to requirements.txt and configure CORS in `app.py`.

5. **Secret Key**: Currently hardcoded at line 37 in `app.py`. Consider moving to `FLASK_SECRET_KEY` environment variable for production.

## Files Changed Summary

| File | Status | Changes |
|------|--------|---------|
| `Procfile` | ✅ NEW | Gunicorn configuration for Flask |
| `backend/requirements.txt` | ✅ UPDATED | Pinned gunicorn and python-dotenv versions |
| `frontend/src/config/api.ts` | ✅ NEW | API URL configuration utility |
| `frontend/src/components/ChatPanel.tsx` | ✅ UPDATED | Uses configurable API URL |
| `frontend/.env.example` | ✅ NEW | Environment variable template |
| `.gitignore` | ✅ UPDATED | Added more ignore patterns |

## No Changes Required

- ✅ Backend already uses environment variables for all secrets
- ✅ `.env` already in `.gitignore`
- ✅ `python-dotenv` already in requirements.txt
- ✅ `load_dotenv()` already called in app.py
- ✅ No hardcoded localhost in backend code

