import os
import json
import re
import pyodbc
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.interpolate import griddata

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key_for_development_only')

# --- LLM API Configuration ---
# Your API key should be set as an environment variable in Azure App Service.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError(
        "ERROR: Gemini API key is not set. Please provide a valid key as an environment variable."
    )
genai.configure(api_key=GEMINI_API_KEY)
model_for_chart_params = genai.GenerativeModel('gemini-2.5-flash')
model_for_suggestions = genai.GenerativeModel('gemini-2.5-flash')

# --- Database Configuration ---
# Credentials and server details should be set as environment variables in Azure App Service.
SERVER = os.environ.get('DB_SERVER')
DATABASE = os.environ.get('DB_DATABASE')
USERNAME = os.environ.get('DB_USERNAME')
PASSWORD = os.environ.get('DB_PASSWORD')

# Define the DB_CONFIG dictionary
DB_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': SERVER,
    'database': DATABASE,
    'uid': USERNAME,
    'pwd': PASSWORD
}

def get_db_connection():
    """Establishes and returns a database connection using pyodbc."""
    try:
        conn_str = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['uid']};PWD={DB_CONFIG['pwd']};"
        )
        return pyodbc.connect(conn_str)
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Database connection error: {sqlstate} - {ex.args[1]}")
        return None

def get_all_table_schemas():
    """Fetches all table names and their column schemas from the configured database."""
    conn = None
    all_table_schemas = {}
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = ?", (DB_CONFIG['database'],))
            table_names = [row.TABLE_NAME for row in cursor.fetchall()]

            for table_name in table_names:
                all_columns = []
                numerical_columns = []
                date_columns = []
                categorical_columns = []
                
                cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? AND TABLE_CATALOG = ?", (table_name, DB_CONFIG['database']))
                for row in cursor.fetchall():
                    col_name = row.COLUMN_NAME
                    data_type = row.DATA_TYPE
                    all_columns.append(col_name)

                    if data_type in ['int', 'smallint', 'bigint', 'decimal', 'numeric', 'real', 'float', 'money']:
                        numerical_columns.append(col_name)
                    elif data_type in ['date', 'datetime', 'datetime2', 'smalldatetime', 'timestamp']:
                        date_columns.append(col_name)
                    else:
                        categorical_columns.append(col_name)
                
                all_table_schemas[table_name] = {
                    'all_columns': all_columns,
                    'numerical_columns': numerical_columns,
                    'date_columns': date_columns,
                    'categorical_columns': categorical_columns
                }
    except Exception as e:
        print(f"Error getting table schemas: {e}")
    finally:
        if conn:
            conn.close()
    return all_table_schemas

