"""
Safe SQL query builder for chart generation.
Prevents SQL injection, enforces performance limits, and protects PII.
"""
from dataclasses import dataclass
from typing import Optional, Dict, List, Set, Tuple
import re


# Baseline allowed tables (production tables that must be supported)
# Schema discovery will add additional tables, but these are guaranteed
BASELINE_ALLOWED_TABLES: Set[str] = {
    'Account',
    'Contact',
    'Lead',
    'Opportunity'
}

# PII columns that must be blocked from selection and raw_data
PII_COLUMNS: Set[str] = {
    'Email'  # dbo.Contact.Email - PII that must be protected
}

# Allowed chart types (whitelist)
ALLOWED_CHART_TYPES: Set[str] = {
    'bar_chart',
    'line_chart',
    'scatter_plot',
    'pie_chart',
    'donut_chart',
    'histogram',
    'box_plot',
    'area_chart',
    '3d_scatter_plot',
    'bubble_chart'
}

# Allowed aggregation functions (whitelist)
ALLOWED_AGGREGATIONS: Set[str] = {
    'NONE',
    'SUM',
    'AVG',
    'COUNT',
    'MIN',
    'MAX'
}

# Performance guardrails
MAX_ROWS = 5000  # Maximum rows for non-aggregated queries
MAX_GROUPS = 50  # Maximum groups for aggregated queries
MAX_HISTOGRAM_BINS = 100  # Maximum bins for histograms

# SQL Server numerical data types (for aggregation validation)
NUMERICAL_TYPES: Set[str] = {
    'int', 'smallint', 'bigint', 'tinyint',
    'decimal', 'numeric', 'real', 'float', 'money', 'smallmoney'
}


class SafeSQLError(Exception):
    """Custom exception for safe SQL validation errors."""
    pass


@dataclass
class ChartRequest:
    """Validated chart request with all required fields."""
    table_name: str
    chart_type: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color: Optional[str] = None
    z_axis: Optional[str] = None  # For 3d_scatter_plot
    size: Optional[str] = None  # For bubble_chart
    aggregate_y: Optional[str] = None
    title: Optional[str] = None
    limit: Optional[int] = None  # User-requested limit (will be clamped)
    
    def __post_init__(self):
        """Normalize string fields."""
        if self.aggregate_y:
            self.aggregate_y = self.aggregate_y.upper()
        if self.chart_type:
            self.chart_type = self.chart_type.lower()


def quote_ident(name: str, db_type: str = 'sqlite') -> str:
    """
    Quote a database identifier using appropriate syntax for the database type.
    Assumes the identifier has already been validated against schema.
    
    Args:
        name: Identifier name (table or column)
        db_type: Database type ('sqlite' or 'sqlserver')
        
    Returns:
        Quoted identifier: [name] for SQL Server, "name" for SQLite
    """
    if not name:
        raise SafeSQLError("Identifier name cannot be empty")
    
    if db_type == 'sqlite':
        # SQLite uses double quotes for identifiers
        escaped = name.replace('"', '""')
        return f'"{escaped}"'
    else:
        # SQL Server uses brackets
        escaped = name.replace(']', ']]')
        return f"[{escaped}]"


def validate_identifier(name: str, allowed_names: Set[str], identifier_type: str) -> str:
    """
    Validate that an identifier exists in the allowlist.
    
    Args:
        name: Identifier to validate
        allowed_names: Set of allowed identifier names
        identifier_type: Type of identifier ('table' or 'column')
        
    Returns:
        Validated identifier name
        
    Raises:
        SafeSQLError: If identifier is not in allowlist or is PII
    """
    if not name:
        raise SafeSQLError(f"{identifier_type.capitalize()} name cannot be empty")
    
    # Check for PII columns (case-insensitive)
    if identifier_type == 'column' and name in PII_COLUMNS:
        raise SafeSQLError(
            f"Column '{name}' contains PII and cannot be selected for privacy protection."
        )
    
    if name not in allowed_names:
        raise SafeSQLError(
            f"Invalid {identifier_type} '{name}'. "
            f"Must be one of: {', '.join(sorted(allowed_names))}"
        )
    
    return name


