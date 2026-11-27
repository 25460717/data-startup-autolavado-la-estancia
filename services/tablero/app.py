import os
import sqlite3
import datetime
import io
from pathlib import Path
import db_manager
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# ==========================================
# CONFIGURACIÓN GENERAL Y ESTILOS DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Autolavado Expréss La Estancia",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS modernos y limpios
st.markdown("""
<style>
    /* Estilos globales y fondo oscuro moderno */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0d1527 0%, #070a12 100%) !important;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header principal con brillo sutil y bordes redondeados */
    .hero-header {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(14, 116, 144, 0.75) 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 26px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px -8px rgba(2, 132, 199, 0.35);
        backdrop-filter: blur(8px);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #e0f2fe;
        opacity: 0.95;
        margin-top: 6px;
        font-weight: 400;
    }
    
    /* Tarjetas de métricas tipo KPI ejecutivas */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.5);
        box-shadow: 0 10px 28px rgba(56, 189, 248, 0.18);
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.95rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.15;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Tarjetas de servicios POS */
    .service-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.65) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .service-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    .service-title {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        white-space: normal !important;
        hyphens: none !important;
        line-height: 1.35 !important;
        min-height: 2.8rem;
        display: flex;
        align-items: center;
    }
    .service-desc {
        font-size: 0.83rem !important;
        color: #94a3b8 !important;
        line-height: 1.35 !important;
        min-height: 2.5rem;
        word-break: normal !important;
        hyphens: none !important;
    }
    
    /* Badges de Categoría */
    .badge-category {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-radius: 6px;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        margin-bottom: 8px;
    }
    
    /* Botones de Cobro con estilo y ergonomía */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        hyphens: none !important;
        padding: 0.6rem 1.1rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.35) !important;
    }
    
    /* Tarjetas de método de pago en corte diario */
    .metodo-card-efectivo {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 78, 59, 0.3) 100%);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
        color: #ecfdf5;
    }
    .metodo-card-transf {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(49, 46, 129, 0.3) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
        color: #eef2ff;
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #0b1120 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Footer personalizado */
    .app-footer {
        text-align: center;
        padding: 24px 0 10px 0;
        margin-top: 36px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        color: #64748b;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# GESTIÓN DE RUTAS Y BASE DE DATOS LOCAL
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "autolavado.db")

# Rutas de respaldo para búsqueda de Excel solo en caso de que autolavado.db no exista
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
EXCEL_CANDIDATES = [
    os.path.join(PROJECT_ROOT, "notebooks", "Registro_Ventas_Autolavado_v3 (1).xlsx"),
    os.path.join(PROJECT_ROOT, "notebooks", "Registro_Ventas_Autolavado_v3.xlsx"),
    os.path.join("notebooks", "Registro_Ventas_Autolavado_v3 (1).xlsx"),
    os.path.join("notebooks", "Registro_Ventas_Autolavado_v3.xlsx")
]

CATALOGO_SERVICIOS = [
    {"tipo": "Taxi", "precio": 70, "icono": "🚕", "categoria": "Taxi / Servicio Público", "desc": "Lavado básico exterior e interior servicio público"},
    {"tipo": "Carro - Servicio Normal", "precio": 100, "icono": "🚗", "categoria": "Carro", "desc": "Exterior + aspirado interior estándar"},
    {"tipo": "Carro - Servicio Detallado", "precio": 120, "icono": "✨", "categoria": "Carro", "desc": "Cera líquida + abrillantador llantas + aromatizante"},
    {"tipo": "Camioneta - Servicio Normal", "precio": 120, "icono": "🚙", "categoria": "Camioneta", "desc": "Lavado completo para SUV / Pick-up"},
    {"tipo": "Camioneta - Servicio Detallado", "precio": 140, "icono": "🌟", "categoria": "Camioneta", "desc": "Detallado premium + abrillantador para SUV/Pick-up"},
    {"tipo": "Cuatrimoto", "precio": 350, "icono": "🏍️", "categoria": "Especial / Motos", "desc": "Desengrase profundo a presión todoterreno"},
    {"tipo": "Can-Am", "precio": 400, "icono": "🚜", "categoria": "Especial / Off-Road", "desc": "Lavado exhaustivo alta demanda Off-Road"}
]

DIAS_SEMANA_MAP = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

def get_connection():
    """Retorna una conexión a SQLite optimizada usando la ruta dinámica local."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@st.cache_resource(show_spinner=False)
def initialize_database():
    """
    Inicializa la base de datos.
    Si autolavado.db ya existe y tiene registros, se conecta directamente sin buscar el Excel.
    Solo busca e importa el Excel si la base de datos no existe o está vacía.
    """
    db_already_existed = os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla e índices si no existen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_ticket TEXT PRIMARY KEY,
            fecha TEXT NOT NULL,
            dia_semana TEXT NOT NULL,
            hora TEXT NOT NULL,
            tipo_servicio TEXT NOT NULL,
            precio REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_servicio ON ventas(tipo_servicio);")
    conn.commit()
    
    # Verificar cantidad de registros
    cursor.execute("SELECT COUNT(*) FROM ventas;")
    count = cursor.fetchone()[0]
    
    # Si ya contiene datos, salir de inmediato sin buscar ningún Excel
    if count > 0:
        conn.close()
        return True
        
    # Solo si está vacía, intentar buscar candidatos de Excel locales
    excel_found = None
    for candidate in EXCEL_CANDIDATES:
        if os.path.exists(candidate):
            excel_found = candidate
            break
            
    if excel_found:
        with st.spinner("Inicializando base de datos desde archivo histórico..."):
            df_excel = pd.read_excel(excel_found, skiprows=3)
            df_excel.columns = [c.strip() for c in df_excel.columns]
            
            col_map = {
                'ID Ticket': 'id_ticket',
                'Fecha': 'fecha',
                'Día de la Semana': 'dia_semana',
                'Hora': 'hora',
                'Tipo de Vehículo / Servicio': 'tipo_servicio',
                'Precio ($)': 'precio'
            }
            df_clean = df_excel[list(col_map.keys())].rename(columns=col_map)
            
            df_clean['id_ticket'] = df_clean['id_ticket'].astype(str).str.strip()
            df_clean['fecha'] = pd.to_datetime(df_clean['fecha']).dt.strftime('%Y-%m-%d')
            df_clean['dia_semana'] = df_clean['dia_semana'].astype(str).str.strip()
            df_clean['hora'] = df_clean['hora'].astype(str).str.strip()
            df_clean['tipo_servicio'] = df_clean['tipo_servicio'].astype(str).str.strip()
            df_clean['precio'] = pd.to_numeric(df_clean['precio'], errors='coerce').fillna(0.0)
            
            df_clean.to_sql('ventas', conn, if_exists='append', index=False, chunksize=10000)
            conn.commit()
    
    conn.close()
    return True

# Inicializar Base de Datos
initialize_database()
db_manager.init_tables()

# ==========================================
# FUNCIONES DE CONSULTA Y NEGOCIO
# ==========================================
def get_next_ticket_id():
    """Genera el siguiente ID Ticket consecutivo en formato TKT-XXXXX."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_ticket FROM ventas ORDER BY rowid DESC LIMIT 1;")
    row = cursor.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return "TKT-10001"
    
    last_id = str(row[0])
    try:
        num_part = int(last_id.split("-")[1])
        next_num = num_part + 1
        return f"TKT-{next_num}"
    except Exception:
        cursor = get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM ventas;")
        total = cursor.fetchone()[0]
        return f"TKT-{10000 + total + 1}"

def registrar_venta(tipo_servicio, precio):
    """Inserta una nueva venta con la fecha y hora actual en tiempo real."""
    ahora = datetime.datetime.now()
    nuevo_id = get_next_ticket_id()
    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA_MAP.get(ahora.weekday(), "Lunes")
    hora_str = ahora.strftime("%H:%M")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ventas (id_ticket, fecha, dia_semana, hora, tipo_servicio, precio)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (nuevo_id, fecha_str, dia_str, hora_str, tipo_servicio, float(precio)))
    conn.commit()
    conn.close()
    
    return nuevo_id, fecha_str, hora_str

def get_ventas_hoy():
    """Obtiene el resumen y las ventas registradas el día de hoy."""
    hoy_str = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    query = """
        SELECT id_ticket, fecha, dia_semana, hora, tipo_servicio, precio 
        FROM ventas 
        WHERE fecha = ? 
        ORDER BY rowid DESC;
    """
    df_hoy = pd.read_sql_query(query, conn, params=(hoy_str,))
    conn.close()
    return df_hoy

@st.cache_data(ttl=60)
def load_historical_data():
    """Carga los datos históricos optimizados para análisis."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id_ticket, fecha, dia_semana, hora, tipo_servicio, precio 
        FROM ventas;
    """, conn)
    conn.close()
    
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['year'] = df['fecha'].dt.year
    df['year_month'] = df['fecha'].dt.to_period('M').dt.to_timestamp()
    
    def parse_hour(h_val):
        try:
            return int(str(h_val).split(":")[0])
        except Exception:
            return 12
    df['hora_num'] = df['hora'].apply(parse_hour)
    return df

# ==========================================
# FUNCIONES DE MACHINE LEARNING Y PRONÓSTICO
# ==========================================
def extract_calendar_features(dt_series):
    """Extrae las variables de calendario requeridas para el modelo."""
    day_of_week = dt_series.dt.dayofweek
    day_of_month = dt_series.dt.day
    month = dt_series.dt.month
    # Indicador de quincena (días 14, 15, 16 o fin de mes 29, 30, 31 o día 1)
    is_quincena = day_of_month.isin([14, 15, 16, 29, 30, 31, 1]).astype(int)
    # Indicador de fin de semana (Viernes=4, Sábado=5, Domingo=6)
    is_weekend = day_of_week.isin([4, 5, 6]).astype(int)
    
    return pd.DataFrame({
        'day_of_week': day_of_week,
        'day_of_month': day_of_month,
        'month': month,
        'is_quincena': is_quincena,
        'is_weekend': is_weekend
    })

@st.cache_data(ttl=300)
def train_and_forecast_ml(target_variable="vehiculos", horizon_days=14):
    """
    Entrena modelos Random Forest con features de calendario y promedios móviles
    para pronosticar vehículos o ingresos.
    """
    conn = get_connection()
    df_raw = pd.read_sql_query("SELECT fecha, precio FROM ventas;", conn)
    conn.close()
    
    df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
    # Agrupación diaria: conteo de vehículos y suma de ingresos
    daily = df_raw.groupby('fecha').agg(
        vehiculos=('precio', 'count'),
        ingresos=('precio', 'sum')
    ).reset_index().sort_values('fecha').reset_index(drop=True)
    
    # Rellenar posibles fechas continuas
    idx_full = pd.date_range(daily['fecha'].min(), daily['fecha'].max(), freq='D')
    daily = daily.set_index('fecha').reindex(idx_full, fill_value=0).reset_index().rename(columns={'index': 'fecha'})
    
    # Calcular promedios móviles con shift para no fugar información
    daily['roll_7'] = daily[target_variable].shift(1).rolling(window=7, min_periods=1).mean()
    daily['roll_14'] = daily[target_variable].shift(1).rolling(window=14, min_periods=1).mean()
    
    # Variables de calendario
    cal_feats = extract_calendar_features(daily['fecha'])
    data_feat = pd.concat([daily, cal_feats], axis=1)
    
    feature_cols = ['day_of_week', 'day_of_month', 'month', 'is_quincena', 'is_weekend', 'roll_7', 'roll_14']
    
    # Eliminar las filas iniciales donde el rolling no está bien formado
    clean_df = data_feat.dropna().reset_index(drop=True)
    
    # Split cronológico de validación (últimos 60 días para test)
    test_size = 60
    train_df = clean_df.iloc[:-test_size]
    test_df = clean_df.iloc[-test_size:]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_variable]
    X_test = test_df[feature_cols]
    y_test = test_df[target_variable]
    
    model = RandomForestRegressor(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluación
    y_pred_test = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred_test)
    r2 = r2_score(y_test, y_pred_test)
    
    # Reentrenar con todo el histórico disponible
    model_full = RandomForestRegressor(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
    model_full.fit(clean_df[feature_cols], clean_df[target_variable])
    
    # Pronóstico iterativo hacia el futuro (recursivo para los rollings)
    future_dates = pd.date_range(daily['fecha'].max() + pd.Timedelta(days=1), periods=horizon_days, freq='D')
    history_target = daily[target_variable].tolist()
    forecasts = []
    
    for f_date in future_dates:
        # roll_7 y roll_14 basados en la serie acumulada
        r7 = np.mean(history_target[-7:])
        r14 = np.mean(history_target[-14:])
        
        cal = extract_calendar_features(pd.Series([f_date]))
        feat_vector = pd.DataFrame([{
            'day_of_week': cal['day_of_week'].iloc[0],
            'day_of_month': cal['day_of_month'].iloc[0],
            'month': cal['month'].iloc[0],
            'is_quincena': cal['is_quincena'].iloc[0],
            'is_weekend': cal['is_weekend'].iloc[0],
            'roll_7': r7,
            'roll_14': r14
        }])
        
        pred_val = max(0.0, float(model_full.predict(feat_vector[feature_cols])[0]))
        forecasts.append(pred_val)
        history_target.append(pred_val)
        
    df_forecast = pd.DataFrame({
        'fecha': future_dates,
        'dia_semana': [DIAS_SEMANA_MAP[d.weekday()] for d in future_dates],
        f'pred_{target_variable}': forecasts
    })
    
    return {
        'model': model_full,
        'mae': mae,
        'r2': r2,
        'daily_history': daily,
        'df_forecast': df_forecast,
        'feature_importance': pd.Series(model_full.feature_importances_, index=feature_cols)
    }

# ==========================================
# FUNCIONES DE BENCHMARK DE MODELOS (AVANCE 2)
# ==========================================
@st.cache_data(ttl=300)
def benchmark_regression_models(target_col='vehiculos', test_size=0.20, n_splits=5):
    """
    Entrena y evalúa 5 modelos de regresión de la Unidad 3 con:
    - Preprocesamiento formal: Imputación, StandardScaler (numéricas) y OneHotEncoder (categóricas).
    - Partición Train/Test y Validación Cruzada K-Fold.
    - Métricas formales: MAE, RMSE, R² y K-Fold Score.
    """
    conn = get_connection()
    df_raw = pd.read_sql_query("SELECT fecha, precio FROM ventas;", conn)
    conn.close()
    
    df_raw['fecha'] = pd.to_datetime(df_raw['fecha'])
    daily = df_raw.groupby('fecha').agg(
        vehiculos=('precio', 'count'),
        ingresos=('precio', 'sum')
    ).reset_index().sort_values('fecha').reset_index(drop=True)
    
    idx_full = pd.date_range(daily['fecha'].min(), daily['fecha'].max(), freq='D')
    daily = daily.set_index('fecha').reindex(idx_full, fill_value=0).reset_index().rename(columns={'index': 'fecha'})
    
    # Feature Engineering
    daily['dia_nombre'] = daily['fecha'].dt.day_name()
    daily['dia_mes'] = daily['fecha'].dt.day
    daily['mes'] = daily['fecha'].dt.month
    daily['es_fin_semana'] = daily['fecha'].dt.dayofweek.isin([4, 5, 6]).astype(int)
    daily['es_quincena'] = daily['dia_mes'].isin([14, 15, 16, 29, 30, 31, 1]).astype(int)
    daily['media_movil_7d'] = daily[target_col].shift(1).rolling(7, min_periods=1).mean()
    daily['media_movil_14d'] = daily[target_col].shift(1).rolling(14, min_periods=1).mean()
    
    daily = daily.dropna().reset_index(drop=True)
    
    num_cols = ['dia_mes', 'mes', 'es_fin_semana', 'es_quincena', 'media_movil_7d', 'media_movil_14d']
    cat_cols = ['dia_nombre']
    
    X = daily[num_cols + cat_cols]
    y = daily[target_col]
    
    # Pipeline de Preprocesamiento Formal
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
    ])
    preprocessor = ColumnTransformer([
        ('num', num_pipeline, num_cols),
        ('cat', cat_pipeline, cat_cols)
    ])
    
    # Partición Train/Test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=False
    )
    
    models = {
        'Regresión Lineal': LinearRegression(),
        'Árbol de Decisión (CART)': DecisionTreeRegressor(max_depth=8, random_state=42),
        'Random Forest Regressor': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        'Gradient Boosting Regressor': GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
        'KNN Regresor (k-Nearest Neighbors)': KNeighborsRegressor(n_neighbors=7)
    }
    
    results = []
    trained_pipes = {}
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    for name, model_inst in models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', model_inst)
        ])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = root_mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Validación Cruzada K-Fold sobre Train
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=kf, scoring='r2', n_jobs=-1)
        
        results.append({
            'Algoritmo': name,
            'Familia': 'Árboles / Ensamble' if 'Forest' in name or 'Tree' in name or 'Boosting' in name else ('Lineal' if 'Lineal' in name else 'Basado en Instancias'),
            'MAE': round(mae, 2),
            'RMSE': round(rmse, 2),
            'R² Score': round(r2, 4),
            'K-Fold CV R² (Promedio)': round(cv_scores.mean(), 4),
            'K-Fold CV Std': round(cv_scores.std(), 4)
        })
        trained_pipes[name] = pipe
        
    df_results = pd.DataFrame(results).sort_values(by='R² Score', ascending=False).reset_index(drop=True)
    return df_results, X_test, y_test, trained_pipes

@st.cache_data(ttl=300)
def benchmark_classification_models(sample_size=25000, test_size=0.20, n_splits=5):
    """
    Entrena y evalúa 4 modelos de clasificación de la Unidad 3:
    - Naive Bayes, KNN, Árbol de Decisión y Random Forest.
    - Problema: Clasificación de clientes que solicitan Servicio Detallado / Especial vs Normal.
    - Preprocesamiento: Imputación, Escalado numérico y One-Hot Encoding.
    - Métricas: Accuracy, Precision, Recall y F1-Score.
    """
    conn = get_connection()
    df_raw = pd.read_sql_query(
        f"SELECT dia_semana, hora, tipo_servicio, precio FROM ventas LIMIT {sample_size};", 
        conn
    )
    conn.close()
    
    def parse_h(h):
        try:
            return int(str(h).split(':')[0])
        except Exception:
            return 12
            
    df_raw['hora_num'] = df_raw['hora'].apply(parse_h)
    df_raw['es_fin_semana'] = df_raw['dia_semana'].isin(['Viernes', 'Sábado', 'Domingo']).astype(int)
    # Variable objetivo binaria: Servicio Detallado o Especial (1) vs Básico (0)
    df_raw['target_detallado'] = df_raw['tipo_servicio'].str.contains('Detallado|Cuatrimoto|Can-Am').astype(int)
    
    num_cols = ['hora_num', 'precio', 'es_fin_semana']
    cat_cols = ['dia_semana']
    
    X = df_raw[num_cols + cat_cols]
    y = df_raw['target_detallado']
    
    preprocessor = ColumnTransformer([
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ]), num_cols),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
        ]), cat_cols)
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    clf_models = {
        'Naive Bayes (GaussianNB)': GaussianNB(),
        'KNN (k-Nearest Neighbors)': KNeighborsClassifier(n_neighbors=7),
        'Árbol de Decisión (CART)': DecisionTreeClassifier(max_depth=6, random_state=42),
        'Random Forest Classifier': RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42, n_jobs=-1)
    }
    
    results = []
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    for name, model_inst in clf_models.items():
        pipe = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', model_inst)
        ])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=kf, scoring='f1', n_jobs=-1)
        
        results.append({
            'Algoritmo': name,
            'Accuracy': round(acc, 4),
            'Precision': round(prec, 4),
            'Recall': round(rec, 4),
            'F1-Score': round(f1, 4),
            'K-Fold CV F1 (Promedio)': round(cv_scores.mean(), 4)
        })
        
    df_results = pd.DataFrame(results).sort_values(by='F1-Score', ascending=False).reset_index(drop=True)
    return df_results, X_test, y_test

# ==========================================
# NAVEGACIÓN LATERAL
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 10px 0 16px 0;'>
        <div style='font-size: 2.8rem; margin-bottom: 4px;'>🚗✨</div>
        <div style='font-size: 1.35rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.01em;'>Autolavado Expréss</div>
        <div style='font-size: 0.9rem; font-weight: 600; color: #38bdf8;'>La Estancia</div>
        <div style='display: inline-block; margin-top: 6px; padding: 3px 10px; font-size: 0.7rem; font-weight: 700; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px;'>
            SISTEMA POS & ANALÍTICA v3.5
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    pagina = st.radio(
        "Menú Principal",
        [
            "Registro de Ventas (Caja POS)",
            "Dashboard Analítico Histórico",
            "Predicción de Demanda e Ingresos (Machine Learning)",
            "Calculadora de Insumos y Turnos de Personal",
            "Avance 2: Modelos ML y Preprocesamiento",
            "Entregable 3: Microservicios y Series de Tiempo (ARIMA/SARIMA)"
        ],
        index=0
    )
    
    db_status = db_manager.get_db_status()
    st.markdown("---")
    st.markdown("**Estado de Conexión:**")
    st.markdown(f"""
    <div style='background: rgba(30, 41, 59, 0.75); border: 1px solid {db_status["badge_color"]}; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;'>
        <div style='font-weight: 700; color: {db_status["badge_color"]};'>{db_status["icon"]} {db_status["status_label"]}</div>
        <div style='font-size: 0.76rem; color: #94a3b8; margin-top: 4px;'>{db_status["engine"]}</div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("☁️ Persistencia Nube (Supabase)"):
        st.markdown(f"""
        **Modo de Guardado:**
        {db_status["description"]}
        
        Para guardar en la nube sin depender del disco de Streamlit:
        1. Crea tu cuenta en [supabase.com](https://supabase.com)
        2. En tus `st.secrets` agrega:
        ```toml
        SUPABASE_URL = "https://tu-proyecto.supabase.co"
        SUPABASE_KEY = "tu-clave-anon"
        ```
        """)
    st.markdown("""
    <div style='background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px 14px; border-radius: 10px; font-size: 0.78rem; color: #94a3b8; margin-top: 10px;'>
        <div style='font-weight: 700; color: #f1f5f9; margin-bottom: 4px;'>📍 Sucursal La Estancia</div>
        <div>👨‍💻 <strong>Proyecto Integrador:</strong> Ciencia de Datos & IA</div>
        <div style='margin-top: 4px;'>👥 <strong>Equipo:</strong> 3 Integrantes</div>
        <div style='margin-top: 4px; color: #38bdf8;'>💼 <strong>Acuerdo:</strong> $600 MXN/semana</div>
        <div style='margin-top: 4px; color: #22c55e;'>🟢 <strong>Estado:</strong> 100% Operativo</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# PÁGINA 1: REGISTRO DE VENTAS (CAJA POS)
# ==========================================
if pagina == "Registro de Ventas (Caja POS)":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">⚡ Punto de Venta Express</div>
        <div class="hero-subtitle">Registro instantáneo de servicios de lavado, cobro multimétodo y corte de caja en tiempo real</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛒 Registrar Servicio al Instante")
    st.caption("Elige el método de pago y haz clic en el servicio para emitir el ticket con autoguardado inmediato en la base de datos.")
    
    # Selector de opciones rápidas de cobro estilizado
    st.markdown("""
    <div style='background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px 18px; margin-bottom: 16px;'>
        <div style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>
            ⚡ Configuración Rápida de Cobro
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c_pay1, c_pay2 = st.columns([1.3, 1])
    with c_pay1:
        metodo_pago_sel = st.radio(
            "Método de Pago Activo:",
            ["💵 Efectivo (Predeterminado)", "📱 Transferencia"],
            horizontal=True,
            index=0,
            help="Elige cómo pagó el cliente para registrarlo de inmediato en el corte de caja."
        )
    with c_pay2:
        notas_placa_input = st.text_input(
            "Placa o descripción del vehículo (opcional):",
            placeholder="Ej: JRD-4521 / Versa blanco / Tsuru",
            help="Puedes anotar la placa o descripción física para control del ticket."
        )
        
    metodo_limpio = "Efectivo"
    if "Transferencia" in metodo_pago_sel:
        metodo_limpio = "Transferencia"

        
    # Grid de tarjetas de cobro organizadas (3 columnas amplias para evitar corte de texto)
    cols = st.columns(3)
    
    for idx, item in enumerate(CATALOGO_SERVICIOS):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"<span class='badge-category'>{item.get('categoria', 'General')}</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='service-title'>{item['icono']} {item['tipo']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 1.6rem; font-weight: 800; color: #38bdf8; margin: 4px 0 8px 0;'>${item['precio']} <span style='font-size: 0.85rem; color: #94a3b8;'>MXN</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='service-desc'>{item['desc']}</div>", unsafe_allow_html=True)
                
                btn_label = f"⚡ Cobrar ${item['precio']} ({metodo_limpio})"
                es_destacado = "Detallado" in item['tipo'] or "Off-Road" in item.get('desc', '')
                if st.button(btn_label, key=f"btn_pos_{idx}", use_container_width=True, type="primary" if es_destacado else "secondary"):
                    nuevo_tkt = db_manager.registrar_ticket(
                        servicio=item['tipo'],
                        categoria_vehiculo=item.get('categoria', 'General'),
                        precio_mxn=item['precio'],
                        metodo_pago=metodo_limpio,
                        notas_placa=notas_placa_input
                    )
                    st.toast(f"✅ ¡Ticket {nuevo_tkt['folio']} registrado con éxito! (${item['precio']} MXN)", icon="🎉")
                    st.rerun()
                    
    st.markdown("---")
    
    # Consulta de tickets del día en tiempo real
    df_hoy = db_manager.get_tickets_dia()
    corte_hoy = db_manager.get_corte_resumen(df_hoy)
    
    st.markdown("### 📊 Métricas del Día en Vivo")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Autos Lavados Hoy</div>
            <div class="metric-value">{corte_hoy['total_lavados']:,}</div>
            <div class="metric-sub">📅 {datetime.date.today().strftime('%d/%m/%Y')} (Solo pagados)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ingresos Netos del Día</div>
            <div class="metric-value">${corte_hoy['total_ingresos_netos']:,.2f}</div>
            <div class="metric-sub">💰 Recaudación neta en caja</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        if not df_hoy.empty and corte_hoy['total_lavados'] > 0:
            df_pagados_sub = df_hoy[df_hoy['estado'] == 'Pagado']
            servicio_top_hoy = df_pagados_sub['servicio'].mode()[0] if not df_pagados_sub.empty else "Sin ventas aún"
        else:
            servicio_top_hoy = "Sin ventas aún"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Servicio Más Pedido</div>
            <div class="metric-value" style="font-size: 1.15rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{servicio_top_hoy}">{servicio_top_hoy}</div>
            <div class="metric-sub">⭐ Preferencia de clientes</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tickets Anulados</div>
            <div class="metric-value" style="color: #f87171;">{corte_hoy['total_cancelados_num']}</div>
            <div class="metric-sub">${corte_hoy['total_cancelados_monto']:,.2f} MXN descontados</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Desglose de corte de caja por método de pago estilizado
    st.markdown("#### 💵 Desglose de Corte de Caja en Vivo")
    met_col1, met_col2 = st.columns(2)
    ef_info = corte_hoy.get('por_metodo', {}).get('Efectivo', {'monto': 0.0, 'conteo': 0})
    tr_info = corte_hoy.get('por_metodo', {}).get('Transferencia', {'monto': 0.0, 'conteo': 0})
    
    with met_col1:
        st.markdown(f"""
        <div class="metodo-card-efectivo">
            <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #6ee7b7;">
                💵 Cobrado en Efectivo
            </div>
            <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; margin-top: 4px;">
                ${ef_info['monto']:,.2f} <span style="font-size: 0.85rem; color: #a7f3d0;">MXN</span>
            </div>
            <div style="font-size: 0.8rem; color: #a7f3d0; margin-top: 2px;">
                {ef_info['conteo']} lavados cobrados en mano
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with met_col2:
        st.markdown(f"""
        <div class="metodo-card-transf">
            <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #a5b4fc;">
                📱 Cobrado por Transferencia
            </div>
            <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; margin-top: 4px;">
                ${tr_info['monto']:,.2f} <span style="font-size: 0.85rem; color: #c7d2fe;">MXN</span>
            </div>
            <div style="font-size: 0.8rem; color: #c7d2fe; margin-top: 2px;">
                {tr_info['conteo']} lavados transferidos al banco
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # Anulación / Cancelación de tickets con auditoría
    with st.expander("⚠️ Anular / Cancelar Ticket por Error de Captura"):
        st.caption("Si se capturó un ticket incorrecto o el cliente canceló el servicio, puedes anularlo aquí. No se borra del historial para conservar la auditoría, pero se descuenta automáticamente del total neto.")
        df_activos = df_hoy[df_hoy['estado'] == 'Pagado'] if not df_hoy.empty else pd.DataFrame()
        if not df_activos.empty:
            opciones_anular = [
                f"{row['folio']} | {str(row['fecha_hora']).split(' ')[1] if ' ' in str(row['fecha_hora']) else row['fecha_hora']} | {row['servicio']} | ${row['precio_mxn']} MXN ({row['metodo_pago']})"
                for _, row in df_activos.iterrows()
            ]
            ticket_sel = st.selectbox("Selecciona el ticket que deseas anular:", opciones_anular)
            folio_sel = ticket_sel.split(" | ")[0]
            col_mot1, col_mot2 = st.columns([2, 1])
            with col_mot1:
                motivo_anular = st.text_input("Motivo de cancelación:", placeholder="Ej: Error al seleccionar servicio / Cliente se retiró / Cobro duplicado")
            with col_mot2:
                st.write("")
                st.write("")
                if st.button("🚨 Confirmar Anulación", type="primary", use_container_width=True):
                    if not motivo_anular.strip():
                        st.warning("Por favor escribe un motivo para anular el ticket.")
                    else:
                        db_manager.cancelar_ticket(folio_sel, motivo_anular)
                        st.toast(f"Ticket {folio_sel} anulado con éxito.", icon="🚫")
                        st.rerun()
        else:
            st.info("No hay tickets activos para anular el día de hoy.")
            
    # Tabla de tickets registrados hoy
    st.markdown("### 📋 Tickets Registrados Hoy")
    if not df_hoy.empty:
        df_mostrar = df_hoy.copy()
        columnas_deseadas = [
            'folio', 'fecha_hora', 'servicio', 'categoria_vehiculo',
            'precio_mxn', 'metodo_pago', 'estado', 'notas_placa', 'motivo_cancelacion'
        ]
        cols_presentes = [c for c in columnas_deseadas if c in df_mostrar.columns]
        df_mostrar = df_mostrar[cols_presentes]
        
        nombres_columnas = {
            'folio': 'Folio',
            'fecha_hora': 'Fecha y Hora',
            'servicio': 'Servicio',
            'categoria_vehiculo': 'Categoría',
            'precio_mxn': 'Precio ($ MXN)',
            'metodo_pago': 'Método Pago',
            'estado': 'Estado',
            'notas_placa': 'Placa / Notas',
            'motivo_cancelacion': 'Motivo Cancelación'
        }
        df_mostrar = df_mostrar.rename(columns=nombres_columnas)
        
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Precio ($ MXN)": st.column_config.NumberColumn(format="$%.2f"),
                "Estado": st.column_config.TextColumn(help="Pagado o Cancelado")
            }
        )
        
        # Botones de exportación del día
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_bytes = df_mostrar.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 Descargar Corte de Hoy en CSV",
                data=csv_bytes,
                file_name=f"corte_caja_{datetime.date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            buf_excel = io.BytesIO()
            with pd.ExcelWriter(buf_excel, engine='openpyxl') as writer:
                df_mostrar.to_excel(writer, index=False, sheet_name=f"Corte_{datetime.date.today().strftime('%Y%m%d')}")
            st.download_button(
                "📊 Descargar Corte de Hoy en Excel (.xlsx)",
                data=buf_excel.getvalue(),
                file_name=f"corte_caja_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("ℹ️ No hay tickets registrados el día de hoy todavía. Utiliza las tarjetas superiores para registrar el primer cobro.")
        
    # Sección de Corte por Rango de Fechas
    with st.expander("📅 Consultar y Exportar Corte por Rango de Fechas (Historial de Caja)"):
        st.caption("Consulta cualquier período anterior para auditar ingresos, revisar métodos de pago y descargar el reporte completo a Excel o CSV.")
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            f_inicio = st.date_input("Fecha Desde:", value=datetime.date.today() - datetime.timedelta(days=7), key="corte_rango_inicio")
        with c_r2:
            f_fin = st.date_input("Fecha Hasta:", value=datetime.date.today(), key="corte_rango_fin")
            
        if f_inicio > f_fin:
            st.error("La fecha de inicio no puede ser posterior a la fecha final.")
        else:
            s_ini = f_inicio.strftime("%Y-%m-%d")
            s_fin = f_fin.strftime("%Y-%m-%d")
            df_rango = db_manager.get_tickets_rango(s_ini, s_fin)
            resumen_rango = db_manager.get_corte_resumen(df_rango)
            
            rg_col1, rg_col2, rg_col3 = st.columns(3)
            with rg_col1:
                st.metric("Autos Lavados en Período", f"{resumen_rango['total_lavados']:,}")
            with rg_col2:
                st.metric("Ingresos Netos del Período", f"${resumen_rango['total_ingresos_netos']:,.2f} MXN")
            with rg_col3:
                st.metric("Tickets Cancelados", f"{resumen_rango['total_cancelados_num']}")
                
            if not df_rango.empty:
                buf_r = io.BytesIO()
                with pd.ExcelWriter(buf_r, engine='openpyxl') as writer:
                    df_rango.to_excel(writer, index=False, sheet_name="Reporte_Caja")
                st.download_button(
                    "📊 Descargar Reporte del Período en Excel (.xlsx)",
                    data=buf_r.getvalue(),
                    file_name=f"reporte_caja_{s_ini}_al_{s_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No se encontraron tickets en el período seleccionado.")


elif pagina == "Dashboard Analítico Histórico":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">📈 Tablero Analítico e Inteligencia de Negocio</div>
        <div class="hero-subtitle">Análisis histórico completo, comportamiento de la demanda y horas pico</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner("Cargando métricas y registros históricos..."):
        df_hist = load_historical_data()
        
    if df_hist.empty:
        st.warning("⚠️ No se encontraron registros en la base de datos.")
        st.stop()
        
    with st.expander("🔍 Filtros de Segmentación", expanded=True):
        f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1.5])
        
        min_date = df_hist['fecha'].min().date()
        max_date = df_hist['fecha'].max().date()
        
        with f_col1:
            date_range = st.date_input(
                "Rango de Fechas:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
        with f_col2:
            years_available = sorted(df_hist['year'].unique(), reverse=True)
            selected_years = st.multiselect(
                "Año(s):",
                options=years_available,
                default=[]
            )
            
        with f_col3:
            services_available = sorted(df_hist['tipo_servicio'].unique())
            selected_services = st.multiselect(
                "Tipo de Vehículo / Servicio:",
                options=services_available,
                default=[]
            )
            
    filtered_df = df_hist.copy()
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df = filtered_df[(filtered_df['fecha'].dt.date >= start_d) & (filtered_df['fecha'].dt.date <= end_d)]
        
    if selected_years:
        filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
        
    if selected_services:
        filtered_df = filtered_df[filtered_df['tipo_servicio'].isin(selected_services)]
        
    if filtered_df.empty:
        st.warning("No hay registros que coincidan con los filtros seleccionados. Intenta ampliar el rango de búsqueda.")
        st.stop()
        
    total_vehiculos = len(filtered_df)
    ingresos_totales = filtered_df['precio'].sum()
    ticket_promedio = filtered_df['precio'].mean() if total_vehiculos > 0 else 0
    dia_mayor_afluencia = filtered_df['dia_semana'].value_counts().idxmax() if total_vehiculos > 0 else "N/A"
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Vehículos Históricos</div>
            <div class="metric-value">{total_vehiculos:,}</div>
            <div class="metric-sub">🚗 Registros analizados</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ingresos Totales</div>
            <div class="metric-value">${ingresos_totales:,.2f}</div>
            <div class="metric-sub">💵 MXN acumulados</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ticket Promedio</div>
            <div class="metric-value">${ticket_promedio:.2f}</div>
            <div class="metric-sub">🏷️ Ingreso medio por lavado</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Día con Mayor Afluencia</div>
            <div class="metric-value" style="font-size: 1.6rem;">{dia_mayor_afluencia}</div>
            <div class="metric-sub">📅 Pico semanal histórico</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    dias_ordenados = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    row1_c1, row1_c2 = st.columns([1.4, 1])
    
    with row1_c1:
        monthly_revenue = filtered_df.groupby('year_month')['precio'].sum().reset_index()
        fig_evolucion = px.area(
            monthly_revenue,
            x='year_month',
            y='precio',
            title='<b>📈 Ganancias Mes por Mes (Crecimiento del Negocio)</b>',
            labels={'year_month': 'Fecha', 'precio': 'Dinero Ganado ($ MXN)'},
            template='plotly_dark'
        )
        fig_evolucion.update_traces(
            line=dict(color='#38bdf8', width=3),
            fillcolor='rgba(56, 189, 248, 0.25)',
            hovertemplate='%{x|%B %Y}<br>Ganancia total: $%{y:,.2f} MXN<extra></extra>'
        )
        fig_evolucion.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_evolucion, use_container_width=True)
        st.caption("💡 Muestra con claridad cómo ha ido creciendo el dinero recaudado por el autolavado a lo largo del tiempo.")
        
    with row1_c2:
        day_counts = filtered_df['dia_semana'].value_counts().reindex(dias_ordenados, fill_value=0).reset_index()
        day_counts.columns = ['dia_semana', 'total_vehiculos']
        
        fig_barras_dia = px.bar(
            day_counts,
            x='dia_semana',
            y='total_vehiculos',
            title='<b>🚗 ¿Qué días de la semana llega más trabajo?</b>',
            labels={'dia_semana': 'Día de la Semana', 'total_vehiculos': 'Total de Autos'},
            text='total_vehiculos',
            template='plotly_dark',
            color='total_vehiculos',
            color_continuous_scale='Teal'
        )
        fig_barras_dia.update_traces(
            texttemplate='%{text:,} autos',
            textposition='outside',
            hovertemplate='%{x}<br>Total lavados: %{y:,} autos<extra></extra>'
        )
        fig_barras_dia.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            showlegend=False,
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_barras_dia, use_container_width=True)
        st.caption("💡 Permite ver fácilmente qué días se llena más el negocio para tener a todos los lavadores activos.")
        
    row2_c1, row2_c2 = st.columns([1.3, 1])
    
    with row2_c1:
        # Gráfica de barras directa y fácil de entender por hora del día
        hora_counts = filtered_df['hora_num'].value_counts().sort_index().reset_index()
        hora_counts.columns = ['hora_num', 'total_vehiculos']
        
        def formato_hora_humana(h):
            if h == 12:
                return "12:00 PM (Mediodía)"
            elif h > 12:
                return f"{h-12}:00 PM"
            else:
                return f"{h}:00 AM"
                
        hora_counts['hora_texto'] = hora_counts['hora_num'].apply(formato_hora_humana)
        
        fig_horas = px.bar(
            hora_counts,
            x='hora_texto',
            y='total_vehiculos',
            title='<b>⏰ ¿A qué horas del día hay más clientes? (Horas Pico)</b>',
            labels={'hora_texto': 'Hora del Día', 'total_vehiculos': 'Autos Lavados'},
            text='total_vehiculos',
            template='plotly_dark',
            color='total_vehiculos',
            color_continuous_scale='Oranges'
        )
        fig_horas.update_traces(
            texttemplate='%{text:,}',
            textposition='outside',
            hovertemplate='Hora: %{x}<br>Total lavados: %{y:,} autos<extra></extra>'
        )
        fig_horas.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            showlegend=False,
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_horas, use_container_width=True)
        st.caption("💡 Las barras más altas indican los momentos con mayor fila en el autolavado (ideal para saber a qué hora no debe faltar personal).")
        
    with row2_c2:
        servicio_revenue = filtered_df.groupby('tipo_servicio')['precio'].sum().reset_index()
        fig_pie = px.pie(
            servicio_revenue,
            names='tipo_servicio',
            values='precio',
            title='<b>🥧 ¿De qué tipo de vehículos entra más dinero?</b>',
            hole=0.45,
            template='plotly_dark',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>Aportó: $%{value:,.2f} MXN (%{percent})<extra></extra>'
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("💡 Proporción del dinero total que aportan los carros normales, taxis y camionetas.")

# ==========================================
# PÁGINA 3: PREDICCIÓN DE DEMANDA E INGRESOS (MACHINE LEARNING)
# ==========================================
elif pagina == "Predicción de Demanda e Ingresos (Machine Learning)":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🤖 Predicción de Demanda e Ingresos (Machine Learning)</div>
        <div class="hero-subtitle">Modelos de regresión predictiva basados en estacionalidad, quincenas y medias móviles</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de configuración del modelo
    st.markdown("### ⚙️ Configuración del Modelo Predictivo")
    cfg_c1, cfg_c2 = st.columns([1, 2])
    
    with cfg_c1:
        target_mode = st.radio(
            "Variable Objetivo a Predecir:",
            options=["vehiculos", "ingresos"],
            format_func=lambda x: "🚗 Total de Vehículos Diarios" if x == "vehiculos" else "💰 Ingresos Diarios ($ MXN)",
            horizontal=False
        )
    with cfg_c2:
        dias_pronostico = st.slider(
            "Horizonte de Pronóstico Futuro (Días):",
            min_value=7,
            max_value=30,
            value=14,
            step=1,
            help="Selecciona cuántos días consecutivos hacia el futuro deseas proyectar."
        )
        
    with st.spinner("Entrenando algoritmo Random Forest Regressor y generando pronóstico..."):
        res_ml = train_and_forecast_ml(target_variable=target_mode, horizon_days=dias_pronostico)
        # Guardar en session_state para la calculadora de insumos
        if target_mode == "vehiculos":
            st.session_state['ml_forecast_vehiculos'] = res_ml['df_forecast']
        else:
            # También pre-entrenar vehículos si no existe en sesión
            if 'ml_forecast_vehiculos' not in st.session_state:
                res_veh = train_and_forecast_ml(target_variable="vehiculos", horizon_days=7)
                st.session_state['ml_forecast_vehiculos'] = res_veh['df_forecast']
                
    # -----------------
    # MÉTRICAS DE EVALUACIÓN DEL MODELO
    # -----------------
    st.markdown("### 🎯 Métricas de Desempeño y Validación del Modelo")
    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    
    label_target = "Vehículos" if target_mode == "vehiculos" else "$ MXN"
    formato_mae = f"{res_ml['mae']:.1f} {label_target}" if target_mode == "vehiculos" else f"${res_ml['mae']:,.2f} MXN"
    
    total_pronosticado = res_ml['df_forecast'][f'pred_{target_mode}'].sum()
    promedio_diario_pred = res_ml['df_forecast'][f'pred_{target_mode}'].mean()
    
    with m_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Error Medio Absoluto (MAE)</div>
            <div class="metric-value">{formato_mae}</div>
            <div class="metric-sub">📉 Desviación media del modelo</div>
        </div>
        """, unsafe_allow_html=True)
    with m_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Coeficiente R² Score</div>
            <div class="metric-value">{res_ml['r2']:.3f}</div>
            <div class="metric-sub">🎯 Precisión de varianza explicada</div>
        </div>
        """, unsafe_allow_html=True)
    with m_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Pronosticado ({dias_pronostico} días)</div>
            <div class="metric-value">{f"{total_pronosticado:,.0f} autos" if target_mode == "vehiculos" else f"${total_pronosticado:,.2f}"}</div>
            <div class="metric-sub">🔮 Acumulado estimado</div>
        </div>
        """, unsafe_allow_html=True)
    with m_c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Promedio Diario Estimado</div>
            <div class="metric-value">{f"{promedio_diario_pred:.1f} autos/día" if target_mode == "vehiculos" else f"${promedio_diario_pred:,.2f}/día"}</div>
            <div class="metric-sub">⚡ Ritmo de demanda diaria</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # -----------------
    # GRÁFICA INTERACTIVA PLOTLY (ÚLTIMOS 30 DÍAS REALES + PREDICCIÓN)
    # -----------------
    st.markdown("### 📈 Proyección de Demanda Futura vs. Histórico Reciente")
    
    daily_hist = res_ml['daily_history'].copy()
    # Tomar últimos 30 días reales
    recent_real = daily_hist.tail(30).copy()
    
    df_fore = res_ml['df_forecast'].copy()
    df_fore['fecha'] = pd.to_datetime(df_fore['fecha'])
    
    # Crear figura combinada sencilla y clara para cualquier persona
    fig_ml = go.Figure()
    
    unidad_texto = "autos" if target_mode == "vehiculos" else "pesos"
    
    # Serie Real Histórica (últimos 30 días)
    fig_ml.add_trace(go.Scatter(
        x=recent_real['fecha'],
        y=recent_real[target_mode],
        mode='lines+markers',
        name='Lo que realmente se lavó (Mes pasado)',
        line=dict(color='#0284c7', width=3),
        marker=dict(size=6, color='#38bdf8'),
        hovertemplate=f'%{{x|%d/%m/%Y}}<br>Real: %{{y:.0f}} {unidad_texto}<extra></extra>'
    ))
    
    # Para unir visualmente la línea real con la predicción
    last_real_pt = recent_real.iloc[-1]
    connect_dates = [last_real_pt['fecha']] + df_fore['fecha'].tolist()
    connect_vals = [last_real_pt[target_mode]] + df_fore[f'pred_{target_mode}'].tolist()
    
    # Serie de Predicción Futura
    fig_ml.add_trace(go.Scatter(
        x=connect_dates,
        y=connect_vals,
        mode='lines+markers',
        name=f'Lo que esperamos que llegue (Próximos {dias_pronostico} días)',
        line=dict(color='#f59e0b', width=3, dash='dash'),
        marker=dict(size=8, color='#fbbf24', symbol='diamond'),
        hovertemplate=f'%{{x|%d/%m/%Y}}<br>Estimado: %{{y:.0f}} {unidad_texto}<extra></extra>'
    ))
    
    etiqueta_eje = "Cantidad de Autos Estimados" if target_mode == "vehiculos" else "Dinero Estimado ($ MXN)"
    fig_ml.update_layout(
        title=f"<b>🔮 Lo que realmente pasó vs. Lo que se espera que llegue (Próximos {dias_pronostico} Días)</b>",
        xaxis_title="Fecha",
        yaxis_title=etiqueta_eje,
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.6)',
        plot_bgcolor='rgba(15, 23, 42, 0.6)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=30, t=60, b=40)
    )
    st.plotly_chart(fig_ml, use_container_width=True)
    st.caption("💡 La línea azul muestra el historial real reciente. La línea naranja punteada con diamantes calcula cuántos autos o cuánto dinero se esperan recibir cada día para que el negocio esté preparado.")
    
    # -----------------
    # TABLA DE PRONÓSTICO Y DESCARGA CSV
    # -----------------
    st.markdown("### 📋 Detalle de Pronóstico Día por Día")
    
    df_table_show = df_fore.copy()
    df_table_show['Fecha'] = df_table_show['fecha'].dt.strftime('%d/%m/%Y')
    df_table_show['Día de la Semana'] = df_table_show['dia_semana']
    
    if target_mode == "vehiculos":
        df_table_show['Vehículos Estimados'] = df_table_show[f'pred_{target_mode}'].round(1)
        df_table_show['Ingresos Estimados Aprox. ($)'] = (df_table_show[f'pred_{target_mode}'] * 98.5).round(2)
        cols_final = ['Fecha', 'Día de la Semana', 'Vehículos Estimados', 'Ingresos Estimados Aprox. ($)']
    else:
        df_table_show['Ingresos Estimados ($ MXN)'] = df_table_show[f'pred_{target_mode}'].round(2)
        df_table_show['Vehículos Estimados Aprox.'] = (df_table_show[f'pred_{target_mode}'] / 98.5).round(1)
        cols_final = ['Fecha', 'Día de la Semana', 'Ingresos Estimados ($ MXN)', 'Vehículos Estimados Aprox.']
        
    st.dataframe(df_table_show[cols_final], use_container_width=True, hide_index=True)
    
    # Botón de Descarga CSV
    csv_bytes = df_table_show[cols_final].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Pronóstico en Formato CSV",
        data=csv_bytes,
        file_name=f"pronostico_autolavado_{target_mode}_{dias_pronostico}dias.csv",
        mime="text/csv",
        type="primary"
    )

# ==========================================
# PÁGINA 4: CALCULADORA DE INSUMOS Y TURNOS DE PERSONAL
# ==========================================
elif pagina == "Calculadora de Insumos y Turnos de Personal":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🧮 Calculadora de Insumos y Turnos de Personal</div>
        <div class="hero-subtitle">Planificación operativa, cálculo de insumos de bodega y dimensionamiento de equipo de trabajo</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Proporciones históricas de servicios para la distribución automática
    PROPORCIONES_HISTORICAS = {
        "Carro - Servicio Normal": 0.35,
        "Taxi": 0.25,
        "Camioneta - Servicio Normal": 0.15,
        "Carro - Servicio Detallado": 0.15,
        "Camioneta - Servicio Detallado": 0.096,
        "Cuatrimoto": 0.002,
        "Can-Am": 0.002
    }
    
    # Comprobar si existe pronóstico ML en session_state o calcular los próximos 7 días
    if 'ml_forecast_vehiculos' not in st.session_state:
        with st.spinner("Calculando proyección base de vehículos próximos 7 días..."):
            res_v = train_and_forecast_ml(target_variable="vehiculos", horizon_days=7)
            st.session_state['ml_forecast_vehiculos'] = res_v['df_forecast']
            
    df_fore_7 = st.session_state['ml_forecast_vehiculos'].head(7)
    total_ml_7_dias = int(round(df_fore_7['pred_vehiculos'].sum()))
    
    st.markdown("### 📥 Origen de la Demanda a Planificar")
    
    origen_c1, origen_c2 = st.columns([1, 1])
    with origen_c1:
        usar_ml = st.checkbox(
            f"🔄 Importar automáticamente pronóstico del Modelo ML (Próximos 7 días: {total_ml_7_dias} vehículos)",
            value=True,
            help="Distribuye el total pronosticado por el modelo entre los 7 servicios según el comportamiento histórico."
        )
    with origen_c2:
        periodo_dias = st.number_input("Días del Período de Planificación:", min_value=1, max_value=30, value=7, step=1)
        
    st.markdown("---")
    st.markdown("### 🚗 Cantidad de Servicios Esperados por Tipo de Vehículo")
    st.caption("Puedes ajustar individualmente la cantidad estimada de cada servicio para el período:")
    
    # Calcular valores sugeridos por defecto
    default_counts = {}
    if usar_ml:
        # Escalar al total de días seleccionado
        factor_escala = periodo_dias / 7.0
        total_vehiculos_periodo = total_ml_7_dias * factor_escala
        for s_item in CATALOGO_SERVICIOS:
            s_name = s_item['tipo']
            prop = PROPORCIONES_HISTORICAS.get(s_name, 0.1)
            default_counts[s_name] = max(1, int(round(total_vehiculos_periodo * prop)))
    else:
        # Valores base estándar por semana
        default_counts = {
            "Taxi": 90,
            "Carro - Servicio Normal": 130,
            "Carro - Servicio Detallado": 55,
            "Camioneta - Servicio Normal": 55,
            "Camioneta - Servicio Detallado": 35,
            "Cuatrimoto": 3,
            "Can-Am": 2
        }
        
    # Formulario interactivo con inputs numéricos
    input_cols_1 = st.columns(4)
    input_cols_2 = st.columns(3)
    
    cantidades_finales = {}
    
    # Primeros 4 servicios
    for i, s_item in enumerate(CATALOGO_SERVICIOS[:4]):
        s_name = s_item['tipo']
        with input_cols_1[i]:
            with st.container(border=True):
                st.markdown(f"**{s_item['icono']} {s_name}**")
                cantidades_finales[s_name] = st.number_input(
                    "Cantidad:",
                    min_value=0,
                    value=default_counts.get(s_name, 10),
                    step=1,
                    key=f"input_calc_{s_name}"
                )
                
    # Siguientes 3 servicios
    for i, s_item in enumerate(CATALOGO_SERVICIOS[4:]):
        s_name = s_item['tipo']
        with input_cols_2[i]:
            with st.container(border=True):
                st.markdown(f"**{s_item['icono']} {s_name}**")
                cantidades_finales[s_name] = st.number_input(
                    "Cantidad:",
                    min_value=0,
                    value=default_counts.get(s_name, 5),
                    step=1,
                    key=f"input_calc_{s_name}"
                )
                
    # -----------------
    # REGLAS DE CÁLCULO DE INSUMOS Y PERSONAL
    # -----------------
    # Rendimientos por vehículo:
    # Shampoo concentrado:
    #   - 50 ml: Taxi / Carro (Normal y Detallado)
    #   - 80 ml: Camioneta (Normal y Detallado) / Cuatrimoto / Can-Am
    # Cera líquida:
    #   - 30 ml: Servicios Normales / Taxi
    #   - 60 ml: Servicios Detallados / Cuatrimoto / Can-Am
    # Armor-All para llantas:
    #   - 25 ml: Por vehículo en todos los servicios
    
    total_vehiculos_calc = sum(cantidades_finales.values())
    
    shampoo_ml = 0
    cera_ml = 0
    armor_all_ml = 0
    
    for s_name, qty in cantidades_finales.items():
        # Shampoo
        if s_name in ["Taxi", "Carro - Servicio Normal", "Carro - Servicio Detallado"]:
            shampoo_ml += qty * 50
        else:
            shampoo_ml += qty * 80
            
        # Cera Líquida
        if s_name in ["Taxi", "Carro - Servicio Normal", "Camioneta - Servicio Normal"]:
            cera_ml += qty * 30
        else:
            cera_ml += qty * 60
            
        # Armor-All (25 ml por vehículo)
        armor_all_ml += qty * 25
        
    shampoo_litros = shampoo_ml / 1000.0
    cera_litros = cera_ml / 1000.0
    armor_all_litros = armor_all_ml / 1000.0
    
    # Cálculo de personal: 1 lavador atiende hasta 12 vehículos en un turno de 8 horas
    vehiculos_por_dia = total_vehiculos_calc / float(periodo_dias) if periodo_dias > 0 else 0
    # Capacidad de 1 lavador por día = 12 autos
    lavadores_optimos_dia = int(np.ceil(vehiculos_por_dia / 12.0)) if vehiculos_por_dia > 0 else 1
    total_turnos_periodo = int(np.ceil(total_vehiculos_calc / 12.0)) if total_vehiculos_calc > 0 else 1
    
    st.markdown("---")
    st.markdown("### 📦 Resultados Operativos para Surtir Bodega y Programar Turnos")
    
    r_c1, r_c2, r_c3, r_c4 = st.columns(4)
    
    with r_c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🧴 Shampoo Concentrado</div>
            <div class="metric-value">{shampoo_litros:.2f} L</div>
            <div class="metric-sub">💧 {shampoo_ml:,} ml requeridos</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">✨ Cera Líquida</div>
            <div class="metric-value">{cera_litros:.2f} L</div>
            <div class="metric-sub">🌟 {cera_ml:,} ml requeridos</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🛡️ Armor-All (Llantas)</div>
            <div class="metric-value">{armor_all_litros:.2f} L</div>
            <div class="metric-sub">🛞 {armor_all_ml:,} ml requeridos</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r_c4:
        st.markdown(f"""
        <div class="metric-card" style="border-color: rgba(59, 130, 246, 0.5);">
            <div class="metric-label">👷 Lavadores Sugeridos / Día</div>
            <div class="metric-value" style="color: #38bdf8;">{lavadores_optimos_dia} personal</div>
            <div class="metric-sub">⏱️ Capacidad: 12 autos/lavador (8h)</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Desglose analítico en dos columnas
    d_c1, d_c2 = st.columns([1.2, 1])
    
    with d_c1:
        st.markdown("#### 📊 Consumo de Insumos por Categoría de Servicio")
        desglose_data = []
        for s_name, qty in cantidades_finales.items():
            if s_name in ["Taxi", "Carro - Servicio Normal", "Carro - Servicio Detallado"]:
                sh = (qty * 50) / 1000.0
            else:
                sh = (qty * 80) / 1000.0
                
            if s_name in ["Taxi", "Carro - Servicio Normal", "Camioneta - Servicio Normal"]:
                cr = (qty * 30) / 1000.0
            else:
                cr = (qty * 60) / 1000.0
                
            ar = (qty * 25) / 1000.0
            
            desglose_data.append({
                'Servicio': s_name,
                'Cantidad': qty,
                'Shampoo (L)': round(sh, 2),
                'Cera (L)': round(cr, 2),
                'Armor-All (L)': round(ar, 2)
            })
            
        df_desglose = pd.DataFrame(desglose_data)
        
        # Gráfica apilada de insumos en litros por servicio
        fig_insumos = px.bar(
            df_desglose,
            x='Servicio',
            y=['Shampoo (L)', 'Cera (L)', 'Armor-All (L)'],
            title='<b>Consumo Estimado de Químicos por Tipo de Servicio (Litros)</b>',
            barmode='stack',
            template='plotly_dark',
            color_discrete_sequence=['#38bdf8', '#fbbf24', '#a855f7']
        )
        fig_insumos.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            legend=dict(title="Insumo", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=30, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_insumos, use_container_width=True)
        
    with d_c2:
        st.markdown("#### 📋 Resumen Ejecutivo de Operación")
        st.markdown(f"""
        - **Total de Vehículos a Procesar:** `{total_vehiculos_calc:,}`
        - **Demanda Diaria Promedio:** `{vehiculos_por_dia:.1f} vehículos/día`
        - **Turnos Totales de Lavador Requeridos:** `{total_turnos_periodo} turnos de 8 hrs`
        - **Personal en Turno Recomendado:** `{lavadores_optimos_dia} lavadores activos por día`
        - **Margen de Capacidad Instalada:** `{lavadores_optimos_dia * 12} vehículos max/día`
        """)
        
        st.dataframe(
            df_desglose,
            use_container_width=True,
            hide_index=True
        )