def fetch_data_for_chart(chart_params):
    """Fetches data from the database based on chart parameters."""
    table_name = chart_params.get('table_name')
    if not table_name:
        print("Error: Table name not provided in chart_params.")
        return None

    conn = None
    df = None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            column_metadata = {}
            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? AND TABLE_CATALOG = ?", (table_name, DB_CONFIG['database']))
            for row in cursor.fetchall():
                column_metadata[row.COLUMN_NAME] = row.DATA_TYPE

            x_col = chart_params.get('x_axis')
            y_col = chart_params.get('y_axis')
            color_col = chart_params.get('color')
            aggregate_y = chart_params.get('aggregate_y')

            columns_to_select_set = set()
            if x_col: columns_to_select_set.add(x_col)
            if y_col: columns_to_select_set.add(y_col)
            if color_col: columns_to_select_set.add(color_col)

            if not columns_to_select_set:
                print(f"No specific columns identified for table {table_name}. Selecting all available columns.")
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? AND TABLE_CATALOG = ?", (table_name, DB_CONFIG['database']))
                all_cols = [row.COLUMN_NAME for row in cursor.fetchall()]
                columns_to_select = ", ".join(all_cols)
            else:
                columns_to_select = ", ".join(list(columns_to_select_set))

            if not columns_to_select:
                print(f"Could not determine columns to select for table {table_name}.")
                return None

            query = f"SELECT {columns_to_select} FROM {table_name}"
            
            df = pd.read_sql(query, conn)

            for col, dtype in column_metadata.items():
                if dtype in ['date', 'datetime', 'datetime2', 'smalldatetime', 'timestamp'] and col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            if aggregate_y and y_col and x_col:
                if aggregate_y.upper() == 'COUNT':
                    df_agg = df.groupby(x_col).size().reset_index(name=f'Count of {y_col}')
                    chart_params['y_axis'] = f'Count of {y_col}'
                    df = df_agg
                elif aggregate_y.upper() in ['SUM', 'AVG', 'MIN', 'MAX'] and y_col in df.columns:
                    if y_col not in column_metadata or column_metadata[y_col] not in ['int', 'smallint', 'bigint', 'decimal', 'numeric', 'real', 'float', 'money']:
                        print(f"Warning: Cannot apply {aggregate_y} to non-numerical column '{y_col}'.")
                        return None

                    if aggregate_y.upper() == 'SUM':
                        df_agg = df.groupby(x_col)[y_col].sum().reset_index(name=f'Sum of {y_col}')
                        chart_params['y_axis'] = f'Sum of {y_col}'
                    elif aggregate_y.upper() == 'AVG':
                        df_agg = df.groupby(x_col)[y_col].mean().reset_index(name=f'Average of {y_col}')
                        chart_params['y_axis'] = f'Average of {y_col}'
                    elif aggregate_y.upper() == 'MIN':
                        df_agg = df.groupby(x_col)[y_col].min().reset_index(name=f'Min of {y_col}')
                        chart_params['y_axis'] = f'Min of {y_col}'
                    elif aggregate_y.upper() == 'MAX':
                        df_agg = df.groupby(x_col)[y_col].max().reset_index(name=f'Max of {y_col}')
                        chart_params['y_axis'] = f'Max of {y_col}'
                    df = df_agg
            
            print(f"Data fetched successfully for table {table_name}. Shape: {df.shape}")
            return df
    except Exception as e:
        print(f"Error fetching data for chart from table {table_name}: {e}")
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

    if chart_type == 'line_chart':
        fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
    elif chart_type == 'bar_chart':
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
    elif chart_type == 'scatter_plot':
        fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
    elif chart_type == 'pie_chart':
        names_col = chart_params.get('pie_names')
        values_col = chart_params.get('pie_values')
        fig = px.pie(df, names=names_col, values=values_col, title=title)
    elif chart_type == 'donut_chart':
        names_col = chart_params.get('pie_names')
        values_col = chart_params.get('pie_values')
        fig = px.pie(df, names=names_col, values=values_col, hole=0.4, title=title)
    elif chart_type == 'histogram':
        fig = px.histogram(df, x=x_col, color=color_col, title=title)
    elif chart_type == 'box_plot':
        fig = px.box(df, x=x_col, y=y_col, color=color_col, title=title)
    elif chart_type == 'heatmap':
        x_col_heatmap = chart_params.get('x_axis')
        y_col_heatmap = chart_params.get('y_axis')
        z_col_heatmap = chart_params.get('z_axis')
        
        if x_col_heatmap and y_col_heatmap and z_col_heatmap and x_col_heatmap in df.columns and y_col_heatmap in df.columns and z_col_heatmap in df.columns:
            # Handle potential non-numeric data in z_col
            if pd.api.types.is_numeric_dtype(df[z_col_heatmap]):
                pivot_table = df.pivot_table(index=y_col_heatmap, columns=x_col_heatmap, values=z_col_heatmap)
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_table.values,
                    x=pivot_table.columns.tolist(),
                    y=pivot_table.index.tolist()))
            else:
                print(f"Heatmap error: z_axis column '{z_col_heatmap}' is not numeric.")
                return {'error': f"Heatmap error: z_axis column '{z_col_heatmap}' is not numeric."}
        else:
            print("Heatmap error: Missing x, y, or z axis parameters or columns not found.")
            return {'error': "Heatmap error: Missing x, y, or z axis parameters or columns not found."}
    elif chart_type == 'area_chart':
        fig = px.area(df, x=x_col, y=y_col, color=color_col, title=title)
    else:
        return {'error': f"Unsupported chart type: {chart_type}"}

    chart_json = fig.to_json()
    print(f"Chart JSON created successfully for {chart_type}.")
    return {'chart_json': json.loads(chart_json)}

