import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import os
from datetime import datetime, timedelta

# Función para calcular alertas predictivas
def calcular_alertas(registro):
    alertas = []
    
    # Verificar niveles de partículas
    fe_ppm = get_safe_value(registro, "Hierro (Fe) ppm")
    si_ppm = get_safe_value(registro, "Silicio (Si) ppm")
    cu_ppm = get_safe_value(registro, "Cobre (Cu) ppm")
    visc = get_safe_value(registro, "Viscosidad 100°C cSt(mm2/s)")
    
    # Predicción de días hasta falla basado en niveles
    dias_estimados = None
    nivel_critico = False
    componente_afectado = None
    
    if fe_ppm > 120:
        dias_estimados = max(1, int(15 - (fe_ppm - 120)/10))
        nivel_critico = True
        alertas.append({
            'componente': 'Motor',
            'nivel': fe_ppm,
            'limite': 120,
            'tipo': 'Crítico',
            'mensaje': f'Nivel crítico de hierro: {fe_ppm:.1f} ppm',
            'dias': dias_estimados
        })
        componente_afectado = "Motor"
    elif fe_ppm > 80:
        alertas.append({
            'componente': 'Motor',
            'nivel': fe_ppm,
            'limite': 80,
            'tipo': 'Advertencia',
            'mensaje': f'Nivel elevado de hierro: {fe_ppm:.1f} ppm',
            'dias': None
        })
    
    if si_ppm > 30:
        dias_temp = max(1, int(10 - (si_ppm - 30)/5))
        if dias_estimados is None or dias_temp < dias_estimados:
            dias_estimados = dias_temp
            componente_afectado = "Sistema de Filtración"
        alertas.append({
            'componente': 'Sistema de Filtración',
            'nivel': si_ppm,
            'limite': 30,
            'tipo': 'Crítico',
            'mensaje': f'Nivel crítico de silicio: {si_ppm:.1f} ppm',
            'dias': dias_temp
        })
    
    if cu_ppm > 40:
        dias_temp = max(1, int(12 - (cu_ppm - 40)/5))
        if dias_estimados is None or dias_temp < dias_estimados:
            dias_estimados = dias_temp
            componente_afectado = "Cojinetes"
        alertas.append({
            'componente': 'Cojinetes',
            'nivel': cu_ppm,
            'limite': 40,
            'tipo': 'Crítico',
            'mensaje': f'Nivel crítico de cobre: {cu_ppm:.1f} ppm',
            'dias': dias_temp
        })
    
    if visc < 12:
        dias_temp = max(1, int(5 + visc/2))
        if dias_estimados is None or dias_temp < dias_estimados:
            dias_estimados = dias_temp
            componente_afectado = "Sistema de Lubricación"
        alertas.append({
            'componente': 'Sistema de Lubricación',
            'nivel': visc,
            'limite': 12,
            'tipo': 'Crítico',
            'mensaje': f'Viscosidad crítica: {visc:.1f} cSt',
            'dias': dias_temp
        })
    
    return alertas, dias_estimados, componente_afectado

# Configuración de la página y estilos
st.set_page_config(page_title="Mantenimiento Predictivo", layout="wide", initial_sidebar_state="collapsed")

# Estilos personalizados con tema oscuro
st.markdown("""
    <style>
        /* Tema oscuro general */
        .main {
            background-color: #0e1117;
            color: #ffffff;
            padding: 0rem 1rem;
        }
        
        /* Estilo para métricas */
        .stMetric {
            background-color: #1e2530;
            color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #2d3748;
        }
        .stMetric:hover {
            transform: translateY(-2px);
            transition: all 0.3s ease;
            box-shadow: 0 6px 8px rgba(0,0,0,0.4);
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 1.4rem !important;
        }
        div[data-testid="stMetricDelta"] {
            color: #a0aec0 !important;
            font-size: 1rem !important;
        }
        
        /* Estilos de texto */
        h1, h2, h3 {
            color: #ffffff !important;
            margin-bottom: 0.5rem;
        }
        h1 {
            font-size: 2.2rem;
            font-weight: 700;
        }
        h2 {
            font-size: 1.8rem;
            padding-top: 1rem;
        }
        h3 {
            font-size: 1.4rem;
            color: #a0aec0 !important;
        }
        .stText {
            background-color: #1e2530;
            color: #ffffff;
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.2rem 0;
        }
        
        /* Estados de alerta */
        .status-critical {
            color: #ff4b4b !important;
            font-weight: bold;
        }
        .status-warning {
            color: #ffa600 !important;
            font-weight: bold;
        }
        .status-normal {
            color: #00cc66 !important;
            font-weight: bold;
        }
        
        /* Separadores */
        hr {
            margin: 1.5rem 0;
            border: none;
            border-top: 1px solid #2d3748;
        }
        
        /* Contenedores personalizados */
        .custom-metric {
            background-color: #1e2530;
            color: #ffffff;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #2d3748;
            margin-bottom: 0.5rem;
        }
        
        /* Sección contenedora */
        .section-container {
            background-color: #1e2530;
            color: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            margin-bottom: 1.5rem;
            border: 1px solid #2d3748;
        }
        
        /* Selectbox y inputs */
        div[data-baseweb="select"] {
            background-color: #1e2530 !important;
            color: #ffffff !important;
        }
        .stSelectbox > div > div {
            background-color: #1e2530 !important;
            color: #ffffff !important;
        }
        
        /* Alertas y mensajes */
        .stAlert {
            background-color: #1e2530 !important;
            color: #ffffff !important;
            border: 1px solid #2d3748 !important;
        }
        
        /* Footer */
        .footer {
            color: #a0aec0;
            text-align: center;
            padding: 1rem;
            font-size: 0.8rem;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 10px;
            background: #0e1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #2d3748;
            border-radius: 5px;
        }
        ::-webkit-scrollbar-track {
            background: #1e2530;
        }
    </style>
""", unsafe_allow_html=True)

