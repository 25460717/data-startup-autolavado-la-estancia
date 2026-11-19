# E2: Cimientos en la Nube y Arquitectura Desacoplada

## 1. Arquitectura de Referencia (Google Cloud Platform)
- **Ruta de escritura asíncrona:** Punto de Venta / CSV → `services/ingesta` (FastAPI) → Almacenamiento en bucket `raw/` + Publicación en cola **Google Cloud Pub/Sub** → `services/worker` (limpieza automatizada) → Escritura en bucket `clean/` y base de datos **PostgreSQL**.
- **Ruta de lectura y predicción:** `services/tablero` (Streamlit) consulta datos limpios en `clean/` y solicita pronósticos en tiempo real a `services/modelos` (FastAPI).

## 2. Justificación de Base de Datos (SQL vs. NoSQL)
Se eligió **PostgreSQL (SQL)** debido a la estructura tabular estricta de las notas de venta (`id_ticket`, `fecha`, `hora`, `tipo_servicio`, `precio`), la necesidad de integridad transaccional ACID en el cobro de caja y la eficiencia en consultas analíticas de agregación por rangos de fecha.
