import base64, json, os
import functions_framework
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME", "autolavado-datalake-demo")

def limpiar_registro(data: dict) -> dict:
    data["tipo_servicio"] = str(data.get("tipo_servicio", "")).strip().title()
    data["precio"] = abs(float(data.get("precio", 0)))
    data["hora"] = int(data.get("hora", 12))
    return data

@functions_framework.cloud_event
def procesar_venta_pubsub(cloud_event):
    mensaje_b64 = cloud_event.data["message"]["data"]
    registro = json.loads(base64.b64decode(mensaje_b64).decode("utf-8"))
    limpio = limpiar_registro(registro)
    
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"clean/{limpio['fecha']}/{limpio['id_ticket']}.json")
    blob.upload_from_string(json.dumps(limpio), content_type="application/json")
    print(f"Registro limpio guardado en clean/: {limpio['id_ticket']}")
