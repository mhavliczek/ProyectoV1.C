import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import os
from datetime import datetime, timedelta

# ==============================
# CONFIGURACIÓN INICIAL Y CSS
# ==============================
st.set_page_config(page_title="Mantenimiento Predictivo", layout="wide")
st.markdown('''
    <style>
    body, .stApp { background-color: #181c23 !important; }
    .main-row { display: flex; gap: 2em; }
    .main-col { flex: 1; }
    .side-col { width: 370px; min-width: 340px; }
    .kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.7em; }
    .kpi-card {
        background: #232b3b;
        border-radius: 12px;
        padding: 18px 0 10px 0;
        text-align: center;
        color: #fff;
        font-weight: 600;
        box-shadow: 0 2px 8px #0002;
    }
    .kpi-title { font-size: 1.1em; color: #b0b8c1; margin-bottom: 6px; }
    .kpi-value { font-size: 2.1em; font-weight: bold; }
    .kpi-blue { background: #22304a; }
    .kpi-green { background: #1e3a34; }
    .kpi-orange { background: #3a2e1e; }
    .kpi-teal { background: #1e3a3a; }
    .card {
        background: #232b3b;
        border-radius: 12px;
        padding: 18px 18px 10px 18px;
        color: #fff;
        margin-bottom: 1em;
        box-shadow: 0 2px 8px #0002;
    }
    .alerta-card {
        background: #2d1c1c;
        border-radius: 12px;
        padding: 18px 18px 10px 18px;
        color: #ffb3b3;
        border: 2px solid #b30000;
        margin-bottom: 1em;
        box-shadow: 0 2px 8px #b3000033;
    }
    .comp-bar-bg {
        background: #232b3b;
        border-radius: 8px;
        height: 22px;
        width: 100%;
        margin-bottom: 8px;
        position: relative;
    }
    .comp-bar {
        background: #3b7ddd;
        border-radius: 8px;
        height: 22px;
        position: absolute;
        left: 0; top: 0;
    }
    .tribo-bar-bg {
        background: #232b3b;
        border-radius: 8px;
        height: 18px;
        width: 100%;
        margin-bottom: 8px;
        position: relative;
    }
    .tribo-bar-red { background: #e74c3c; }
    .tribo-bar-orange { background: #e67e22; }
    .tribo-bar-green { background: #16a085; }
    .tribo-bar {
        border-radius: 8px;
        height: 18px;
        position: absolute;
        left: 0; top: 0;
    }
    .impacto-card {
        background: #232b3b;
        border-radius: 12px;
        padding: 18px 18px 10px 18px;
        color: #fff;
        margin-bottom: 1em;
        box-shadow: 0 2px 8px #0002;
        text-align: left;
    }
    .detalle-alerta-card {
        background: #232b3b;
        border-radius: 12px;
        padding: 24px 24px 18px 24px;
        color: #fff;
        margin-bottom: 8px;
        box-shadow: 0 2px 8px #0002;
    }
    .stButton>button { background: #b30000; color: #fff; border-radius: 8px; }
    </style>
''', unsafe_allow_html=True)

# Rutas de datos
DATA_PATH = "data/datos_generados_Disponibilidad.parquet"
MODEL_PATH = "data/modelo_entrenado.joblib"
FEATURES_PATH = "data/feature_names.joblib"

componentes_aceites = {
    "MANDO FINAL": "MOBIL MOBILTRANS HD 30",
    "TRANSMISIÓN": "MOBIL MOBILTRANS HD 30",
    "DIFERENCIAL DEL": "MOBIL MOBILTRANS HD 30",
    "MOTOR": "MOBIL DELVAC 15W40",
    "SISTEMA HIDRAULICO": "MOBIL DTE 24",
    "MANDO FINAL TRA.DER": "MOBIL MOBILTRANS HD 30",
    "MANDO FINAL TRA.IZQ": "MOBIL MOBILTRANS HD 30",
    "MASA DERECHA": "MOBIL MOBILTRANS HD 30",
    "MASA IZQUIERDA": "MOBIL MOBILTRANS HD 30",
    "MOTOR TRACCION IZQ": "MOBIL SHC GEAR 680",
    "MOTOR TRACCION DER": "MOBIL SHC GEAR 680",
    "DIFERENCIAL TRA": "MOBIL MOBILTRANS HD 30"
}

# ==============================
# CARGA DE DATOS Y MODELO
# ==============================
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_parquet(DATA_PATH)
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

@st.cache_resource
def cargar_modelo():
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        try:
            modelo = joblib.load(MODEL_PATH)
            feature_names = joblib.load(FEATURES_PATH)
            return modelo, feature_names
        except Exception as e:
            st.warning(f"No se pudo cargar el modelo: {e}")
    return None, None

