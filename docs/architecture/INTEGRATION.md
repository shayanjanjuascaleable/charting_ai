# React Frontend Integration Guide

This document explains how the React frontend (Lovable-generated) is integrated with the Flask backend.

## Architecture

- **Backend**: Flask serves the API (`/chat`) and static files
- **Frontend**: React (Vite) app built to `frontend/dist/`
- **Routing**: React Router handles client-side routing for `/` and `/insights`
- **API**: Frontend makes requests to `/chat` (relative URLs work in both dev and prod)

## Development Mode

### Option 1: Separate Servers (Recommended for frontend development)

**Terminal 1 - Flask Backend:**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate  # Linux/Mac

# Run Flask
python app.py
# Flask runs on http://localhost:5000
```

**Terminal 2 - React Frontend:**
```bash
cd frontend
npm install  # First time only
npm run dev
# Vite dev server runs on http://localhost:8080
# Vite proxy forwards /chat to Flask on port 5000
```

**Access**: Open http://localhost:8080 in your browser

### Option 2: Flask Only (Production-like)

**Build React frontend first:**
```bash
cd frontend
npm install
npm run build
```

**Run Flask:**
```bash
.\venv\Scripts\Activate.ps1
python app.py
```

**Access**: Open http://localhost:5000 in your browser

## Production Mode

1. **Build React frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   This creates `frontend/dist/` with production assets.

2. **Run Flask:**
   ```bash
   .\venv\Scripts\Activate.ps1
   python app.py
   ```
   Flask automatically serves the React build from `frontend/dist/`.

3. **Deploy**: Flask serves both the React UI and the `/chat` API.

## Routes

- **GET /** → Serves React `index.html` (Landing page)
- **GET /insights** → Serves React `index.html` (Dashboard page)
- **POST /chat** → Flask API endpoint (unchanged)
- **GET /assets/** → Static assets from React build
- **GET /favicon.ico, /robots.txt, etc.** → Static files from React build

## Client-Side Routing

React Router handles routing on the client:
- `/` → `Landing` component
- `/insights` → `Insights` component
- All routes serve the same `index.html`, React Router handles the rest

## API Integration

The frontend makes API calls to `/chat`:
```typescript
fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'user query',
    language: 'en' | 'ar'
  })
})
```

**Response format (unchanged):**
```json
{
  "chart_json": Plotly JSON | null,
  "raw_data": array,
  "suggestions": string[]
}
```

## Troubleshooting

### React build not found
If Flask shows "React frontend build not found", ensure:
1. You've run `npm run build` in the `frontend/` directory
2. `frontend/dist/index.html` exists

### CORS errors in development
The Vite proxy should handle this. If you see CORS errors:
1. Ensure Flask is running on port 5000
2. Ensure Vite dev server is running on port 8080
3. Check `vite.config.ts` proxy configuration

### Routes not working
- Ensure React Router is configured correctly in `App.tsx`
- Check browser console for routing errors
- Verify `frontend/dist/index.html` is being served

## File Structure

```
vibecharting/
├── app.py                 # Flask backend (serves React build)
├── frontend/
│   ├── src/              # React source code
│   ├── dist/             # Production build (generated)
│   ├── vite.config.ts    # Vite config with Flask proxy
│   └── package.json
└── templates/            # Old templates (fallback only)
```

