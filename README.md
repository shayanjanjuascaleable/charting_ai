# Charting AI Project

A Flask web application that uses AI (Google Gemini) to generate interactive data visualizations from Azure SQL Server databases. Users can ask questions in natural language, and the app automatically creates charts based on their queries.

## Features

- **AI-Powered Chart Generation**: Natural language queries converted to SQL queries and visualizations
- **Interactive Visualizations**: Supports 12 chart types (bar, line, pie, scatter, heatmap, 3D, etc.)
- **Secure SQL Layer**: Production-grade protection against SQL injection, PII exposure, and expensive queries
- **Multi-language Support**: Interface available in 7 languages (EN, ES, FR, DE, JA, KO, AR)
- **Real-time Suggestions**: AI provides follow-up chart suggestions based on user interactions

## Tech Stack

- **Backend**: Flask (Python)
- **AI**: Google Gemini API
- **Database**: Azure SQL Server (pyodbc)
- **Visualization**: Plotly
- **Data Processing**: Pandas, NumPy

## Project Structure

```
vibecharting/
├── backend/            # Backend application code
│   ├── app.py         # Main Flask application
│   ├── config.py      # Configuration management
│   ├── safe_sql.py    # Safe SQL query builder
│   ├── static/        # Static assets
│   ├── templates/     # HTML templates
│   ├── data/          # Database files
│   └── tests/         # Test files
├── frontend/          # React frontend application
├── docs/              # Documentation (organized by category)
│   ├── architecture/  # Architecture & design docs
│   ├── security/      # Security documentation
│   ├── sql/           # SQL safety docs
│   ├── fixes/         # Fix history
│   ├── setup/         # Setup & development guides
│   └── history/       # Repository history
├── run.py             # Application entry point
├── README.md          # This file
├── QUICK_START.md     # Quick start guide
├── QUICK_BUILD.md     # Quick build guide
└── BUILD_INSTRUCTIONS.md  # Build instructions
```

## Security Features

### Implemented Protections

1. **SQL Injection Prevention**
   - Allowlist validation for tables and columns
   - Identifier quoting with SQL Server brackets
   - No raw SQL from AI model output

2. **PII Protection**
   - Email column automatically blocked from selection and raw_data
   - Multiple filtering layers ensure PII never reaches frontend

3. **Performance Guardrails**
   - Maximum 5000 rows for non-aggregated queries
   - Maximum 50 groups for aggregated charts
   - SQL-level limits via TOP clause

4. **Secure Configuration**
   - All secrets loaded from environment variables
   - No hardcoded credentials
   - Secure session cookie settings (production-ready)

## Quick Start

### Prerequisites

- Python 3.12+
- Database: SQLite (default, for local dev) or Azure SQL Server (production)
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vibecharting
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```
   This installs all required packages including `plotly==6.2.0`, `pandas`, `flask`, `pyodbc`, `google-generativeai`, etc.

4. **Initialize SQLite database (if using SQLite)**
   ```bash
   python backend/db_init.py
   ```
   This creates the required tables (Account, Contact, Lead, Opportunity) matching your Azure SQL schema.
   **Note**: The schema is automatically initialized when the app starts if using SQLite, so this step is optional.

5. **Install Node.js (REQUIRED for building frontend)**
   - Download from: https://nodejs.org/ (choose LTS version)
   - Install and restart your terminal
   - Verify: `node --version` and `npm --version` should show versions
   
6. **Build React frontend (REQUIRED)**
   
   **Windows PowerShell:**
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```
   
   This creates the production build in `frontend/dist/`. Flask will serve this build.
   
   **Important**: 
   - Without this build, Flask will show a helpful error page (not blank screen)
   - You must have Node.js installed first (see step 5)
   - See `docs/setup/DEV_SETUP.md` for detailed development workflow

7. **Seed SQLite with dummy data (optional, for local testing)**
   ```bash
   python backend/seed_sqlite_data.py
   ```
   This inserts realistic test data:
   - 30 Accounts
   - 30 Contacts
   - 20 Leads
   - 20 Opportunities
   
   **Note**: Safe to run multiple times (uses `INSERT OR IGNORE` to avoid duplicates).

8. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env with your credentials
   ```

9. **Required Environment Variables**
   
   **Minimum required (SQLite - default for local dev):**
   ```env
   FLASK_ENV=development
   FLASK_SECRET_KEY=your-secret-key
   GEMINI_API_KEY=your-gemini-api-key
   DATABASE_URL=sqlite:///./data/charting_ai.db
   ```
   
   **For Azure SQL Server (production):**
   ```env
   DATABASE_URL=mssql+pyodbc://...
   AZURE_SQL_SERVER=your-server.database.windows.net
   AZURE_SQL_DATABASE=your-database-name
   AZURE_SQL_USERNAME=your-username
   AZURE_SQL_PASSWORD=your-password
   ```
   
   **Note**: 
   - SQLite is the default for local development (no Azure SQL credentials needed)
   - The `./data` directory will be created automatically if it doesn't exist
   - For production, set `DATABASE_URL` to your Azure SQL connection string or provide Azure SQL environment variables

8. **Run the application**
   
   **Option 1: Using the entry point (Recommended)**
   ```bash
   python run.py
   ```
   
   **Option 2: Using Python directly**
   ```bash
   python backend/app.py
   ```
   
   **Option 3: Using Flask CLI**
   ```bash
   flask run
   ```
   
   **⚠️ Important**: This is a **Flask (WSGI) application**, not FastAPI.
   - ✅ **Correct**: `python run.py`, `python backend/app.py`, or `flask run`
   - ❌ **Wrong**: `uvicorn app.main:app` (uvicorn is for FastAPI/ASGI apps only)
   
   If you see `ModuleNotFoundError: No module named 'plotly'`, ensure you:
   1. Activated the virtual environment: `.\venv\Scripts\Activate.ps1`
   2. Installed dependencies: `pip install -r requirements.txt`

10. **Access the app**
   - Open `http://localhost:5000` in your browser
   - The app runs on port 5000 by default

