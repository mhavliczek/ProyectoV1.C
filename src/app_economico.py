import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Económico de Mantenimiento",
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
        .economic-container {
            background-color: #1e2530;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .savings {color: #00cc66 !important;}
        .cost {color: #ff4b4b !important;}
        .neutral {color: #ffa600 !important;}
    </style>
""", unsafe_allow_html=True)

# Carga de datos
@st.cache_data(ttl=300)
def cargar_datos():
    df_disp = pd.read_parquet("data/datos_generados_Disponibilidad.parquet")
    df_conf = pd.read_parquet("data/metricas_confiabilidad.parquet")
    return df_disp, df_conf

df_disp, df_conf = cargar_datos()

# Constantes económicas
COSTO_HORA_OPERACION = 850  # USD por hora
COSTO_MANTENIMIENTO_PREVENTIVO = 5000  # USD por intervención
COSTO_MANTENIMIENTO_CORRECTIVO = 15000  # USD por intervención

# Título principal
st.title("💰 Dashboard Económico de Mantenimiento")

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

# Cálculos económicos
df_filtrado["Costo Hora"] = COSTO_HORA_OPERACION
df_filtrado["Horas Perdidas"] = df_filtrado["Tiempo Parada"]
df_filtrado["Costo Perdido"] = df_filtrado["Horas Perdidas"] * df_filtrado["Costo Hora"]

# Impacto Económico General
st.markdown("### 📊 Impacto Económico General")
col1, col2, col3, col4 = st.columns(4)

# Costo total perdido
costo_total = df_filtrado["Costo Perdido"].sum()
with col1:
    st.metric(
        "Costo Total Perdido",
        f"${costo_total:,.0f}",
        delta="-10% vs mes anterior"
    )

# Ahorro estimado
ahorro_estimado = costo_total * 0.3  # 30% de ahorro potencial
with col2:
    st.metric(
        "Ahorro Potencial",
        f"${ahorro_estimado:,.0f}",
        delta="Preventivo vs Correctivo"
    )

# Costo por hora promedio
costo_hora_promedio = df_filtrado["Costo Perdido"].mean()
with col3:
    st.metric(
        "Costo por Hora Promedio",
        f"${costo_hora_promedio:,.0f}",
        delta="vs objetivo"
    )

# Eficiencia económica
eficiencia = (1 - df_filtrado["Tiempo Parada"].sum() / (len(df_filtrado) * 24)) * 100
with col4:
    st.metric(
        "Eficiencia Económica",
        f"{eficiencia:.1f}%",
        delta=f"{eficiencia - 90:.1f}%"
    )

# Análisis de Costos por Tipo de Mantenimiento
st.markdown("### 💵 Análisis de Costos por Tipo de Mantenimiento")
col1, col2 = st.columns(2)

with col1:
    # Gráfico de torta de costos
    datos_costos = {
        "Tipo": ["Preventivo", "Correctivo", "Predictivo"],
        "Costo": [COSTO_MANTENIMIENTO_PREVENTIVO * 10,
                 COSTO_MANTENIMIENTO_CORRECTIVO * 5,
                 COSTO_MANTENIMIENTO_PREVENTIVO * 2]
    }
    df_costos = pd.DataFrame(datos_costos)
    
    fig_costos = px.pie(df_costos, values="Costo", names="Tipo",
                       title="Distribución de Costos por Tipo de Mantenimiento")
    st.plotly_chart(fig_costos)

with col2:
    # Comparativa de costos
    fig_comp = go.Figure(data=[
        go.Bar(name="Real", x=["Preventivo", "Correctivo", "Predictivo"],
               y=[50000, 75000, 10000]),
        go.Bar(name="Presupuestado", x=["Preventivo", "Correctivo", "Predictivo"],
               y=[60000, 40000, 15000])
    ])
    fig_comp.update_layout(title="Comparativa Costos Real vs Presupuestado")
    st.plotly_chart(fig_comp)

# Proyección de Costos
st.markdown("### 📈 Proyección de Costos y Ahorros")
col1, col2 = st.columns(2)

with col1:
    # Tendencia de costos
    fecha_inicial = pd.to_datetime(df_filtrado["Fecha"].min())
    fecha_final = pd.to_datetime(df_filtrado["Fecha"].max())
    fechas = pd.date_range(
        start=fecha_inicial,
        end=fecha_final + pd.Timedelta(days=30),
        freq='D'
    )
    
    tendencia = pd.DataFrame({
        "Fecha": fechas,
        "Costo Proyectado": range(len(fechas))
    })
    
    fig_tendencia = px.line(tendencia, x="Fecha", y="Costo Proyectado",
                           title="Tendencia y Proyección de Costos")
    st.plotly_chart(fig_tendencia)

with col2:
    # ROI por intervención
    intervenciones = {
        "Tipo": ["Cambio Aceite", "Overhaul Motor", "Cambio Filtros", "Reparación Transmisión"],
        "Costo": [1000, 50000, 500, 25000],
        "Beneficio": [5000, 150000, 2000, 75000]
    }
    df_roi = pd.DataFrame(intervenciones)
    df_roi["ROI"] = (df_roi["Beneficio"] - df_roi["Costo"]) / df_roi["Costo"] * 100
    
    fig_roi = px.bar(df_roi, x="Tipo", y="ROI",
                     title="ROI por Tipo de Intervención")
    st.plotly_chart(fig_roi)

# Oportunidades de Ahorro
st.markdown("### 💡 Oportunidades de Ahorro Identificadas")

oportunidades = [
    {
        "titulo": "Optimización de Mantenimiento Preventivo",
        "ahorro": 25000,
        "descripcion": "Reducción de frecuencia basada en análisis predictivo"
    },
    {
        "titulo": "Mejora en Gestión de Inventario",
        "ahorro": 15000,
        "descripcion": "Optimización de stock de repuestos críticos"
    },
    {
        "titulo": "Implementación de Monitoreo Continuo",
        "ahorro": 35000,
        "descripcion": "Reducción de paradas no programadas"
    }
]

for oportunidad in oportunidades:
    st.markdown(f"""
    <div class="economic-container">
        <h4>{oportunidad['titulo']}</h4>
        <p class="savings">Ahorro Potencial: ${oportunidad['ahorro']:,}</p>
        <p>{oportunidad['descripcion']}</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Tipo de cambio: 1 USD = 850 CLP") 