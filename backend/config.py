"""
Configuration module for Flask application.
Loads settings from environment variables with safe defaults where appropriate.
"""
import os
import secrets
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import timedelta
from backend.paths import data_path, DATA_DIR

logger = logging.getLogger(__name__)


def get_absolute_sqlite_path(database_url: str) -> str:
    """
    Get absolute SQLite database path based on vibecharting project directory.
    This is the SINGLE SOURCE OF TRUTH for database path.
    
    Always uses: <vibecharting_project_root>/data/charting_ai.db
    
    Args:
        database_url: Database URL (e.g., 'sqlite:///./data/charting_ai.db')
        Note: The path component is ignored - we always use the project-relative path.
    
    Returns:
        Absolute path to SQLite database file: <vibecharting>/data/charting_ai.db
    """
    if not database_url.startswith('sqlite:///'):
        raise ValueError(f"Not a SQLite database URL: {database_url}")
    
    # Use paths.py helper to get data directory path
    db_path = str(data_path('charting_ai.db'))
    
    return db_path


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    # Flask settings
    flask_env: str
    flask_debug: bool
    flask_secret_key: str
    
    # Flask session security settings
    session_cookie_secure: bool
    session_cookie_httponly: bool
    session_cookie_samesite: str
    permanent_session_lifetime_days: int
    
    # Gemini API
    gemini_api_key: str
    gemini_enabled: bool
    
    # Database Configuration
    database_url: str  # SQLite or Azure SQL connection string
    
    # Azure SQL Database (optional, only needed if using Azure SQL)
    azure_sql_server: Optional[str]
    azure_sql_database: Optional[str]
    azure_sql_username: Optional[str]
    azure_sql_password: Optional[str]
    azure_sql_driver: str
    azure_sql_encrypt: str
    azure_sql_trust_cert: str
    azure_sql_timeout: str
    database_auth_mode: str
    
    # Frontend serving (default: false in dev, true in prod)
    serve_frontend: bool