modelo, feature_names = cargar_modelo()

# ==============================
# HEADER Y SELECTOR CON FILTROS
# ==============================
st.markdown("<h2 style='color:#fff;font-weight:700;margin-bottom:0.2em;'>Mantenimiento Predictivo – Camión</h2>", unsafe_allow_html=True)
st.markdown("<div style='color:#b0b8c1;font-size:1.1em;margin-bottom:1.5em;'>Seleccione un camión para ver su estado actual y predicción de fallas.</div>", unsafe_allow_html=True)

# Filtros por marca y modelo
marca_options = sorted(df['Marca'].unique())
marca_sel = st.selectbox("Marca", marca_options)
modelos_options = sorted(df[df['Marca'] == marca_sel]['Modelo'].unique())
modelo_sel = st.selectbox("Modelo", modelos_options)

# Selector de camión filtrado por marca y modelo
camiones_filtrados = sorted(df[(df['Marca'] == marca_sel) & (df['Modelo'] == modelo_sel)]['flota'].unique())
camion_sel = st.selectbox("Camión", camiones_filtrados, format_func=lambda x: f"Camión {x}")
df_camion = df[(df['flota'] == camion_sel) & (df['Marca'] == marca_sel) & (df['Modelo'] == modelo_sel)].sort_values('Fecha', ascending=False)

registro = df_camion.iloc[0]

# ==============================
# LAYOUT PRINCIPAL
# ==============================
main_col, side_col = st.columns([2,1], gap="large")

