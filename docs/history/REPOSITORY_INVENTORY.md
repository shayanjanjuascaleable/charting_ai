# Repository Inventory & Dependency Analysis

**Generated:** Inventory scan for refactoring preparation  
**Status:** STEP 1 - Analysis only, no files modified

---

## 1. Runtime Dependency List (Python Modules)

### Directly Imported by `app.py`:
- `app.py` - Main Flask application entrypoint
- `config.py` - Configuration management (Settings, environment variables)
- `safe_sql.py` - Safe SQL query builder and validation
- `llm.py` - Gemini API wrapper (`call_gemini`)
- `intent_chart.py` - Intent-based chart generation (`validate_intent`, `build_sql_from_intent`, `get_field_info_for_chart`, `determine_chart_type`, schema constants)
- `db_init.py` - SQLite schema initialization (`init_sqlite_schema`) - **conditionally imported**

### Standard Library Dependencies:
- `os`, `json`, `re`, `logging`, `sqlite3`, `pyodbc`, `uuid`, `hashlib`, `datetime`, `pathlib`, `secrets`, `dataclasses`, `typing`

### Third-Party Dependencies (from `requirements.txt`):
- `flask` - Web framework
- `google.generativeai` - Gemini AI API
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `plotly.express`, `plotly.graph_objects` - Chart generation
- `scipy.interpolate` - Data interpolation
- `python-dotenv` - Environment variable loading
- `gunicorn` - Production WSGI server

---

## 2. Runtime File Paths Used

### Database Files:
- `data/charting_ai.db` - SQLite database (created/accessed at runtime)
- `data/` directory - Created automatically if missing (via `config.py`)

### Frontend Build Files:
- `frontend/dist/index.html` - React frontend build output (served at `/` and `/insights`)
- `frontend/dist/assets/*` - Static assets (JS, CSS, images) served at `/assets/<filename>`
- `frontend/dist/favicon.ico` - Served at `/favicon.ico`
- `frontend/dist/robots.txt` - Served at `/robots.txt`
- `frontend/package.json` - Read at startup to detect frontend framework type (Vite/Next.js)

### Configuration Files:
- `.env` - Optional environment variables file (loaded if exists via `python-dotenv`)

### **NOT USED AT RUNTIME:**
- `templates/` - Legacy HTML templates (not used - React frontend replaces them)
- `static/` - Legacy static files (not used - React build serves assets)
- `roles.json` - Not imported or referenced anywhere in runtime code

---

## 3. Build/Run Scripts Used

### Frontend Build Scripts:
- `build_frontend.bat` - Windows batch script for building React frontend
- `build_frontend.sh` - Unix shell script for building React frontend

### Deployment/Startup Scripts:
- `startup.sh` - ODBC driver installation script (for Azure SQL deployment)

### **NOT USED:**
- `.oryx_build.sh` - Appears to be Azure deployment script (not referenced in main code)

---

## 4. File Classification (Buckets)

### **BUCKET A: MUST KEEP (Runtime/Build Critical)**

#### Python Runtime Modules:
- `app.py` - Main entrypoint
- `config.py` - Configuration (required)
- `safe_sql.py` - SQL security and validation (required)
- `llm.py` - AI API integration (required)
- `intent_chart.py` - Chart generation logic (required)
- `db_init.py` - Database initialization (required for SQLite)

#### Configuration & Dependencies:
- `requirements.txt` - Python dependencies
- `.env` (if exists) - Environment variables
- `data/` directory - Database location
- `data/charting_ai.db` - Database file (runtime data)

#### Frontend Build Output:
- `frontend/dist/` - React build output (served by Flask)
- `frontend/package.json` - Read at startup for frontend detection
- `frontend/` directory - Source code for building frontend

#### Build Scripts:
- `build_frontend.bat` - Windows build script
- `build_frontend.sh` - Unix build script

---

### **BUCKET B: SAFE TO MOVE (Documentation, Notes, Summaries)**

#### Documentation Files:
- `README.md` - Project documentation
- `BUILD_INSTRUCTIONS.md` - Build instructions
- `QUICK_START.md` - Quick start guide
- `QUICK_BUILD.md` - Quick build guide
- `SECURITY.md` - Security documentation
- `INTEGRATION.md` - Integration guide
- `frontend/README.md` - Frontend documentation