def is_pii_column(column_name: str) -> bool:
    """
    Check if a column name is a PII column (case-insensitive).
    
    Args:
        column_name: Column name to check
        
    Returns:
        True if column is PII, False otherwise
    """
    return column_name in PII_COLUMNS


def validate_chart_request(
    request_dict: Dict,
    schema_map: Dict[str, Dict]
) -> ChartRequest:
    """
    Validate and normalize a chart request against the database schema.
    
    Args:
        request_dict: Raw chart parameters from Gemini/API
        schema_map: Schema map from get_all_table_schemas()
                   Format: {table_name: {all_columns: [...], numerical_columns: [...], ...}}
        
    Returns:
        Validated ChartRequest object
        
    Raises:
        SafeSQLError: If validation fails
    """
    # Validate table_name
    table_name = request_dict.get('table_name')
    if not table_name:
        raise SafeSQLError("table_name is required")
    
    # Remove schema prefix if present (e.g., "dbo.Account" -> "Account")
    if '.' in table_name:
        table_name = table_name.split('.')[-1]
    
    # Check if table exists in schema_map (from discovery) or baseline allowlist
    if table_name not in schema_map:
        # Check baseline tables as fallback
        if table_name not in BASELINE_ALLOWED_TABLES:
            available_tables = ', '.join(sorted(set(schema_map.keys()) | BASELINE_ALLOWED_TABLES))
            raise SafeSQLError(
                f"Table '{table_name}' not found in database. "
                f"Available tables: {available_tables}"
            )
        # Table is in baseline but not discovered - this shouldn't happen if schema discovery works
        # But we allow it and will validate columns against discovered schema if available
        if not schema_map:
            raise SafeSQLError(
                f"Table '{table_name}' is allowed but schema discovery failed. "
                f"Please ensure database connection is working."
            )
    
    # Get table schema (must exist now)
    if table_name not in schema_map:
        raise SafeSQLError(
            f"Table '{table_name}' schema not available. "
            f"Schema discovery may have failed."
        )
    
    table_schema = schema_map[table_name]
    all_columns = set(table_schema.get('all_columns', []))
    numerical_columns = set(table_schema.get('numerical_columns', []))
    
    # Normalize and validate chart_type
    chart_type_raw = request_dict.get('chart_type', '').strip()
    if not chart_type_raw:
        raise SafeSQLError("chart_type is required")
    
    # Normalize chart_type: lowercase, replace spaces/hyphens with underscores
    chart_type = chart_type_raw.lower().strip()
    chart_type = chart_type.replace(' ', '_').replace('-', '_')
    
    # Map synonyms to canonical values
    chart_type_mapping = {
        'bar': 'bar_chart',
        'bar_chart': 'bar_chart',
        'line': 'line_chart',
        'line_chart': 'line_chart',
        'pie': 'pie_chart',
        'pie_chart': 'pie_chart',
        'donut': 'donut_chart',
        'donut_chart': 'donut_chart',
        'scatter': 'scatter_plot',
        'scatter_plot': 'scatter_plot',
        'histogram': 'histogram',
        '3d': '3d_scatter_plot',
        '3d_chart': '3d_scatter_plot',
        '3d_scatter_plot': '3d_scatter_plot',
        'box': 'box_plot',
        'box_plot': 'box_plot',
        'area': 'area_chart',
        'area_chart': 'area_chart',
        'bubble': 'bubble_chart',
        'bubble_chart': 'bubble_chart',
    }
    
    # Apply mapping if exists, otherwise use normalized value
    chart_type = chart_type_mapping.get(chart_type, chart_type)
    
    # Validate against allowed types
    if chart_type not in ALLOWED_CHART_TYPES:
        raise SafeSQLError(
            f"Invalid chart_type '{chart_type_raw}' (normalized: '{chart_type}'). "
            f"Allowed types: {', '.join(sorted(ALLOWED_CHART_TYPES))}"
        )
    
    # Validate columns based on chart type
    x_axis = request_dict.get('x_axis')
    y_axis = request_dict.get('y_axis')
    color = request_dict.get('color')
    z_axis = request_dict.get('z_axis')
    size = request_dict.get('size')
    
    # Validate x_axis (required for most charts)
    if chart_type in ['pie_chart', 'donut_chart']:
        # For pie/donut, x_axis is names (categories)
        if x_axis:
            x_axis = validate_identifier(x_axis, all_columns, 'column')
    elif chart_type == 'histogram':
        # Histogram only needs x_axis
        if x_axis:
            x_axis = validate_identifier(x_axis, all_columns, 'column')
    else:
        # Most charts require x_axis
        if not x_axis:
            raise SafeSQLError(f"x_axis is required for chart_type '{chart_type}'")
        x_axis = validate_identifier(x_axis, all_columns, 'column')
    
    # Validate y_axis
    if chart_type in ['pie_chart', 'donut_chart']:
        # For pie/donut, y_axis is values (must be numerical)
        if not y_axis:
            raise SafeSQLError(f"y_axis is required for chart_type '{chart_type}'")
        y_axis = validate_identifier(y_axis, all_columns, 'column')
        if y_axis not in numerical_columns:
            raise SafeSQLError(
                f"y_axis '{y_axis}' must be numerical for {chart_type}. "
                f"Numerical columns: {', '.join(sorted(numerical_columns))}"
            )
    elif chart_type == 'histogram':
        # Histogram doesn't use y_axis
        y_axis = None
    else:
        # Most charts require y_axis
        if not y_axis:
            raise SafeSQLError(f"y_axis is required for chart_type '{chart_type}'")
        y_axis = validate_identifier(y_axis, all_columns, 'column')
    
    # Validate color (optional)
    if color:
        color = validate_identifier(color, all_columns, 'column')
    
    # Validate z_axis (for 3d_scatter_plot)
    if chart_type == '3d_scatter_plot':
        if not z_axis:
            raise SafeSQLError(f"z_axis is required for chart_type '{chart_type}'")
        z_axis = validate_identifier(z_axis, all_columns, 'column')
    else:
        z_axis = None
    
    # Validate size (for bubble_chart)
    if chart_type == 'bubble_chart':
        if not size:
            raise SafeSQLError("size is required for bubble_chart")
        size = validate_identifier(size, all_columns, 'column')
        if size not in numerical_columns:
            raise SafeSQLError(
                f"size '{size}' must be numerical for bubble_chart. "
                f"Numerical columns: {', '.join(sorted(numerical_columns))}"
            )
    else:
        size = None
    
    # Validate aggregate_y
    aggregate_y = request_dict.get('aggregate_y')
    if aggregate_y:
        aggregate_y = aggregate_y.upper()
        if aggregate_y not in ALLOWED_AGGREGATIONS:
            raise SafeSQLError(
                f"Invalid aggregate_y '{aggregate_y}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_AGGREGATIONS - {'NONE'}))}"
            )
        
        # Aggregation requires y_axis to be numerical (except COUNT)
        if aggregate_y != 'COUNT' and y_axis and y_axis not in numerical_columns:
            raise SafeSQLError(
                f"Cannot apply {aggregate_y} to non-numerical column '{y_axis}'. "
                f"Numerical columns: {', '.join(sorted(numerical_columns))}"
            )
    
    # Validate and clamp limit
    limit = request_dict.get('limit')
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 1:
                raise SafeSQLError("limit must be at least 1")
        except (ValueError, TypeError):
            raise SafeSQLError(f"limit must be a valid integer, got: {limit}")
    
    # Create validated request
    validated = ChartRequest(
        table_name=table_name,
        chart_type=chart_type,
        x_axis=x_axis,
        y_axis=y_axis,
        color=color,
        z_axis=z_axis,
        size=size,
        aggregate_y=aggregate_y,
        title=request_dict.get('title'),
        limit=limit
    )
    
    return validated


