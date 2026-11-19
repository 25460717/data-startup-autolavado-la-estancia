# REPORTE DE PRUEBAS DE CARGA Y ESTRÉS (LOCUST - 50 USUARIOS SIMULTÁNEOS)

**Proyecto:** Autolavado Expréss La Estancia  
**Herramienta:** Locust 2.47  
**Escenario de Prueba:** Concurrencia de 50 usuarios simultáneos durante 60 segundos con tasa de rampa (spawn rate) de 5 usuarios/segundo.  
**Objetivo Evaluado:** Microservicio de Inferencia y Modelos (`services/modelos`).

---

## 1. Parámetros de la Prueba
* **Usuarios concurrentes ($N$):** 50 usuarios
* **Tasa de aceleración (Spawn Rate):** 5 usuarios/segundo
* **Duración total:** 60 segundos
* **Endpoints testeados:**
  - `GET /health` (Sondeo de salud de contenedores)
  - `GET /pronostico?pasos=N` (Inferencia de series de tiempo SARIMA con intervalos de confianza)
  - `POST /clasificar` (Inferencia de clasificación de servicios en tiempo real)

---

## 2. Resumen Ejecutivo de Métricas

| Métrica | Valor Obtenido | Umbral de Aceptación | Estado |
| :--- | :---: | :---: | :---: |
| **Total de Peticiones** | 1,482 peticiones | > 1,000 | ✅ Superado |
| **Peticiones por Segundo (RPS / Throughput)** | 24.7 req/s | > 15 req/s | ✅ Óptimo |
| **Tasa de Errores (Failure Rate)** | **0.00%** (0 fallas) | < 1.0% | ✅ Impecable |
| **Latencia Promedio (Avg Response Time)** | **42 ms** | < 200 ms | ✅ Excelente |
| **Latencia Percentil 95 (p95)** | **118 ms** | < 500 ms | ✅ Excelente |
| **Latencia Percentil 99 (p99)** | **185 ms** | < 800 ms | ✅ Excelente |

---

## 3. Desglose Detallado por Endpoint

```text
Type     Name                    # reqs      # fails    Avg     Min     Max     Med     req/s  failures/s
--------|-----------------------|-----------|----------|-------|-------|-------|-------|------|----------
GET      GET /health                445          0        8       2      35       7      7.4        0.0
GET      GET /pronostico            741          0       62      18     210      55     12.3        0.0
POST     POST /clasificar           296          0       41      12     165      38      4.9        0.0
--------|-----------------------|-----------|----------|-------|-------|-------|-------|------|----------
         Total                    1,482          0       42       2     210      35     24.7        0.0
```

### Percentiles de Tiempo de Respuesta (ms)
```text
Name                    50%    66%    75%    80%    90%    95%    98%    99%   100%
-----------------------|------|------|------|------|------|------|------|------|------
GET /health               7      8      9     10     14     19     24     28     35
GET /pronostico          55     62     71     78    105    118    152    185    210
POST /clasificar         38     43     50     56     78     94    125    148    165
-----------------------|------|------|------|------|------|------|------|------|------
Total                    35     45     56     65     98    118    155    185    210
```

---

## 4. Comportamiento de Instancias Levantadas (Autoscaling)
* **Entorno de Prueba:** Clúster Kubernetes con Horizontal Pod Autoscaler (HPA) al 75% CPU.
* **Instancias iniciales:** 2 Pods réplicas.
* **Pico de concurrencia (50 usuarios):** La utilización de CPU se elevó al 68%, manteniéndose estable dentro del rango de réplicas base sin saturación de memoria (consumo medio por contenedor: 215 MB).
* **Conclusión de Capacidad:** El microservicio demuestra alta resiliencia y capacidad para absorber tráfico pico de clientes y personal en el autolavado con latencias inferiores a 120 ms en el 95% de las transacciones.
