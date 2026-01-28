# Azure SQL Migration Guide

## Summary
The backend has been migrated from SQLite to Azure SQL Server. All SQLite-specific code has been removed, and the application now exclusively uses Azure SQL with SQLAlchemy connection pooling.

## Changes Made

### 1. Database Connection Layer
- **Removed**: `sqlite3` imports and connection logic
- **Removed**: `USE_SQLITE` flag and SQLite path configuration
- **Added**: SQLAlchemy engine with connection pooling
- **Added**: Environment variable-based configuration

### 2. Schema Introspection
- **Removed**: SQLite `PRAGMA table_info()` queries
- **Removed**: `sqlite_master` table queries
- **Updated**: Uses `INFORMATION_SCHEMA` exclusively
- **Updated**: Only queries target tables: Account, Contact, Lead, Opportunity
- **Cached**: Schema cached for 30 minutes at startup

### 3. SQL Generation
- **Removed**: SQLite `LIMIT` clause
- **Removed**: SQLite double-quote identifier quoting (`"column"`)
- **Updated**: Uses SQL Server `TOP` clause
- **Updated**: Uses SQL Server bracket quoting (`[column]`)
- **Updated**: All queries use parameterized queries via SQLAlchemy `text()`

### 4. Chart Field Validation
- **Added**: `validate_chart_fields()` function
- **Validates**:
  - Histogram: requires 1 numeric field
  - Scatter: requires 2 numeric fields
  - 3D Scatter: requires 3 numeric fields
- **Returns**: Helpful error messages with suggested valid numeric fields

### 5. Configuration
- **Removed**: Hardcoded database credentials
- **Added**: Environment variable support:
  - `AZURE_SQL_SERVER`
  - `AZURE_SQL_DATABASE`
  - `AZURE_SQL_USERNAME`
  - `AZURE_SQL_PASSWORD`
  - `AZURE_SQL_DRIVER` (optional, defaults to ODBC Driver 17)

## Environment Variables

Create a `.env` file in the project root:

```env
# Azure SQL Server Configuration
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database-name
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DRIVER={ODBC Driver 17 for SQL Server}

# Gemini API (if not hardcoded)
GEMINI_API_KEY=your-api-key
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

**New dependency**: `sqlalchemy==2.0.36` (added to requirements.txt)

### 2. Set Environment Variables
```bash
# Windows PowerShell
$env:AZURE_SQL_SERVER="your-server.database.windows.net"
$env:AZURE_SQL_DATABASE="your-database-name"
$env:AZURE_SQL_USERNAME="your-username"
$env:AZURE_SQL_PASSWORD="your-password"

# Linux/Mac
export AZURE_SQL_SERVER="your-server.database.windows.net"
export AZURE_SQL_DATABASE="your-database-name"
export AZURE_SQL_USERNAME="your-username"
export AZURE_SQL_PASSWORD="your-password"
```

Or use a `.env` file with `python-dotenv` (already in requirements.txt).

### 3. Run the Application
```bash
# From project root
python run.py

# Or directly
cd backend
python app.py
```

## Connection Pooling

The application uses SQLAlchemy's `QueuePool` with:
- **Pool size**: 5 connections
- **Max overflow**: 10 connections
- **Pool timeout**: 30 seconds
- **Connection recycle**: 1 hour

This ensures efficient connection management and prevents connection exhaustion.

## Target Tables

The application only queries these tables:
- `Account`
- `Contact`
- `Lead`
- `Opportunity`

Schema introspection is limited to these tables for security and performance.

## SQL Server Dialect

All SQL queries use SQL Server syntax:
- `SELECT TOP 1000` instead of `SELECT ... LIMIT 1000`
- `[ColumnName]` bracket quoting instead of `"ColumnName"`
- `INFORMATION_SCHEMA` for metadata queries
- Parameterized queries via SQLAlchemy `text()` with named parameters

## Chart Field Validation

Before fetching data, the application validates chart field requirements:

### Histogram
- Requires: 1 numeric field for X-axis
- Error: "Histogram requires 1 numeric field for X-axis"
- Suggests: List of valid numeric fields

### Scatter Plot
- Requires: 2 numeric fields (X and Y)
- Error: "Scatter plot requires 2 numeric fields (X and Y)"
- Suggests: List of valid numeric fields

### 3D Scatter Plot
- Requires: 3 numeric fields (X, Y, Z)
- Error: "3D scatter plot requires 3 numeric fields (X, Y, Z)"
- Suggests: List of valid numeric fields

## Removed Files

The following SQLite-specific files are no longer needed:
- `backend/db_init.py` - SQLite initialization (kept for reference but not used)
- `backend/seed_sqlite_data.py` - SQLite seeding (kept for reference but not used)

These files can be removed or kept for historical reference.

## Migration Checklist

- [x] Remove SQLite imports (`sqlite3`)
- [x] Remove SQLite connection logic
- [x] Remove `USE_SQLITE` flag
- [x] Implement SQLAlchemy connection pooling
- [x] Update schema introspection to `INFORMATION_SCHEMA`
- [x] Update SQL generation to SQL Server dialect
- [x] Add chart field validation
- [x] Move credentials to environment variables
- [x] Update requirements.txt with SQLAlchemy
- [x] Test all chart types (bar, line, pie, scatter, 3D, histogram)
- [x] Verify API response format unchanged

## Testing

### Test Chart Generation
```bash
# Run the test script
cd backend
python test_chart_generation.py
```

### Manual Test
```bash
# Start the server
python run.py

# In another terminal, test the /chat endpoint
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me revenue by region", "language": "en"}'
```

## Troubleshooting

### Connection Errors
- Verify environment variables are set correctly
- Check Azure SQL firewall rules allow your IP
- Verify ODBC driver is installed: `{ODBC Driver 17 for SQL Server}`

### Import Errors
- Ensure SQLAlchemy is installed: `pip install sqlalchemy==2.0.36`
- Verify pyodbc is installed: `pip install pyodbc`

### Schema Errors
- Verify target tables exist: Account, Contact, Lead, Opportunity
- Check table names match exactly (case-sensitive in some configurations)

## Notes

- All existing API endpoints and response formats remain unchanged
- Frontend integration requires no changes
- Chart generation logic is unchanged (only database layer modified)
- Performance improvements from connection pooling and schema caching

