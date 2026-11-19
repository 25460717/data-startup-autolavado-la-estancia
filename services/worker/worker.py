import os
import time
import json
import sqlite3
import datetime

"""
Worker Asincrono disparado por eventos / cola de tareas.
Simula el procesamiento en segundo plano de tickets, generacion de resumenes de caja
y envio de eventos a Cloud Storage / SQS.
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_CANDIDATES = [
    os.path.join(BASE_DIR, "..", "tablero", "autolavado.db"),
    os.path.join(BASE_DIR, "autolavado.db"),
    os.path.abspath(os.path.join(BASE_DIR, "..", "..", "services", "tablero", "autolavado.db"))
]

def get_db():
    for p in DB_CANDIDATES:
        if os.path.exists(p):
            return p
    return DB_CANDIDATES[0]

def procesar_cierre_diario():
    db_path = get_db()
    if not os.path.exists(db_path):
        print(f"[Worker] Base de datos no encontrada en {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(precio) FROM ventas;")
    total_autos, total_ingresos = cur.fetchone()
    conn.close()
    
    timestamp = datetime.datetime.now().isoformat()
    evento = {
        "event_id": f"evt-{int(time.time())}",
        "timestamp": timestamp,
        "tipo_evento": "CIERRE_DIARIO_CALCULADO",
        "total_historico_vehiculos": total_autos,
        "total_historico_ingresos": total_ingresos,
        "status": "PROCESSED_SUCCESSFULLY"
    }
    print(f"[Worker Evento Procesado]: {json.dumps(evento, indent=2)}")

def main():
    print("[Worker Serverless Event Listener] Iniciado y escuchando eventos...")
    # Ejecuta una ronda y duerme
    while True:
        try:
            procesar_cierre_diario()
        except Exception as e:
            print(f"[Worker Error]: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