# ==========================================
# PÁGINA 5: AVANCE 2: MODELOS ML Y PREPROCESAMIENTO
# ==========================================
elif pagina == "Avance 2: Modelos ML y Preprocesamiento":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">📌 Avance 2: Preprocesamiento y Benchmark de Modelos ML</div>
        <div class="hero-subtitle">Entrenamiento y comparación de modelos de la Unidad 3 (Regresión y Clasificación)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Selector de Enfoque Académico
    st.markdown("### 🔀 Selección de Enfoque y Tipo de Aprendizaje")
    enfoque = st.radio(
        "Selecciona el problema a evaluar:",
        options=[
            "Enfoque 1: Modelos de Series de Tiempo / Regresión (Demanda e Ingresos)",
            "Enfoque 2: Modelos de Clasificación (Naive Bayes, KNN, Árboles, Random Forest)"
        ],
        index=0,
        horizontal=True
    )
    
    st.markdown("---")
    
    # ----------------------------------------------------
    # ENFOQUE 1: REGRESIÓN / SERIES DE TIEMPO
    # ----------------------------------------------------
    if "Enfoque 1" in enfoque:
        st.markdown("### ⚙️ 1. Configuración de Preprocesamiento y Partición de Datos")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            target_reg = st.selectbox(
                "Variable Objetivo:",
                options=['vehiculos', 'ingresos'],
                format_func=lambda x: "🚗 Vehículos Lavados por Día" if x == 'vehiculos' else "💰 Ingresos Diarios ($ MXN)"
            )
        with c2:
            test_ratio = st.slider(
                "Proporción de Partición Train / Test:",
                min_value=0.10,
                max_value=0.40,
                value=0.20,
                step=0.05,
                help="Ej. 0.20 equivale a una división formal 80% Train / 20% Test."
            )
        with c3:
            k_folds = st.slider("Folds de Validación Cruzada (K-Fold):", min_value=3, max_value=10, value=5, step=1)
            
        with st.expander("🛠️ Ver Pipeline de Preprocesamiento e Ingeniería de Características Aplicado", expanded=False):
            st.markdown("""
            * **Imputación de Nulos:** `SimpleImputer` (mediana para numéricas continuas y moda para categóricas).
            * **Estandarización / Escalamiento:** `StandardScaler` aplicado sobre `dia_mes`, `mes`, `es_fin_semana`, `es_quincena`, `media_movil_7d` y `media_movil_14d`.
            * **Codificación Categórica:** `OneHotEncoder(drop='first', sparse_output=False)` aplicado sobre `dia_nombre` (Día de la semana).
            * **Partición de Datos:** `train_test_split` con proporción seleccionada + Validación Cruzada K-Fold ($K={k_folds}$).
            """)
            
        with st.spinner("Entrenando y validando los 5 modelos de regresión..."):
            df_comp_reg, X_test_reg, y_test_reg, trained_reg_pipes = benchmark_regression_models(
                target_col=target_reg, test_size=test_ratio, n_splits=k_folds
            )
            
        # Métricas de Resumen del Mejor Modelo
        best_model_reg = df_comp_reg.iloc[0]
        st.markdown("### 🏆 Algoritmo con Mejor Rendimiento")
        top_c1, top_c2, top_c3, top_c4 = st.columns(4)
        with top_c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Modelo Ganador</div>
                <div class="metric-value" style="font-size: 1.3rem;">{best_model_reg['Algoritmo']}</div>
                <div class="metric-sub">Familia: {best_model_reg['Familia']}</div>
            </div>
            """, unsafe_allow_html=True)
        with top_c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">R² Score (Test)</div>
                <div class="metric-value">{best_model_reg['R² Score']:.4f}</div>
                <div class="metric-sub">Varianza explicada</div>
            </div>
            """, unsafe_allow_html=True)
        with top_c3:
            unit_str = "autos" if target_reg == 'vehiculos' else "$ MXN"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">MAE (Error Medio)</div>
                <div class="metric-value">{best_model_reg['MAE']} {unit_str}</div>
                <div class="metric-sub">Desviación promedio</div>
            </div>
            """, unsafe_allow_html=True)
        with top_c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">RMSE (Raíz Error Cuadrático)</div>
                <div class="metric-value">{best_model_reg['RMSE']} {unit_str}</div>
                <div class="metric-sub">Penalización de atípicos</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabla Comparativa de Rendimiento Preliminar
        st.markdown("### 📊 4. Tabla Comparativa de Rendimiento Preliminar")
        st.dataframe(
            df_comp_reg,
            use_container_width=True,
            hide_index=True,
            column_config={
                "R² Score": st.column_config.NumberColumn(format="%.4f"),
                "MAE": st.column_config.NumberColumn(format="%.2f"),
                "RMSE": st.column_config.NumberColumn(format="%.2f"),
                "K-Fold CV R² (Promedio)": st.column_config.NumberColumn(format="%.4f")
            }
        )
        
        # Gráfica de calificación porcentual fácil de entender (0 a 100%)
        df_comp_reg_show = df_comp_reg.copy()
        df_comp_reg_show['Certeza del Modelo (%)'] = (df_comp_reg_show['R² Score'] * 100).round(1)
        
        fig_comp = px.bar(
            df_comp_reg_show,
            x='Algoritmo',
            y='Certeza del Modelo (%)',
            text='Certeza del Modelo (%)',
            title='<b>🎯 ¿Qué tan certero y confiable es cada modelo matemático? (Calificación de 0 a 100%)</b>',
            template='plotly_dark',
            color='Certeza del Modelo (%)',
            color_continuous_scale='Blues'
        )
        fig_comp.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside',
            hovertemplate='%{x}<br>Calificación: %{y:.1f}% de certeza<extra></extra>'
        )
        fig_comp.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            yaxis=dict(range=[0, 105]),
            showlegend=False,
            margin=dict(l=30, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        st.caption("💡 Entre más alta esté la barra, más exacta y confiable es la estimación que hace ese modelo.")
        
    # ----------------------------------------------------
    # ENFOQUE 2: CLASIFICACIÓN (UNIDAD 3)
    # ----------------------------------------------------
    else:
        st.markdown("### ⚙️ 1. Configuración de Preprocesamiento y Partición (Clasificación)")
        st.caption("Objetivo: Clasificar si un ticket corresponde a Servicio Detallado / Especial (1) o Servicio Normal / Taxi (0).")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            sample_reg = st.select_slider(
                "Muestra de Datos para Entrenamiento Rápido:",
                options=[10000, 25000, 50000],
                value=25000,
                format_func=lambda x: f"{x:,} registros"
            )
        with c2:
            test_clf_ratio = st.slider(
                "División Train/Test:",
                min_value=0.10,
                max_value=0.40,
                value=0.20,
                step=0.05,
                key="slider_clf_split"
            )
            
        with st.expander("🛠️ Preprocesamiento e Ingeniería de Características Aplicada", expanded=False):
            st.markdown("""
            * **Imputación de Nulos:** `SimpleImputer` (media en numéricas, moda en categóricas).
            * **Estandarización / Escalamiento:** `StandardScaler` en `hora_num`, `precio` y `es_fin_semana`.
            * **Codificación Categórica:** `OneHotEncoder(drop='first')` en `dia_semana`.
            * **Partición Estratificada:** `train_test_split(stratify=y, test_size=...)` para conservar proporciones de clases.
            * **Validación Cruzada:** 5-Fold Cross Validation evaluando `F1-Score`.
            """)
            
        with st.spinner("Entrenando modelos de la Unidad 3: Naive Bayes, KNN, Árbol de Decisión y Random Forest..."):
            df_comp_clf, X_test_clf, y_test_clf = benchmark_classification_models(
                sample_size=sample_reg, test_size=test_clf_ratio
            )
            
        best_clf = df_comp_clf.iloc[0]
        st.markdown("### 🏆 Modelo Clasificador Más Óptimo")
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Mejor Algoritmo</div>
                <div class="metric-value" style="font-size: 1.25rem;">{best_clf['Algoritmo']}</div>
                <div class="metric-sub">Mayor F1-Score</div>
            </div>
            """, unsafe_allow_html=True)
        with b2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Accuracy</div>
                <div class="metric-value">{best_clf['Accuracy'] * 100:.2f}%</div>
                <div class="metric-sub">Exactitud global</div>
            </div>
            """, unsafe_allow_html=True)
        with b3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Precision</div>
                <div class="metric-value">{best_clf['Precision'] * 100:.2f}%</div>
                <div class="metric-sub">Fiabilidad de positivos</div>
            </div>
            """, unsafe_allow_html=True)
        with b4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Recall / Sensibilidad</div>
                <div class="metric-value">{best_clf['Recall'] * 100:.2f}%</div>
                <div class="metric-sub">Detección de clase positiva</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabla Comparativa de Rendimiento Preliminar
        st.markdown("### 📊 4. Tabla Comparativa de Rendimiento Preliminar")
        st.dataframe(
            df_comp_clf,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Accuracy": st.column_config.NumberColumn(format="%.4f"),
                "Precision": st.column_config.NumberColumn(format="%.4f"),
                "Recall": st.column_config.NumberColumn(format="%.4f"),
                "F1-Score": st.column_config.NumberColumn(format="%.4f"),
                "K-Fold CV F1 (Promedio)": st.column_config.NumberColumn(format="%.4f")
            }
        )
        
        # Gráfica de porcentaje de aciertos fácil de entender
        df_comp_clf_show = df_comp_clf.copy()
        df_comp_clf_show['Porcentaje de Aciertos (%)'] = (df_comp_clf_show['Accuracy'] * 100).round(1)
        
        fig_clf = px.bar(
            df_comp_clf_show,
            x='Algoritmo',
            y='Porcentaje de Aciertos (%)',
            text='Porcentaje de Aciertos (%)',
            title='<b>🎯 Porcentaje de Aciertos de Cada Modelo (¿Qué tan bien adivinan?)</b>',
            template='plotly_dark',
            color='Porcentaje de Aciertos (%)',
            color_continuous_scale='Greens'
        )
        fig_clf.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside',
            hovertemplate='%{x}<br>Acierto general: %{y:.1f}% de las veces<extra></extra>'
        )
        fig_clf.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            yaxis=dict(range=[0, 110]),
            showlegend=False,
            margin=dict(l=30, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_clf, use_container_width=True)
        st.caption("💡 Si un modelo tiene 85%, significa que de cada 100 clientes que llegan, adivina correctamente lo que van a pedir en 85 ocasiones.")

