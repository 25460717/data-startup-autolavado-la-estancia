import os
import sqlite3
import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

    /* Botones POS */
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
SERVICES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVICES_DIR.parent.parent
DB_PATH = SERVICES_DIR / "autolavado.db"

EXCEL_CANDIDATES = [
    PROJECT_ROOT / "notebooks" / "Registro_Ventas_Autolavado_v3 (1).xlsx",
    PROJECT_ROOT / "notebooks" / "Registro_Ventas_Autolavado_v3.xlsx",
    Path("notebooks/Registro_Ventas_Autolavado_v3 (1).xlsx"),
    Path("C:/Users/josea/data-startup-autolavado-la-estancia/notebooks/Registro_Ventas_Autolavado_v3 (1).xlsx"),
    Path("C:/Users/josea/Documents/Registro_Ventas_Autolavado_v3 (1).xlsx"),
    Path("C:/Users/josea/Downloads/Registro_Ventas_Autolavado_v3 (1).xlsx")
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
    """Retorna una conexión a SQLite optimizada."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@st.cache_resource(show_spinner=False)
def initialize_database():
    """Inicializa la base de datos importando el Excel histórico si aún no existe."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla si no existe
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
    
    # Verificar si ya cuenta con registros
    cursor.execute("SELECT COUNT(*) FROM ventas;")
    count = cursor.fetchone()[0]
    
    if count == 0:
        excel_found = None
        for candidate in EXCEL_CANDIDATES:
            if candidate.exists():
                excel_found = candidate
                break
                
        if excel_found:
            with st.spinner(f"Inicializando base de datos desde {excel_found.name} (103k+ registros)..."):
                # Leer excel saltando 2 filas de título, encabezados en fila 3 (índice 0-based -> skiprows=3)
                df_excel = pd.read_excel(excel_found, skiprows=3)
                df_excel.columns = [c.strip() for c in df_excel.columns]
                
                # Mapeo y limpieza de datos
                col_map = {
                    'ID Ticket': 'id_ticket',
                    'Fecha': 'fecha',
                    'Día de la Semana': 'dia_semana',
                    'Hora': 'hora',
                    'Tipo de Vehículo / Servicio': 'tipo_servicio',
                    'Precio ($)': 'precio'
                }
                df_clean = df_excel[list(col_map.keys())].rename(columns=col_map)
                
                # Normalización de tipos
                df_clean['id_ticket'] = df_clean['id_ticket'].astype(str).str.strip()
                df_clean['fecha'] = pd.to_datetime(df_clean['fecha']).dt.strftime('%Y-%m-%d')
                df_clean['dia_semana'] = df_clean['dia_semana'].astype(str).str.strip()
                df_clean['hora'] = df_clean['hora'].astype(str).str.strip()
                df_clean['tipo_servicio'] = df_clean['tipo_servicio'].astype(str).str.strip()
                df_clean['precio'] = pd.to_numeric(df_clean['precio'], errors='coerce').fillna(0.0)
                
                # Inserción masiva eficiente
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
        # Respaldo en caso de formato no estándar
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
    
    # Extraer hora entera para mapas de calor
    def parse_hour(h_val):
        try:
            return int(str(h_val).split(":")[0])
        except Exception:
            return 12
    df['hora_num'] = df['hora'].apply(parse_hour)
    return df

# ==========================================
# NAVEGACIÓN LATERAL
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3202/3202926.png", width=75)
    st.markdown("## **Autolavado Expréss**\n*La Estancia*")
    st.markdown("---")
    
    pagina = st.radio(
        "Menú Principal",
        ["Registro de Ventas (Caja POS)", "Dashboard Analítico Histórico"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    <div style='background-color: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; font-size: 0.8rem; color: #94a3b8;'>
        <strong>📍 Sucursal:</strong> La Estancia<br>
        <strong>⚡ Base de Datos:</strong> SQLite WAL<br>
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
    
    # Disposición de botones interactivos para los servicios
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
    
    # Consulta de ventas del día actual
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
        
    # -----------------
    # FILTROS DINÁMICOS
    # -----------------
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
            
    # Aplicar filtros
    filtered_df = df_hist.copy()
    
    # Filtro por rango de fechas
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df = filtered_df[(filtered_df['fecha'].dt.date >= start_d) & (filtered_df['fecha'].dt.date <= end_d)]
        
    # Filtro por años
    if selected_years:
        filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]
        
    # Filtro por tipos de vehículo
    if selected_services:
        filtered_df = filtered_df[filtered_df['tipo_servicio'].isin(selected_services)]
        
    if filtered_df.empty:
        st.warning("No hay registros que coincidan con los filtros seleccionados. Intenta ampliar el rango de búsqueda.")
        st.stop()
        
    # -----------------
    # 4 TARJETAS KPIS PRINCIPALES
    # -----------------
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
    
    # -----------------
    # GRÁFICAS INTERACTIVAS PLOTLY
    # -----------------
    dias_ordenados = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    # Fila 1 de Gráficas: Evolución Mensual & Afluencia por Día
    row1_c1, row1_c2 = st.columns([1.4, 1])
    
    with row1_c1:
        # Evolución de ingresos mensuales a lo largo de los 6 años
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
        # Barras con afluencia de vehículos por día de la semana (Lunes a Domingo)
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
        
    # Fila 2 de Gráficas: Heatmap (Día vs Hora) & Gráfica de Dona de Ingresos
    row2_c1, row2_c2 = st.columns([1.3, 1])
    
    with row2_c1:
        # Mapa de Calor: Día de la Semana vs. Hora del día (Horas pico)
        heatmap_data = filtered_df.pivot_table(
            index='dia_semana',
            columns='hora_num',
            values='id_ticket',
            aggfunc='count',
            fill_value=0
        )
        # Reindexar días y ordenar horas
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
        # Dona con participación de ingresos por tipo de vehículo
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
