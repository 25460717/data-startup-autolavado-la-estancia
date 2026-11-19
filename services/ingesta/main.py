import os, json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import storage, pubsub_v1

app = FastAPI(title="API Ingesta - Autolavado Expréss La Estancia")

BUCKET_NAME = os.getenv("BUCKET_NAME", "autolavado-datalake-demo")
TOPIC_ID = os.getenv("TOPIC_ID", "ingesta-ventas-topic")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "demo-project")

class Venta(BaseModel):
    id_ticket: str
    fecha: str
    dia_semana: str
    hora: int
    tipo_servicio: str
    precio: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ventas")
def registrar_venta(venta: Venta):
    if venta.precio <= 0 or not (0 <= venta.hora <= 23):
        raise HTTPException(status_code=400, detail="Datos fuera de rango lógico")
    payload = venta.model_dump()
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"raw/{venta.fecha}/{venta.id_ticket}.json")
        blob.upload_from_string(json.dumps(payload), content_type="application/json")
        
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        publisher.publish(topic_path, json.dumps(payload).encode("utf-8"))
    except Exception as e:
        return {"mensaje": "Recibido en modo local/simulado", "detalle": str(e), "venta": payload}
    return {"mensaje": "Venta enviada a raw/ y cola Pub/Sub", "ticket": venta.id_ticket}
