import os
import json
import re
import time
import hashlib
import uuid
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
try:
    import google.generativeai as genai
except ModuleNotFoundError as e:
    raise RuntimeError("Missing dependency: google-generativeai. Ensure requirements are installed.") from e
import google.api_core.exceptions as genai_exceptions
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from scipy.interpolate import griddata
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
import pyodbc

# Configure FastAPI with backend-relative paths
# Get backend directory path
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_STATIC_DIR = BACKEND_DIR / 'static' / 'frontend'

app = FastAPI()

# Mount static files for Vite frontend assets
if FRONTEND_STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_STATIC_DIR / "assets")), name="assets")

# Request model for /chat endpoint
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = None
    forced_chart_type: Optional[str] = None

# --- LLM API Configuration ---
# Load from environment variable, with fallback for backward compatibility
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAjlVk5Ai8nyzK5dwBRFqfKmN9_FYP18UA')

if not GEMINI_API_KEY:
    raise ValueError(
        "ERROR: Gemini API key is not set. Please provide a valid key as an environment variable."
    )
genai.configure(api_key=GEMINI_API_KEY)
# Use temperature=0 for deterministic chart parameter extraction
model_for_chart_params = genai.GenerativeModel('gemini-2.5-flash', generation_config={'temperature': 0})
model_for_suggestions = genai.GenerativeModel('gemini-2.5-flash')

# --- Database Configuration (Azure SQL) ---
# All credentials loaded from environment variables (required)
AZURE_SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
AZURE_SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
AZURE_SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
AZURE_SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')
AZURE_SQL_DRIVER = os.getenv('AZURE_SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')

# Validate required environment variables
if not all([AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD]):
    raise ValueError(
        "Missing required Azure SQL environment variables. Please set:\n"
        "  - AZURE_SQL_SERVER\n"
        "  - AZURE_SQL_DATABASE\n"
        "  - AZURE_SQL_USERNAME\n"
        "  - AZURE_SQL_PASSWORD\n"
        "Optional: AZURE_SQL_DRIVER (defaults to '{ODBC Driver 17 for SQL Server}')\n"
        "See .env.example for template."
    )

# Build connection string for SQLAlchemy
# URL-encode driver name and credentials for proper connection string
driver_encoded = urllib.parse.quote_plus(AZURE_SQL_DRIVER)
username_encoded = urllib.parse.quote_plus(AZURE_SQL_USERNAME)
password_encoded = urllib.parse.quote_plus(AZURE_SQL_PASSWORD)

CONNECTION_STRING = (
    f"mssql+pyodbc://{username_encoded}:{password_encoded}@"
    f"{AZURE_SQL_SERVER}/{AZURE_SQL_DATABASE}?"
    f"driver={driver_encoded}&"
    f"Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"
)

# --- Caching Configuration ---
# Schema cache: {value: schema_dict, expires_at: timestamp}
_schema_cache: Optional[Tuple[Dict, float]] = None
SCHEMA_CACHE_TTL = 1800  # 30 minutes

# Response cache: {cache_key: (response_dict, expires_at)}
_response_cache: Dict[str, Tuple[Dict, float]] = {}
RESPONSE_CACHE_TTL = 120  # 2 minutes
MAX_RESPONSE_CACHE_ENTRIES = 200

# --- Chart Type Constants ---
VALID_CHART_TYPES = {
    'bar', 'bar_chart', 'bar chart',
    'line', 'line_chart', 'line chart',
    'pie', 'pie_chart', 'pie chart',
    'scatter', 'scatter_plot', 'scatter plot',
    'area', 'area_chart', 'area chart',
    'stacked_bar', 'stacked_bar_chart', 'stacked bar',
    'donut', 'donut_chart', 'donut chart',
    'bubble', 'bubble_chart', 'bubble chart',
    'box', 'box_plot', 'box plot',
    'histogram',
    '3d', '3d_scatter', '3d_scatter_plot', '3d scatter',
}

CHART_TYPE_MAPPING = {
    'bar': 'bar_chart', 'bar_chart': 'bar_chart', 'bar chart': 'bar_chart',
    'line': 'line_chart', 'line_chart': 'line_chart', 'line chart': 'line_chart',
    'pie': 'pie_chart', 'pie_chart': 'pie_chart', 'pie chart': 'pie_chart',
    'scatter': 'scatter_plot', 'scatter_plot': 'scatter_plot', 'scatter plot': 'scatter_plot',
    'area': 'area_chart', 'area_chart': 'area_chart', 'area chart': 'area_chart',
    'stacked_bar': 'stacked_bar_chart', 'stacked_bar_chart': 'stacked_bar_chart', 'stacked bar': 'stacked_bar_chart',
    'donut': 'donut_chart', 'donut_chart': 'donut_chart', 'donut chart': 'donut_chart',
    'bubble': 'bubble_chart', 'bubble_chart': 'bubble_chart', 'bubble chart': 'bubble_chart',
    'box': 'box_plot', 'box_plot': 'box_plot', 'box plot': 'box_plot',
    'histogram': 'histogram',
    '3d': '3d_scatter_plot', '3d_scatter': '3d_scatter_plot', '3d_scatter_plot': '3d_scatter_plot', '3d scatter': '3d_scatter_plot',
}

def normalize_chart_type(chart_type: Optional[str]) -> Optional[str]:
    """Normalize chart type to canonical backend value."""
    if not chart_type:
        return None
    normalized = chart_type.lower().strip()
    return CHART_TYPE_MAPPING.get(normalized, normalized if normalized in VALID_CHART_TYPES else None)

# --- Helper Functions ---
def ensure_json_dict(x: Any) -> Optional[Dict]:
    """
    Robust helper to ensure we have a Python dict for JSON serialization.
    - Returns None if x is None
    - Returns x if x is already a dict
    - Parses x if x is str/bytes
    - Raises TypeError otherwise
    """
    if x is None:
        return None
    if isinstance(x, dict):
        return x
    if isinstance(x, (str, bytes)):
        return json.loads(x)
    raise TypeError(f"Expected dict, str, bytes, or None, got {type(x).__name__}")

