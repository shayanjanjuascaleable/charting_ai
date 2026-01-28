# Gemini Rate Limit Protection - Implementation Summary

## Overview
Implemented server-side deduplication/caching, robust error handling, and request tracing to prevent Gemini quota/rate limit issues and protect against duplicate frontend requests.

## Files Modified

### 1. `gemini_wrapper.py` (NEW)
**Purpose**: Wrapper module for Gemini API calls with caching and error handling.

**Features**:
- **Caching**: SHA256-based cache keyed by prompt text, 120-second TTL
- **Error Handling**: 
  - 429 errors (quota/rate limit) → Returns HTTP 429 with `retry_seconds`
  - Other provider errors → Returns HTTP 503
- **Request Tracing**: Logs `request_id`, timestamp, client IP, user-agent, message length, cache hit/miss
- **Deduplication**: Prevents duplicate Gemini calls for identical prompts within TTL window

**Key Functions**:
- `generate_content_with_caching()`: Main function that wraps Gemini calls with caching and error handling
- `clear_cache()`: Utility to clear cache (for testing)
- `get_cache_stats()`: Monitor cache performance

### 2. `config.py` (MODIFIED)
**Changes**:
- Added `gemini_enabled: bool` field to `Settings` dataclass
- Added `GEMINI_ENABLED` environment variable (default: `true`)
- Updated validation to only require `GEMINI_API_KEY` when `GEMINI_ENABLED=true`
- Added `gemini_enabled` to safe log summary

**Environment Variable**:
```bash
GEMINI_ENABLED=true  # or false to disable Gemini
```

### 3. `app.py` (MODIFIED)
**Changes**:

1. **Imports**:
   - Added `uuid` for request ID generation
   - Added `generate_content_with_caching` from `gemini_wrapper`

2. **Gemini Configuration**:
   - Only configures Gemini if `settings.gemini_enabled` is true
   - Creates dummy models if disabled (prevents errors)

3. **`/chat` Route**:
   - **Request Tracing**: Generates unique `request_id` (8-char UUID) for each request
   - **Client Info**: Extracts `client_ip` and `user_agent` for logging
   - **Wrapper Integration**: Replaced direct `model.generate_content()` calls with `generate_content_with_caching()`
   - **Error Handling**: 
     - Returns HTTP 429 for rate limit errors (with `retry_seconds`)
     - Returns HTTP 503 for other Gemini provider errors
     - Returns HTTP 500 for unexpected errors
   - **Backward Compatibility**: All existing response fields (`response`, `suggestions`, `chart_json`, `raw_data`) remain unchanged
   - **Optional Fields**: Added `cached`, `request_id`, `retry_seconds` for debugging (only when applicable)

4. **Gemini Call Optimization**:
   - First call (chart_params): Uses caching wrapper
   - Second call (suggestions): Uses caching wrapper (cached separately, keyed by prompt)
   - Both calls benefit from deduplication within 120-second window

## Key Features

### 1. Server-Side Deduplication
- **Cache Key**: SHA256 hash of the full prompt text
- **TTL**: 120 seconds (2 minutes)
- **Benefit**: Identical requests within TTL window return cached response without calling Gemini
- **Use Case**: Prevents React StrictMode/effects or retries from burning quota

### 2. Robust Error Handling
- **429 Rate Limit**:
  - Detects quota/rate limit errors
  - Returns HTTP 429 status code
  - Includes `retry_seconds` field (extracted from error message or defaults to 60)
  - Frontend can use this to implement exponential backoff

- **503 Provider Errors**:
  - Catches other Gemini API errors
  - Returns HTTP 503 status code
  - Includes error message in response

- **Gemini Disabled**:
  - If `GEMINI_ENABLED=false`, returns HTTP 503 with helpful message
  - App continues to work (just returns errors for chat requests)

