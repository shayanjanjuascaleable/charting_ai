# Quick Build Guide - Windows PowerShell

## Problem: White Screen / "Frontend Build Not Found"

If you see a white screen or error message, the frontend hasn't been built yet.

## Solution: Build the Frontend

### Step 1: Install Node.js (if not already installed)

1. Download from: https://nodejs.org/ (choose **LTS** version)
2. Install and **restart PowerShell**
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

### Step 2: Build the Frontend

**Run these commands in PowerShell (from project root):**

```powershell
cd frontend
npm install
npm run build
cd ..
```

**Expected output:**
- Creates `frontend/dist/` directory
- Creates `frontend/dist/index.html`
- Creates `frontend/dist/assets/*.js` and `frontend/dist/assets/*.css`

### Step 3: Verify Build

```powershell
Test-Path "frontend\dist\index.html"
```

Should return: `True`

### Step 4: Run Flask

```powershell
python app.py
```

**Check logs for:**
```
[FRONTEND] ✓ React frontend build found and ready to serve
```

### Step 5: Open Browser

Navigate to: `http://localhost:5000`

You should now see the app (not a white screen).

## Development Mode (Optional)

If you want hot-reload during development:

**Terminal 1 (Backend):**
```powershell
python app.py
```

**Terminal 2 (Frontend Dev Server):**
```powershell
cd frontend
npm run dev
```

Then access the app at: `http://localhost:8080` (not 5000)

## Troubleshooting

### "npm: command not found"
- Node.js is not installed or not in PATH
- Restart PowerShell after installing Node.js
- Verify: `npm --version`

### Build fails with errors
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
npm run build
```

### Build succeeds but Flask still shows error
1. Verify: `Test-Path "frontend\dist\index.html"` returns `True`
2. Check Flask logs for the exact path it's looking for
3. Ensure you're in project root when running `python app.py`

## Full Command Sequence

**First time setup:**
```powershell
# 1. Install Node.js (download from nodejs.org if needed)
node --version  # Verify

# 2. Build frontend
cd frontend
npm install
npm run build
cd ..

# 3. Run backend
python app.py
```

**Subsequent runs (after frontend is built):**
```powershell
python app.py
```

That's it! The frontend build persists until you delete `frontend/dist/` or run `npm run build` again.