def to_json_safe_plotly(obj: Any) -> Any:
    """
    Convert Plotly objects (and nested numpy/pandas types) to JSON-serializable Python types.
    Uses PlotlyJSONEncoder to handle numpy arrays, pandas timestamps, and Plotly-specific types.
    """
    if obj is None:
        return None
    try:
        # Use PlotlyJSONEncoder to serialize, then parse back to get pure Python types
        json_str = json.dumps(obj, cls=PlotlyJSONEncoder)
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        # Fallback: return as-is if serialization fails (shouldn't happen with PlotlyJSONEncoder)
        print(f"Warning: Failed to convert Plotly object to JSON-safe format: {e}")
        return obj

def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    Extract the first valid JSON object from text that may contain markdown, code fences, or extra text.
    Returns None if no valid JSON found.
    """
    if not text:
        return None
    
    # Try direct parse first
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return parsed
    except:
        pass
    
    # Remove markdown code fences
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try parsing again after cleaning
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except:
        pass
    
    # Try to find JSON object boundaries
    # Look for first { and matching }
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    # Find matching closing brace
    brace_count = 0
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start_idx:i+1]
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
                break
    
    return None

def validate_chart_params(params: Dict, request_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate chart parameters against required schema.
    Returns (is_valid, error_message, recommended_params).
    """
    required_fields = ['table_name', 'chart_type', 'x_axis', 'y_axis', 'title']
    
    # Check required fields
    missing = [f for f in required_fields if f not in params or not params[f]]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}", None
    
    # Validate chart_type
    chart_type = normalize_chart_type(params.get('chart_type'))
    if not chart_type:
        return False, f"Invalid chart_type: {params.get('chart_type')}", None
    
    params['chart_type'] = chart_type
    
    # Validate field types
    if not isinstance(params['table_name'], str):
        return False, "table_name must be a string", None
    if not isinstance(params['x_axis'], str):
        return False, "x_axis must be a string", None
    if not isinstance(params['y_axis'], str):
        return False, "y_axis must be a string", None
    if not isinstance(params['title'], str):
        return False, "title must be a string", None
    
    return True, None, params

def assess_chart_suitability(chart_type: str, df: pd.DataFrame, chart_params: Dict) -> Dict:
    """
    Assess if the requested chart type is suitable for the data.
    Returns dict with recommended_chart_type, reason_not_best, chart_warnings.
    Never blocks chart generation - always returns a recommendation.
    """
    result = {
        'recommended_chart_type': chart_type,
        'reason_not_best': None,
        'chart_warnings': []
    }
    
    x_col = chart_params.get('x_axis')
    y_col = chart_params.get('y_axis')
    
    # Check if 3D chart is requested but missing z_axis
    if chart_type == '3d_scatter_plot':
        z_col = chart_params.get('z_axis')
        if not z_col or z_col not in df.columns:
            result['recommended_chart_type'] = 'scatter_plot'
            result['reason_not_best'] = "3D scatter plot requires a Z-axis column. Using 2D scatter plot instead."
            result['chart_warnings'].append("Missing Z-axis for 3D chart")
    
    # Check if bubble chart is requested but missing size
    elif chart_type == 'bubble_chart':
        size_col = chart_params.get('size')
        if not size_col or size_col not in df.columns:
            result['recommended_chart_type'] = 'scatter_plot'
            result['reason_not_best'] = "Bubble chart requires a size column. Using scatter plot instead."
            result['chart_warnings'].append("Missing size column for bubble chart")
    
    # Check if pie/donut chart has too many categories
    elif chart_type in ['pie_chart', 'donut_chart']:
        if x_col in df.columns:
            unique_count = df[x_col].nunique()
            if unique_count > 10:
                result['chart_warnings'].append(f"Pie chart has {unique_count} categories, which may be hard to read. Consider using a bar chart.")
    
    # Check if bar chart would benefit from stacking
    elif chart_type == 'bar_chart':
        color_col = chart_params.get('color')
        if color_col and color_col in df.columns:
            unique_count = df[color_col].nunique()
            if unique_count <= 5:
                result['chart_warnings'].append("Consider using a stacked bar chart to show breakdown by color.")
    
    return result

def _get_response_cache_key(message: str, language: str, forced_chart_type: Optional[str] = None) -> str:
    """Generate cache key for response caching."""
    normalized = message.lower().strip()
    key_input = f"{normalized}|{language}|{forced_chart_type or ''}"
    return hashlib.sha256(key_input.encode('utf-8')).hexdigest()

def _clean_response_cache():
    """Remove expired entries and enforce LRU size limit."""
    current_time = time.time()
    expired_keys = [k for k, (_, exp) in _response_cache.items() if exp < current_time]
    for k in expired_keys:
        del _response_cache[k]
    
    # LRU: if over limit, remove oldest entries
    if len(_response_cache) > MAX_RESPONSE_CACHE_ENTRIES:
        sorted_items = sorted(_response_cache.items(), key=lambda x: x[1][1])
        to_remove = len(_response_cache) - MAX_RESPONSE_CACHE_ENTRIES
        for k, _ in sorted_items[:to_remove]:
            del _response_cache[k]

# SQLAlchemy engine with connection pooling
_db_engine: Optional[Engine] = None

def get_db_engine() -> Engine:
    """
    Get or create SQLAlchemy engine with connection pooling.
    Uses QueuePool for connection management with timeouts.
    """
    global _db_engine
    if _db_engine is None:
        _db_engine = create_engine(
            CONNECTION_STRING,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False  # Set to True for SQL query logging
        )
    return _db_engine

def get_db_connection():
    """
    Establishes and returns a database connection using SQLAlchemy.
    Returns a connection from the connection pool.
    """
    try:
        engine = get_db_engine()
        return engine.connect()
    except Exception as ex:
        print(f"Database connection error: {type(ex).__name__}: {ex}")
        return None

