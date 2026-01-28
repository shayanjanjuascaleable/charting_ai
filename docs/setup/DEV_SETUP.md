# Development Setup Guide

## Project Structure

This is a **Flask backend + Vite/React frontend** application.

- **Backend**: Flask (Python) on port 5000
- **Frontend**: Vite/React (TypeScript) - builds to `frontend/dist/`

## Quick Start

### Option 1: Production Mode (Recommended for Testing)

**Step 1: Build the Frontend**
```powershell
cd frontend
npm install
npm run build
cd ..
```

**Step 2: Run the Backend**
```powershell
python app.py
```

**Step 3: Open Browser**
- Navigate to: `http://localhost:5000`
- The Flask server serves the built React app

### Option 2: Development Mode (Hot Reload)

**Terminal 1: Backend (Flask)**
```powershell
python app.py
```
Backend runs on: `http://localhost:5000`

**Terminal 2: Frontend (Vite Dev Server)**
```powershell
cd frontend
npm install
npm run dev
```
Frontend dev server runs on: `http://localhost:8080`

**Important**: In development mode:
- Use `http://localhost:8080` to access the app (not port 5000)
- Vite dev server proxies `/chat` API calls to Flask backend (port 5000)
- Hot reload is enabled for frontend changes
- Backend changes require Flask restart

## Build Process

### Frontend Build Output

When you run `npm run build` in the `frontend/` directory:
- Output goes to: `frontend/dist/`
- Main file: `frontend/dist/index.html`
- Assets: `frontend/dist/assets/*.js`, `frontend/dist/assets/*.css`

### Backend Static Serving

The Flask backend serves:
- `GET /` → `frontend/dist/index.html`
- `GET /insights` → `frontend/dist/index.html` (client-side routing)
- `GET /assets/*` → `frontend/dist/assets/*`
- `POST /chat` → Flask API endpoint (not static)

## Troubleshooting

### White Screen / "Frontend Build Not Found"

**Symptom**: Browser shows white screen or error message

**Solution**:
1. Check if `frontend/dist/index.html` exists
2. If not, run:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```
3. Restart Flask: `python app.py`
4. Refresh browser

### Build Fails with "npm: command not found"

**Solution**: Install Node.js from https://nodejs.org/ (LTS version)

### Port Already in Use

**Backend (port 5000)**:
```powershell
# Find process using port 5000
netstat -ano | findstr :5000
# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Frontend Dev Server (port 8080)**:
- Change port in `frontend/vite.config.ts`:
  ```typescript
  server: {
    port: 3000,  // Change to available port
  }
  ```

### Frontend Build Succeeds but Still Shows Error

**Check**:
1. Verify `frontend/dist/index.html` exists
2. Check Flask logs for the exact path it's looking for
3. Ensure you're in the project root when running `python app.py`
4. Check file permissions (Windows should be fine)

## File Structure

```
vibecharting/
├── app.py                 # Flask backend
├── frontend/
│   ├── src/              # React source code
│   ├── dist/             # Build output (created by npm run build)
│   ├── package.json      # Frontend dependencies
│   └── vite.config.ts    # Vite configuration
└── data/
    └── charting_ai.db     # SQLite database
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=0
FLASK_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///./data/charting_ai.db

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_ENABLED=true
```

## Development Workflow

### Making Frontend Changes

**Development Mode** (recommended):
1. Run `npm run dev` in `frontend/` directory
2. Access app at `http://localhost:8080`
3. Changes hot-reload automatically
4. No need to rebuild

**Production Testing**:
1. Make changes to frontend code
2. Run `npm run build` in `frontend/` directory
3. Restart Flask: `python app.py`
4. Access app at `http://localhost:5000`

### Making Backend Changes

1. Edit Python files (`app.py`, etc.)
2. Restart Flask: `python app.py`
3. Changes take effect immediately

## Common Commands

### Windows PowerShell

**Build Frontend:**
```powershell
cd frontend
npm install          # First time only
npm run build
cd ..
```

**Run Backend:**
```powershell
python app.py
```

**Run Both (Development):**
```powershell
# Terminal 1
python app.py

# Terminal 2
cd frontend
npm run dev
```

**Check Build Status:**
```powershell
Test-Path "frontend\dist\index.html"
```

## Verification Checklist

After setup, verify:
- [ ] `frontend/dist/index.html` exists
- [ ] `frontend/dist/assets/` directory exists with `.js` and `.css` files
- [ ] Flask logs show: `[FRONTEND] ✓ React frontend build found and ready to serve`
- [ ] Browser at `http://localhost:5000` shows the app (not error page)
- [ ] `/chat` API endpoint works (test with a query)

## Next Steps

Once the build is complete:
1. The app should load at `http://localhost:5000`
2. Navigate to `/insights` to see the dashboard
3. Try asking a question in the chat to generate a chart