# Rutas de datos
DATA_PATH = "data/datos_generados_Disponibilidad.parquet"
MODEL_PATH = "data/modelo_entrenado.joblib"
FEATURES_PATH = "data/feature_names.joblib"

# Función auxiliar para obtener valor seguro del registro
def get_safe_value(registro, key, default=0):
    try:
        return float(registro[key]) if key in registro else default
    except (ValueError, TypeError):
        return default

# Carga de datos
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_parquet(DATA_PATH)
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

# Carga del modelo
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

# Título y descripción
st.title("Sistema de Mantenimiento Predictivo")

# Contenedor para filtros
with st.container():
    st.markdown("### 🔍 Selección de Equipo")
    col1, col2, col3 = st.columns(3)
    with col1:
        marca_options = sorted(df['Marca'].unique())
        marca_sel = st.selectbox("Marca", marca_options)
    with col2:
        modelos_options = sorted(df[df['Marca'] == marca_sel]['Modelo'].unique())
        modelo_sel = st.selectbox("Modelo", modelos_options)
    with col3:
        camiones_filtrados = sorted(df[(df['Marca'] == marca_sel) & (df['Modelo'] == modelo_sel)]['flota'].unique())
        camion_sel = st.selectbox("Número de Camión", camiones_filtrados, format_func=lambda x: f"Camión {x}")

# Filtrar datos para el camión seleccionado
df_camion = df[(df['flota'] == camion_sel) & 
               (df['Marca'] == marca_sel) & 
               (df['Modelo'] == modelo_sel)].sort_values('Fecha', ascending=False)
registro = df_camion.iloc[0]