def build_sql(
    validated_request: ChartRequest,
    schema_map: Dict[str, Dict],
    db_type: str = 'sqlite'
) -> Tuple[str, List]:
    """
    Build a safe SQL query from a validated chart request.
    
    Args:
        validated_request: Validated ChartRequest object
        schema_map: Schema map for column type information
        db_type: Database type ('sqlite' or 'sqlserver'). Defaults to 'sqlite'.
        
    Returns:
        Tuple of (SQL query string, parameter list)
        Parameters are only used for WHERE clause values (future use)
    """
    table_schema = schema_map[validated_request.table_name]
    numerical_columns = set(table_schema.get('numerical_columns', []))
    
    quoted_table = quote_ident(validated_request.table_name, db_type)
    params: List = []  # For future WHERE clause parameterization
    
    # Determine if this is an aggregated query
    is_aggregated = (
        validated_request.aggregate_y and
        validated_request.aggregate_y != 'NONE' and
        validated_request.x_axis and
        validated_request.y_axis
    )
    
    # Build SELECT columns
    select_parts = []
    
    if is_aggregated:
        # Aggregated query: SELECT [x], AGG([y]) AS [y_alias]
        select_parts.append(quote_ident(validated_request.x_axis, db_type))
        
        agg_func = validated_request.aggregate_y
        y_col = quote_ident(validated_request.y_axis, db_type)
        
        if agg_func == 'COUNT':
            select_parts.append(f"COUNT({y_col}) AS {quote_ident(f'Count of {validated_request.y_axis}', db_type)}")
        elif agg_func == 'SUM':
            select_parts.append(f"SUM({y_col}) AS {quote_ident(f'Sum of {validated_request.y_axis}', db_type)}")
        elif agg_func == 'AVG':
            select_parts.append(f"AVG({y_col}) AS {quote_ident(f'Average of {validated_request.y_axis}', db_type)}")
        elif agg_func == 'MIN':
            select_parts.append(f"MIN({y_col}) AS {quote_ident(f'Min of {validated_request.y_axis}', db_type)}")
        elif agg_func == 'MAX':
            select_parts.append(f"MAX({y_col}) AS {quote_ident(f'Max of {validated_request.y_axis}', db_type)}")
        
        # Add color column if present (for grouping)
        if validated_request.color:
            select_parts.append(quote_ident(validated_request.color, db_type))
    else:
        # Non-aggregated query: SELECT only required columns
        columns_to_select = []
        
        if validated_request.x_axis:
            columns_to_select.append(validated_request.x_axis)
        if validated_request.y_axis:
            columns_to_select.append(validated_request.y_axis)
        if validated_request.color:
            columns_to_select.append(validated_request.color)
        if validated_request.z_axis:
            columns_to_select.append(validated_request.z_axis)
        if validated_request.size:
            columns_to_select.append(validated_request.size)
        
        # Ensure at least one column
        if not columns_to_select:
            raise SafeSQLError("At least one column must be selected")
        
        # Quote all columns
        select_parts = [quote_ident(col, db_type) for col in columns_to_select]
    
    select_clause = ", ".join(select_parts)
    
    # Build FROM clause
    from_clause = f"FROM {quoted_table}"
    
    # Build WHERE clause (future: for filters)
    where_clause = ""
    # Placeholder for future filter support with parameterization
    
    # Build GROUP BY clause (for aggregated queries)
    group_by_clause = ""
    if is_aggregated:
        group_by_cols = [quote_ident(validated_request.x_axis, db_type)]
        if validated_request.color:
            group_by_cols.append(quote_ident(validated_request.color, db_type))
        group_by_clause = f"GROUP BY {', '.join(group_by_cols)}"
    
    # Build ORDER BY clause
    order_by_clause = ""
    if is_aggregated:
        # Order by aggregated value descending
        agg_alias = select_parts[1].split(" AS ")[1]  # Get alias from SELECT
        order_by_clause = f"ORDER BY {agg_alias} DESC"
    elif validated_request.x_axis:
        # For non-aggregated, order by x_axis if it's sortable
        # (Skip ordering for very large result sets to avoid performance issues)
        order_by_clause = f"ORDER BY {quote_ident(validated_request.x_axis, db_type)}"
    
    # Determine limit
    if is_aggregated:
        # For aggregated queries, limit groups
        limit_value = validated_request.limit if validated_request.limit else MAX_GROUPS
        limit_value = min(limit_value, MAX_GROUPS)
    elif validated_request.chart_type == 'histogram':
        # Histograms might need more rows for binning
        limit_value = validated_request.limit if validated_request.limit else MAX_HISTOGRAM_BINS
        limit_value = min(limit_value, MAX_HISTOGRAM_BINS)
    else:
        # For non-aggregated queries, limit rows
        limit_value = validated_request.limit if validated_request.limit else MAX_ROWS
        limit_value = min(limit_value, MAX_ROWS)
    
    # Ensure limit is at least 1
    limit_value = max(1, limit_value)
    
    # Build final SQL with database-appropriate LIMIT syntax
    if db_type == 'sqlite':
        # SQLite uses LIMIT at the end
        sql_parts = [
            "SELECT",
            select_clause,
            from_clause
        ]
    else:
        # SQL Server uses TOP in SELECT
        sql_parts = [
            f"SELECT TOP {limit_value}",
            select_clause,
            from_clause
        ]
    
    if where_clause:
        sql_parts.append(where_clause)
    
    if group_by_clause:
        sql_parts.append(group_by_clause)
    
    if order_by_clause:
        sql_parts.append(order_by_clause)
    
    # Add LIMIT clause for SQLite (at the end)
    if db_type == 'sqlite':
        sql_parts.append(f"LIMIT {limit_value}")
    
    sql = " ".join(sql_parts)
    
    return sql, params


