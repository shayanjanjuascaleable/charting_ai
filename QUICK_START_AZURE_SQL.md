# Quick Start - Azure SQL

## Prerequisites
- Python 3.12+
- Azure SQL Server database with tables: Account, Contact, Lead, Opportunity
- ODBC Driver 17 for SQL Server installed
- Google Gemini API key

## Setup

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

**New dependency**: `sqlalchemy==2.0.36` (automatically installed)

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database-name
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DRIVER={ODBC Driver 17 for SQL Server}
GEMINI_API_KEY=your-api-key
```

Or set environment variables directly:

**Windows PowerShell:**
```powershell
$env:AZURE_SQL_SERVER="your-server.database.windows.net"
$env:AZURE_SQL_DATABASE="your-database-name"
$env:AZURE_SQL_USERNAME="your-username"
$env:AZURE_SQL_PASSWORD="your-password"
```

**Linux/Mac:**
```bash
export AZURE_SQL_SERVER="your-server.database.windows.net"
export AZURE_SQL_DATABASE="your-database-name"
export AZURE_SQL_USERNAME="your-username"
export AZURE_SQL_PASSWORD="your-password"
```

### 3. Run the Application

```bash
# From project root
python run.py

# Or directly
cd backend
python app.py
```

The application will:
1. Connect to Azure SQL Server using the provided credentials
2. Cache schema information for Account, Contact, Lead, Opportunity tables
3. Start Flask server on http://localhost:5000

## Verify Connection

The app will raise an error at startup if:
- Environment variables are missing
- Connection to Azure SQL fails
- Target tables don't exist

Check the console output for connection status.

## Test Chart Generation

```bash
# Test endpoint
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me revenue by region", "language": "en"}'
```

## Troubleshooting

### Connection Errors
- Verify Azure SQL firewall allows your IP address
- Check credentials are correct
- Ensure ODBC Driver 17 is installed

### Missing Tables
- Verify tables exist: Account, Contact, Lead, Opportunity
- Check table names match exactly (case-sensitive)

### Import Errors
- Run: `pip install sqlalchemy==2.0.36`
- Verify all dependencies: `pip install -r backend/requirements.txt`

