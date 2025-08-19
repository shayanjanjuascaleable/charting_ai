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
# Flask secret key is hard-coded as per your request
app.secret_key = 'YourStrongSecretKey123!'

# --- LLM API Configuration ---
# Gemini API Key is hard-coded as per your request
GEMINI_API_KEY = 'AIzaSyAjlVk5Ai8nyzK5dwBRFqfKmN9_FYP18UA'

if not GEMINI_API_KEY:
    raise ValueError(
        "ERROR: Gemini API key is not set. Please provide a valid key as an environment variable."
    )
genai.configure(api_key=GEMINI_API_KEY)
model_for_chart_params = genai.GenerativeModel('gemini-2.5-flash')
model_for_suggestions = genai.GenerativeModel('gemini-2.5-flash')

# --- Database Configuration ---
# All database credentials are now hard-coded as per your request
SERVER = 'aiserverscaleable.database.windows.net'
DATABASE = 'Charting_Dataset_DB'
USERNAME = 'webuser'
PASSWORD = 'Secure#P@ssw0rd'

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
    elif chart_type == 'heatmap':
        z_col = chart_params.get('z_axis')
        if not z_col or z_col not in df.columns:
            return {'error': f"Heatmap requires X, Y, and Z (value) columns. Z-axis column '{z_col}' not found."}
       
        if df[y_col].dtype == 'datetime64[ns]':
            df[y_col] = df[y_col].dt.strftime('%Y-%m-%d')
        if df[x_col].dtype == 'datetime64[ns]':
            df[x_col] = df[x_col].dt.strftime('%Y-%m-%d')
           
        pivot_df = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc='mean')
        pivot_df = pivot_df.fillna(0)
 
        fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                colorscale='Viridis')) # Viridis is a good default for heatmaps
        fig.update_layout(title=title, xaxis_title=x_col, yaxis_title=y_col)
 
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
 
    return fig.to_json()
 
@app.route('/')
def index():
    """Renders the main landing page."""
    return render_template('index.html')
 
@app.route('/insights')
def insights():
    """Renders the insights dashboard page."""
    return render_template('insights_page.html')
 
INITIAL_CHART_SUGGESTIONS = [
    "bar chart", "pie chart", "donut chart", "3d chart", "line chart", "scatter plot", "histogram",
    "box plot", "area chart", "heatmap", "bubble chart"
]
 