def get_settings() -> Settings:
    """
    Load and return application settings from environment variables.
    
    Returns:
        Settings: Configuration object with all required values.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Flask environment settings
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    flask_debug = os.environ.get('FLASK_DEBUG', '0').lower() in ('1', 'true', 'yes')
    
    # Flask secret key handling
    flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not flask_secret_key:
        if flask_env == 'production':
            raise ValueError(
                "FLASK_SECRET_KEY is required in production. "
                "Please set it as an environment variable."
            )
        else:
            # Generate a temporary key for development
            flask_secret_key = secrets.token_urlsafe(32)
            logger.warning(
                "FLASK_SECRET_KEY not set. Generated temporary key for development. "
                "Set FLASK_SECRET_KEY environment variable for production use."
            )
    
    # Gemini API key (required always, but can be disabled)
    gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
    if not gemini_api_key:
        # Only raise error if Gemini is enabled
        gemini_enabled_env = os.environ.get('GEMINI_ENABLED', 'true').lower() in ('1', 'true', 'yes')
        if gemini_enabled_env:
            raise ValueError(
                "GEMINI_API_KEY is required when GEMINI_ENABLED is true. "
                "Please set it as an environment variable or set GEMINI_ENABLED=false."
            )
        else:
            # Generate a dummy key if disabled (won't be used)
            gemini_api_key = 'disabled'
            logger.warning("GEMINI_API_KEY not set, but GEMINI_ENABLED is false. Using dummy key.")
    
    # Gemini enabled toggle (default: true)
    gemini_enabled = os.environ.get('GEMINI_ENABLED', 'true').lower() in ('1', 'true', 'yes')
    
    # Database URL (defaults to SQLite for local development)
    database_url_env = os.environ.get('DATABASE_URL', 'sqlite:///./backend/data/charting_ai.db')
    
    # Ensure data directory exists for SQLite (Windows-friendly)
    if database_url_env.startswith('sqlite:///'):
        import pathlib
        # Get absolute path using single source of truth function
        db_path = get_absolute_sqlite_path(database_url_env)
        # Ensure data directory exists
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data directory: {DATA_DIR}")
        # Always use absolute path in database_url
        database_url = f'sqlite:///{db_path}'
    else:
        database_url = database_url_env
    
    # Azure SQL Database settings (optional, only required if using Azure SQL)
    # Check if DATABASE_URL indicates Azure SQL or if Azure SQL vars are explicitly set
    is_azure_sql = (
        database_url.startswith('mssql+pyodbc://') or
        database_url.startswith('mssql://') or
        os.environ.get('AZURE_SQL_SERVER') is not None
    )
    
    if is_azure_sql or not database_url.startswith('sqlite:///'):
        # Azure SQL settings are required
        azure_sql_server = os.environ.get('AZURE_SQL_SERVER')
        if not azure_sql_server:
            raise ValueError(
                "AZURE_SQL_SERVER is required when using Azure SQL. "
                "Set DATABASE_URL to sqlite:///./backend/data/charting_ai.db for SQLite, "
                "or provide AZURE_SQL_SERVER for Azure SQL."
            )
        
        azure_sql_database = os.environ.get('AZURE_SQL_DATABASE')
        if not azure_sql_database:
            raise ValueError(
                "AZURE_SQL_DATABASE is required when using Azure SQL. "
                "Please set it as an environment variable."
            )
        
        azure_sql_username = os.environ.get('AZURE_SQL_USERNAME')
        if not azure_sql_username:
            raise ValueError(
                "AZURE_SQL_USERNAME is required when using Azure SQL. "
                "Please set it as an environment variable."
            )
        
        azure_sql_password = os.environ.get('AZURE_SQL_PASSWORD')
        if not azure_sql_password:
            raise ValueError(
                "AZURE_SQL_PASSWORD is required when using Azure SQL. "
                "Please set it as an environment variable."
            )
    else:
        # SQLite mode - Azure SQL settings not required
        azure_sql_server = None
        azure_sql_database = None
        azure_sql_username = None
        azure_sql_password = None
    
    # Flask session security settings
    # SESSION_COOKIE_SECURE: True in production (HTTPS only), False in development
    session_cookie_secure = (flask_env == 'production')
    
    # SESSION_COOKIE_HTTPONLY: Always True to prevent XSS attacks
    session_cookie_httponly = True
    
    # SESSION_COOKIE_SAMESITE: Configurable, default "Lax"
    session_cookie_samesite = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    if session_cookie_samesite not in ('Strict', 'Lax', 'None'):
        raise ValueError(
            f"SESSION_COOKIE_SAMESITE must be 'Strict', 'Lax', or 'None'. "
            f"Got: {session_cookie_samesite}"
        )
    
    # PERMANENT_SESSION_LIFETIME: Configurable in days, default 7
    try:
        permanent_session_lifetime_days = int(os.environ.get('PERMANENT_SESSION_DAYS', '7'))
        if permanent_session_lifetime_days < 1:
            raise ValueError("PERMANENT_SESSION_DAYS must be at least 1")
    except (ValueError, TypeError) as e:
        env_value = os.environ.get('PERMANENT_SESSION_DAYS', '7')
        raise ValueError(
            f"PERMANENT_SESSION_DAYS must be a valid integer (>= 1). Got: {env_value}"
        ) from e
    
    # Azure SQL optional settings with defaults
    azure_sql_driver = os.environ.get('AZURE_SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
    azure_sql_encrypt = os.environ.get('AZURE_SQL_ENCRYPT', 'yes')
    azure_sql_trust_cert = os.environ.get('AZURE_SQL_TRUST_CERT', 'no')
    azure_sql_timeout = os.environ.get('AZURE_SQL_TIMEOUT', '30')
    
    # Database authentication mode (for future managed identity/AAD support)
    # Current default: "sql_password" (SQL username/password authentication)
    # TODO: Future support for "managed_identity" and "aad" authentication modes
    database_auth_mode = os.environ.get('DATABASE_AUTH_MODE', 'sql_password')
    if database_auth_mode not in ('sql_password',):
        # Placeholder for future modes: 'managed_identity', 'aad'
        logger.warning(
            f"DATABASE_AUTH_MODE '{database_auth_mode}' is not yet implemented. "
            f"Falling back to 'sql_password'. "
            f"Supported modes: 'sql_password'"
        )
        database_auth_mode = 'sql_password'
    
    # Frontend serving: default false in dev, true in prod
    # In dev mode, frontend should run separately (npm run dev)
    # In prod mode, Flask serves the built frontend from dist/
    serve_frontend_env = os.environ.get('SERVE_FRONTEND', '').lower()
    if serve_frontend_env in ('1', 'true', 'yes'):
        serve_frontend = True
    elif serve_frontend_env in ('0', 'false', 'no'):
        serve_frontend = False
    else:
        # Auto-detect: false in dev, true in prod
        serve_frontend = (flask_env == 'production')
    
    return Settings(
        flask_env=flask_env,
        flask_debug=flask_debug,
        flask_secret_key=flask_secret_key,
        session_cookie_secure=session_cookie_secure,
        session_cookie_httponly=session_cookie_httponly,
        session_cookie_samesite=session_cookie_samesite,
        permanent_session_lifetime_days=permanent_session_lifetime_days,
        gemini_api_key=gemini_api_key,
        gemini_enabled=gemini_enabled,
        database_url=database_url,
        azure_sql_server=azure_sql_server,
        azure_sql_database=azure_sql_database,
        azure_sql_username=azure_sql_username,
        azure_sql_password=azure_sql_password,
        azure_sql_driver=azure_sql_driver,
        azure_sql_encrypt=azure_sql_encrypt,
        azure_sql_trust_cert=azure_sql_trust_cert,
        azure_sql_timeout=azure_sql_timeout,
        database_auth_mode=database_auth_mode,
        serve_frontend=serve_frontend
    )


def validate_settings(settings: Settings) -> None:
    """
    Validate that all required settings are present and valid.
    
    This function NEVER prints or logs secret values. Only validation status is logged.
    
    Args:
        settings: Settings object to validate.
        
    Raises:
        ValueError: If any required settings are missing or invalid.
    """
    errors = []
    
    # Validate Flask settings
    if not settings.flask_secret_key:
        errors.append("FLASK_SECRET_KEY is required")
    elif len(settings.flask_secret_key) < 16:
        errors.append("FLASK_SECRET_KEY must be at least 16 characters long")
    
    # Validate session cookie settings
    if settings.session_cookie_samesite not in ('Strict', 'Lax', 'None'):
        errors.append(f"SESSION_COOKIE_SAMESITE must be 'Strict', 'Lax', or 'None'. Got: {settings.session_cookie_samesite}")
    
    if settings.permanent_session_lifetime_days < 1:
        errors.append(f"PERMANENT_SESSION_DAYS must be at least 1. Got: {settings.permanent_session_lifetime_days}")
    
    # Validate Gemini API (only if enabled)
    if settings.gemini_enabled and not settings.gemini_api_key:
        errors.append("GEMINI_API_KEY is required when GEMINI_ENABLED is true")
    # Note: We don't validate the format of the API key, just presence
    
    # Validate database URL
    if not settings.database_url:
        errors.append("DATABASE_URL is required")
    
    # Validate Azure SQL settings only if using Azure SQL (not SQLite)
    if settings.database_url and not settings.database_url.startswith('sqlite:///'):
        if not settings.azure_sql_server:
            errors.append("AZURE_SQL_SERVER is required when using Azure SQL")
        
        if not settings.azure_sql_database:
            errors.append("AZURE_SQL_DATABASE is required when using Azure SQL")
        
        if settings.database_auth_mode == 'sql_password':
            # Only validate username/password if using SQL password auth
            if not settings.azure_sql_username:
                errors.append("AZURE_SQL_USERNAME is required when DATABASE_AUTH_MODE=sql_password")
            
            if not settings.azure_sql_password:
                errors.append("AZURE_SQL_PASSWORD is required when DATABASE_AUTH_MODE=sql_password")
    
    if errors:
        # Log validation failure without exposing secrets
        logger.error("Configuration validation failed. Check required environment variables.")
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        )
    
    # Log successful validation (without secrets)
    logger.debug("Configuration validation passed")


def get_safe_log_summary(settings: Settings) -> str:
    """
    Generate a safe log summary that redacts all secrets.
    
    Args:
        settings: Settings object to summarize.
        
    Returns:
        str: Safe log message without any secret values.
    """
    # Determine database type for logging
    db_type = "SQLite" if settings.database_url.startswith('sqlite:///') else "Azure SQL"
    db_info = f"db_type={db_type}"
    if settings.azure_sql_server:
        db_info += f", db_server={settings.azure_sql_server}, db_database={settings.azure_sql_database}"
    else:
        db_info += f", db_path={settings.database_url.replace('sqlite:///', '')}"
    
    return (
        f"Config loaded: env={settings.flask_env}, "
        f"debug={settings.flask_debug}, "
        f"{db_info}, "
        f"db_auth_mode={settings.database_auth_mode}, "
        f"session_secure={settings.session_cookie_secure}, "
        f"session_samesite={settings.session_cookie_samesite}, "
        f"session_lifetime_days={settings.permanent_session_lifetime_days}, "
        f"gemini_enabled={settings.gemini_enabled}"
        # Note: username, password, API keys, and secret keys are intentionally omitted
    )