#### Summary/History Files:
- `CHART_RECOMMENDATION_SUMMARY.md`
- `CHART_SCHEMA_FIX.md`
- `DB_VERIFICATION_SUMMARY.md`
- `DEV_SETUP.md`
- `DEV_SETUP_FIXED.md`
- `FIXES_APPLIED.md`
- `FIXES_SUMMARY.md`
- `FRONTEND_INTEGRATION_SUMMARY.md`
- `GEMINI_PROTECTION_SUMMARY.md`
- `INTENT_CHART_EXAMPLES.md`
- `MANUAL_CHART_SELECTION_FIX.md`
- `MANUAL_VERIFICATION_CHECKLIST.md`
- `RULES_FIRST_IMPLEMENTATION.md`
- `SAFE_SQL_IMPLEMENTATION_SUMMARY.md`
- `SAFE_SQL_MANUAL_TEST.md`
- `SAFE_SQL_PRODUCTION.md`
- `SAFE_SQL_SECURITY.md`
- `SAFE_SQL_TEST_CHECKLIST.md`

---

### **BUCKET C: UNSURE (Might be Used - Do Not Touch Without Proof)**

#### Legacy/Unused Python Modules (Not Imported):
- `rule_sql.py` - **UNSURE** - Not imported in `app.py`, but has test file `tests/test_rule_sql.py`
- `chart_recommender.py` - **UNSURE** - Not imported in `app.py`, but has test file `tests/test_chart_recommender.py`
- `fallback_sql.py` - **UNSURE** - Not imported in `app.py`
- `gemini_wrapper.py` - **UNSURE** - Not imported in `app.py`, mentioned in `GEMINI_PROTECTION_SUMMARY.md`
- `app_helpers.py` - **UNSURE** - Not imported in `app.py`
- `db_verification.py` - **UNSURE** - Not imported in `app.py`

#### Legacy Template/Static Files:
- `templates/index.html` - **UNSURE** - Legacy template, `render_template` imported but never called
- `templates/insights_page.html` - **UNSURE** - Legacy template, not referenced
- `static/` directory - **UNSURE** - Legacy static files, not served by Flask routes
  - `static/download_icon.svg`
  - `static/image_409c9f.png`
  - `static/save_icon.png`
  - `static/style.css`

#### Configuration Files:
- `roles.json` - **UNSURE** - Not imported or referenced in code, but may be used by external tools

#### Utility Scripts:
- `seed_sqlite_data.py` - **UNSURE** - Utility script for seeding test data, not imported at runtime
- `test_safe_sql.py` - **UNSURE** - Test script, not imported at runtime

#### Test Files:
- `tests/test_rule_sql.py` - **UNSURE** - Tests for `rule_sql.py` (which is not imported)
- `tests/test_chart_recommender.py` - **UNSURE** - Tests for `chart_recommender.py` (which is not imported)

#### Build/Deployment Scripts:
- `.oryx_build.sh` - **UNSURE** - Azure deployment script, not referenced in main code

---

## 5. Additional Notes

### Frontend Architecture:
- **Current:** React (Vite) frontend served from `frontend/dist/` after build
- **Legacy:** HTML templates in `templates/` are **NOT USED** - Flask serves React SPA
- **Static Files:** Legacy `static/` directory is **NOT USED** - React build includes all assets

### Database:
- **SQLite:** Default database at `data/charting_ai.db` (absolute path via `config.py`)
- **Azure SQL:** Optional, configured via environment variables

### Environment Variables:
- Loaded from `.env` if exists (development)
- Production uses system environment variables
- See `config.py` for all required variables

### Import Analysis:
- `render_template` is imported from Flask but **never called** - React frontend replaces templates
- All routes use `send_file()` to serve React build, not `render_template()`

---

## Summary Statistics

- **Runtime Python Modules:** 6 files (app.py + 5 dependencies)
- **Runtime File Paths:** 3 directories (data/, frontend/dist/, frontend/)
- **Build Scripts:** 2 files (build_frontend.bat, build_frontend.sh)
- **Documentation Files:** 25+ markdown files
- **Unused/Legacy Files:** ~15 files (templates/, static/, unused Python modules)
- **Uncertain Files:** ~10 files (may be used by tests, utilities, or external tools)

---

**END OF INVENTORY**