@app.route('/chat', methods=['POST'])
def chat():
    """Handles chatbot interactions."""
    user_message = request.json.get('message').lower()
    user_language = request.json.get('language', 'en') # Get language from request
    forced_chart_type = request.json.get('forced_chart_type') # New: Get forced chart type from frontend
   
    all_table_schemas = get_all_table_schemas()
    if not all_table_schemas:
        return jsonify({'response': {
            'en': 'Error: Could not retrieve database schema. Please check database connection.',
            'es': 'Error: No se pudo recuperar el esquema de la base de datos. Por favor, verifica la conexión a la base de datos.',
            'fr': 'Erreur : Impossible de récupérer le schéma de la base de données. Veuillez vérifier la conexión a la base de données.',
            'de': 'Fehler: Datenbankschema konnte nicht abgerufen werden. Bitte überprüfen Sie die Datenbankverbindung.',
            'ja': 'エラー: データベーススキーマを取得できませんでした。データベース接続を確認してください。',
            'ko': '오류: 데이터베이스 스키마를 검색할 수 없습니다. 데이터베이스 연결을 확인하십시오.',
            'ar': 'خطأ: تعذر استرداد مخطط قاعدة البيانات. يرجى التحقق من اتصال قاعدة البيانات.'
        }.get(user_language, 'Error: Could not retrieve database schema. Please check database connection.'), 'suggestions': []})
 
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
        return jsonify({'response': welcome_message, 'suggestions': suggestions})
   
    # If the user's message is an initial chart type suggestion, respond with a follow-up question
    # and indicate the requested_chart_type for the frontend to store.
    if user_message in [s.lower() for s in INITIAL_CHART_SUGGESTIONS]:
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
        return jsonify({'response': response_text, 'suggestions': [], 'forced_chart_type': user_message})
 
    try:
        # Include forced_chart_type in the prompt if available, but primarily for context.
        # The actual enforcement will happen after LLM response.
        prompt_for_chart_params = f"""
            You are an AI assistant that helps users visualize data by generating chart parameters.
            The user will describe the chart they want, and you need to extract the following parameters:
            'table_name', 'chart_type', 'x_axis', 'y_axis', 'color', 'title', 'aggregate_y', 'z_axis', 'size'.
           
            Respond in {user_language}.
 
            Here is the database schema:
            {schema_info}
 
            Rules for parameter extraction:
            1.  **table_name**: Must be one of the tables in the schema. Prioritize tables explicitly mentioned or strongly implied.
            2.  **chart_type**: Can be 'bar_chart', 'line_chart', 'scatter_plot', 'pie_chart', 'histogram', 'box_plot', 'area_chart', 'heatmap', '3d_scatter_plot', 'bubble_chart', 'donut_chart'.
                {'The user previously selected a chart type and expects the next chart to be of that type: ' + forced_chart_type + '. Prioritize this type.' if forced_chart_type else ''}
            3.  **x_axis**: Column name from the specified table.
            4.  **y_axis**: Column name from the specified table.
            5.  **color**: Optional column name from the specified table for coloring data points/bars.
            6.  **title**: Optional, a descriptive title for the chart.
            7.  **aggregate_y**: Optional, can be 'SUM', 'AVG', 'COUNT', 'MIN', 'MAX'. Only apply if the user explicitly asks for aggregation on the y-axis (e.g., "total sales", "average price"). Ensure y_axis is numerical for SUM, AVG, MIN, MAX. For COUNT, y_axis can be any suitable column to count, often an ID.
            8.  **z_axis**: Required for 'heatmap' and '3d_scatter_plot'. Must be a column name from the specified table.
            9.  **size**: Required for 'bubble_chart'. Must be a numerical column name from the specified table.
            10. **Column Matching**: Ensure selected 'x_axis', 'y_axis', 'color', 'z_axis', 'size' columns exist in the chosen 'table_name' and match their data types (e.g., numerical for aggregations).
            11. **Pie Chart/Donut Chart**: For 'pie_chart' and 'donut_chart', 'x_axis' should represent 'names' (categories) and 'y_axis' should represent 'values' (numerical).
            12. **Default Chart Type**: If the user's request is ambiguous, default to 'bar_chart'.
            13. **Missing Columns**: If the user asks for a chart but doesn't specify columns, suggest common columns or ask for clarification.
 
            Respond with a JSON object containing the extracted parameters. If you cannot extract meaningful parameters, return an empty JSON object or indicate what information is missing.
 
            User request: {user_message}
        """
 
        response_chart_params = model_for_chart_params.generate_content(prompt_for_chart_params)
        chart_params_str = response_chart_params.text
        chart_params_str = chart_params_str.replace("```json", "").replace("```", "").strip()
       
        try:
            chart_params = json.loads(chart_params_str)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Problematic JSON string: {chart_params_str}")
            return jsonify({'response': {
                'en': 'I had trouble understanding your request for a chart. Could you please rephrase it?',
                'es': 'Tuve problemas para entender tu solicitud de un gráfico. ¿Podrías reformularla?',
                'fr': 'J\'ai eu du mal à comprendre votre demande de graphique. Pourriez-vous la reformuler ?',
                'de': 'Ich hatte Schwierigkeiten, Ihre Anfrage für ein Diagramm zu verstehen. Könnten Sie sie bitte umformulieren?',
                'ja': 'チャートのリクエストを理解できませんでした。別の表現でお願いします。',
                'ko': '차트 요청을 이해하는 데 문제가 있었습니다. 다시 말씀해 주시겠어요?',
                'ar': 'واجهت صعوبة في فهم طلبك للرسم البياني. هل يمكنك إعادة صياغته من فضلك؟'
            }.get(user_language, 'I had trouble understanding your request for a chart. Could you please rephrase it?'), 'suggestions': []})
 
        if chart_params and 'table_name' in chart_params:
            table_name = chart_params['table_name']
           
            if table_name not in all_table_schemas:
                return jsonify({'response': {
                    'en': f"I couldn't find the table '{table_name}' in the database. Please specify a valid table from the schema. Available tables are: {', '.join(all_table_schemas.keys())}",
                    'es': f"No pude encontrar la tabla '{table_name}' en la base de datos. Por favor, especifica una tabla válida del esquema. Las tablas disponibles son: {', '.join(all_table_schemas.keys())}",
                    'fr': f"Je n'ai pas pu trouver la table '{table_name}' dans la base de données. Veuillez spécifier une table valide du schéma. Les tables disponibles sont : {', '.join(all_table_schemas.keys())}",
                    'de': f"Ich konnte die Tabelle '{table_name}' in der Datenbank nicht finden. Bitte geben Sie eine gültige Tabelle aus dem Schema an. Verfügbare Tabellen sind: {', '.join(all_table_schemas.keys())}",
                    'ja': f"データベースにテーブル「{table_name}」が見つかりませんでした。スキーマから有効なテーブルを指定してください。利用可能なテーブルは次のとおりです: {', '.join(all_table_schemas.keys())}",
                    'ko': f"데이터베이스에서 테이블 '{table_name}'을(를) 찾을 수 없습니다. 스키마에서 유효한 테이블을 지정하십시오. 사용 가능한 테이블은 다음과 같습니다: {', '.join(all_table_schemas.keys())}",
                    'ar': f"لم أتمكن من العثور على الجدول '{table_name}' في قاعدة البيانات. يرجى تحديد جدول صالح من المخطط. الجداول المتاحة هي: {', '.join(all_table_schemas.keys())}"
                }.get(user_language, f"I couldn't find the table '{table_name}' in the database. Please specify a valid table from the schema. Available tables are: {', '.join(all_table_schemas.keys())}"), 'suggestions': []})
 
            # --- Enforce forced_chart_type if present and valid ---
            if forced_chart_type and forced_chart_type in INITIAL_CHART_SUGGESTIONS:
                chart_params['chart_type'] = forced_chart_type
                print(f"Forcing chart type to: {forced_chart_type}")
            # --- End Enforce ---
 
            df = fetch_data_for_chart(chart_params)
            if df is not None and not df.empty:
                chart_json_string = create_chart_json(df, chart_params)
               
                chart_data = json.loads(chart_json_string)
 
                if 'error' in chart_data:
                    return jsonify({'response': chart_data['error'], 'suggestions': []})
 
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
               
                response_follow_up_suggestions = model_for_suggestions.generate_content(prompt_for_follow_up_suggestions)
                follow_up_suggestions_text = response_follow_up_suggestions.text.strip()
                follow_up_suggestions_list = [s.strip() for s in follow_up_suggestions_text.split(',')] if follow_up_suggestions_text else []
               
                # Return raw_data along with chart_json
                return jsonify({'chart_json': chart_data, 'raw_data': df.to_json(orient='records', date_format='iso'), 'suggestions': follow_up_suggestions_list})
            else:
                return jsonify({'response': {
                    'en': 'I could not fetch data for the requested chart. The table might be empty or the columns are incorrect.',
                    'es': 'No pude obtener datos para el gráfico solicitado. La tabla podría estar vacía o las columnas son incorrectas.',
                    'fr': 'Je n\'ai pas pu récupérer les données pour le graphique demandé. La table est peut-être vide ou les colonnes sont incorrectes.',
                    'de': 'Ich konnte keine Daten für das angeforderte Diagramm abrufen. Die Tabelle ist möglicherweise leer oder die Spalten sind falsch.',
                    'ja': '要求されたチャートのデータを取得できませんでした。テーブルが空であるか、列が正しくない可能性があります。',
                    'ko': '요청한 차트에 대한 데이터를 가져올 수 없습니다. 테이블이 비어 있거나 열이 올바르지 않을 수 있습니다.',
                    'ar': 'لم أتمكن من جلب البيانات للرسم البياني المطلوب. قد يكون الجدول فارغًا أو الأعمدة غير صحيحة.'
                }.get(user_language, 'I could not fetch data for the requested chart. The table might be empty or the columns are incorrect.'), 'suggestions': []})
        else:
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
           
            return jsonify({'response': {
                'en': "I didn't fully understand your request. Perhaps you could try one of these, or be more specific:",
                'es': "No entendí completamente tu solicitud. Quizás podrías intentar una de estas opciones, o ser más específico:",
                'fr': "Je n'ai pas entièrement compris votre demande. Vous pourriez peut-être essayer l'une de ces options, ou être plus précis :",
                'de': "Ich habe Ihre Anfrage nicht vollständig verstanden. Vielleicht könnten Sie eine dieser Optionen ausprobieren oder spezifischer sein:",
                'ja': "リクエストを完全に理解できませんでした。これらのいずれかを試すか、より具体的にしてください：",
                'ko': "요청을 완전히 이해하지 못했습니다. 다음 중 하나를 시도하거나 더 구체적으로 말씀해 주십시오:",
                'ar': "لم أفهم طلبك بالكامل. ربما يمكنك تجربة أحد هذه الخيارات، أو كن أكثر تحديدًا:"
            }.get(user_language, "I didn't fully understand your request. Perhaps you could try one of these, or be more specific:"), 'suggestions': general_suggestions_list})
 
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'response': {
            'en': f'An unexpected error occurred: {e}. Please try again.',
            'es': f'Ocurrió un error inesperado: {e}. Por favor, inténtalo de nuevo.',
            'fr': f'Une erreur inesperada es survenue : {e}. Veuillez réessayer.',
            'de': f'Ein unerwarteter Fehler ist aufgetreten: {e}. Bitte versuchen Sie es erneut.',
            'ja': f'予期せぬエラーが発生しました: {e}。もう一度お試しください。',
            'ko': f'예상치 못한 오류가 발생했습니다: {e}. 다시 시도해 주세요.',
            'ar': f'حدث خطأ غير متوقع: {e}. يرجى المحاولة مرة أخرى.'
        }.get(user_language, f'An unexpected error occurred: {e}. Please try again.'), 'suggestions': []})
 
if __name__ == '__main__':
    app.run(debug=True)
 
 
 