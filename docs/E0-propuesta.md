# E0: Propuesta de Startup — Autolavado Expréss La Estancia

## 1. Validación con el cliente y entrevista
Alianza directa con el propietario de **Autolavado Expréss La Estancia**, con acceso histórico a **103,309 notas de venta** acumuladas durante 6 años.
- **Problema principal:** Compra de insumos químicos (shampoo, cera, Armor-All) al tanteo, asignación ineficiente de turnos de lavadores y cobro manual desconectado del análisis histórico.
- **Solución:** Plataforma web en la nube con Punto de Venta (POS), tablero ejecutivo y pronóstico de demanda con calculadora automática de insumos y personal.
- **Modelo de ingresos:** Suscripción semanal de **$600 MXN** ($2,400 MXN mensuales) por mantenimiento, soporte y operación continua.

## 2. Lean Canvas
- **Segmento de clientes:** Autolavados independientes y negocios locales de estética automotriz.
- **Propuesta de valor:** Certeza operativa semanal en 30 segundos: cuántos autos llegarán, cuántos litros de químico comprar y cuántos lavadores citar.
- **Cadena de preguntas:** *¿Cuántos insumos compro y cuántos lavadores cito la próxima semana?* → *¿Cuál será la demanda diaria de vehículos en los próximos 7 a 30 días?* → Variable: `total_vehiculos_diarios`.
- **Inventario de datos:** 103,309 registros (6 años), columnas: `id_ticket`, `fecha`, `dia_semana`, `hora`, `tipo_servicio`, `precio`.
