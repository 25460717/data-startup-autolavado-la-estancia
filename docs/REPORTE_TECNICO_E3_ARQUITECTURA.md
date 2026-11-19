# DOCUMENTACIÓN TÉCNICA Y ARQUITECTURA CLOUD (ENTREGABLE 3)
**Proyecto Integrador:** Autolavado Expréss La Estancia  
**Empresa / Negocio:** Autolavado Expréss La Estancia  
**Fecha:** Noviembre 2026  

---

## 1. Arquitectura de Microservicios y Contenedores

La solución fue desacoplada en una arquitectura de microservicios contenerizados mediante Docker y orquestados para despliegues elásticos en la nube:

1. **`services/tablero` (Frontend Streamlit):**
   - Interfaz web interactiva (Caja POS, Dashboard Histórico, Calculadora de Insumos y Turnos de Personal, Análisis de Modelos).
   - Consume los microservicios backend de manera desacoplada vía HTTP REST.
2. **`services/modelos` (Backend Inferencia FastAPI):**
   - Microservicio de inferencia analítica de alto desempeño.
   - Expone endpoints `/pronostico` (SARIMA con bandas de confianza) y `/clasificar` (Random Forest para clasificación de tipo de servicio).
3. **`services/ingesta` (API de Registro y Transacciones):**
   - Recepción rápida de tickets emitidos en caja, generación de consecutivos y persistencia atómica.
4. **`services/worker` (Worker Asíncrono / Event-Driven):**
   - Servicio en segundo plano para cálculo de cierres diarios y procesamiento de colas (simulación SQS / EventBridge).

---

## 2. Despliegue en Servicios Administrados de Contenedores

El sistema está diseñado para operar de forma nativa en plataformas Serverless de contenedores administrados:
* **Google Cloud Run / AWS App Runner / Azure Container Apps:**
  - Despliegue sin servidor (Serverless Containers) con escalado a cero para optimizar costos operativos.
  - Conexión mediante variables de entorno `API_MODELOS_URL` y `API_INGESTA_URL`.
* **Worker Serverless Disparado por Eventos:**
  - Desacoplamiento mediante colas SQS / Cloud PubSub para procesar cierres de turno, alertas de stock bajo en bodega y reportes nocturnos sin impactar la latencia de la caja POS.

---

## 3. Justificación Técnica: CPU vs. GPU para Inferencia y Entrenamiento

### Contexto del Negocio y Características del Dataset
El modelo de datos de "Autolavado Expréss La Estancia" consta de 103,309 registros tabulares estructurados (fechas, horas, tipo de vehículo y montos de cobro). Para la toma de decisiones del negocio se emplean algoritmos de Machine Learning tabular (Random Forest, Gradient Boosting, Árboles de Decisión, Regresión Lineal) y modelos autorregresivos lineales estacionales de series de tiempo (SARIMA).

### Evaluación de Rendimiento y Latencia
Los modelos tabulares y las series de tiempo SARIMA no se benefician de la paralelización masiva de miles de núcleos que ofrecen las unidades GPU (diseñadas para multiplicación tensorial masiva en Deep Learning, Visión por Computadora y LLMs). En pruebas empíricas sobre CPU x86-64 moderna:
* El ajuste y pronóstico SARIMA toma **< 80 milisegundos**.
* La inferencia unitaria de clasificación con Random Forest toma **< 2 milisegundos**.
* El consumo de memoria del proceso de inferencia ronda los **200 MB**.

### Análisis de Costos y Eficiencia Operativa (FinOps)
* **Instancia con GPU (ej. AWS `g4dn.xlarge` / GCP `n1-standard-4 + NVIDIA T4`):** Costo aproximado de **\$350 - \$500 USD mensuales**, con tiempos de encendido en frío (*cold start*) superiores a 30-45 segundos debido a la carga de controladores CUDA y librerías de GPU.
* **Instancia administrada CPU Serverless (ej. Cloud Run / Container Apps con 1 vCPU y 1 GB RAM):** Costo aproximado de **\$5 - \$15 USD mensuales** (dentro del nivel gratuito para bajo/medio tráfico), con arranque en frío menor a 1.5 segundos.

### Decisión de Arquitectura
**Se selecciona una arquitectura basada 100% en CPU**. La CPU ofrece la menor latencia de arranque, costo operativo mínimo, portabilidad universal en contenedores ligeros Alpine/Slim y rendimiento óptimo para el volumen de transacciones del autolavado (más de 24 req/s en pruebas de estrés).

---

## 4. Análisis de Series de Tiempo: Justificación de Parámetros SARIMA $(p, d, q) \times (P, D, Q)_s$

Para el modelado de la demanda diaria de vehículos se seleccionó un modelo **SARIMAX(1, 1, 1) $\times$ (1, 0, 1)$_7$**:

1. **Diferenciación No Estacional ($d = 1$):**
   - La prueba de Dickey-Fuller Aumentada (ADF Test) sobre la serie original reportó estacionariedad tras la primera diferencia ($p\text{-value} = 1.34 \times 10^{-13} < 0.05$), eliminando tendencias de largo plazo.
2. **Componentes Autorregresivo y Media Móvil ($p = 1, q = 1$):**
   - La función de autocorrelación parcial (PACF) muestra un corte abrupto tras el rezago 1, justificando $p = 1$.
   - La función de autocorrelación (ACF) muestra un decaimiento exponencial con un pico significativo en el rezago 1, justificando $q = 1$.
3. **Estacionalidad Semanal ($s = 7, P = 1, D = 0, Q = 1$):**
   - El negocio presenta un patrón cíclico semanal estricto (afluencia disparada viernes, sábados y domingos frente a días de semana). El término estacional $s = 7$ con $P=1, Q=1$ minimizó el Criterio de Información de Akaike (**AIC = 2637.01** frente a > 2800 en modelos sin estacionalidad).
4. **Intervalos de Confianza al 95%:**
   - Cada predicción emitida por el endpoint `/pronostico` calcula los límites inferior y superior con base en la varianza condicional del error:
   $$\hat{y}_{t+h} \pm 1.96 \cdot \sigma_h$$
   lo que permite al negocio planificar con escenarios optimistas y conservadores para compras de insumos en bodega.
