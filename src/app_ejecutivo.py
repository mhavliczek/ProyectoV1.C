import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configurar el layout para usar todo el ancho de la pantalla
st.set_page_config(layout="wide", page_title="Sistema de Mantenimiento Predictivo - Vista Ejecutiva")

# Estilos personalizados
st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
            color: #ffffff;
        }
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
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .parameter-critical {
            color: #ff4b4b !important;
            font-weight: bold;
        }
        .parameter-warning {
            color: #ffa600 !important;
            font-weight: bold;
        }
        .parameter-normal {
            color: #00cc66 !important;
            font-weight: bold;
        }
        .custom-metric {
            background-color: #1e2530;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .custom-metric b {
            color: #ffffff;
            font-size: 1.1em;
        }
        /* Estilo para los contenedores */
        div[data-testid="stVerticalBlock"] > div {
            background-color: #1e2530;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        /* Estilo para los títulos */
        h1, h2, h3 {
            color: #ffffff !important;
            font-weight: bold;
        }
        /* Estilo para los selectbox */
        div[data-baseweb="select"] {
            background-color: #262730;
            border-radius: 5px;
        }
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
st.title("🎯 Dashboard Ejecutivo de Mantenimiento")
st.markdown("### Vista General de la Flota CAEX")

# Filtros superiores
col1, col2, col3 = st.columns(3)
with col1:
    marca_sel = st.selectbox("Marca", df_disp["Marca"].unique())
with col2:
    modelo_sel = st.selectbox("Modelo", df_disp[df_disp["Marca"] == marca_sel]["Modelo"].unique())
with col3:
    periodo = st.selectbox("Período", ["Último Mes", "Última Semana", "Últimas 24 horas"])

# Filtrar datos
df_filtrado = df_disp[
    (df_disp["Marca"] == marca_sel) &
    (df_disp["Modelo"] == modelo_sel)
].copy()

# KPIs Principales
st.markdown("### 📊 KPIs Principales")
col1, col2, col3, col4 = st.columns(4)

# Disponibilidad promedio
disponibilidad = df_filtrado["Disponibilidad"].mean() * 100
with col1:
    st.metric(
        "Disponibilidad Flota",
        f"{disponibilidad:.1f}%",
        delta=f"{(disponibilidad - 85):.1f}%" if disponibilidad > 85 else f"{(disponibilidad - 85):.1f}%",
        delta_color="normal" if disponibilidad > 85 else "inverse"
    )

# MTTR promedio
mttr = df_filtrado["Tiempo Parada"].mean()
with col2:
    st.metric(
        "MTTR Promedio",
        f"{mttr:.1f} hrs",
        delta=f"{(24 - mttr):.1f} hrs",
        delta_color="normal" if mttr < 24 else "inverse"
    )

# MTBF promedio
mtbf = df_filtrado["TBF"].mean()
with col3:
    st.metric(
        "MTBF Promedio",
        f"{mtbf:.1f} hrs",
        delta=f"{(mtbf - 168):.1f} hrs",
        delta_color="normal" if mtbf > 168 else "inverse"
    )

# Confiabilidad promedio
confiabilidad = df_filtrado["Confiabilidad"].mean() * 100
with col4:
    st.metric(
        "Confiabilidad",
        f"{confiabilidad:.1f}%",
        delta=f"{(confiabilidad - 90):.1f}%",
        delta_color="normal" if confiabilidad > 90 else "inverse"
    )

# Mapa de calor de criticidad
st.markdown("### 🔥 Mapa de Criticidad por Unidad")
df_heatmap = df_filtrado.pivot_table(
    index="flota",
    columns="Componente",
    values="Criticidad",
    aggfunc="last"
)

# Convertir criticidad a valores numéricos
criticidad_map = {"Normal": 0, "Precaución": 1, "Crítico": 2}
df_heatmap = df_heatmap.replace(criticidad_map)

fig_heatmap = px.imshow(
    df_heatmap,
    color_continuous_scale=["green", "yellow", "red"],
    aspect="auto"
)
fig_heatmap.update_layout(
    title="Estado de Componentes por Unidad",
    xaxis_title="Componente",
    yaxis_title="Número de Flota",
    height=400
)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Tendencias de disponibilidad
st.markdown("### 📈 Tendencias de Disponibilidad")
df_tendencia = df_filtrado.groupby("Fecha")["Disponibilidad"].mean().reset_index()
fig_tendencia = px.line(
    df_tendencia,
    x="Fecha",
    y="Disponibilidad",
    title="Evolución de Disponibilidad"
)
fig_tendencia.update_layout(height=400)
st.plotly_chart(fig_tendencia, use_container_width=True)

# Alertas Activas
st.markdown("### ⚠️ Alertas Activas")
alertas = df_filtrado[df_filtrado["Criticidad"] != "Normal"].sort_values("Fecha", ascending=False)

if not alertas.empty:
    for _, alerta in alertas.head(5).iterrows():
        with st.container():
            fecha_str = alerta['Fecha']
            if isinstance(fecha_str, str):
                try:
                    fecha = pd.to_datetime(fecha_str)
                    fecha_formateada = fecha.strftime('%Y-%m-%d %H:%M')
                except:
                    fecha_formateada = fecha_str
            else:
                fecha_formateada = alerta['Fecha'].strftime('%Y-%m-%d %H:%M')
                
            st.markdown(f"""
            <div class="metric-container">
                <h4>Alerta en {alerta['flota']} - {alerta['Componente']}</h4>
                <p class="{alerta['Criticidad'].lower()}">{alerta['Criticidad']}</p>
                <p>Fecha: {fecha_formateada}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No hay alertas activas en este momento")

# Footer
st.markdown("---")
st.caption("Dashboard actualizado en tiempo real | Última actualización: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")) 