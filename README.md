# Autolavado Expréss La Estancia - Sistema Integral de Gestión y Analítica Predictiva

Sistema integral y punto de venta inteligente (POS) para la gestión operativa, analítica de demanda, machine learning y series de tiempo para **Autolavado Expréss La Estancia**.

---

## 🚀 Características Principales

1. **Punto de Venta Express (Caja POS):**
   - Registro instantáneo de servicios de lavado con cobro rápido.
   - Selector de método de pago: **Efectivo (Predeterminado)**, **Transferencia** y **Tarjeta**.
   - Campo para captura de placa o notas del vehículo.
   - Tarjetas responsivas sin saltos de palabras o sílabas en pantallas angostas.
   - **Autoguardado persistente en la nube** (Supabase PostgreSQL / REST) con respaldo automático en SQLite local.
   - **Corte de caja en vivo:** separación de ingresos netos por método de pago y conteo de vehículos lavados.
   - **Anulación / Cancelación de tickets:** función con auditoría y motivo para corregir errores de captura sin borrar el historial, recalculando totales netos en tiempo real.
   - **Exportación de reportes:** descarga de cortes diarios y por rangos de fechas en **CSV** y **Excel (.xlsx)**.

2. **Tablero Analítico Histórico (BI):**
   - Análisis de 103,309 registros históricos (más de 6 años de operación).
   - Patrones de demanda por día de la semana, horas pico y distribución de servicios.

3. **Predicción de Demanda e Ingresos (Machine Learning):**
   - Modelos predictivos de regresión basados en Random Forest con variables de calendario, quincenas y promedios móviles.

4. **Calculadora de Insumos y Turnos de Personal:**
   - Estimación de insumos requeridos (shampoo, cera líquida, aromatizante, agua) y sugerencia de lavadores necesarios.

5. **Avance 2: Modelos ML y Preprocesamiento:**
   - Comparativa de 5 regresores y 4 clasificadores con validación cruzada (K-Fold), MAE, RMSE, R² y matrices de confusión.

6. **Entregable 3: Microservicios y Series de Tiempo (ARIMA / SARIMA):**
   - Modelos SARIMA con prueba Dickey-Fuller aumentada, justificación de órdenes (p, d, q) y bandas de confianza al 95%.
   - Arquitectura de microservicios con Docker Compose, Kubernetes y Terraform.

7. **Proyecto Integrador: Modelado y Análisis Predictivo (`.ipynb`):**
   - Jupyter Notebook reproducible de principio a fin (`proyecto_integrador_modelado_predictivo.ipynb`).
   - Selección y exploración de datasets enriquecidos (>500 filas y >5 variables explicativas).
   - Preprocesamiento formal con Scikit-Learn (`Pipeline` y `ColumnTransformer`).
   - Comparativa de 4 algoritmos de regresión supervisada y modelo autoregresivo SARIMA con descomposición y prueba ADF.
   - Comparativa de 4 algoritmos de clasificación (Naive Bayes, KNN, Árbol de Decisión y Random Forest) con matrices de confusión.
   - Conclusiones ejecutivas orientadas a la optimización de turnos e insumos del autolavado.

---

## 🛠️ Ejecución Local

### 1. Iniciar la Aplicación Web (Streamlit POS y Tablero)
```bash
# Entrar a la carpeta
cd data-startup-autolavado-la-estancia

# Instalar dependencias
pip install -r requirements.txt

# Iniciar Streamlit
python -m streamlit run services/tablero/app.py
```
Abre en tu navegador: `http://localhost:8501`.

### 2. Abrir y Ejecutar el Jupyter Notebook del Proyecto Integrador
Puedes abrirlo en VS Code, Jupyter Lab o Jupyter Notebook:
```bash
jupyter notebook notebooks/proyecto_integrador_modelado_predictivo.ipynb
```
O directamente el archivo espejo ubicado en la raíz del proyecto:
```bash
jupyter notebook proyecto_integrador_modelado_predictivo.ipynb
```

---

## ☁️ Configuración de Persistencia en la Nube (Supabase)

Para desplegar en **Streamlit Community Cloud** sin perder tickets al reiniciarse el contenedor:

1. Crea una cuenta gratuita en [Supabase](https://supabase.com) y crea un nuevo proyecto.
2. En el editor SQL de Supabase (`SQL Editor`), ejecuta el siguiente script para crear la tabla de tickets:

```sql
CREATE TABLE IF NOT EXISTS tickets (
    id BIGSERIAL PRIMARY KEY,
    folio TEXT UNIQUE NOT NULL,
    fecha_hora TEXT NOT NULL,
    fecha_operativa TEXT NOT NULL,
    servicio TEXT NOT NULL,
    categoria_vehiculo TEXT NOT NULL,
    precio_mxn NUMERIC NOT NULL,
    metodo_pago TEXT NOT NULL DEFAULT 'Efectivo',
    estado TEXT NOT NULL DEFAULT 'Pagado',
    notas_placa TEXT DEFAULT '',
    motivo_cancelacion TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Políticas de lectura y escritura para la clave anónima (si RLS está activo)
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Acceso publico lectura y escritura tickets" ON tickets
FOR ALL USING (true) WITH CHECK (true);
```

3. En Streamlit Community Cloud (o en tu archivo `.streamlit/secrets.toml` local):
Dirígete a la configuración de la app (`App Settings` > `Secrets`) y agrega:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-clave-anonima-de-supabase"
```

Si no configuras las credenciales, el sistema funcionará automáticamente en **Modo Respaldo Local (SQLite)** sin errores.

---

## 📦 Estructura del Proyecto

```text
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── requirements.txt
├── proyecto_integrador_modelado_predictivo.ipynb  <-- Notebook maestro en la raíz
├── data/
│   ├── autolavado_enriquecido.csv                 <-- 15,000 registros con >12 variables explicativas
│   └── demanda_diaria_enriquecida.csv             <-- 2,221 días continuos de series temporales
├── docs/
│   └── REPORTE_TECNICO_E3_ARQUITECTURA.md
├── infra/
│   └── terraform/
├── k8s/
│   ├── modelos-deployment.yaml
│   └── tablero-deployment.yaml
├── notebooks/
│   ├── Avance1_EDA_Autolavado.ipynb
│   ├── Avance2_Modelos_Machine_Learning.ipynb
│   └── proyecto_integrador_modelado_predictivo.ipynb  <-- Notebook maestro en carpeta notebooks
├── scripts/
│   ├── preparar_proyecto_integrador.py
│   └── generar_notebook.py
├── services/
│   ├── ingesta/
│   ├── modelos/
│   ├── worker/
│   └── tablero/
│       ├── app.py
│       ├── autolavado.db
│       ├── db_manager.py
│       ├── Dockerfile
│       └── requirements.txt
└── tests/
    ├── locustfile.py
    └── REPORTE_PRUEBA_CARGA_LOCUST.md
```
