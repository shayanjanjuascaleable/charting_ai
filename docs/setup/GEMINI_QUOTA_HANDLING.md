# Gemini API Quota/Rate Limit Handling

## Overview
The `/chat` endpoint now includes robust handling for Gemini API quota and rate limit errors (429) with retry logic, caching, and graceful error responses.

## Implementation Details

### 1. Retry Logic with Exponential Backoff
- **Max Retries**: 2 attempts (3 total calls)
- **Backoff Strategy**:
  - Uses `retry_delay` from API response if provided
  - Otherwise: exponential backoff (1s, 2s)
  - Capped at 60 seconds maximum delay

### 2. Error Detection
Detects the following quota/rate limit indicators:
- HTTP 429 status code
- "RESOURCE_EXHAUSTED" error type
- "quota exceeded" in error message
- "rate limit" or "too many requests" in error message
- `genai_exceptions.ResourceExhausted` exception type

### 3. Caching
- **Cache Key**: SHA256 hash of (normalized_message + language + forced_chart_type)
- **TTL**: 15 minutes (900 seconds)
- **Max Entries**: 200 (oldest entries removed when limit exceeded)
- **Scope**: Only caches chart parameter extraction (intent), not suggestions

### 4. Error Response Format
When quota is exceeded after all retries:
```json
{
  "chart_json": null,
  "raw_data": [],
  "suggestions": [],
  "error_code": "AI_QUOTA_EXCEEDED",
  "error_message": "AI quota exceeded. Try again shortly or upgrade billing."
}
```

### 5. Clean Logging
- No secrets logged (API keys, full responses)
- Logs include: attempt number, error type, cache status
- Example: `[Gemini] Request successful (attempt 1)`
- Example: `[Gemini] Quota error detected, retrying after 2s...`

## Manual Test Steps

### Test 1: Normal Request (Cache Miss)
1. Send a new query: `POST /chat` with `{"message": "show me revenue by region", "language": "en"}`
2. **Expected**: Chart generated successfully
3. **Check logs**: Should see `[Gemini] Request successful (attempt 1)`
4. **Check logs**: Should see `[Gemini] Cached chart params response`

### Test 2: Cache Hit
1. Send the exact same query again immediately
2. **Expected**: Chart generated instantly (from cache)
3. **Check logs**: Should see `[Gemini] Cache hit for chart params`

### Test 3: Quota Error Handling (Simulated)
To test quota handling, you can temporarily modify the code to raise a ResourceExhausted exception, or wait for actual quota to be exceeded.

**Expected behavior**:
1. First attempt fails with 429
2. Waits 1 second
3. Second attempt fails with 429
4. Waits 2 seconds
5. Third attempt fails with 429
6. Returns error response with `error_code: "AI_QUOTA_EXCEEDED"`

### Test 4: Cache Size Limit
1. Send 201 different unique queries
2. **Expected**: Cache maintains max 200 entries
3. **Check logs**: Oldest entries automatically removed

### Test 5: Cache Expiration
1. Send a query (cached)
2. Wait 16 minutes
3. Send the same query again
4. **Expected**: Cache miss, new API call made

### Test 6: Non-Quota Errors
1. Temporarily break API key or network
2. **Expected**: Returns `error_code: "AI_ERROR"` (not quota error)
3. **Expected**: No retries for non-quota errors

## Code Changes Summary

### Modified Files
- `backend/app.py`:
  - Added `call_gemini_with_retry()` function (lines ~40-120)
  - Added caching functions: `_get_cache_key()`, `_clean_expired_cache()`
  - Added error detection: `_is_quota_error()`, `_extract_retry_delay()`
  - Updated `/chat` endpoint to use retry logic and caching
  - Updated suggestions generation to use retry logic (non-cached)

### Key Functions
- `call_gemini_with_retry()`: Main retry wrapper with exponential backoff
- `_get_cache_key()`: Generates cache key from message + language + chart type
- `_clean_expired_cache()`: Removes expired entries and enforces size limit
- `_is_quota_error()`: Detects quota/rate limit errors
- `_extract_retry_delay()`: Extracts retry delay from error message

## Monitoring

Check logs for:
- `[Gemini] Cache hit` - Cache working
- `[Gemini] Quota error detected` - Quota issues detected
- `[Gemini] Request successful` - Normal operation
- Cache size in logs: `(cache size: X)`

## Notes
- Suggestions are NOT cached (they're contextual and change based on previous charts)
- Cache is in-memory only (cleared on server restart)
- All existing routes and response structures remain unchanged
- Frontend receives proper error codes for display