def get_all_table_schemas():
    """
    Fetches all table names and their column schemas from Azure SQL Server.
    Uses INFORMATION_SCHEMA and caches for 30 minutes to improve performance.
    Only includes target tables: Account, Contact, Lead, Opportunity.
    """
    global _schema_cache
    
    # Check cache
    current_time = time.time()
    if _schema_cache is not None:
        schema_dict, expires_at = _schema_cache
        if expires_at > current_time:
            return schema_dict
    
    # Cache miss or expired - fetch fresh
    conn = None
    all_table_schemas = {}
    try:
        conn = get_db_connection()
        if conn:
            # Target tables only
            target_tables = ['Account', 'Contact', 'Lead', 'Opportunity']
            
            for table_name in target_tables:
                all_columns = []
                numerical_columns = []
                date_columns = []
                categorical_columns = []
                
                # Query INFORMATION_SCHEMA for column metadata
                query = text("""
                    SELECT COLUMN_NAME, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = :table_name 
                    AND TABLE_CATALOG = :database
                    ORDER BY ORDINAL_POSITION
                """)
                result = conn.execute(query, {'table_name': table_name, 'database': AZURE_SQL_DATABASE})
                
                for row in result:
                    col_name = row.COLUMN_NAME
                    data_type = row.DATA_TYPE.lower()
                    all_columns.append(col_name)
        
                    # Classify column types
                    if data_type in ['int', 'smallint', 'bigint', 'tinyint', 'decimal', 'numeric', 'real', 'float', 'money', 'smallmoney', 'bit']:
                        numerical_columns.append(col_name)
                    elif data_type in ['date', 'datetime', 'datetime2', 'smalldatetime', 'timestamp', 'time', 'datetimeoffset']:
                        date_columns.append(col_name)
                    else:
                        categorical_columns.append(col_name)
                
                if all_columns:  # Only add if table exists and has columns
                    all_table_schemas[table_name] = {
                        'all_columns': all_columns,
                        'numerical_columns': numerical_columns,
                        'date_columns': date_columns,
                        'categorical_columns': categorical_columns
                    }
    except Exception as e:
        print(f"Error getting table schemas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
    
    # Update cache
    _schema_cache = (all_table_schemas, current_time + SCHEMA_CACHE_TTL)
    return all_table_schemas
    
def validate_chart_fields(chart_type: str, chart_params: Dict, schema_info: Dict) -> Tuple[bool, Optional[str], Optional[List[str]]]:
    """
    Validate chart field requirements before data fetch.
    Returns (is_valid, error_message, suggested_fields).
    """
    table_name = chart_params.get('table_name')
    if table_name not in schema_info:
        return False, f"Table '{table_name}' not found in schema", None
    
    table_schema = schema_info[table_name]
    x_col = chart_params.get('x_axis')
    y_col = chart_params.get('y_axis')
    z_col = chart_params.get('z_axis')
    
    # Histogram: needs 1 numeric field
    if chart_type == 'histogram':
        if not x_col:
            return False, "Histogram requires 1 numeric field for X-axis", table_schema['numerical_columns']
        if x_col not in table_schema['numerical_columns']:
            return False, f"Histogram X-axis '{x_col}' must be numeric", table_schema['numerical_columns']
    
    # Scatter: needs 2 numeric fields
    elif chart_type == 'scatter_plot':
        if not x_col or not y_col:
            return False, "Scatter plot requires 2 numeric fields (X and Y)", table_schema['numerical_columns']
        if x_col not in table_schema['numerical_columns']:
            return False, f"Scatter plot X-axis '{x_col}' must be numeric", table_schema['numerical_columns']
        if y_col not in table_schema['numerical_columns']:
            return False, f"Scatter plot Y-axis '{y_col}' must be numeric", table_schema['numerical_columns']
    
    # 3D Scatter: needs 3 numeric fields
    elif chart_type == '3d_scatter_plot':
        if not x_col or not y_col or not z_col:
            return False, "3D scatter plot requires 3 numeric fields (X, Y, Z)", table_schema['numerical_columns']
        if x_col not in table_schema['numerical_columns']:
            return False, f"3D scatter plot X-axis '{x_col}' must be numeric", table_schema['numerical_columns']
        if y_col not in table_schema['numerical_columns']:
            return False, f"3D scatter plot Y-axis '{y_col}' must be numeric", table_schema['numerical_columns']
        if z_col not in table_schema['numerical_columns']:
            return False, f"3D scatter plot Z-axis '{z_col}' must be numeric", table_schema['numerical_columns']
    
    return True, None, None

def fetch_data_for_chart(chart_params):
    """
    Fetches data from Azure SQL Server based on chart parameters.
    Applies row limits: 1000 for non-aggregated, 50 groups for aggregated.
    Uses SQL Server dialect (TOP instead of LIMIT, bracket quoting).
    """
    table_name = chart_params.get('table_name')
    if not table_name:
        print("Error: Table name not provided in chart_params.")
        return None
    
    conn = None
    df = None
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        # Get column metadata from INFORMATION_SCHEMA
        column_metadata = {}
        query = text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = :table_name 
            AND TABLE_CATALOG = :database
            ORDER BY ORDINAL_POSITION
        """)
        result = conn.execute(query, {'table_name': table_name, 'database': AZURE_SQL_DATABASE})
        for row in result:
            column_metadata[row.COLUMN_NAME] = row.DATA_TYPE
    
        x_col = chart_params.get('x_axis')
        y_col = chart_params.get('y_axis')
        color_col = chart_params.get('color')
        z_col = chart_params.get('z_axis')
        size_col = chart_params.get('size')
        aggregate_y = chart_params.get('aggregate_y')
        
        # Build column list (never SELECT *)
        columns_to_select_set = set()
        if x_col: columns_to_select_set.add(x_col)
        if y_col: columns_to_select_set.add(y_col)
        if color_col: columns_to_select_set.add(color_col)
        if z_col: columns_to_select_set.add(z_col)
        if size_col: columns_to_select_set.add(size_col)
        
        if not columns_to_select_set:
            print(f"No specific columns identified for table {table_name}. Selecting all available columns.")
            # Get all columns from schema
            query = text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = :table_name 
                AND TABLE_CATALOG = :database
                ORDER BY ORDINAL_POSITION
            """)
            result = conn.execute(query, {'table_name': table_name, 'database': AZURE_SQL_DATABASE})
            all_cols = [row.COLUMN_NAME for row in result]
            columns_to_select = ", ".join([f'[{col}]' for col in all_cols])
        else:
            # Quote column names with SQL Server brackets
            columns_to_select = ", ".join([f'[{col}]' for col in columns_to_select_set])
        
        if not columns_to_select:
            print(f"Could not determine columns to select for table {table_name}.")
            return None
        
        # Build query with SQL Server TOP clause (not LIMIT)
        if not aggregate_y:
            query_str = f"SELECT TOP 1000 {columns_to_select} FROM [{table_name}]"
        else:
            query_str = f"SELECT {columns_to_select} FROM [{table_name}]"
        
        # Use pandas with SQLAlchemy connection
        df = pd.read_sql(text(query_str), conn)
        
        # Apply row limit in pandas if needed (fallback)
        if not aggregate_y and len(df) > 1000:
            df = df.head(1000)
        
        # Convert date columns
        date_types = ['date', 'datetime', 'datetime2', 'smalldatetime', 'timestamp', 'time', 'datetimeoffset']
        for col, dtype in column_metadata.items():
            if dtype.lower() in date_types and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Apply aggregation with group limit
        if aggregate_y and y_col and x_col:
            if aggregate_y.upper() == 'COUNT':
                df_agg = df.groupby(x_col).size().reset_index(name=f'Count of {y_col}')
                # Limit groups to 50
                if len(df_agg) > 50:
                    df_agg = df_agg.head(50)
                chart_params['y_axis'] = f'Count of {y_col}'
                df = df_agg
            elif aggregate_y.upper() in ['SUM', 'AVG', 'MIN', 'MAX'] and y_col in df.columns:
                # Check if numerical
                is_numerical = column_metadata.get(y_col, '').lower() in [
                    'int', 'smallint', 'bigint', 'tinyint', 'decimal', 'numeric', 
                    'real', 'float', 'money', 'smallmoney', 'bit'
                ]
                
                if not is_numerical:
                    print(f"Warning: Cannot apply {aggregate_y} to non-numerical column '{y_col}'.")
                    return None
    
                if aggregate_y.upper() == 'SUM':
                    df_agg = df.groupby(x_col)[y_col].sum().reset_index(name=f'Sum of {y_col}')
                elif aggregate_y.upper() == 'AVG':
                    df_agg = df.groupby(x_col)[y_col].mean().reset_index(name=f'Average of {y_col}')
                elif aggregate_y.upper() == 'MIN':
                    df_agg = df.groupby(x_col)[y_col].min().reset_index(name=f'Min of {y_col}')
                elif aggregate_y.upper() == 'MAX':
                    df_agg = df.groupby(x_col)[y_col].max().reset_index(name=f'Max of {y_col}')
                
                # Limit groups to 50
                if len(df_agg) > 50:
                    df_agg = df_agg.head(50)
                
                chart_params['y_axis'] = df_agg.columns[1]  # Use the aggregated column name
                df = df_agg
        
        print(f"Data fetched successfully for table {table_name}. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"Error fetching data for chart from table {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()
    
def create_chart_json(df, chart_params):
    """Generates Plotly chart JSON based on DataFrame and chart parameters."""
    chart_type = chart_params.get('chart_type')
    x_col = chart_params.get('x_axis')
    y_col = chart_params.get('y_axis')
    color_col = chart_params.get('color')
    title = chart_params.get('title', f"{chart_type.replace('_', ' ').title()} of {y_col} vs {x_col}")
    
    if x_col and x_col not in df.columns:
        return {'error': f"X-axis column '{x_col}' not found in data. Available columns: {list(df.columns)}"}
    if y_col and y_col not in df.columns and chart_type != 'pie_chart' and chart_type != 'donut_chart':
        return {'error': f"Y-axis column '{y_col}' not found in data. Available columns: {list(df.columns)}"}
    if color_col and color_col not in df.columns:
        return {'error': f"Color column '{color_col}' not found in data. Available columns: {list(df.columns)}"}
    
    fig = go.Figure()
    
    # Use Plotly's qualitative color sequence for vibrant charts
    color_sequence = px.colors.qualitative.Plotly
    
    if chart_type == 'bar_chart':
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'line_chart':
        fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'scatter_plot':
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'pie_chart':
        if not x_col or not y_col:
            return {'error': "Pie chart requires both names (x_axis) and values (y_axis)."}
        fig = px.pie(df, names=x_col, values=y_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'donut_chart': # Added support for donut chart
        if not x_col or not y_col:
            return {'error': "Donut chart requires both names (x_axis) and values (y_axis)."}
        fig = px.pie(df, names=x_col, values=y_col, title=title, hole=0.4, color_discrete_sequence=color_sequence) # hole creates the donut
    elif chart_type == 'histogram':
        fig = px.histogram(df, x=x_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'box_plot':
        fig = px.box(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'area_chart':
        fig = px.area(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'stacked_bar_chart':
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=color_sequence, barmode='stack')
    elif chart_type == '3d_scatter_plot':
        z_col = chart_params.get('z_axis')
        if not z_col or z_col not in df.columns:
            return {'error': f"3D Scatter plot requires X, Y, and Z columns. Z-axis column '{z_col}' not found."}
        fig = px.scatter_3d(df, x=x_col, y=y_col, z=z_col, color=color_col, title=title, color_discrete_sequence=color_sequence)
    elif chart_type == 'bubble_chart':
        size_col = chart_params.get('size')
        if not size_col or size_col not in df.columns:
            return {'error': f"Bubble chart requires a 'size' column. Size column '{size_col}' not found."}
        fig = px.scatter(df, x=x_col, y=y_col, size=size_col, color=color_col, hover_name=x_col, title=title, color_discrete_sequence=color_sequence)
    else:
        return {'error': "Unsupported chart type requested."}
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=app.config.get('PLOTLY_FONT_COLOR', '#333'),
        title_font_size=20,
        title_x=0.5,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # Use to_plotly_json() to get dict directly (faster, avoids double serialization)
    return fig.to_plotly_json()
    
INITIAL_CHART_SUGGESTIONS = [
    "bar chart", "pie chart", "donut chart", "3d chart", "line chart", "scatter plot", "histogram",
    "box plot", "area chart", "bubble chart"
]

def detect_language(text: str) -> str:
    """
    Detect language from text input.
    Returns 'ar' if Arabic characters are found, otherwise 'en'.
    """
    # Check for Arabic Unicode range (0600-06FF)
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    if arabic_pattern.search(text):
        return 'ar'
    return 'en'

# API routes (must come before SPA fallback)
@app.post('/chat')
async def chat(request_body: ChatRequest):
    """Handles chatbot interactions with robust error handling and JSON parsing."""
    request_id = str(uuid.uuid4())[:8]
    user_message_raw = request_body.message
    user_message = user_message_raw.lower()
    # Detect language from input if not explicitly provided
    detected_lang = detect_language(user_message_raw)
    user_language = request_body.language if request_body.language else detected_lang # Use detected language as fallback
    forced_chart_type_raw = request_body.forced_chart_type # Get forced chart type from frontend
    forced_chart_type = normalize_chart_type(forced_chart_type_raw) if forced_chart_type_raw else None
    
    print(f"[{request_id}] Request: message='{user_message_raw[:50]}...', lang={user_language}, forced_type={forced_chart_type}")
    
    all_table_schemas = get_all_table_schemas()
    if not all_table_schemas:
        error_messages = {
            'en': 'Error: Could not retrieve database schema. Please check database connection.',
            'es': 'Error: No se pudo recuperar el esquema de la base de datos. Por favor, verifica la conexión a la base de datos.',
            'fr': 'Erreur : Impossible de récupérer le schéma de la base de données. Veuillez vérifier la conexión a la base de données.',
            'de': 'Fehler: Datenbankschema konnte nicht abgerufen werden. Bitte überprüfen Sie die Datenbankverbindung.',
            'ja': 'エラー: データベーススキーマを取得できませんでした。データベース接続を確認してください。',
            'ko': '오류: 데이터베이스 스키마를 검색할 수 없습니다. 데이터베이스 연결을 확인하십시오.',
            'ar': 'خطأ: تعذر استرداد مخطط قاعدة البيانات. يرجى التحقق من اتصال قاعدة البيانات.'
        }
        return {
            'response': error_messages.get(user_language, 'Error: Could not retrieve database schema. Please check database connection.'),
            'suggestions': []
        }
    
    schema_info = ""
    for table_name, schema in all_table_schemas.items():
        schema_info += f"Table: {table_name}\n"
        schema_info += f"  All Columns: {', '.join(schema['all_columns'])}\n"
        schema_info += f"  Numerical Columns: {', '.join(schema['numerical_columns'])}\n"
        schema_info += f"  Date Columns: {', '.join(schema['date_columns'])}\n"
        schema_info += f"  Categorical Columns: {', '.join(schema['categorical_columns'])}\n"
    
    if user_message == "__initial_load__":
        welcome_message = {
            'en': "I am your AI Insight Assistant. How can I visualize your data?",
            'es': "Soy tu Asistente de IA para Insights. ¿Cómo puedo visualizar tus datos?",
            'fr': "Je suis votre Assistant IA d'Insights. Comment puis-je visualiser vos données ?",
            'de': "Ich bin Ihr KI-Analyseassistent. Wie kann ich Ihre Daten visualisieren?",
            'ja': "AIインサイトアシスタントです。データをどのように視覚化できますか？",
            'ko': "AI 인사이트 어시스턴트입니다. 데이터를 어떻게 시각화해 드릴까요?",
            'ar': "أنا مساعدك الذكي للتحليلات. كيف يمكنني تصور بياناتك؟"
        }.get(user_language, "I am your AI Insight Assistant. How can I visualize your data?")
        suggestions = ["Bar Chart", "Pie Chart", "Donut Chart", "3D Chart", "Line Chart", "Scatter Plot", "Histogram"]
        return {'response': welcome_message, 'suggestions': suggestions}
    
    # If the user's message is an initial chart type suggestion, respond with a follow-up question
    # and indicate the requested_chart_type for the frontend to store.
    if user_message in [s.lower() for s in INITIAL_CHART_SUGGESTIONS]:
        normalized_type = normalize_chart_type(user_message)
        response_texts = {
            'en': f"Great! What data would you like to see in a {user_message}?",
            'es': f"¡Genial! ¿Qué datos te gustaría ver en un {user_message}?",
            'fr': f"Super ! Quelles données souhaitez-vous voir dans un {user_message} ?",
            'de': f"Großartig! Welche Daten möchten Sie in einem {user_message} sehen?",
            'ja': f"素晴らしい！{user_message}でどのようなデータを見たいですか？",
            'ko': f"좋아요! {user_message}에서 어떤 데이터를 보고 싶으신가요?",
            'ar': f"رائع! ما هي البيانات التي ترغب في رؤيتها في {user_message}؟"
        }
        response_text = response_texts.get(user_language, f"Great! What data would you like to see in a {user_message}?")
        return {'response': response_text, 'suggestions': [], 'forced_chart_type': normalized_type or user_message}
    
    try:
        # Include forced_chart_type in the prompt if available, but primarily for context.
        # The actual enforcement will happen after LLM response.
        chart_type_hint = f" The user previously selected chart type '{forced_chart_type}' and expects this chart to be of that type. Prioritize this type." if forced_chart_type else ""
        
        prompt_for_chart_params = f"""You are an AI assistant that generates chart parameters from natural language queries.

CRITICAL: You MUST respond with ONLY a valid JSON object. No markdown, no code fences, no explanatory text before or after.

Database schema:
{schema_info}

Required JSON schema:
{{
  "table_name": "string (must be from schema)",
  "chart_type": "string (bar_chart|line_chart|scatter_plot|pie_chart|histogram|box_plot|area_chart|stacked_bar_chart|3d_scatter_plot|bubble_chart|donut_chart)",
  "x_axis": "string (column name from table)",
  "y_axis": "string (column name from table)",
  "title": "string (user-friendly title in {user_language})",
  "summary": "string (1-2 sentence explanation in {user_language})",
  "aggregate_y": "string|null (SUM|AVG|COUNT|MIN|MAX|null)",
  "color": "string|null (optional column for coloring)",
  "z_axis": "string|null (required for 3d_scatter_plot)",
  "size": "string|null (required for bubble_chart)",
  "chart_reasoning": "string|null (optional: why this chart type was chosen)",
  "chart_warnings": "array|null (optional: array of warning strings)"
}}

Rules:
1. table_name: Must exist in schema. Choose most relevant if unclear.
2. chart_type: {chart_type_hint} If vague, infer best type (time→line_chart, categories→bar_chart, default→bar_chart).
3. x_axis: Categorical or date column. Required.
4. y_axis: Numerical column. Required.
5. title: Clear, conversational title in {user_language}.
6. summary: Brief explanation in {user_language}.
7. aggregate_y: Use if user asks for totals/averages/counts.
8. z_axis: Required only for 3d_scatter_plot.
9. size: Required only for bubble_chart.
10. All column names must exist in the chosen table.

Example output (JSON only):
{{"table_name":"Account","chart_type":"bar_chart","x_axis":"Region","y_axis":"Revenue","title":"Revenue by Region","summary":"This chart shows total revenue by region","aggregate_y":"SUM","color":null,"z_axis":null,"size":null,"chart_reasoning":null,"chart_warnings":null}}

User request: {user_message_raw}
"""
    
        # Call Gemini with retry on JSON parsing failure
        chart_params = None
        parse_error = None
        
        for attempt in range(2):  # Try twice
            try:
                response_chart_params = model_for_chart_params.generate_content(prompt_for_chart_params)
                chart_params_str = response_chart_params.text
                print(f"[{request_id}] Gemini response (attempt {attempt+1}): {chart_params_str[:200]}...")
                
                # Extract JSON from text (handles markdown, code fences, extra text)
                chart_params = extract_json_from_text(chart_params_str)
                
                if chart_params:
                    # Validate schema
                    is_valid, error_msg, validated_params = validate_chart_params(chart_params, request_id)
                    if is_valid:
                        chart_params = validated_params
                        print(f"[{request_id}] JSON parse success, chart_type={chart_params.get('chart_type')}")
                        break
                    else:
                        parse_error = error_msg
                        print(f"[{request_id}] Validation failed: {parse_error}")
                        if attempt == 0:
                            # Retry with fix prompt
                            prompt_for_chart_params = f"""The previous response had invalid JSON. Fix it to match this exact schema:

{{
  "table_name": "string",
  "chart_type": "bar_chart|line_chart|scatter_plot|pie_chart|histogram|box_plot|area_chart|stacked_bar_chart|3d_scatter_plot|bubble_chart|donut_chart",
  "x_axis": "string",
  "y_axis": "string",
  "title": "string",
  "summary": "string",
  "aggregate_y": "string|null",
  "color": "string|null",
  "z_axis": "string|null",
  "size": "string|null",
  "chart_reasoning": "string|null",
  "chart_warnings": "array|null"
}}

Previous invalid response: {chart_params_str[:500]}

Error: {parse_error}

Database schema:
{schema_info}

User request: {user_message_raw}

Respond with ONLY valid JSON matching the schema above."""
                else:
                    parse_error = "No valid JSON object found in response"
                    print(f"[{request_id}] JSON extraction failed: {parse_error}")
                    if attempt == 0:
                        # Retry with fix prompt
                        prompt_for_chart_params = f"""The previous response did not contain valid JSON. Respond with ONLY a JSON object, no markdown or code fences.

Database schema:
{schema_info}

User request: {user_message_raw}

Required JSON schema:
{{"table_name":"string","chart_type":"bar_chart|line_chart|...","x_axis":"string","y_axis":"string","title":"string","summary":"string","aggregate_y":"string|null","color":"string|null","z_axis":"string|null","size":"string|null","chart_reasoning":"string|null","chart_warnings":"array|null"}}"""
            except genai_exceptions.ResourceExhausted as e:
                print(f"[{request_id}] Gemini quota exceeded: {e}")
                return {
                    'error_type': 'RATE_LIMIT',
                    'message': 'AI quota exceeded. Please try again shortly or upgrade billing.',
                    'suggestions': []
                }
            except Exception as e:
                print(f"[{request_id}] Gemini call error (attempt {attempt+1}): {type(e).__name__}: {e}")
                if attempt == 1:
                    return {
                        'error_type': 'MODEL_OUTPUT_ERROR',
                        'message': f'Failed to generate chart parameters: {str(e)}',
                        'suggestions': []
                    }
        
        # If still no valid params after retries
        if not chart_params:
            print(f"[{request_id}] Failed to parse JSON after retries: {parse_error}")
            return {
                'error_type': 'MODEL_OUTPUT_ERROR',
                'message': f'Could not parse chart parameters from AI response. {parse_error}',
                'suggestions': []
            }
    
        table_name = chart_params.get('table_name')
        
        if table_name not in all_table_schemas:
            print(f"[{request_id}] Invalid table: {table_name}")
            return {
                'error_type': 'DATA_ERROR',
                'message': f"Table '{table_name}' not found in database. Available: {', '.join(all_table_schemas.keys())}",
                'suggestions': []
            }
        
        # Normalize and enforce forced_chart_type if present
        if forced_chart_type:
            chart_params['chart_type'] = forced_chart_type
            print(f"[{request_id}] Forcing chart_type to: {forced_chart_type}")
        else:
            # Ensure chart_type is normalized
            chart_params['chart_type'] = normalize_chart_type(chart_params.get('chart_type')) or 'bar_chart'
        
        print(f"[{request_id}] Normalized chart_type: {chart_params['chart_type']}")
        
        # Validate chart field requirements before fetching data
        is_valid, validation_error, suggested_fields = validate_chart_fields(
            chart_params['chart_type'], 
            chart_params, 
            all_table_schemas
        )
        
        if not is_valid:
            # Retry logic: For scatter_plot or 3d_scatter_plot with non-numeric axis, retry once with explicit numeric field guidance
            chart_type = chart_params.get('chart_type')
            should_retry = (
                chart_type in ['scatter_plot', '3d_scatter_plot'] and 
                suggested_fields and 
                len(suggested_fields) > 0 and
                ('must be numeric' in validation_error.lower() or ('requires' in validation_error.lower() and 'numeric' in validation_error.lower()))
            )
            
            if should_retry:
                print(f"[{request_id}] Chart validation failed for {chart_type}, retrying with explicit numeric field guidance...")
                table_name = chart_params.get('table_name')
                if table_name in all_table_schemas:
                    numeric_fields = all_table_schemas[table_name]['numerical_columns']
                    if numeric_fields:
                        # Build retry prompt with explicit numeric field list
                        field_guidance = f"Pick ONLY numeric fields for "
                        if chart_type == 'scatter_plot':
                            field_guidance += f"x_axis and y_axis from this allowed list: {', '.join(numeric_fields[:10])}."
                        else:  # 3d_scatter_plot
                            field_guidance += f"x_axis, y_axis, and z_axis from this allowed list: {', '.join(numeric_fields[:10])}."
                        
                        retry_prompt = f"""The previous chart parameters had invalid non-numeric axes. {field_guidance}

Database schema:
{schema_info}

Required JSON schema:
{{
  "table_name": "{table_name}",
  "chart_type": "{chart_type}",
  "x_axis": "string (MUST be numeric field from: {', '.join(numeric_fields[:10])})",
  "y_axis": "string (MUST be numeric field from: {', '.join(numeric_fields[:10])})",
  "z_axis": "string|null (MUST be numeric field from: {', '.join(numeric_fields[:10])} if chart_type is 3d_scatter_plot)",
  "title": "string",
  "summary": "string",
  "aggregate_y": "string|null",
  "color": "string|null",
  "size": "string|null",
  "chart_reasoning": "string|null",
  "chart_warnings": "array|null"
}}

User request: {user_message_raw}

Respond with ONLY valid JSON matching the schema above."""
                        
                        try:
                            response_retry = model_for_chart_params.generate_content(retry_prompt)
                            chart_params_retry_str = response_retry.text
                            chart_params_retry = extract_json_from_text(chart_params_retry_str)
                            
                            if chart_params_retry:
                                is_valid_retry, error_msg_retry, validated_params_retry = validate_chart_params(chart_params_retry, request_id)
                                if is_valid_retry:
                                    # Re-validate field requirements
                                    is_valid_fields, validation_error_retry, suggested_fields_retry = validate_chart_fields(
                                        chart_params_retry.get('chart_type', chart_type),
                                        chart_params_retry,
                                        all_table_schemas
                                    )
                                    if is_valid_fields:
                                        chart_params = validated_params_retry
                                        is_valid = True  # Mark as valid so we skip error return
                                        print(f"[{request_id}] Retry successful: fixed numeric axes")
                                        # Continue with valid chart_params (skip the error return below)
                                    else:
                                        # Retry still failed validation - fall through to error return
                                        error_msg = validation_error_retry
                                        if suggested_fields_retry:
                                            error_msg += f" Valid numeric fields: {', '.join(suggested_fields_retry[:5])}"
                                        print(f"[{request_id}] Retry validation still failed: {error_msg}")
                                        return {
                                            'error_type': 'DATA_ERROR',
                                            'message': error_msg,
                                            'suggestions': []
                                        }
                                else:
                                    print(f"[{request_id}] Retry JSON validation failed: {error_msg_retry}")
                            else:
                                print(f"[{request_id}] Retry JSON extraction failed")
                        except Exception as e:
                            print(f"[{request_id}] Retry Gemini call failed: {type(e).__name__}: {e}")
            
            # If retry didn't succeed or wasn't attempted, return error
            if not is_valid:
                error_msg = validation_error
                if suggested_fields:
                    error_msg += f" Valid numeric fields: {', '.join(suggested_fields[:5])}"
                print(f"[{request_id}] Chart validation failed: {error_msg}")
                return {
                    'error_type': 'DATA_ERROR',
                    'message': error_msg,
                    'suggestions': []
                }
        
        df = fetch_data_for_chart(chart_params)
        if df is not None and not df.empty:
            # Assess chart suitability (doesn't block, just provides recommendations)
            suitability = assess_chart_suitability(chart_params['chart_type'], df, chart_params)
            recommended_type = suitability['recommended_chart_type']
            
            # Use recommended type if different from requested
            if recommended_type != chart_params['chart_type']:
                print(f"[{request_id}] Chart suitability: requested={chart_params['chart_type']}, recommended={recommended_type}, reason={suitability['reason_not_best']}")
                chart_params['chart_type'] = recommended_type
            
            # Check response cache first
            cache_key = _get_response_cache_key(user_message_raw, user_language, forced_chart_type)
            _clean_response_cache()
            
            cached_response = _response_cache.get(cache_key)
            if cached_response:
                response_dict, expires_at = cached_response
                if expires_at > time.time():
                    print(f"[{request_id}] Cache hit")
                    # Convert chart_json to JSON-safe format before returning
                    if 'chart_json' in response_dict:
                        response_dict['chart_json'] = to_json_safe_plotly(response_dict['chart_json'])
                    return response_dict
                else:
                    del _response_cache[cache_key]
            
            # Generate chart
            try:
                chart_json_result = create_chart_json(df, chart_params)
                chart_data = ensure_json_dict(chart_json_result)
                
                if chart_data is None or 'error' in chart_data:
                    error_msg = chart_data.get('error', 'Failed to generate chart') if chart_data else 'Failed to generate chart'
                    print(f"[{request_id}] Chart generation error: {error_msg}")
                    return {
                        'error_type': 'DATA_ERROR',
                        'message': error_msg,
                        'suggestions': []
                    }
            except Exception as e:
                print(f"[{request_id}] Chart creation exception: {type(e).__name__}: {e}")
                return {
                    'error_type': 'DATA_ERROR',
                    'message': f'Failed to create chart: {str(e)}',
                    'suggestions': []
                }
            
            # Generate follow-up suggestions
            chart_context = f"You just created a {chart_params['chart_type']} showing {chart_params.get('y_axis', 'data')} by {chart_params.get('x_axis', 'category')} from the '{table_name}' table."
            
            prompt_for_follow_up_suggestions = f"""
            You are an AI assistant that provides follow-up suggestions for data analysis.
            The user has just seen a chart based on their previous request.
            
            Respond in {user_language}.

            Here is the database schema:
            {schema_info}
            
            Here is the context of the last generated chart:
            {chart_context}
            
            Based on this context and the schema, suggest 3-5 relevant next questions or types of charts for further insights.
            Focus on logical next steps like drilling down, comparing related metrics, or looking at trends.
            For example, if the last chart was sales by region, suggest "Show me sales over time" or "Break down sales by product category in a pie chart".
            
            Provide 3-5 concise suggestions as a comma-separated list.
            Example: "Show me sales by product, show me average price by category"
            """
            
            try:
                response_follow_up_suggestions = model_for_suggestions.generate_content(prompt_for_follow_up_suggestions)
                follow_up_suggestions_text = response_follow_up_suggestions.text.strip()
                follow_up_suggestions_list = [s.strip() for s in follow_up_suggestions_text.split(',')] if follow_up_suggestions_text else []
            except Exception as e:
                print(f"[{request_id}] Suggestions generation failed: {e}")
                follow_up_suggestions_list = []
            
            # Convert df to JSON once (optimization)
            raw_data_json = df.to_json(orient='records', date_format='iso')
        
            # Build response with all fields
            response_data = {
                'chart_json': chart_data,
                'raw_data': raw_data_json,
                'suggestions': follow_up_suggestions_list,
                'chart_type': chart_params['chart_type'],
                'title': chart_params.get('title', '')
            }
            
            # Add optional fields
            summary = chart_params.get('summary')
            if summary:
                response_data['summary'] = summary
            
            # Add chart suitability info (never blocks, just informs)
            if suitability['reason_not_best']:
                response_data['reason_not_best'] = suitability['reason_not_best']
            if suitability['chart_warnings']:
                response_data['chart_warnings'] = suitability['chart_warnings']
            if chart_params.get('chart_reasoning'):
                response_data['chart_reasoning'] = chart_params['chart_reasoning']
            
            # Convert chart_json to JSON-safe format (handles numpy arrays, pandas timestamps, etc.)
            if 'chart_json' in response_data:
                response_data['chart_json'] = to_json_safe_plotly(response_data['chart_json'])
            
            # Cache response
            _response_cache[cache_key] = (response_data, time.time() + RESPONSE_CACHE_TTL)
            print(f"[{request_id}] Success: chart_type={chart_params['chart_type']}, cache_size={len(_response_cache)}")
            
            return response_data
        else:
            print(f"[{request_id}] No data fetched or empty dataframe")
            return {
                'error_type': 'DATA_ERROR',
                'message': 'Could not fetch data for the requested chart. The table might be empty or the columns are incorrect.',
                'suggestions': []
            }
        
        # No table_name in params - provide general suggestions
        try:
            prompt_for_general_suggestions = f"""
            You are an AI assistant that provides helpful suggestions to a user based on the available database schema.
            The user's last message was: "{user_message}".
            
            Respond in {user_language}.
    
            Here is the database schema:
            {schema_info}
    
            Based on the user's message and the schema, suggest relevant questions or types of charts they could ask for.
            Focus on insights that can be derived from the available columns.
            
            For example, if a user mentions "sales", suggest "Show me total sales by region (Bar Chart)" or "What is the trend of sales over time (Line Chart)".
            
            Provide 3-5 concise suggestions as a comma-separated list.
            Example: "Show me sales by product, show me average price by category"
            """
            response_general_suggestions = model_for_suggestions.generate_content(prompt_for_general_suggestions)
            general_suggestions_text = response_general_suggestions.text.strip()
            general_suggestions_list = [s.strip() for s in general_suggestions_text.split(',')] if general_suggestions_text else []
        except Exception as e:
            print(f"[{request_id}] General suggestions failed: {e}")
            general_suggestions_list = []
            
            error_messages = {
                'en': "I didn't fully understand your request. Perhaps you could try one of these, or be more specific:",
                'es': "No entendí completamente tu solicitud. Quizás podrías intentar una de estas opciones, o ser más específico:",
                'fr': "Je n'ai pas entièrement compris votre demande. Vous pourriez peut-être essayer l'une de ces options, ou être plus précis :",
                'de': "Ich habe Ihre Anfrage nicht vollständig verstanden. Vielleicht könnten Sie eine dieser Optionen ausprobieren oder spezifischer sein:",
                'ja': "リクエストを完全に理解できませんでした。これらのいずれかを試すか、より具体的にしてください：",
                'ko': "요청을 완전히 이해하지 못했습니다. 다음 중 하나를 시도하거나 더 구체적으로 말씀해 주십시오:",
                'ar': "لم أفهم طلبك بالكامل. ربما يمكنك تجربة أحد هذه الخيارات، أو كن أكثر تحديدًا:"
            }
            return {
                'response': error_messages.get(user_language, "I didn't fully understand your request. Perhaps you could try one of these, or be more specific:"),
                'suggestions': general_suggestions_list
            }
    
    except genai_exceptions.ResourceExhausted as e:
        print(f"[{request_id}] Gemini quota exceeded: {e}")
        return {
            'error_type': 'RATE_LIMIT',
            'message': 'AI quota exceeded. Please try again shortly or upgrade billing.',
            'suggestions': []
        }
    except Exception as e:
        print(f"[{request_id}] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error_type': 'DATA_ERROR',
            'message': f'An unexpected error occurred: {str(e)}. Please try again.',
            'suggestions': []
        }

# SPA fallback: serve index.html for all non-API routes
# These routes must come AFTER all API routes (like /chat) so FastAPI matches them first
# Order matters: more specific routes (/ and /insights) before catch-all
@app.get('/')
async def serve_root():
    """Serve the Vite React app for root path."""
    index_path = FRONTEND_STATIC_DIR / 'index.html'
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not built")

@app.get('/{path:path}')
async def serve_spa(path: str):
    """Serve the Vite React app for all non-API routes (SPA fallback)."""
    # Don't serve index.html for static assets (they're handled by /assets/ mount)
    if path.startswith('assets/'):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve index.html from Vite build
    index_path = FRONTEND_STATIC_DIR / 'index.html'
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        # Fallback: return 404 if Vite build not available
        raise HTTPException(status_code=404, detail="Frontend not built")
    
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
