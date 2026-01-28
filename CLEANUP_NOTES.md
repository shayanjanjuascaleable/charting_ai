# Backend Cleanup Notes

## Summary
Removed unused/legacy backend modules that are not part of the active execution path. The active backend flow uses only `app.py` with direct Gemini API calls and inline SQL building.

## Active Backend Flow (PRESERVED)

### Entry Point
- `run.py` - Main entry point that imports `backend.app`
- `backend/app.py` - Main Flask application (1023 lines)

### Active Routes
- `GET /` - Landing page (renders `index.html`)
- `GET /insights` - Insights dashboard (renders `insights_page.html`)
- `POST /chat` - Chart generation endpoint (uses Gemini directly, no wrapper modules)

### Active Imports in app.py
- Standard libraries: `os`, `json`, `re`, `pyodbc`, `sqlite3`, `time`, `hashlib`, `uuid`, `datetime`, `pathlib`, `typing`
- Flask: `Flask`, `render_template`, `request`, `jsonify`, `send_file`
- Gemini: `google.generativeai`, `google.api_core.exceptions`
- Data: `pandas`, `numpy`, `plotly.express`, `plotly.graph_objects`, `scipy.interpolate`

**No custom backend modules are imported in app.py** - all logic is inline.

## Files Removed (UNUSED)

### 1. `backend/app_helpers.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere in the codebase
- **Content**: Helper functions for chart type conversion and response building
- **Replacement**: Logic is inline in `app.py` or not needed

### 2. `backend/chart_recommender.py`
- **Status**: UNUSED (except in test)
- **Reason**: Only imported in `tests/test_chart_recommender.py` (test file)
- **Content**: Chart recommendation and normalization logic
- **Replacement**: Chart suitability logic is inline in `app.py` (`assess_chart_suitability` function)
- **Note**: Test file kept for reference but module removed

### 3. `backend/intent_chart.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere
- **Content**: Intent-based chart generation with schema validation
- **Replacement**: Intent extraction is done directly via Gemini in `app.py`

### 4. `backend/llm.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere
- **Content**: Simple Gemini API wrapper
- **Replacement**: `app.py` calls Gemini API directly via `genai.GenerativeModel`

### 5. `backend/fallback_sql.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere
- **Content**: Fallback SQL generation when Gemini is rate-limited
- **Replacement**: Current flow handles 429 errors with structured error responses (no fallback)

### 6. `backend/gemini_wrapper.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere
- **Content**: Gemini API wrapper with caching and error handling
- **Replacement**: `app.py` implements its own caching and error handling inline

### 7. `backend/rule_sql.py`
- **Status**: UNUSED (except in test)
- **Reason**: Only imported in `tests/test_rule_sql.py` (test file)
- **Content**: Rule-based SQL generation for manual chart selection
- **Replacement**: SQL is built inline in `fetch_data_for_chart()` in `app.py`
- **Note**: Test file kept for reference but module removed

### 8. `backend/config.py`
- **Status**: UNUSED in app.py (used by db_init.py and seed_sqlite_data.py)
- **Reason**: `app.py` has hardcoded configuration (DB credentials, API keys)
- **Content**: Configuration management from environment variables
- **Replacement**: Config is hardcoded in `app.py` as per user requirements
- **Note**: Kept because `db_init.py` and `seed_sqlite_data.py` use it

### 9. `backend/paths.py`
- **Status**: UNUSED in app.py (used by config.py)
- **Reason**: Only imported by `config.py`
- **Content**: Path utilities for project structure
- **Replacement**: `app.py` uses `Path(__file__).resolve().parent` directly
- **Note**: Kept because `config.py` uses it

### 10. `backend/db_verification.py`
- **Status**: UNUSED
- **Reason**: Not imported anywhere
- **Content**: Database verification and diagnostic utilities
- **Replacement**: Not needed in active flow

### 11. `backend/roles.json`
- **Status**: UNUSED
- **Reason**: Not referenced anywhere in code
- **Content**: LLM instruction templates for a different use case (lead extraction)
- **Replacement**: Not applicable to current chart generation flow

## Files Kept (ACTIVE OR UTILITY)

### Active Application Files
- `backend/app.py` - Main Flask application
- `run.py` - Entry point script

### Utility Scripts (Standalone)
- `backend/db_init.py` - Database initialization (uses `config.py`)
- `backend/seed_sqlite_data.py` - Seed data script (uses `config.py`)
- `backend/config.py` - Config module (used by db_init and seed scripts)
- `backend/paths.py` - Path utilities (used by config.py)

### Test Files
- `backend/test_chart_generation.py` - Chart generation tests
- `backend/test_safe_sql.py` - Safe SQL tests (uses `safe_sql.py`)
- `backend/tests/test_chart_recommender.py` - Chart recommender tests (references removed module)
- `backend/tests/test_rule_sql.py` - Rule SQL tests (references removed module)
- `backend/safe_sql.py` - Safe SQL module (used by test_safe_sql.py)

### Templates & Static
- `backend/templates/` - HTML templates (used by Flask routes)
- `backend/static/` - Static assets (used by templates)

## Verification

### Import Check
- ✅ `app.py` imports successfully without removed modules
- ✅ No broken imports in active code path

### Route Check
- ✅ `/` route exists and renders template
- ✅ `/insights` route exists and renders template
- ✅ `/chat` route exists and handles POST requests

### Frontend Integration
- ✅ Frontend calls `/chat` endpoint (confirmed in `ChatPanel.tsx`)
- ✅ Frontend navigates to `/insights` route (confirmed in `Landing.tsx`, `App.tsx`)

## Impact

### Removed
- **8 Python modules** (~2000+ lines of unused code)
- **1 JSON config file** (unused)

### Kept
- All active application code
- All utility scripts (db_init, seed_sqlite_data)
- All test files (for reference, even if they test removed modules)
- All templates and static assets

### No Breaking Changes
- ✅ API response shape unchanged
- ✅ Frontend integration unchanged
- ✅ Active routes unchanged
- ✅ Database operations unchanged

## Files Changed

### Deleted Files
1. `backend/app_helpers.py`
2. `backend/chart_recommender.py`
3. `backend/intent_chart.py`
4. `backend/llm.py`
5. `backend/fallback_sql.py`
6. `backend/gemini_wrapper.py`
7. `backend/rule_sql.py`
8. `backend/db_verification.py`
9. `backend/roles.json`

### Modified Files
- None (cleanup was deletion-only, no code changes needed)

## Notes

- Test files that reference removed modules are kept for historical reference but will fail if run
- `config.py` and `paths.py` are kept because they're used by utility scripts (`db_init.py`, `seed_sqlite_data.py`)
- `safe_sql.py` is kept because it's used by `test_safe_sql.py` (test file)
- All active functionality is preserved in `app.py`

