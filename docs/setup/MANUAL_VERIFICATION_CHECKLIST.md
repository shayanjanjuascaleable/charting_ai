# Manual Verification Checklist

Use this checklist to verify that all security improvements are working correctly after deployment.

## Pre-Deployment Verification

### 1. Configuration Loading
- [ ] Start the application: `python app.py`
- [ ] Verify no errors in startup logs
- [ ] Check that configuration summary is logged (should show env, db_server, db_database, but NOT passwords/keys)
- [ ] Verify no secret values appear in logs (check for: API keys, passwords, secret keys, connection strings)

### 2. Environment Variable Validation
- [ ] Test with missing `GEMINI_API_KEY`: Application should fail fast with clear error message
- [ ] Test with missing `AZURE_SQL_PASSWORD`: Application should fail fast with clear error message
- [ ] Test with missing `FLASK_SECRET_KEY` in development: Should generate temporary key with warning
- [ ] Test with missing `FLASK_SECRET_KEY` in production (`FLASK_ENV=production`): Should fail fast

### 3. Session Cookie Security (Development)
- [ ] Set `FLASK_ENV=development` and start app
- [ ] Open browser DevTools → Application → Cookies
- [ ] Verify `session` cookie has:
  - `HttpOnly` = ✅ (checked/true)
  - `Secure` = ❌ (unchecked/false) - OK in development
  - `SameSite` = `Lax` (or your configured value)

### 4. Session Cookie Security (Production)
- [ ] Set `FLASK_ENV=production` and start app
- [ ] Access via HTTPS (required for Secure cookies)
- [ ] Open browser DevTools → Application → Cookies
- [ ] Verify `session` cookie has:
  - `HttpOnly` = ✅ (checked/true)
  - `Secure` = ✅ (checked/true) - Required in production
  - `SameSite` = `Lax` (or your configured value)

### 5. Application Routes
- [ ] **GET /** - Navigate to `http://localhost:5000/`
  - [ ] Page loads without errors
  - [ ] No console errors in browser DevTools
  - [ ] No secrets visible in page source or network requests

- [ ] **GET /insights** - Navigate to `http://localhost:5000/insights`
  - [ ] Page loads without errors
  - [ ] No console errors in browser DevTools
  - [ ] No secrets visible in page source or network requests

- [ ] **POST /chat** - Send POST request to `http://localhost:5000/chat`
  - [ ] Request body: `{"message": "__initial_load__", "language": "en"}`
  - [ ] Response contains suggestions array
  - [ ] No secrets in response body
  - [ ] Test with actual chart request to verify database connectivity

### 6. Database Connection
- [ ] Verify database connection works with environment variables
- [ ] Check that connection string is NOT logged (should not appear in logs)
- [ ] Verify database queries execute successfully
- [ ] Test `/chat` endpoint with a chart request that queries the database

### 7. Configuration Values
- [ ] Verify `SESSION_COOKIE_SAMESITE` can be set to `Strict`, `Lax`, or `None`
- [ ] Verify invalid `SESSION_COOKIE_SAMESITE` value fails with clear error
- [ ] Verify `PERMANENT_SESSION_DAYS` defaults to 7 if not set
- [ ] Verify `PERMANENT_SESSION_DAYS` can be customized (e.g., set to 30)
- [ ] Verify invalid `PERMANENT_SESSION_DAYS` (negative, non-integer) fails with clear error
- [ ] Verify `DATABASE_AUTH_MODE` defaults to `sql_password`
- [ ] Verify unsupported `DATABASE_AUTH_MODE` logs warning and falls back to `sql_password`

### 8. Secret Redaction in Logs
- [ ] Search application logs for any of these strings (should NOT appear):
  - Your actual `GEMINI_API_KEY` value
  - Your actual `AZURE_SQL_PASSWORD` value
  - Your actual `FLASK_SECRET_KEY` value
  - Your actual `AZURE_SQL_USERNAME` value
  - Full database connection strings
- [ ] Verify logs show safe values only:
  - Database server name ✅
  - Database name ✅
  - Environment mode ✅
  - Session settings ✅

### 9. Production Readiness
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_SECRET_KEY` to a strong value (32+ characters)
- [ ] Verify application starts without warnings about temporary keys
- [ ] Verify `SESSION_COOKIE_SECURE=True` in production
- [ ] Test that application fails if `FLASK_SECRET_KEY` is missing in production

## Post-Deployment Verification (Production)

### 10. Production Environment
- [ ] Verify HTTPS is enabled and working
- [ ] Verify session cookies are marked `Secure` in production
- [ ] Verify all environment variables are set correctly
- [ ] Verify no debug mode is enabled (`FLASK_DEBUG=0`)
- [ ] Check application logs for any secret leaks
- [ ] Verify database firewall rules are configured
- [ ] Test all routes work correctly in production environment

## Quick Test Script

You can use this Python script to verify configuration loading:

```python
import os
os.environ['FLASK_ENV'] = 'development'
os.environ['GEMINI_API_KEY'] = 'test-key'
os.environ['AZURE_SQL_SERVER'] = 'test-server'
os.environ['AZURE_SQL_DATABASE'] = 'test-db'
os.environ['AZURE_SQL_USERNAME'] = 'test-user'
os.environ['AZURE_SQL_PASSWORD'] = 'test-pass'

from config import get_settings, get_safe_log_summary

try:
    settings = get_settings()
    print("✅ Configuration loaded successfully")
    print(get_safe_log_summary(settings))
    print("\n✅ No secrets in log summary above")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

## Expected Behavior Summary

✅ **Should Work:**
- Application starts with all required env vars
- Session cookies have correct security flags
- All routes function normally
- Database connections work
- Logs show safe configuration summary (no secrets)

❌ **Should Fail:**
- Missing required environment variables (with clear error messages)
- Invalid `SESSION_COOKIE_SAMESITE` values
- Invalid `PERMANENT_SESSION_DAYS` values
- Missing `FLASK_SECRET_KEY` in production

🔒 **Security Requirements:**
- No secrets in logs
- No secrets in error messages
- Secure session cookies in production
- HttpOnly cookies always enabled
- Connection strings never logged