with main_col:
    # KPIs
    st.markdown("<div class='kpi-grid'>" +
        f"<div class='kpi-card kpi-blue'><div class='kpi-title'>Disponibilidad</div><div class='kpi-value'>{registro['Disponibilidad']*100:.0f} %</div></div>" +
        f"<div class='kpi-card kpi-teal'><div class='kpi-title'>MTTR</div><div class='kpi-value'>{registro['Tiempo Parada']:.1f} hr</div></div>" +
        f"<div class='kpi-card kpi-orange'><div class='kpi-title'>MTBF</div><div class='kpi-value'>{registro['TBF']:.1f} hr</div></div>" +
        f"<div class='kpi-card kpi-green'><div class='kpi-title'>Confiabilidad</div><div class='kpi-value'>{registro['Confiabilidad']:.0f} %</div></div>" +
        "</div>", unsafe_allow_html=True)

    # Alerta Predictiva
    def calcular_fallo():
        nivel = registro['Hierro (Fe) ppm']
        if nivel > 120:
            return True, 7, "Alto nivel de partículas"
        return False, None, None
    falla, dias, motivo = calcular_fallo()
    st.markdown(f"""
    <div class='alerta-card'>
        <div style='font-size:1.2em;font-weight:600;color:#ffb3b3;'>Alerta Predictiva</div>
        <div style='display:flex;align-items:center;gap:1em;margin-top:0.5em;'>
            <span style='font-size:2.5em;'>❗</span>
            <div>
                <span style='font-size:1.3em;font-weight:700;color:#fff;'>Fallo en {dias} días</span><br>
                <span style='font-size:1em;color:#ffb3b3;'>{motivo}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Estado Tribológico
    st.markdown("<div class='card' style='margin-bottom:0.7em;'><div style='font-size:1.2em;font-weight:600;margin-bottom:0.5em;'>Estado Tribológico</div>", unsafe_allow_html=True)
    # Partículas Metálicas
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;'>
        <span>Particulas Metalicas</span>
        <span style='background:#e74c3c;color:#fff;padding:2px 16px;border-radius:8px;font-size:1.2em;font-weight:600;'>{registro['Hierro (Fe) ppm']} ppm</span>
    </div>
    <div class='tribo-bar-bg'><div class='tribo-bar tribo-bar-red' style='width:{min(registro['Hierro (Fe) ppm']/200,1)*100}%;background:#e74c3c;'></div></div>
    """, unsafe_allow_html=True)
    # TAN/TBN
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;'>
        <span>TAN/TBN</span>
        <span style='background:#e67e22;color:#fff;padding:2px 16px;border-radius:8px;font-size:1.2em;font-weight:600;'>{registro['TAN mg KOH/g']:.1f}</span>
    </div>
    <div class='tribo-bar-bg'><div class='tribo-bar tribo-bar-orange' style='width:{min(registro['TAN mg KOH/g']/5,1)*100}%;background:#e67e22;'></div></div>
    """, unsafe_allow_html=True)
    # Viscosidad
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;'>
        <span>Viscosidad</span>
        <span style='background:#16a085;color:#fff;padding:2px 16px;border-radius:8px;font-size:1.2em;font-weight:600;'>{registro['Viscosidad 100°C cSt(mm2/s)']:.1f} cSt</span>
    </div>
    <div class='tribo-bar-bg'><div class='tribo-bar tribo-bar-green' style='width:{min(registro['Viscosidad 100°C cSt(mm2/s)']/20,1)*100}%;background:#16a085;'></div></div>
    </div>
    """, unsafe_allow_html=True)

    # Tendencia Partículas Metálicas
    st.markdown("<div class='card' style='margin-bottom:0.7em;'><div style='font-size:1.1em;font-weight:600;margin-bottom:0.5em;'>Tendencia Particulas Metálicas</div>", unsafe_allow_html=True)
    df_camion['Fecha'] = pd.to_datetime(df_camion['Fecha'])
    df_camion_sorted = df_camion.sort_values('Fecha')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_camion_sorted['Fecha'], y=df_camion_sorted['Hierro (Fe) ppm'], mode='lines', line=dict(color='#3b7ddd', width=3)))
    fig.update_layout(
        plot_bgcolor='#232b3b',
        paper_bgcolor='#232b3b',
        font_color='#fff',
        margin=dict(l=0, r=0, t=0, b=0),
        height=110,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Componentes Críticos
    st.markdown("<div class='card' style='margin-bottom:0.7em;'><div style='font-size:1.1em;font-weight:600;margin-bottom:0.5em;'>Componentes Criticos</div>", unsafe_allow_html=True)
    for comp, val in zip(['Motor', 'Transmisión', 'Eje'], [0.7, 0.4, 0.6]):
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:0.7em;margin-bottom:0.2em;'>
            <span style='width:110px;'>{comp}</span>
            <div class='comp-bar-bg'><div class='comp-bar' style='width:{val*100}%;background:#3b7ddd;'></div></div>
        </div>
        """, unsafe_allow_html=True)

    # Impacto Económico
    st.markdown("<div class='impacto-card' style='margin-bottom:0.7em;'><div style='font-size:1.1em;font-weight:600;margin-bottom:0.5em;'>Impacto Económico <span style='font-size:0.8em;color:#b0b8c1;'>(Estim.)</span></div>", unsafe_allow_html=True)
    horas_ganadas = 85
    costo_evitado = 68000
    st.markdown(f"""
        <div style='display:flex;align-items:center;justify-content:space-between;'>
            <span>Horas Ganadas</span><span style='font-size:1.3em;font-weight:700;'>{horas_ganadas}</span>
        </div>
        <div style='display:flex;align-items:center;justify-content:space-between;'>
            <span>Costo Evitado</span><span style='font-size:1.3em;font-weight:700;'>${costo_evitado//1000}k</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='impacto-card'><div style='font-size:1.1em;font-weight:600;'>Impacto Económico<br><span style='font-size:0.8em;color:#b0b8c1;'>Estimado</span></div><div style='font-size:2em;font-weight:700;margin-top:0.2em;'>${costo_evitado//1000}k</div></div>", unsafe_allow_html=True)

with side_col:
    # Detalle de la Alerta
    st.markdown(f"""
    <div class='detalle-alerta-card'>
        <div style='font-size:1.3em;font-weight:700;margin-bottom:0.7em;'>Detalle de la Alerta</div>
        <div style='font-size:1.1em;'><b>Camion</b> &nbsp; {camion_sel}</div>
        <div style='font-size:1.1em;'><b>Componente</b> &nbsp; Motor</div>
        <div style='font-size:1.1em;'><b>Nivel actual de partículas</b> &nbsp; {registro['Hierro (Fe) ppm']} ppm (critico)</div>
        <div style='font-size:1.1em;'><b>Rango permitido</b> &nbsp; 0-80 ppm</div>
        <div style='font-size:1.1em;'><b>Fecha del último análisis</b> &nbsp; 1 Junio 2025</div>
        <div style='font-size:1.1em;'><b>Pronóstico de falla</b> &nbsp; 7 días</div>
        <div style='font-size:1.1em;'><b>Acción recomendada</b> &nbsp; Revisión técnica<br>y cambio de aceite</div>
        <div style='font-size:1.1em;'><b>Observaciones anteriores</b> &nbsp; Incremento<br>constante desde abril</div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='color:#b0b8c1;font-size:0.9em;'>Dashboard generado automáticamente. Datos reales y simulados para fines demostrativos.</div>", unsafe_allow_html=True)