# Contenedor principal
with st.container():
    # Sección 1: KPIs Principales
    st.markdown("### 📊 Indicadores Clave")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fallas Totales", 
                 len(df_camion[df_camion["Criticidad"] != "Normal"]),
                 delta="vs anterior")
    with col2:
        st.metric("Camiones Disponibles", 
                 len(df_camion[df_camion["Disponibilidad"] > 0.9]),
                 delta="activos")
    with col3:
        st.metric("MTTR (horas)", 
                 f"{round(df_camion['Tiempo Parada'].mean(), 2)}",
                 delta="promedio")
    with col4:
        st.metric("Confiabilidad", 
                 f"{round(df_camion['Confiabilidad'].mean(), 2)}%",
                 delta="del sistema")

    # Alerta Predictiva
    alertas, dias_estimados, componente_afectado = calcular_alertas(registro)
    
    if alertas:
        st.markdown("### ⚠️ Alerta Predictiva")
        col1, col2 = st.columns([2,1])
        
        with col1:
            for alerta in alertas:
                if alerta['tipo'] == 'Crítico':
                    st.error(f"🚨 {alerta['mensaje']}")
                else:
                    st.warning(f"⚠️ {alerta['mensaje']}")
        
        with col2:
            if dias_estimados is not None:
                st.markdown(f"""
                <div style='background-color: #2d1c1c; padding: 1rem; border-radius: 8px; border: 2px solid #ff4b4b;'>
                    <h4 style='color: #ff4b4b; margin: 0;'>Predicción de Falla</h4>
                    <p style='color: #ffffff; font-size: 1.2rem; margin: 0.5rem 0;'>
                        ⏰ {dias_estimados} días
                    </p>
                    <p style='color: #ff9999; margin: 0;'>
                        Componente: {componente_afectado}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Recomendaciones
                st.markdown("""
                <div style='background-color: #1c2d1c; padding: 1rem; border-radius: 8px; border: 2px solid #4bff4b; margin-top: 0.5rem;'>
                    <h4 style='color: #4bff4b; margin: 0;'>Acciones Recomendadas</h4>
                    <ul style='color: #ffffff; margin: 0.5rem 0;'>
                        <li>Programar mantenimiento preventivo</li>
                        <li>Realizar análisis de aceite adicional</li>
                        <li>Inspección visual del componente</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

    # Sección 2: Estado Tribológico
    st.markdown("### 🔬 Estado Tribológico")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        metricas = {
            "Hierro (Fe)": get_safe_value(registro, "Hierro (Fe) ppm"),
            "Silicio (Si)": get_safe_value(registro, "Silicio (Si) ppm"),
            "Cobre (Cu)": get_safe_value(registro, "Cobre (Cu) ppm"),
            "Viscosidad": get_safe_value(registro, "Viscosidad 100°C cSt(mm2/s)")
        }
        
        for nombre, valor in metricas.items():
            if nombre == "Hierro (Fe)":
                delta_color = "inverse" if valor > 80 else "normal"
                st.metric(f"{nombre} (ppm)", f"{valor:.1f}", 
                         delta=f"Límite: 80 ppm", 
                         delta_color=delta_color)
            elif nombre == "Silicio (Si)":
                delta_color = "inverse" if valor > 15 else "normal"
                st.metric(f"{nombre} (ppm)", f"{valor:.1f}", 
                         delta=f"Límite: 15 ppm",
                         delta_color=delta_color)
            elif nombre == "Cobre (Cu)":
                delta_color = "inverse" if valor > 20 else "normal"
                st.metric(f"{nombre} (ppm)", f"{valor:.1f}", 
                         delta=f"Límite: 20 ppm",
                         delta_color=delta_color)
            else:
                delta_color = "inverse" if valor < 14 else "normal"
                st.metric(f"{nombre} (cSt)", f"{valor:.1f}", 
                         delta=f"Mínimo: 14 cSt",
                         delta_color=delta_color)

    with col2:
        st.markdown("#### Estado de Criticidad")
        for nombre, valor in metricas.items():
            if nombre == "Hierro (Fe)":
                estado = "🔴 Crítico" if valor > 120 else "🟡 Precaución" if valor > 80 else "🟢 Normal"
                color = "status-critical" if valor > 120 else "status-warning" if valor > 80 else "status-normal"
            elif nombre == "Silicio (Si)":
                estado = "🔴 Crítico" if valor > 30 else "🟡 Precaución" if valor > 15 else "🟢 Normal"
                color = "status-critical" if valor > 30 else "status-warning" if valor > 15 else "status-normal"
            elif nombre == "Cobre (Cu)":
                estado = "🔴 Crítico" if valor > 40 else "🟡 Precaución" if valor > 20 else "🟢 Normal"
                color = "status-critical" if valor > 40 else "status-warning" if valor > 20 else "status-normal"
            else:
                estado = "🔴 Crítico" if valor < 12 else "🟡 Precaución" if valor < 14 else "🟢 Normal"
                color = "status-critical" if valor < 12 else "status-warning" if valor < 14 else "status-normal"
            st.markdown(f"<div class='custom-metric'><b>{nombre}</b>: <span class='{color}'>{estado}</span></div>", unsafe_allow_html=True)

    # Sección 3: Componentes Críticos
    st.markdown("### ⚙️ Componentes Críticos")
    componentes = {
        "Motor": 0.85,
        "Transmisión": 0.75,
        "Diferencial": 0.92,
        "Hidráulico": 0.88
    }

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (componente, valor) in enumerate(componentes.items()):
        with cols[i]:
            delta_color = "normal" if valor > 0.8 else "inverse"
            st.metric(componente, 
                     f"{valor*100:.1f}%",
                     delta=f"{'Óptimo' if valor > 0.8 else 'Atención'}",
                     delta_color=delta_color)

    # Sección 4: Impacto Económico
    st.markdown("### 💰 Impacto Económico")
    tiempo_operacion = get_safe_value(registro, "TBF", 24)
    costo_hora_operacion = 850
    costo_evitado = int(tiempo_operacion * costo_hora_operacion)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Horas Ganadas", 
                 int(tiempo_operacion),
                 delta="tiempo efectivo")
    with col2:
        st.metric("Costo Evitado", 
                 f"${costo_evitado//1000}k",
                 delta="ahorros")

    # Sección 5: Información Detallada
    st.markdown("### ℹ️ Información Detallada")
    detalles = {
        "Fecha del último análisis": registro['Fecha'],
        "Nivel de partículas de hierro": f"{get_safe_value(registro, 'Hierro (Fe) ppm')} ppm",
        "Rango permitido": "0-80 ppm",
        "Estado actual": "Crítico" if get_safe_value(registro, 'Hierro (Fe) ppm') > 120 else "Normal"
    }

    col1, col2 = st.columns(2)
    for i, (key, value) in enumerate(detalles.items()):
        with col1 if i < len(detalles)//2 else col2:
            st.markdown(f"<div class='custom-metric'><b>{key}</b>: {value}</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.caption("Dashboard de mantenimiento predictivo - Actualizado en tiempo real")