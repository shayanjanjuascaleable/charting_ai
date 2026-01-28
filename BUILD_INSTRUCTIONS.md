# Building the React Frontend

## Error Message
```
{"error":"React frontend build not found","message":"Please run: cd frontend && npm run build"}
```

This error occurs because the React frontend hasn't been built yet. You need Node.js and npm to build it.

## Solution: Install Node.js

### Step 1: Install Node.js
1. Download Node.js from: https://nodejs.org/
2. Choose the **LTS (Long Term Support)** version
3. Run the installer and follow the setup wizard
4. **Important**: Make sure to check "Add to PATH" during installation

### Step 2: Verify Installation
Open a **new** PowerShell/Command Prompt window and run:
```bash
node --version
npm --version
```

Both commands should show version numbers (e.g., `v20.10.0` and `10.2.3`).

### Step 3: Build the Frontend
Once Node.js is installed, run:
```bash
cd frontend
npm install
npm run build
cd ..
```

This will create:
- `frontend/dist/index.html`
- `frontend/dist/assets/*.js`
- `frontend/dist/assets/*.css`

### Step 4: Run Flask
```bash
python app.py
```

Now Flask will serve the new Lovable UI!

## Alternative: Temporary Workaround

If you can't install Node.js right now, you can temporarily restore the old UI by modifying `app.py`:

**Option 1: Quick fix (temporary)**
In `app.py`, change lines 374-380 and 385-391 to:
```python
if not FRONTEND_DIST_EXISTS:
    return render_template('index.html')  # Temporary fallback
return send_file(FRONTEND_INDEX)
```

**Note**: This is only a temporary workaround. You should build the frontend for the new UI.

## Verification

After building, verify:
1. `frontend/dist/index.html` exists
2. `frontend/dist/assets/` directory exists with `.js` and `.css` files
3. Flask logs show: "React frontend build found at: ..."
4. Browser shows new Lovable UI (not old template)

## Troubleshooting

### "node is not recognized"
- Node.js is not installed or not in PATH
- Restart your terminal after installing Node.js
- Verify installation: `node --version`

### "npm is not recognized"
- npm comes with Node.js
- If node works but npm doesn't, reinstall Node.js
- Verify: `npm --version`

### Build fails with errors
1. Delete `frontend/node_modules` folder
2. Delete `frontend/package-lock.json`
3. Run `npm install` again
4. Run `npm run build`

### Build succeeds but Flask still shows error
1. Verify `frontend/dist/index.html` exists
2. Check Flask logs for the exact path it's looking for
3. Ensure you're in the correct directory when running Flask