def generate_chart_params(prompt, table_schemas):
    """
    Generates JSON parameters for a chart based on a user prompt and database schema.
    Uses the Gemini API to understand the user's request.
    """
    print("Generating chart parameters...")
    try:
        # Construct the prompt for the LLM
        prompt_with_schema = f"""
I need to generate a JSON object to create a chart based on the user's request.
The JSON object must follow this structure:
{{
  "chart_type": "string", // e.g., "line_chart", "bar_chart", "scatter_plot", "pie_chart", "donut_chart", "histogram", "box_plot", "heatmap", "area_chart"
  "table_name": "string",
  "x_axis": "string", // column name for x-axis
  "y_axis": "string", // column name for y-axis
  "color": "string", // optional, column name for color encoding
  "aggregate_y": "string", // optional, "SUM", "AVG", "COUNT", "MIN", "MAX"
  "title": "string" // optional, chart title
}}

For pie_chart and donut_chart, use this structure:
{{
  "chart_type": "string", // "pie_chart" or "donut_chart"
  "table_name": "string",
  "pie_names": "string", // column name for slices
  "pie_values": "string", // column name for slice sizes
  "title": "string" // optional, chart title
}}

For heatmap, use this structure:
{{
  "chart_type": "string", // "heatmap"
  "table_name": "string",
  "x_axis": "string", // column name for x-axis
  "y_axis": "string", // column name for y-axis
  "z_axis": "string", // column name for color values
  "title": "string" // optional, chart title
}}

I will provide the user's request and the database schema. You must parse the request and schema to create the JSON object.

Important rules:
1.  Match the table and column names exactly as they appear in the schema.
2.  If the user asks for a chart type that doesn't fit the schema (e.g., a scatter plot on two categorical columns), choose a more suitable chart type (e.g., a bar chart or pie chart).
3.  If a column is clearly a date, use a date-based chart like a line chart.
4.  If the user asks for a visualization that aggregates data (e.g., "total sales by month"), use the "aggregate_y" field.
5.  If a user asks for a pie or donut chart, use "pie_names" and "pie_values" instead of "x_axis" and "y_axis".
6.  If a chart type is not specified, infer the best chart type from the prompt and column types (e.g., use a scatter plot for two numerical columns).
7.  The response must ONLY contain the JSON object. Do not include any extra text, explanations, or code.

Database Schema (in JSON format):
{table_schemas}

User's Request:
{prompt}
"""
        response = model_for_chart_params.generate_content(prompt_with_schema)
        
        # Extract and clean the JSON string from the response
        json_string = response.text.strip('`').strip()
        if json_string.startswith('json'):
            json_string = json_string[4:].strip()
        
        return json.loads(json_string)

    except Exception as e:
        print(f"Error generating chart parameters: {e}")
        return None
        
def generate_suggestions(prompt, table_schemas):
    """
    Generates a list of suggestions for follow-up queries.
    """
    print("Generating suggestions...")
    try:
        prompt_for_suggestions = f"""
You are a helpful assistant for data visualization. Based on the user's last request and the provided database schema, generate a JSON object with a list of 5 concise and relevant follow-up suggestions for data exploration. These suggestions should be creative and insightful.

Example JSON output:
{{
    "suggestions": [
        "Show a bar chart of [example_col1] vs [example_col2]",
        "What is the average [example_col3]?",
        "Create a pie chart showing the distribution of [example_col4]"
    ]
}}

Database Schema (in JSON format):
{table_schemas}

User's last request:
{prompt}

Your response must ONLY be the JSON object.
"""
        response = model_for_suggestions.generate_content(prompt_for_suggestions)

        # Clean the JSON string from the response
        json_string = response.text.strip('`').strip()
        if json_string.startswith('json'):
            json_string = json_string[4:].strip()
            
        return json.loads(json_string)
    
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return {'suggestions': []}


@app.route('/')
def home():
    """Renders the main HTML page for the application."""
    return render_template('index.html')

@app.route('/get_db_info', methods=['GET'])
def get_db_info():
    """
    Retrieves database schema information and generates initial suggestions
    for the user. Returns a JSON response.
    """
    all_table_schemas = get_all_table_schemas()

    if not all_table_schemas:
        return jsonify({
            'response': "Could not retrieve database schema. Please check your database connection details.",
            'suggestions': []
        })

    # Generate initial suggestions based on the retrieved schema
    # Use a generic prompt to get an initial set of suggestions
    initial_suggestions = generate_suggestions("What charts can I create?", all_table_schemas)
    
    return jsonify({
        'table_schemas': all_table_schemas,
        'suggestions': initial_suggestions['suggestions']
    })


