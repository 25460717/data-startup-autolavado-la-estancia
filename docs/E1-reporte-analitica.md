# E1: Reporte de Limpieza y Analítica Empresarial

## 1. Auditoría de Limpieza de Datos (103,309 registros)
1. **Duplicados:** Se verificó la unicidad mediante `id_ticket`, eliminando registros duplicados exactos.
2. **Valores faltantes:** Se imputaron o descartaron registros sin fecha o tipo de servicio válido.
3. **Tipos de dato:** Estandarización de fechas a formato ISO `YYYY-MM-DD`, horarios a entero 24h (`0-23`) y precios a flotante limpio.
4. **Valores atípicos:** Validación de rangos de precio oficiales ($70 MXN a $400 MXN) y horarios operativos.
5. **Errores lógicos:** Normalización de nombres de servicios (eliminación de espacios extra y diferencias de mayúsculas/minúsculas).

## 2. Hallazgos del Análisis Espectral (FFT) y Recomendaciones
- **Ciclo semanal (7 días):** Incremento marcado de afluencia de viernes a domingo.
- **Ciclo quincenal (15 días):** Picos recurrentes alrededor de los días 15 y 30/1 de cada mes.
- **Recomendaciones al dueño:**
  1. Realizar pedidos de shampoo, cera y Armor-All los jueves previos a fin de semana y quincena.
  2. Reforzar la plantilla de lavadores los sábados y días de quincena (15 y 30), reduciendo turnos los martes.
  3. Promover paquetes de *Carro Detallado* ($110 MXN) y *Camioneta Detallada* ($130 MXN) en días de baja afluencia.
