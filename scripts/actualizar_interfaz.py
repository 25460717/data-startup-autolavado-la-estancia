"""
Script para actualizar la interfaz visual de app.py con diseno moderno,
colores elegantes, tarjetas llamativas y detalles profesionales.
"""

import os

app_path = r"C:\Users\josea\data-startup-autolavado-la-estancia\services\tablero\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Nuevos estilos CSS premium
old_css_start = "st.markdown(\"\"\"\n<style>"
old_css_end = "</style>\n\"\"\", unsafe_allow_html=True)"

start_idx = text.find(old_css_start)
end_idx = text.find(old_css_end)

if start_idx != -1 and end_idx != -1:
    end_idx += len(old_css_end)
    
    new_css = """st.markdown(\"\"\"
<style>
    /* Estilos globales y fondo oscuro moderno */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0d1527 0%, #070a12 100%) !important;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header principal con brillo sutil y bordes redondeados */
    .hero-header {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.85) 0%, rgba(14, 116, 144, 0.75) 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 26px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px -8px rgba(2, 132, 199, 0.35);
        backdrop-filter: blur(8px);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #e0f2fe;
        opacity: 0.95;
        margin-top: 6px;
        font-weight: 400;
    }
    
    /* Tarjetas de métricas tipo KPI ejecutivas */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.5);
        box-shadow: 0 10px 28px rgba(56, 189, 248, 0.18);
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.95rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.15;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Tarjetas de servicios POS */
    .service-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.65) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .service-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.45);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    .service-title {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        white-space: normal !important;
        hyphens: none !important;
        line-height: 1.35 !important;
        min-height: 2.8rem;
        display: flex;
        align-items: center;
    }
    .service-desc {
        font-size: 0.83rem !important;
        color: #94a3b8 !important;
        line-height: 1.35 !important;
        min-height: 2.5rem;
        word-break: normal !important;
        hyphens: none !important;
    }
    
    /* Badges de Categoría */
    .badge-category {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-radius: 6px;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        margin-bottom: 8px;
    }
    
    /* Botones de Cobro con estilo y ergonomía */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        hyphens: none !important;
        padding: 0.6rem 1.1rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.35) !important;
    }
    
    /* Tarjetas de método de pago en corte diario */
    .metodo-card-efectivo {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 78, 59, 0.3) 100%);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
        color: #ecfdf5;
    }
    .metodo-card-transf {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(49, 46, 129, 0.3) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
        color: #eef2ff;
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #0b1120 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Footer personalizado */
    .app-footer {
        text-align: center;
        padding: 24px 0 10px 0;
        margin-top: 36px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        color: #64748b;
        font-size: 0.8rem;
    }
</style>
\"\"\", unsafe_allow_html=True)"""
    
    text = text[:start_idx] + new_css + text[end_idx:]
    print("CSS updated successfully!")

# 2. Mejorar la barra lateral (Sidebar)
old_sidebar_code = """with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3202/3202926.png", width=75)
    st.markdown("## **Autolavado Expréss**\\n*La Estancia*")
    st.markdown("---")"""

new_sidebar_code = """with st.sidebar:
    st.markdown(\"\"\"
    <div style='text-align: center; padding: 10px 0 16px 0;'>
        <div style='font-size: 2.8rem; margin-bottom: 4px;'>🚗✨</div>
        <div style='font-size: 1.35rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.01em;'>Autolavado Expréss</div>
        <div style='font-size: 0.9rem; font-weight: 600; color: #38bdf8;'>La Estancia</div>
        <div style='display: inline-block; margin-top: 6px; padding: 3px 10px; font-size: 0.7rem; font-weight: 700; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px;'>
            SISTEMA POS & ANALÍTICA v3.5
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)
    st.markdown("---")"""

if old_sidebar_code in text:
    text = text.replace(old_sidebar_code, new_sidebar_code, 1)
    print("Sidebar header updated!")

# 3. Mejorar el pie de la barra lateral con detalles del equipo
old_sidebar_bottom = """    st.markdown(\"\"\"
    <div style='background-color: rgba(255,255,255,0.03); padding: 10px 12px; border-radius: 8px; font-size: 0.78rem; color: #94a3b8;'>
        <strong>📍 Sucursal:</strong> La Estancia<br>
        <strong>🤖 ML Engine:</strong> Scikit-Learn + Statsmodels<br>
        <strong>🟢 Sistema:</strong> 100% Operativo
    </div>
    \"\"\", unsafe_allow_html=True)"""

new_sidebar_bottom = """    st.markdown(\"\"\"
    <div style='background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px 14px; border-radius: 10px; font-size: 0.78rem; color: #94a3b8; margin-top: 10px;'>
        <div style='font-weight: 700; color: #f1f5f9; margin-bottom: 4px;'>📍 Sucursal La Estancia</div>
        <div>👨‍💻 <strong>Proyecto Integrador:</strong> Ciencia de Datos & IA</div>
        <div style='margin-top: 4px;'>👥 <strong>Equipo:</strong> 3 Integrantes</div>
        <div style='margin-top: 4px; color: #38bdf8;'>💼 <strong>Acuerdo:</strong> $600 MXN/semana</div>
        <div style='margin-top: 4px; color: #22c55e;'>🟢 <strong>Estado:</strong> 100% Operativo</div>
    </div>
    \"\"\", unsafe_allow_html=True)"""