## Database Configuration

### SQLite (Default - Local Development)

SQLite is the **default database** for local development. No additional setup required:

   - **Default location**: `./backend/data/charting_ai.db`
   - **Auto-created**: The `./backend/data` directory is created automatically if it doesn't exist
   - **No credentials needed**: Just set `DATABASE_URL=sqlite:///./backend/data/charting_ai.db` (or leave it unset for default)

**Example `.env` for SQLite:**
```env
DATABASE_URL=sqlite:///./backend/data/charting_ai.db
GEMINI_API_KEY=your-key
FLASK_SECRET_KEY=your-secret
```

### Azure SQL Server (Production)

For production or when using Azure SQL Server:

1. Set `DATABASE_URL` to your Azure SQL connection string, OR
2. Provide Azure SQL environment variables:
   ```env
   AZURE_SQL_SERVER=your-server.database.windows.net
   AZURE_SQL_DATABASE=your-database-name
   AZURE_SQL_USERNAME=your-username
   AZURE_SQL_PASSWORD=your-password
   ```

**Note**: Azure SQL requires `pyodbc` and ODBC drivers to be installed.

## How It Works

1. **User Query**: User asks a question like "Show me sales by region"
2. **AI Processing**: Gemini extracts chart parameters (table, columns, chart type, aggregations)
3. **Safe Validation**: `safe_sql.py` validates all parameters against database schema
4. **SQL Generation**: Safe SQL query built programmatically with proper quoting and limits (SQLite or SQL Server syntax)
5. **Data Fetching**: Query executed against database (SQLite for local dev, Azure SQL Server for production)
6. **Visualization**: Plotly generates interactive chart JSON
7. **Response**: Frontend receives chart, raw data (PII-filtered), and AI suggestions

## Supported Chart Types

- Bar Chart
- Line Chart
- Scatter Plot
- Pie Chart
- Donut Chart
- Histogram
- Box Plot
- Area Chart
- Heatmap
- 3D Scatter Plot
- Bubble Chart

## API Endpoints

- `GET /` - Main landing page
- `GET /insights` - Insights dashboard
- `POST /chat` - Chatbot endpoint for chart generation
  ```json
  {
    "message": "show me revenue by region",
    "language": "en"
  }
  ```

## Security Notes

- **Never commit `.env` file** - It's in `.gitignore`
- **Rotate secrets regularly** - See `SECURITY.md` for rotation procedures
- **Use HTTPS in production** - Session cookies require secure connections
- **Review logs** - Ensure no secrets are logged

## 📚 Documentation

Comprehensive documentation is organized in the `docs/` directory:

### Architecture & Design
- [Integration Guide](docs/architecture/INTEGRATION.md) - Frontend-backend integration details
- [Intent Chart Examples](docs/architecture/INTENT_CHART_EXAMPLES.md) - Chart type examples and use cases
- [Chart Schema Fix](docs/architecture/CHART_SCHEMA_FIX.md) - Schema-related fixes and improvements
- [Chart Recommendation Summary](docs/architecture/CHART_RECOMMENDATION_SUMMARY.md) - AI chart recommendation system

### Security
- [Security Overview](docs/security/SECURITY.md) - Security best practices and secret rotation
- [Gemini Protection](docs/security/GEMINI_PROTECTION_SUMMARY.md) - AI API protection mechanisms
- [Safe SQL Security](docs/security/SAFE_SQL_SECURITY.md) - SQL security implementation
- [Safe SQL Production](docs/security/SAFE_SQL_PRODUCTION.md) - Production-ready SQL safety
- [Safe SQL Implementation](docs/security/SAFE_SQL_IMPLEMENTATION_SUMMARY.md) - Implementation details

### SQL Safety
- [Safe SQL Manual Test](docs/sql/SAFE_SQL_MANUAL_TEST.md) - Manual testing procedures
- [Safe SQL Test Checklist](docs/sql/SAFE_SQL_TEST_CHECKLIST.md) - Testing checklist

### Fixes & Change Logs
- [Fixes Applied](docs/fixes/FIXES_APPLIED.md) - List of applied fixes
- [Fixes Summary](docs/fixes/FIXES_SUMMARY.md) - Summary of fixes and improvements
- [Database Verification Summary](docs/fixes/DB_VERIFICATION_SUMMARY.md) - Database verification details
- [Manual Chart Selection Fix](docs/fixes/MANUAL_CHART_SELECTION_FIX.md) - Chart selection fixes

### Setup & Development
- [Development Setup](docs/setup/DEV_SETUP.md) - Development environment setup
- [Development Setup (Fixed)](docs/setup/DEV_SETUP_FIXED.md) - Updated setup instructions
- [Frontend Integration Summary](docs/setup/FRONTEND_INTEGRATION_SUMMARY.md) - Frontend integration guide
- [Manual Verification Checklist](docs/setup/MANUAL_VERIFICATION_CHECKLIST.md) - Testing and verification guide

### History & Meta
- [Repository Inventory](docs/history/REPOSITORY_INVENTORY.md) - Repository structure and contents
- [Rules First Implementation](docs/history/RULES_FIRST_IMPLEMENTATION.md) - Initial implementation details

### Quick Reference
- [Quick Start](QUICK_START.md) - Get started quickly
- [Quick Build](QUICK_BUILD.md) - Fast build instructions
- [Build Instructions](BUILD_INSTRUCTIONS.md) - Detailed build guide

## License

[Your License Here]