# ==========================================
# PÁGINA 6: ENTREGABLE 3: MICROSERVICIOS Y SERIES DE TIEMPO (ARIMA/SARIMA)
# ==========================================
elif pagina == "Entregable 3: Microservicios y Series de Tiempo (ARIMA/SARIMA)":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🚀 Entregable 3: Microservicios, ARIMA / SARIMA e Inferencia Cloud</div>
        <div class="hero-subtitle">Integración con endpoints REST (/pronostico y /clasificar), matrices de confusión y bandas de confianza al 95%</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_e3_1, tab_e3_2, tab_e3_3 = st.tabs([
        "📈 Pronóstico SARIMA e Intervalos de Confianza",
        "🎯 Matriz de Confusión de Clasificadores",
        "☁️ Arquitectura Cloud y Microservicios E3"
    ])
    
    with tab_e3_1:
        st.markdown("### 🔮 Pronóstico Avanzado de Demanda con SARIMAX(1,1,1)x(1,0,1,7)")
        st.caption("Consumo directo del microservicio analítico `services/modelos` con cálculo matemático de límites al 95% de confianza.")
        
        c_p1, c_p2 = st.columns([1, 2])
        with c_p1:
            dias_sarima = st.slider("Días a Pronosticar:", min_value=7, max_value=30, value=14, step=1, key="slider_sarima_steps")
            st.markdown("""
            **Justificación de Parámetros Estadísticos:**
            - **Orden no estacional $(p=1, d=1, q=1)$:**
              - $d=1$: Diferenciación simple tras prueba ADF estacionaria ($p < 0.05$).
              - $p=1, q=1$: Rezagos autorregresivos y de media móvil identificados en PACF y ACF.
            - **Orden estacional $(P=1, D=0, Q=1, s=7)$:**
              - Periodicidad semanal ($s=7$) confirmada por picos cíclicos de fin de semana.
            - **Criterio de Información:**
              - $\\text{AIC} = 2,637.01$ (óptimo frente a modelos no estacionales).
            """)
            
        with c_p2:
            # Invocar localmente o vía endpoint
            with st.spinner("Calculando inferencia SARIMA con bandas de confianza..."):
                conn = get_connection()
                df_ventas_s = pd.read_sql_query("SELECT fecha, precio FROM ventas;", conn)
                conn.close()
                df_ventas_s['fecha'] = pd.to_datetime(df_ventas_s['fecha'])
                daily_s = df_ventas_s.groupby('fecha').agg(vehiculos=('precio', 'count')).reset_index().sort_values('fecha')
                daily_s = daily_s.set_index('fecha').asfreq('D', fill_value=0)
                
                from statsmodels.tsa.statespace.sarimax import SARIMAX
                model_s = SARIMAX(daily_s['vehiculos'][-365:], order=(1,1,1), seasonal_order=(1,0,1,7))
                fit_s = model_s.fit(disp=False)
                fc_s = fit_s.get_forecast(steps=dias_sarima)
                pred_s_mean = fc_s.predicted_mean
                conf_s_int = fc_s.conf_int(alpha=0.05)
                
                df_sarima_res = pd.DataFrame({
                    'fecha': pred_s_mean.index,
                    'prediccion': np.maximum(0.0, pred_s_mean.values).round(1),
                    'lim_inf': np.maximum(0.0, conf_s_int.iloc[:, 0].values).round(1),
                    'lim_sup': np.maximum(0.0, conf_s_int.iloc[:, 1].values).round(1)
                })
                
                # Gráfica clara con banda normal de variación
                fig_band = go.Figure()
                
                # Últimos 30 días reales
                recent_s = daily_s.tail(30).reset_index()
                fig_band.add_trace(go.Scatter(
                    x=recent_s['fecha'],
                    y=recent_s['vehiculos'],
                    mode='lines+markers',
                    name='Autos reales de días anteriores',
                    line=dict(color='#38bdf8', width=2.5),
                    marker=dict(size=5),
                    hovertemplate='%{x|%d/%m/%Y}<br>Real: %{y} autos<extra></extra>'
                ))
                
                # Banda superior e inferior
                fig_band.add_trace(go.Scatter(
                    x=df_sarima_res['fecha'],
                    y=df_sarima_res['lim_sup'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    name='Máximo esperado',
                    hovertemplate='Máximo esperado: %{y} autos en día lleno<extra></extra>'
                ))
                fig_band.add_trace(go.Scatter(
                    x=df_sarima_res['fecha'],
                    y=df_sarima_res['lim_inf'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(251, 191, 36, 0.2)',
                    name='Margen normal (mínimo a máximo)',
                    hovertemplate='Mínimo esperado: %{y} autos en día flojo<extra></extra>'
                ))
                
                # Línea central de predicción
                fig_band.add_trace(go.Scatter(
                    x=df_sarima_res['fecha'],
                    y=df_sarima_res['prediccion'],
                    mode='lines+markers',
                    line=dict(color='#f59e0b', width=3),
                    marker=dict(size=7, color='#fbbf24'),
                    name='Pronóstico más probable',
                    hovertemplate='%{x|%d/%m/%Y}<br>Esperado: %{y} autos<extra></extra>'
                ))
                
                fig_band.update_layout(
                    title=f"<b>📅 Pronóstico Diario para los Próximos {dias_sarima} Días (Con Margen Esperado)</b>",
                    xaxis_title="Fecha",
                    yaxis_title="Autos que se esperan por día",
                    template='plotly_dark',
                    paper_bgcolor='rgba(15, 23, 42, 0.6)',
                    plot_bgcolor='rgba(15, 23, 42, 0.6)',
                    margin=dict(l=30, r=20, t=50, b=30),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_band, use_container_width=True)
                st.caption("💡 La línea naranja indica cuántos autos es casi seguro que lleguen cada día. La zona dorada sombreada muestra el margen normal entre un día flojo y un día muy concurrido.")
                
        st.markdown("#### 📋 Detalle de la Banda de Confianza y Pronóstico Diario")
        st.dataframe(
            df_sarima_res.rename(columns={
                'fecha': 'Fecha',
                'prediccion': 'Vehículos Estimados',
                'lim_inf': 'Límite Inferior (95% Confianza)',
                'lim_sup': 'Límite Superior (95% Confianza)'
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_e3_2:
        st.markdown("### 🎯 Matrices de Confusión de los Modelos Clasificadores")
        st.caption("Evaluación de aciertos y falsos positivos/negativos en la detección de servicios detallados/especiales.")
        
        # Calcular matriz de confusión para los 4 modelos
        with st.spinner("Generando matrices de confusión..."):
            conn = get_connection()
            df_clf_m = pd.read_sql_query("SELECT dia_semana, hora, tipo_servicio, precio FROM ventas LIMIT 20000;", conn)
            conn.close()
            
            def parse_h_m(h):
                try: return int(str(h).split(':')[0])
                except Exception: return 12
                
            df_clf_m['hora_num'] = df_clf_m['hora'].apply(parse_h_m)
            df_clf_m['es_fin_semana'] = df_clf_m['dia_semana'].isin(['Viernes', 'Sábado', 'Sabado', 'Domingo']).astype(int)
            df_clf_m['target_detallado'] = df_clf_m['tipo_servicio'].str.contains('Detallado|Cuatrimoto|Can-Am').astype(int)
            
            X_m = df_clf_m[['hora_num', 'precio', 'es_fin_semana', 'dia_semana']]
            y_m = df_clf_m['target_detallado']
            
            pre_m = ColumnTransformer([
                ('num', Pipeline([('imputer', SimpleImputer(strategy='mean')), ('scaler', StandardScaler())]), ['hora_num', 'precio', 'es_fin_semana']),
                ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('encoder', OneHotEncoder(drop='first', sparse_output=False))]), ['dia_semana'])
            ])
            
            X_tr_m, X_te_m, y_tr_m, y_te_m = train_test_split(X_m, y_m, test_size=0.20, random_state=42, stratify=y_m)
            
            clfs_m = {
                'Árbol de Decisión': DecisionTreeClassifier(max_depth=6, random_state=42),
                'KNN (Vecinos Cercanos)': KNeighborsClassifier(n_neighbors=7),
                'Random Forest': RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42),
                'Naive Bayes': GaussianNB()
            }
            
            cols_conf = st.columns(4)
            for idx_c, (c_name, c_inst) in enumerate(clfs_m.items()):
                pipe_c = Pipeline([('prep', pre_m), ('model', c_inst)])
                pipe_c.fit(X_tr_m, y_tr_m)
                preds_c = pipe_c.predict(X_te_m)
                cm = confusion_matrix(y_te_m, preds_c)
                
                with cols_conf[idx_c]:
                    fig_cm = px.imshow(
                        cm,
                        text_auto=True,
                        labels=dict(x="Lo que predijo el modelo", y="Lo que el cliente pidió realmente", color="Clientes"),
                        x=['Pidió Normal', 'Pidió Detallado'],
                        y=['Era Normal', 'Era Detallado'],
                        title=f"<b>🎯 Aciertos de {c_name}</b>",
                        color_continuous_scale='Blues',
                        template='plotly_dark'
                    )
                    fig_cm.update_layout(
                        paper_bgcolor='rgba(15, 23, 42, 0.6)',
                        plot_bgcolor='rgba(15, 23, 42, 0.6)',
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_cm, use_container_width=True)
                    st.caption("💡 Casillas oscuras = Aciertos directos.")
                    
    with tab_e3_3:
        st.markdown("### ☁️ Arquitectura de Microservicios, Docker, Kubernetes y Terraform (E3)")
        
        st.markdown("""
        #### 📦 1. Desacoplamiento en Microservicios
        - **`services/tablero`:** Frontend interactivo en Streamlit.
        - **`services/modelos`:** API FastAPI para inferencia de Machine Learning y SARIMA (`/pronostico` y `/clasificar`).
        - **`services/ingesta`:** API FastAPI para registro seguro de tickets de caja en SQLite WAL.
        - **`services/worker`:** Proceso asíncrono disparado por eventos para cálculo de cierres diarios y tareas pesadas.
        - **`docker-compose.yml`:** Orquestación multicontenedor local con red aislada y volúmenes compartidos.

        #### ☸️ 2. Manifiestos de Kubernetes (`k8s/`)
        - `k8s/modelos-deployment.yaml`: Deployment con réplicas elásticas, Service ClusterIP y **HorizontalPodAutoscaler (HPA)** al 75% CPU.
        - `k8s/tablero-deployment.yaml`: Deployment con Service tipo LoadBalancer y HPA al 70% CPU.

        #### 🏗️ 3. Infraestructura como Código (`infra/terraform/`)
        - Archivos de Terraform (`main.tf`, `variables.tf`, `outputs.tf`) para provisionar:
          - Bucket S3 de datalake con versionado.
          - Cola SQS de eventos con Dead Letter Queue (DLQ).
          - Roles IAM y políticas de privilegios mínimos para Cloud Run / App Runner.
        - Evidencia formal documentada en `infra/terraform/EVIDENCIA_TERRAFORM.md`.

        #### 🧪 4. Pruebas de Carga con Locust (`tests/`)
        - Script `tests/locustfile.py` simulando **50 usuarios concurrentes**.
        - Reporte formal en `tests/REPORTE_PRUEBA_CARGA_LOCUST.md`: **1,482 peticiones**, **0% errores** y latencia p95 de **118 ms**.

        #### 📄 5. Justificación Técnica CPU vs. GPU (`docs/`)
        - Documento formal en `docs/REPORTE_TECNICO_E3_ARQUITECTURA.md`: demostración de que la inferencia de datos tabulares y SARIMA sobre CPU x86-64 toma menos de 80 ms, reduciendo costos operativos de $400 USD/mes (GPU) a menos de $15 USD/mes (CPU Serverless).
        """)