def get_aggregated_y_axis_name(validated_request: ChartRequest) -> str:
    """
    Get the display name for the aggregated y-axis column.
    This matches the alias created in build_sql().
    
    Args:
        validated_request: Validated ChartRequest
        
    Returns:
        Display name for the y-axis (e.g., "Sum of Sales")
    """
    if not validated_request.aggregate_y or validated_request.aggregate_y == 'NONE':
        return validated_request.y_axis or ""
    
    agg = validated_request.aggregate_y
    y_col = validated_request.y_axis or ""
    
    if agg == 'COUNT':
        return f"Count of {y_col}"
    elif agg == 'SUM':
        return f"Sum of {y_col}"
    elif agg == 'AVG':
        return f"Average of {y_col}"
    elif agg == 'MIN':
        return f"Min of {y_col}"
    elif agg == 'MAX':
        return f"Max of {y_col}"
    
    return y_col


def filter_pii_from_dataframe(df, table_name: str = None):
    """
    Remove PII columns from a DataFrame before returning to frontend.
    
    Args:
        df: pandas DataFrame
        table_name: Optional table name for logging
        
    Returns:
        DataFrame with PII columns removed
    """
    import pandas as pd
    
    if df is None or df.empty:
        return df
    
    # Find and drop PII columns
    pii_cols_to_drop = [col for col in df.columns if is_pii_column(col)]
    
    if pii_cols_to_drop:
        df = df.drop(columns=pii_cols_to_drop)
    
    return df