@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    """
    Receives user prompts, generates a chart, and returns its JSON.
    Also generates follow-up suggestions.
    """
    data = request.json
    user_prompt = data.get('prompt')
    table_schemas = data.get('table_schemas')

    if not user_prompt or not table_schemas:
        return jsonify({
            'response': {
                'en': "Invalid request. Please provide a prompt and table schemas.",
                'es': "Petición inválida. Por favor, proporcione un mensaje y los esquemas de las tablas.",
                'fr': "Requête invalide. Veuillez fournir une invite et les schémas de table.",
                'de': "Ungültige Anfrage. Bitte geben Sie eine Aufforderung und die Tabellenschemata an.",
                'ja': "無効なリクエストです。プロンプトとテーブルスキーマを提供してください。",
                'ko': "잘못된 요청입니다. 프롬프트와 테이블 스키마를 제공해 주십시오.",
                'ar': "طلب غير صالح. يرجى تقديم طلب ومخططات الجدول."
            }
        })
    
    # Generate chart parameters from the user's prompt and schema
    chart_params = generate_chart_params(user_prompt, table_schemas)

    if chart_params and chart_params.get('error'):
        print(f"Error from LLM: {chart_params['error']}")
        return jsonify({
            'response': {
                'en': f"I couldn't generate a chart based on your request. Error: {chart_params['error']}",
                'es': f"No pude generar un gráfico basado en su solicitud. Error: {chart_params['error']}",
                'fr': f"Je n'ai pas pu générer de graphique à partir de votre demande. Erreur : {chart_params['error']}",
                'de': f"Ich konnte basierend auf Ihrer Anfrage kein Diagramm erstellen. Fehler: {chart_params['error']}",
                'ja': f"リクエストに基づいてチャートを生成できませんでした。エラー：{chart_params['error']}",
                'ko': f"요청에 따라 차트를 생성할 수 없습니다. 오류: {chart_params['error']}",
                'ar': f"لم أتمكن من إنشاء مخطط بناءً على طلبك. خطأ: {chart_params['error']}"
            }
        })

    # Fetch data from the database
    df = fetch_data_for_chart(chart_params)
    if df is None or df.empty:
        return jsonify({
            'response': {
                'en': "Could not fetch data for this chart. The table or columns might be missing or the query was invalid.",
                'es': "No se pudieron obtener datos para este gráfico. Es posible que falte la tabla o las columnas, o que la consulta no sea válida.",
                'fr': "Impossible de récupérer les données pour ce graphique. La table ou les colonnes sont peut-être manquantes ou la requête était invalide.",
                'de': "Daten für dieses Diagramm konnten nicht abgerufen werden. Die Tabelle oder Spalten fehlen möglicherweise oder die Abfrage war ungültig.",
                'ja': "このチャートのデータを取得できませんでした。テーブルまたは列が見つからないか、クエリが無効だった可能性があります。",
                'ko': "이 차트에 대한 데이터를 가져올 수 없습니다. 테이블이나 열이 없거나 쿼리가 유효하지 않았을 수 있습니다.",
                'ar': "تعذر جلب البيانات لهذا المخطط. قد تكون الجداول أو الأعمدة مفقودة أو أن الاستعلام غير صالح."
            }
        })

    # Generate the chart JSON
    chart_json_data = create_chart_json(df, chart_params)
    if 'error' in chart_json_data:
        print(f"Error creating chart: {chart_json_data['error']}")
        return jsonify({'response': {
            'en': f"Error creating chart: {chart_json_data['error']}",
            'es': f"Error al crear el gráfico: {chart_json_data['error']}",
            'fr': f"Erreur lors de la création du graphique : {chart_json_data['error']}",
            'de': f"Fehler beim Erstellen des Diagramms: {chart_json_data['error']}",
            'ja': f"チャートの作成中にエラーが発生しました：{chart_json_data['error']}",
            'ko': f"차트 작성 오류: {chart_json_data['error']}",
            'ar': f"خطأ في إنشاء المخطط: {chart_json_data['error']}"
        }})

    # Generate follow-up suggestions
    suggestions_data = generate_suggestions(user_prompt, table_schemas)

    return jsonify({
        'chart_json': chart_json_data['chart_json'],
        'suggestions': suggestions_data['suggestions']
    })

@app.route('/favicon.ico')
def favicon():
    """Returns a dummy favicon."""
    # Assuming a favicon.ico is in the static folder, otherwise, you can create a dummy one
    return send_file('static/favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)
