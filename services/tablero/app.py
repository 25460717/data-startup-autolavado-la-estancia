import os
import sqlite3
import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

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
    /* Estilos globales */
    .main {
        background-color: #0e1117;
    }
    
    /* Tarjetas de métricas personalizadas */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #38bdf8;
        margin-top: 4px;
    }
    
    /* Header estilizado */
    .hero-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #0284c7 100%);
        padding: 24px 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        opacity: 0.9;
        margin-top: 4px;
    }

    /* Botones POS y controles */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
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
    {"tipo": "Taxi", "precio": 70, "icono": "🚕", "desc": "Lavado básico servicio público"},
    {"tipo": "Carro - Servicio Normal", "precio": 90, "icono": "🚗", "desc": "Exterior + aspirado interior estándar"},
    {"tipo": "Carro - Servicio Detallado", "precio": 110, "icono": "✨", "desc": "Cera líquida + llantas + aromatizante"},
    {"tipo": "Camioneta - Servicio Normal", "precio": 110, "icono": "🚙", "desc": "Lavado completo para SUV/Pick-up"},
    {"tipo": "Camioneta - Servicio Detallado", "precio": 130, "icono": "🌟", "desc": "Detallado premium para SUV/Pick-up"},
    {"tipo": "Cuatrimoto", "precio": 350, "icono": "🏍️", "desc": "Desengrase profundo y lavado todoterreno"},
    {"tipo": "Can-Am", "precio": 400, "icono": "🚜", "desc": "Lavado exhaustivo alta demanda Off-Road"}
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
# NAVEGACIÓN LATERAL
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3202/3202926.png", width=75)
    st.markdown("## **Autolavado Expréss**\n*La Estancia*")
    st.markdown("---")
    
    pagina = st.radio(
        "Menú Principal",
        [
            "Registro de Ventas (Caja POS)",
            "Dashboard Analítico Histórico",
            "Predicción de Demanda e Ingresos (Machine Learning)",
            "Calculadora de Insumos y Turnos de Personal"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    <div style='background-color: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; font-size: 0.8rem; color: #94a3b8;'>
        <strong>📍 Sucursal:</strong> La Estancia<br>
        <strong>⚡ Base de Datos:</strong> SQLite WAL<br>
        <strong>🤖 ML Engine:</strong> Scikit-Learn RF<br>
        <strong>🟢 Sistema:</strong> Operativo
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# PÁGINA 1: REGISTRO DE VENTAS (CAJA POS)
# ==========================================
if pagina == "Registro de Ventas (Caja POS)":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">⚡ Punto de Venta Express</div>
        <div class="hero-subtitle">Registro instantáneo de servicios de lavado y control de caja en vivo</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛒 Registrar Servicio al Instante")
    st.caption("Selecciona el tipo de servicio para emitir el ticket consecutivo y guardarlo automáticamente en la base de datos.")
    
    col_grid1, col_grid2, col_grid3, col_grid4 = st.columns(4)
    cols = [col_grid1, col_grid2, col_grid3, col_grid4]
    
    for idx, item in enumerate(CATALOGO_SERVICIOS):
        with cols[idx % 4]:
            with st.container(border=True):
                st.markdown(f"#### {item['icono']} {item['tipo']}")
                st.markdown(f"<div style='font-size: 1.5rem; font-weight: 800; color: #38bdf8; margin-bottom: 4px;'>${item['precio']} <span style='font-size: 0.85rem; color: #94a3b8;'>MXN</span></div>", unsafe_allow_html=True)
                st.caption(item['desc'])
                if st.button(f"Cobrar ${item['precio']}", key=f"btn_pos_{idx}", use_container_width=True, type="primary" if "Detallado" in item['tipo'] else "secondary"):
                    tkt_id, f_val, h_val = registrar_venta(item['tipo'], item['precio'])
                    st.toast(f"✅ ¡Ticket {tkt_id} registrado con éxito! (${item['precio']} MXN)", icon="🎉")
                    st.success(f"**Ticket Emitido Exitosamente:** `{tkt_id}` | Servicio: **{item['tipo']}** | Monto: **${item['precio']} MXN** | Hora: **{h_val}**")
    
    st.markdown("---")
    
    df_hoy = get_ventas_hoy()
    total_lavados_hoy = len(df_hoy)
    total_ingresos_hoy = df_hoy['precio'].sum() if not df_hoy.empty else 0.0
    servicio_top_hoy = df_hoy['tipo_servicio'].mode()[0] if not df_hoy.empty else "Sin ventas aún"
    
    st.markdown("### 📊 Métricas del Día en Vivo")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Autos Lavados Hoy</div>
            <div class="metric-value">{total_lavados_hoy:,}</div>
            <div class="metric-sub">📅 Fecha: {datetime.date.today().strftime('%d/%m/%Y')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Ingresos del Día</div>
            <div class="metric-value">${total_ingresos_hoy:,.2f}</div>
            <div class="metric-sub">💳 Recaudación acumulada</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Servicio Más Pedido Hoy</div>
            <div class="metric-value" style="font-size: 1.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{servicio_top_hoy}">{servicio_top_hoy}</div>
            <div class="metric-sub">⭐ Preferencia de clientes</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### 📋 Tickets Registrados Hoy")
    if not df_hoy.empty:
        df_display = df_hoy.rename(columns={
            'id_ticket': 'ID Ticket',
            'fecha': 'Fecha',
            'dia_semana': 'Día',
            'hora': 'Hora',
            'tipo_servicio': 'Servicio / Vehículo',
            'precio': 'Precio ($ MXN)'
        })
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Precio ($ MXN)": st.column_config.NumberColumn(format="$%.2f")
            }
        )
    else:
        st.info("ℹ️ No hay tickets registrados el día de hoy todavía. Utiliza los botones superiores para registrar el primer servicio.")

# ==========================================
# PÁGINA 2: DASHBOARD ANALÍTICO HISTÓRICO
# ==========================================
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
        fig_evolucion = px.line(
            monthly_revenue,
            x='year_month',
            y='precio',
            title='<b>Evolución de Ingresos Mensuales Históricos</b>',
            labels={'year_month': 'Mes y Año', 'precio': 'Ingresos ($ MXN)'},
            template='plotly_dark'
        )
        fig_evolucion.update_traces(
            line=dict(color='#38bdf8', width=3),
            mode='lines+markers',
            marker=dict(size=4)
        )
        fig_evolucion.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            hovermode='x unified',
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_evolucion, use_container_width=True)
        
    with row1_c2:
        day_counts = filtered_df['dia_semana'].value_counts().reindex(dias_ordenados, fill_value=0).reset_index()
        day_counts.columns = ['dia_semana', 'total_vehiculos']
        
        fig_barras_dia = px.bar(
            day_counts,
            x='dia_semana',
            y='total_vehiculos',
            title='<b>Afluencia de Vehículos por Día de la Semana</b>',
            labels={'dia_semana': 'Día', 'total_vehiculos': 'Total de Vehículos'},
            text='total_vehiculos',
            template='plotly_dark',
            color='total_vehiculos',
            color_continuous_scale='Blues'
        )
        fig_barras_dia.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_barras_dia.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            showlegend=False,
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_barras_dia, use_container_width=True)
        
    row2_c1, row2_c2 = st.columns([1.3, 1])
    
    with row2_c1:
        heatmap_data = filtered_df.pivot_table(
            index='dia_semana',
            columns='hora_num',
            values='id_ticket',
            aggfunc='count',
            fill_value=0
        )
        heatmap_data = heatmap_data.reindex(dias_ordenados, fill_value=0)
        all_hours = sorted(heatmap_data.columns)
        
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Hora del Día (Formato 24h)", y="Día de la Semana", color="Vehículos"),
            x=[f"{h:02d}:00" for h in all_hours],
            y=dias_ordenados,
            title='<b>Mapa de Calor de Horas Pico (Día vs. Hora del Día)</b>',
            color_continuous_scale='Turbo',
            template='plotly_dark',
            aspect='auto'
        )
        fig_heatmap.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
    with row2_c2:
        servicio_revenue = filtered_df.groupby('tipo_servicio')['precio'].sum().reset_index()
        fig_pie = px.pie(
            servicio_revenue,
            names='tipo_servicio',
            values='precio',
            title='<b>Participación de Ingresos por Tipo de Vehículo</b>',
            hole=0.45,
            template='plotly_dark',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}: $%{value:,.2f} MXN (%{percent})'
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0.6)',
            plot_bgcolor='rgba(15, 23, 42, 0.6)',
            showlegend=False,
            margin=dict(l=20, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

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
    
    # Crear figura combinada
    fig_ml = go.Figure()
    
    # Serie Real Histórica (últimos 30 días)
    fig_ml.add_trace(go.Scatter(
        x=recent_real['fecha'],
        y=recent_real[target_mode],
        mode='lines+markers',
        name='Demanda Real (Últimos 30 días)',
        line=dict(color='#0284c7', width=3),
        marker=dict(size=6, color='#38bdf8'),
        hovertemplate='%{x|%d/%m/%Y}<br>Real: %{y:.1f}'
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
        name=f'Pronóstico ML (+{dias_pronostico} días)',
        line=dict(color='#f59e0b', width=3, dash='dash'),
        marker=dict(size=7, color='#fbbf24'),
        hovertemplate='%{x|%d/%m/%Y}<br>Pronóstico: %{y:.1f}'
    ))
    
    fig_ml.update_layout(
        title=f"<b>Demanda Real Reciente y Pronóstico a {dias_pronostico} Días ({'Vehículos' if target_mode == 'vehiculos' else 'Ingresos $ MXN'})</b>",
        xaxis_title="Fecha",
        yaxis_title="Cantidad de Vehículos" if target_mode == "vehiculos" else "Ingresos ($ MXN)",
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.6)',
        plot_bgcolor='rgba(15, 23, 42, 0.6)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=30, t=60, b=40)
    )
    st.plotly_chart(fig_ml, use_container_width=True)
    
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