if old_sidebar_bottom in text:
    text = text.replace(old_sidebar_bottom, new_sidebar_bottom, 1)
    print("Sidebar footer updated!")

# 4. Mejorar el selector de pago rápido en Caja POS
old_pay_selector = """    # Selector de opciones rápidas de cobro
    c_pay1, c_pay2 = st.columns([1.3, 1])
    with c_pay1:
        metodo_pago_sel = st.radio(
            "Método de Pago para este cobro:",
            ["💵 Efectivo (Predeterminado)", "📱 Transferencia"],
            horizontal=True,
            index=0,
            help="Selecciona cómo pagó el cliente antes de registrar el servicio."
        )
    with c_pay2:
        notas_placa_input = st.text_input(
            "Placa o descripción del auto (opcional):",
            placeholder="Ej: JRD-4521 o Versa blanco",
            help="Puedes anotar la placa o modelo para mayor control."
        )"""

new_pay_selector = """    # Selector de opciones rápidas de cobro estilizado
    st.markdown(\"\"\"
    <div style='background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px 18px; margin-bottom: 16px;'>
        <div style='font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;'>
            ⚡ Configuración Rápida de Cobro
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)
    
    c_pay1, c_pay2 = st.columns([1.3, 1])
    with c_pay1:
        metodo_pago_sel = st.radio(
            "Método de Pago Activo:",
            ["💵 Efectivo (Predeterminado)", "📱 Transferencia"],
            horizontal=True,
            index=0,
            help="Elige cómo pagó el cliente para registrarlo de inmediato en el corte de caja."
        )
    with c_pay2:
        notas_placa_input = st.text_input(
            "Placa o descripción del vehículo (opcional):",
            placeholder="Ej: JRD-4521 / Versa blanco / Tsuru",
            help="Puedes anotar la placa o descripción física para control del ticket."
        )"""

if old_pay_selector in text:
    text = text.replace(old_pay_selector, new_pay_selector, 1)
    print("Payment selector updated!")

# 5. Mejorar el desglose de métodos de pago en Caja POS
old_corte_cards = """    # Desglose de corte de caja por método de pago (Efectivo y Transferencia)
    st.markdown("#### 💵 Desglose de Corte por Método de Pago")
    met_col1, met_col2 = st.columns(2)
    ef_info = corte_hoy.get('por_metodo', {}).get('Efectivo', {'monto': 0.0, 'conteo': 0})
    tr_info = corte_hoy.get('por_metodo', {}).get('Transferencia', {'monto': 0.0, 'conteo': 0})
    
    with met_col1:
        st.info(f"💵 **Efectivo:** ${ef_info['monto']:,.2f} MXN ({ef_info['conteo']} lavados)")
    with met_col2:
        st.info(f"📱 **Transferencia:** ${tr_info['monto']:,.2f} MXN ({tr_info['conteo']} lavados)")"""

new_corte_cards = """    # Desglose de corte de caja por método de pago estilizado
    st.markdown("#### 💵 Desglose de Corte de Caja en Vivo")
    met_col1, met_col2 = st.columns(2)
    ef_info = corte_hoy.get('por_metodo', {}).get('Efectivo', {'monto': 0.0, 'conteo': 0})
    tr_info = corte_hoy.get('por_metodo', {}).get('Transferencia', {'monto': 0.0, 'conteo': 0})
    
    with met_col1:
        st.markdown(f\"\"\"
        <div class="metodo-card-efectivo">
            <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #6ee7b7;">
                💵 Cobrado en Efectivo
            </div>
            <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; margin-top: 4px;">
                ${ef_info['monto']:,.2f} <span style="font-size: 0.85rem; color: #a7f3d0;">MXN</span>
            </div>
            <div style="font-size: 0.8rem; color: #a7f3d0; margin-top: 2px;">
                {ef_info['conteo']} lavados cobrados en mano
            </div>
        </div>
        \"\"\", unsafe_allow_html=True)
        
    with met_col2:
        st.markdown(f\"\"\"
        <div class="metodo-card-transf">
            <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #a5b4fc;">
                📱 Cobrado por Transferencia
            </div>
            <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; margin-top: 4px;">
                ${tr_info['monto']:,.2f} <span style="font-size: 0.85rem; color: #c7d2fe;">MXN</span>
            </div>
            <div style="font-size: 0.8rem; color: #c7d2fe; margin-top: 2px;">
                {tr_info['conteo']} lavados transferidos al banco
            </div>
        </div>
        \"\"\", unsafe_allow_html=True)"""

if old_corte_cards in text:
    text = text.replace(old_corte_cards, new_corte_cards, 1)
    print("Corte cards updated!")

# 6. Guardar cambios en app.py
with open(app_path, "w", encoding="utf-8") as f:
    f.write(text)

print("All visual upgrades applied successfully to app.py!")
