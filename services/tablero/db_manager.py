"""
Módulo de Persistencia y Base de Datos - Autolavado Expréss La Estancia
Soporta persistencia en la nube mediante Supabase (PostgreSQL / REST)
con respaldo automático y fallback a SQLite local si no hay credenciales en st.secrets.
"""

import os
import sqlite3
import datetime
import json
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import requests
import streamlit as st

# Rutas locales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "autolavado.db")

DIAS_SEMANA_MAP = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}

def get_sqlite_connection():
    """Retorna conexión a la base SQLite local con modo WAL activado."""
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def get_cloud_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Detecta credenciales de Supabase en st.secrets o variables de entorno.
    Busca SUPABASE_URL y SUPABASE_KEY.
    """
    supabase_url = None
    supabase_key = None
    
    # 1. Intentar desde st.secrets
    try:
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
                supabase_url = st.secrets["SUPABASE_URL"]
                supabase_key = st.secrets["SUPABASE_KEY"]
            elif "supabase" in st.secrets:
                sec = st.secrets["supabase"]
                supabase_url = sec.get("url") or sec.get("SUPABASE_URL")
                supabase_key = sec.get("key") or sec.get("SUPABASE_KEY")
    except Exception:
        pass
        
    # 2. Intentar desde variables de entorno
    if not supabase_url:
        supabase_url = os.environ.get("SUPABASE_URL")
    if not supabase_key:
        supabase_key = os.environ.get("SUPABASE_KEY")
        
    if supabase_url and supabase_key:
        supabase_url = supabase_url.rstrip("/")
        return supabase_url, supabase_key
    return None, None

def is_cloud_enabled() -> bool:
    """Verifica si las credenciales de nube están disponibles."""
    url, key = get_cloud_credentials()
    return bool(url and key)

def get_db_status() -> Dict[str, Any]:
    """Retorna el estado de la conexión a la base de datos."""
    url, key = get_cloud_credentials()
    if url and key:
        try:
            # Probar ping rápido a Supabase REST
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}"
            }
            res = requests.get(f"{url}/rest/v1/tickets?select=count", headers=headers, timeout=4)
            if res.status_code in (200, 206):
                return {
                    "is_cloud": True,
                    "engine": "Supabase Cloud (PostgreSQL)",
                    "icon": "🟢",
                    "badge_color": "#22c55e",
                    "status_label": "Nube Supabase Conectada",
                    "description": "Persistencia en tiempo real activa en PostgreSQL (Nube). No se perderán datos al reiniciar Streamlit.",
                    "cloud_url": url
                }
            else:
                return {
                    "is_cloud": False,
                    "engine": "SQLite Local (Fallback por error en Nube)",
                    "icon": "🟠",
                    "badge_color": "#f97316",
                    "status_label": "Alerta Nube (Usando SQLite)",
                    "description": f"Error de autenticación o tabla no encontrada en Supabase (Código HTTP {res.status_code}). Guardando localmente en SQLite.",
                    "cloud_url": url
                }
        except Exception as e:
            return {
                "is_cloud": False,
                "engine": "SQLite Local (Sin conexión a Nube)",
                "icon": "🟠",
                "badge_color": "#f97316",
                "status_label": "Nube Inalcanzable (Usando SQLite)",
                "description": f"No se pudo conectar a Supabase ({str(e)[:60]}...). Operando en modo local seguro.",
                "cloud_url": url
            }
    
    return {
        "is_cloud": False,
        "engine": "SQLite Local (Modo Respaldo)",
        "icon": "🟡",
        "badge_color": "#eab308",
        "status_label": "Respaldo Local SQLite",
        "description": "Operando con autolavado.db en disco local. Para persistencia permanente en la nube al apagar Streamlit, configura SUPABASE_URL y SUPABASE_KEY en st.secrets.",
        "cloud_url": None
    }

def init_tables():
    """Inicializa y asegura la estructura de tablas tanto en SQLite como en Nube."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # 1. Tabla ventas (histórica)
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
    
    # Migrar columnas nuevas a ventas si no existen
    cursor.execute("PRAGMA table_info(ventas)")
    cols_existentes = {row[1] for row in cursor.fetchall()}
    columnas_a_agregar = [
        ("folio", "TEXT DEFAULT ''"),
        ("fecha_hora", "TEXT DEFAULT ''"),
        ("fecha_operativa", "TEXT DEFAULT ''"),
        ("servicio", "TEXT DEFAULT ''"),
        ("categoria_vehiculo", "TEXT DEFAULT ''"),
        ("precio_mxn", "REAL DEFAULT 0.0"),
        ("metodo_pago", "TEXT DEFAULT 'Efectivo'"),
        ("estado", "TEXT DEFAULT 'Pagado'"),
        ("notas_placa", "TEXT DEFAULT ''"),
        ("motivo_cancelacion", "TEXT DEFAULT ''")
    ]
    for col_name, col_type in columnas_a_agregar:
        if col_name not in cols_existentes:
            try:
                cursor.execute(f"ALTER TABLE ventas ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass
                
    # 2. Tabla tickets formal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            fecha_hora TEXT NOT NULL,
            fecha_operativa TEXT NOT NULL,
            servicio TEXT NOT NULL,
            categoria_vehiculo TEXT NOT NULL,
            precio_mxn REAL NOT NULL,
            metodo_pago TEXT NOT NULL DEFAULT 'Efectivo',
            estado TEXT NOT NULL DEFAULT 'Pagado',
            notas_placa TEXT DEFAULT '',
            motivo_cancelacion TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_fecha_op ON tickets(fecha_operativa);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_folio ON tickets(folio);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_estado ON tickets(estado);")
    
    conn.commit()
    conn.close()

def get_next_folio() -> str:
    """Genera el siguiente número consecutivo de ticket (Folio)."""
    # Intentar leer desde Supabase si está disponible
    url, key = get_cloud_credentials()
    if url and key:
        try:
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            res = requests.get(f"{url}/rest/v1/tickets?select=folio&order=id.desc&limit=1", headers=headers, timeout=3)
            if res.status_code == 200 and res.json():
                ultimo_folio = res.json()[0]["folio"]
                num_part = int(str(ultimo_folio).split("-")[1])
                return f"TKT-{num_part + 1}"
        except Exception:
            pass
            
    # Fallback a SQLite
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Primero revisar tabla tickets
    cursor.execute("SELECT folio FROM tickets ORDER BY id DESC LIMIT 1;")
    row_tkt = cursor.fetchone()
    if row_tkt and row_tkt[0]:
        try:
            num = int(str(row_tkt[0]).split("-")[1])
            conn.close()
            return f"TKT-{num + 1}"
        except Exception:
            pass
            
    # Si no, revisar tabla ventas histórica
    cursor.execute("SELECT id_ticket FROM ventas ORDER BY rowid DESC LIMIT 1;")
    row_v = cursor.fetchone()
    conn.close()
    
    if row_v and row_v[0]:
        try:
            num = int(str(row_v[0]).split("-")[1])
            return f"TKT-{num + 1}"
        except Exception:
            pass
            
    return "TKT-10001"

def registrar_ticket(
    servicio: str,
    categoria_vehiculo: str,
    precio_mxn: float,
    metodo_pago: str = "Efectivo",
    notas_placa: str = ""
) -> Dict[str, Any]:
    """
    Registra un ticket de venta en la base de datos (Nube y/o Local).
    Garantiza autoguardado inmediato.
    """
    ahora = datetime.datetime.now()
    fecha_hora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    fecha_operativa = ahora.strftime("%Y-%m-%d")
    hora_corta = ahora.strftime("%H:%M")
    dia_nombre = DIAS_SEMANA_MAP.get(ahora.weekday(), "Lunes")
    folio = get_next_folio()
    
    ticket_data = {
        "folio": folio,
        "fecha_hora": fecha_hora_str,
        "fecha_operativa": fecha_operativa,
        "servicio": servicio,
        "categoria_vehiculo": categoria_vehiculo,
        "precio_mxn": float(precio_mxn),
        "metodo_pago": metodo_pago,
        "estado": "Pagado",
        "notas_placa": notas_placa.strip() if notas_placa else "",
        "motivo_cancelacion": ""
    }
    
    guardado_nube = False
    error_nube = None
    
    # 1. Guardar en Supabase Cloud si está configurado
    url, key = get_cloud_credentials()
    if url and key:
        try:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            res = requests.post(f"{url}/rest/v1/tickets", headers=headers, json=ticket_data, timeout=5)
            if res.status_code in (200, 201):
                guardado_nube = True
            else:
                error_nube = f"HTTP {res.status_code}: {res.text[:100]}"
        except Exception as e:
            error_nube = str(e)
            
    # 2. Guardar SIEMPRE en SQLite local como respaldo / caché de alta velocidad
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # Insertar en tabla tickets
        cursor.execute("""
            INSERT INTO tickets (folio, fecha_hora, fecha_operativa, servicio, categoria_vehiculo, precio_mxn, metodo_pago, estado, notas_placa, motivo_cancelacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            folio, fecha_hora_str, fecha_operativa, servicio, categoria_vehiculo,
            float(precio_mxn), metodo_pago, "Pagado", notas_placa.strip(), ""
        ))
        
        # Insertar también en tabla ventas para compatibilidad total con modelos ML y analítica previa
        cursor.execute("""
            INSERT INTO ventas (
                id_ticket, fecha, dia_semana, hora, tipo_servicio, precio,
                folio, fecha_hora, fecha_operativa, servicio, categoria_vehiculo,
                precio_mxn, metodo_pago, estado, notas_placa
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            folio, fecha_operativa, dia_nombre, hora_corta, servicio, float(precio_mxn),
            folio, fecha_hora_str, fecha_operativa, servicio, categoria_vehiculo,
            float(precio_mxn), metodo_pago, "Pagado", notas_placa.strip()
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        if not guardado_nube:
            raise RuntimeError(f"Error al guardar ticket: {e}")
            
    ticket_data["guardado_nube"] = guardado_nube
    ticket_data["error_nube"] = error_nube
    return ticket_data

def cancelar_ticket(folio: str, motivo: str) -> bool:
    """
    Cancela un ticket existente cambiando su estado a 'Cancelado' y registrando el motivo.
    No elimina el registro histórico para mantener la auditoría intacta.
    """
    motivo_limpio = motivo.strip() if motivo else "Cancelado por operador de caja"
    actualizado_nube = False
    
    # 1. Actualizar en Supabase Cloud si está activo
    url, key = get_cloud_credentials()
    if url and key:
        try:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            res = requests.patch(
                f"{url}/rest/v1/tickets?folio=eq.{folio}",
                headers=headers,
                json={"estado": "Cancelado", "motivo_cancelacion": motivo_limpio},
                timeout=5
            )
            if res.status_code in (200, 204):
                actualizado_nube = True
        except Exception:
            pass
            
    # 2. Actualizar en SQLite local
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets 
        SET estado = 'Cancelado', motivo_cancelacion = ? 
        WHERE folio = ?;
    """, (motivo_limpio, folio))
    
    cursor.execute("""
        UPDATE ventas 
        SET estado = 'Cancelado', motivo_cancelacion = ? 
        WHERE folio = ? OR id_ticket = ?;
    """, (motivo_limpio, folio, folio))
    
    conn.commit()
    conn.close()
    return True

def get_tickets_dia(fecha_op: Optional[str] = None) -> pd.DataFrame:
    """
    Obtiene todos los tickets de una fecha operativa dada (por defecto hoy).
    Retorna un DataFrame limpio y seguro aunque no haya registros.
    """
    if not fecha_op:
        fecha_op = datetime.date.today().strftime("%Y-%m-%d")
        
    url, key = get_cloud_credentials()
    if url and key:
        try:
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            res = requests.get(
                f"{url}/rest/v1/tickets?fecha_operativa=eq.{fecha_op}&order=id.desc",
                headers=headers,
                timeout=4
            )
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    # Asegurar columnas numéricas
                    df['precio_mxn'] = pd.to_numeric(df['precio_mxn'], errors='coerce').fillna(0.0)
                    return df
        except Exception:
            pass
            
    # Fallback a SQLite
    conn = get_sqlite_connection()
    query = """
        SELECT id, folio, fecha_hora, fecha_operativa, servicio, categoria_vehiculo, 
               precio_mxn, metodo_pago, estado, notas_placa, motivo_cancelacion
        FROM tickets 
        WHERE fecha_operativa = ? 
        ORDER BY id DESC;
    """
    try:
        df = pd.read_sql_query(query, conn, params=(fecha_op,))
    except Exception:
        # Si tickets está vacía o sin registros de hoy, revisar ventas con esa fecha
        query_v = """
            SELECT rowid as id, 
                   COALESCE(NULLIF(folio, ''), id_ticket) as folio,
                   COALESCE(NULLIF(fecha_hora, ''), fecha || ' ' || hora) as fecha_hora,
                   fecha as fecha_operativa,
                   tipo_servicio as servicio,
                   COALESCE(NULLIF(categoria_vehiculo, ''), 'Vehículo') as categoria_vehiculo,
                   precio as precio_mxn,
                   COALESCE(NULLIF(metodo_pago, ''), 'Efectivo') as metodo_pago,
                   COALESCE(NULLIF(estado, ''), 'Pagado') as estado,
                   COALESCE(notas_placa, '') as notas_placa,
                   COALESCE(motivo_cancelacion, '') as motivo_cancelacion
            FROM ventas 
            WHERE fecha = ? 
            ORDER BY rowid DESC;
        """
        df = pd.read_sql_query(query_v, conn, params=(fecha_op,))
    finally:
        conn.close()
        
    if df.empty:
        # Retornar DataFrame con columnas esperadas vacío
        return pd.DataFrame(columns=[
            'id', 'folio', 'fecha_hora', 'fecha_operativa', 'servicio',
            'categoria_vehiculo', 'precio_mxn', 'metodo_pago', 'estado',
            'notas_placa', 'motivo_cancelacion'
        ])
        
    df['precio_mxn'] = pd.to_numeric(df['precio_mxn'], errors='coerce').fillna(0.0)
    return df

def get_corte_resumen(df_tickets: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula el corte de caja con totales netos, desgloses por método de pago y cancelaciones.
    Garantiza que ningún ticket cancelado sume a los ingresos netos.
    """
    if df_tickets.empty:
        return {
            "total_lavados": 0,
            "total_ingresos_netos": 0.0,
            "total_cancelados_num": 0,
            "total_cancelados_monto": 0.0,
            "por_metodo": {
                "Efectivo": {"monto": 0.0, "conteo": 0},
                "Transferencia": {"monto": 0.0, "conteo": 0}
            },
            "por_categoria": {}
        }
        
    df_validos = df_tickets[df_tickets['estado'] == 'Pagado']
    df_cancelados = df_tickets[df_tickets['estado'] == 'Cancelado']
    
    total_lavados = len(df_validos)
    total_ingresos_netos = float(df_validos['precio_mxn'].sum())
    total_cancelados_num = len(df_cancelados)
    total_cancelados_monto = float(df_cancelados['precio_mxn'].sum())
    
    # Desglose por método de pago
    metodos = ["Efectivo", "Transferencia"]
    por_metodo = {}
    for m in metodos:
        sub = df_validos[df_validos['metodo_pago'] == m]
        por_metodo[m] = {
            "monto": float(sub['precio_mxn'].sum()),
            "conteo": len(sub)
        }
        
    # Desglose por categoría
    por_cat = {}
    if not df_validos.empty and 'categoria_vehiculo' in df_validos.columns:
        cat_group = df_validos.groupby('categoria_vehiculo').agg(
            monto=('precio_mxn', 'sum'),
            conteo=('precio_mxn', 'count')
        ).to_dict('index')
        por_cat = cat_group
        
    return {
        "total_lavados": total_lavados,
        "total_ingresos_netos": total_ingresos_netos,
        "total_cancelados_num": total_cancelados_num,
        "total_cancelados_monto": total_cancelados_monto,
        "por_metodo": por_metodo,
        "por_categoria": por_cat
    }

def get_tickets_rango(fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
    """Consulta tickets en un rango de fechas para reportes y exportación."""
    url, key = get_cloud_credentials()
    if url and key:
        try:
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            res = requests.get(
                f"{url}/rest/v1/tickets?fecha_operativa=gte.{fecha_inicio}&fecha_operativa=lte.{fecha_fin}&order=fecha_operativa.desc,id.desc",
                headers=headers,
                timeout=6
            )
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    df['precio_mxn'] = pd.to_numeric(df['precio_mxn'], errors='coerce').fillna(0.0)
                    return df
        except Exception:
            pass
            
    conn = get_sqlite_connection()
    query = """
        SELECT id, folio, fecha_hora, fecha_operativa, servicio, categoria_vehiculo, 
               precio_mxn, metodo_pago, estado, notas_placa, motivo_cancelacion
        FROM tickets 
        WHERE fecha_operativa BETWEEN ? AND ? 
        ORDER BY fecha_operativa DESC, id DESC;
    """
    df = pd.read_sql_query(query, conn, params=(fecha_inicio, fecha_fin))
    conn.close()
    return df