### 3. Request Tracing
Every `/chat` request logs:
- `request_id`: Unique 8-character identifier
- `timestamp`: UTC ISO timestamp
- `client_ip`: Client IP address (or 'unknown')
- `user_agent`: Browser/user agent string
- `message_length`: Length of user message
- `cache_hit`: Whether response came from cache (true/false)
- `cache_key`: First 16 chars of cache key (for debugging)
- `gemini_success`: Whether Gemini call succeeded
- `gemini_error`: Error type if Gemini call failed

**Log Format Example**:
```
[REQUEST_TRACE] request_id=a1b2c3d4 timestamp=2024-01-15T10:30:00.123Z client_ip=192.168.1.1 user_agent=Mozilla/5.0... message_length=42
[REQUEST_TRACE] request_id=a1b2c3d4 cache_hit=false cache_key=abc123def4567890... calling_gemini=true
[REQUEST_TRACE] request_id=a1b2c3d4 cache_hit=false gemini_success=true response_length=123
```

### 4. Backward Compatibility
- **Existing Fields**: All existing response fields remain unchanged
  - `response`: Text response (for language-specific messages)
  - `suggestions`: Array of suggestion strings
  - `chart_json`: Plotly JSON object
  - `raw_data`: Array of data records (PII filtered)
  - `error`: Error message (if any)

- **New Optional Fields** (only added when applicable):
  - `ok`: Boolean indicating success/failure
  - `cached`: Boolean indicating if response came from cache
  - `request_id`: Request identifier for tracing
  - `retry_seconds`: Number of seconds to wait before retrying (429 errors only)

### 5. Environment Toggle
- **GEMINI_ENABLED**: Can be set to `false` to disable Gemini completely
  - Useful for maintenance, testing, or when quota is exhausted
  - App continues to run (just returns errors for chat requests)
  - No need to remove `GEMINI_API_KEY`

## Testing Checklist

1. **Caching**:
   - ✅ Send same prompt twice within 120 seconds → Second response should be cached
   - ✅ Check logs for `cache_hit=true` on second request

2. **Error Handling**:
   - ✅ Simulate 429 error → Should return HTTP 429 with `retry_seconds`
   - ✅ Simulate other Gemini error → Should return HTTP 503
   - ✅ Set `GEMINI_ENABLED=false` → Should return HTTP 503 with helpful message

3. **Request Tracing**:
   - ✅ Check logs for `[REQUEST_TRACE]` entries with all required fields
   - ✅ Verify `request_id` is unique for each request

4. **Backward Compatibility**:
   - ✅ Verify existing frontend still works (all expected fields present)
   - ✅ Verify successful responses include `chart_json`, `raw_data`, `suggestions`

5. **Performance**:
   - ✅ Cached responses should be faster (no Gemini API call)
   - ✅ Check cache statistics via `get_cache_stats()` if needed

## Usage Examples

### Enable/Disable Gemini
```bash
# Enable (default)
export GEMINI_ENABLED=true

# Disable (for maintenance)
export GEMINI_ENABLED=false
```

### Monitor Cache
```python
from gemini_wrapper import get_cache_stats
stats = get_cache_stats()
print(f"Active cache entries: {stats['active_entries']}")
```

### Clear Cache (if needed)
```python
from gemini_wrapper import clear_cache
clear_cache()
```

## Notes

1. **Cache Storage**: In-memory only (cleared on server restart)
2. **Cache Key**: Based on full prompt text, so schema changes invalidate cache
3. **Error Retry**: Frontend should use `retry_seconds` from 429 responses for exponential backoff
4. **Logging**: Request tracing logs at INFO level, errors at ERROR level
5. **Performance**: Cache lookup is O(1), minimal overhead

## Breaking Changes
**None** - All changes are backward-compatible. Existing frontend code will continue to work.

## Future Enhancements (Optional)
- Persistent cache (Redis/file-based) for multi-instance deployments
- Configurable TTL via environment variable
- Cache warming strategies
- Cache invalidation by pattern
- Metrics/analytics dashboard for cache hit rates