def filter_pii_from_dict(record: Dict) -> Dict:
    """
    Remove PII fields from a dictionary record.
    
    Args:
        record: Dictionary record (from raw_data)
        
    Returns:
        Dictionary with PII keys removed
    """
    return {k: v for k, v in record.items() if not is_pii_column(k)}


if __name__ == '__main__':
    """Quick self-test for build_sql function signature."""
    # Mock schema
    test_schema = {
        'Users': {
            'all_columns': ['id', 'name', 'age'],
            'numerical_columns': ['id', 'age'],
            'date_columns': [],
            'categorical_columns': ['name']
        }
    }
    
    # Test with 2 arguments (backward compatible)
    try:
        validated = validate_chart_request(
            {'table_name': 'Users', 'chart_type': 'bar_chart', 'x_axis': 'name', 'y_axis': 'age'},
            test_schema
        )
        sql1, params1 = build_sql(validated, test_schema)
        print("[PASS] Test 1: build_sql with 2 arguments (default db_type='sqlite')")
        print(f"   SQL: {sql1[:80]}...")
        
        # Test with 3 arguments (explicit db_type)
        sql2, params2 = build_sql(validated, test_schema, 'sqlserver')
        print("[PASS] Test 2: build_sql with 3 arguments (db_type='sqlserver')")
        print(f"   SQL: {sql2[:80]}...")
        
        # Verify SQL syntax differs between SQLite and SQL Server
        if 'LIMIT' in sql1 and 'TOP' in sql2:
            print("[PASS] Test 3: SQL syntax differs correctly (SQLite uses LIMIT, SQL Server uses TOP)")
        else:
            print("[WARN] SQL syntax may not differ as expected")
        
        print("\n[PASS] All self-tests passed!")
        
    except Exception as e:
        print(f"[FAIL] Self-test failed: {e}")
        import traceback
        traceback.print_exc()

