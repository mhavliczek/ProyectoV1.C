import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Técnico de Mantenimiento",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados
st.markdown("""
    <style>
        .main {background-color: #0e1117; color: #ffffff;}
        .stMetric {
            background-color: #1e2530;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .technical-container {
            background-color: #1e2530;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .parameter-critical {color: #ff4b4b !important;}
        .parameter-warning {color: #ffa600 !important;}
        .parameter-normal {color: #00cc66 !important;}
    </style>
""", unsafe_allow_html=True)

# Carga de datos
@st.cache_data(ttl=300)
def cargar_datos():
    df_disp = pd.read_parquet("data/datos_generados_Disponibilidad.parquet")
    df_conf = pd.read_parquet("data/metricas_confiabilidad.parquet")
    return df_disp, df_conf

df_disp, df_conf = cargar_datos()

# Título principal
st.title("⚙️ Dashboard Técnico de Mantenimiento")

# Filtros superiores
col1, col2, col3 = st.columns(3)
with col1:
    marca_sel = st.selectbox("Marca", df_disp["Marca"].unique())
with col2:
    modelo_sel = st.selectbox("Modelo", df_disp[df_disp["Marca"] == marca_sel]["Modelo"].unique())
with col3:
    flota_sel = st.selectbox("Unidad", df_disp[(df_disp["Marca"] == marca_sel) & 
                                              (df_disp["Modelo"] == modelo_sel)]["flota"].unique())

# Filtrar datos
df_unidad = df_disp[
    (df_disp["Marca"] == marca_sel) &
    (df_disp["Modelo"] == modelo_sel) &
    (df_disp["flota"] == flota_sel)
].copy()

# Análisis Tribológico
st.markdown("### 🔬 Análisis Tribológico")

# Partículas metálicas
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Concentración de Partículas Metálicas")
    particulas = {
        "Hierro (Fe)": {"valor": df_unidad["Hierro (Fe) ppm"].iloc[-1], "limite": 120},
        "Cobre (Cu)": {"valor": df_unidad["Cobre (Cu) ppm"].iloc[-1], "limite": 40},
        "Silicio (Si)": {"valor": df_unidad["Silicio (Si) ppm"].iloc[-1], "limite": 30},
        "Aluminio (Al)": {"valor": df_unidad["Aluminio (Al) ppm"].iloc[-1], "limite": 25}
    }
    
    for elemento, datos in particulas.items():
        valor = datos["valor"]
        limite = datos["limite"]
        estado = "normal" if valor < limite*0.7 else "warning" if valor < limite else "critical"
        
        st.markdown(f"""
        <div class="technical-container">
            <h4>{elemento}</h4>
            <p class="parameter-{estado}">{valor:.1f} ppm</p>
            <p>Límite: {limite} ppm</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    # Gráfico de radar para partículas
    categorias = list(particulas.keys())
    valores = [datos["valor"]/datos["limite"]*100 for datos in particulas.values()]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name='Actual'
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 150]
            )),
        showlegend=False,
        title="Análisis de Partículas (% del límite)"
    )
    st.plotly_chart(fig_radar)

# Tendencias de desgaste
st.markdown("### 📈 Tendencias de Desgaste")
col1, col2 = st.columns(2)

with col1:
    # Gráfico de tendencia Fe
    fig_fe = px.line(df_unidad, x="Fecha", y="Hierro (Fe) ppm",
                     title="Tendencia de Hierro (Fe)")
    fig_fe.add_hline(y=120, line_dash="dash", line_color="red",
                     annotation_text="Límite crítico")
    st.plotly_chart(fig_fe)

with col2:
    # Gráfico de tendencia Cu
    fig_cu = px.line(df_unidad, x="Fecha", y="Cobre (Cu) ppm",
                     title="Tendencia de Cobre (Cu)")
    fig_cu.add_hline(y=40, line_dash="dash", line_color="red",
                     annotation_text="Límite crítico")
    st.plotly_chart(fig_cu)

# Estado de Componentes
st.markdown("### 🛠️ Estado de Componentes Críticos")
componentes = ["Motor", "Transmisión", "Diferencial", "Sistema Hidráulico"]
col1, col2, col3, col4 = st.columns(4)

for comp, col in zip(componentes, [col1, col2, col3, col4]):
    with col:
        # Calcular estado del componente basado en partículas y otros parámetros
        estado = df_unidad[df_unidad["Componente"] == comp]["Criticidad"].iloc[-1] if not df_unidad[df_unidad["Componente"] == comp].empty else "Normal"
        color = "normal" if estado == "Normal" else "warning" if estado == "Precaución" else "critical"
        
        st.markdown(f"""
        <div class="technical-container">
            <h4>{comp}</h4>
            <p class="parameter-{color.lower()}">{estado}</p>
        </div>
        """, unsafe_allow_html=True)

# Predicción de Vida Útil
st.markdown("### ⏳ Predicción de Vida Útil")
col1, col2 = st.columns(2)

with col1:
    # Tabla de predicciones
    predicciones = pd.DataFrame({
        "Componente": componentes,
        "Horas Restantes": np.random.randint(100, 5000, size=len(componentes)),
        "Estado": ["Normal", "Precaución", "Normal", "Crítico"]
    })
    
    st.dataframe(predicciones.style.apply(lambda x: [
        f"background-color: {'#1e2530' if i%2==0 else '#2d3748'}; color: white" 
        for i in range(len(x))
    ], axis=0))

with col2:
    # Gráfico de barras para horas restantes
    fig_horas = px.bar(predicciones, x="Componente", y="Horas Restantes",
                      color="Estado",
                      color_discrete_map={
                          "Normal": "#00cc66",
                          "Precaución": "#ffa600",
                          "Crítico": "#ff4b4b"
                      })
    st.plotly_chart(fig_horas)

# Footer
st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Unidad: {flota_sel}") 