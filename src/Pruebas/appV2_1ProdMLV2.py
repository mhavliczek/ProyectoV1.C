import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import joblib

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Tribológico",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

############################### Modelo Machine Learning ################################################
# Cargar el modelo entrenado
@st.cache_resource
def cargar_modelo():
    return joblib.load("data/modelo_entrenado.joblib")

modelo = cargar_modelo()

# Cargar los nombres de características
@st.cache_resource
def cargar_feature_names():
    return joblib.load("data/feature_names.joblib")

feature_names = cargar_feature_names()

# Función para hacer predicciones
def predecir_criticidad(datos):
    # Codificar las variables categóricas
    datos_encoded = pd.get_dummies(datos).reindex(columns=feature_names, fill_value=0)
    # Hacer la predicción
    prediccion = modelo.predict(datos_encoded)
    return prediccion

# Función para generar valores automáticos de minerales y otros parámetros
def generar_valores_automaticos(equipo, componente, aceite_lubricante):
    # Definir rangos típicos basados en el equipo, componente y aceite lubricante
    valores_generados = {
        "Viscosidad 100°C cSt(mm2/s)": np.round(np.random.uniform(10, 20), 2),
        "TAN mg KOH/g": np.round(np.random.uniform(0, 4), 2),
        "TBN mg KOH/g": np.random.randint(0, 10),
        "Silicio (Si) ppm": np.random.randint(0, 50),
        "Hierro (Fe) ppm": np.random.randint(0, 300),
        "Aluminio (Al) ppm": np.random.randint(0, 30),
        "Cobre (Cu) ppm": np.random.randint(0, 50),
        "Cromo (Cr) ppm": np.random.randint(0, 10),
        "Níquel (Ni) ppm": np.random.randint(0, 10),
        "Residuo Ferroso Total mg/kg": np.random.randint(0, 600),
        "Contenido de Partículas Sólidas mg/L": np.random.randint(0, 100),
        "Índice de Oxidación": np.random.randint(0, 5)
    }
    return valores_generados

# Interfaz de usuario para hacer predicciones
st.subheader("Predicción Automática de Criticidad")

# Equipos generados en el script
equipos = [
    "CATERPILLAR 797F", "CATERPILLAR 988H", "CATERPILLAR 24M", "KOMATSU 930-E4",
    "KOMATSU 930E-4SE", "KOMATSU 980 E5", "KOMATSU 930 E3", "KOMATSU 930 E4", "KOMATSU 930 E5",
    "KOMATSU 950 E3", "CAEX", "KOMATSU 950 E4", "KOMATSU 960 E2-K"
]
equipo = st.selectbox("Selecciona Equipo:", equipos)

# Componentes generados en el script
componentes = [
    "MANDO FINAL", "TRANSMISIÓN", "DIFERENCIAL DEL", "MOTOR", "SISTEMA HIDRAULICO",
    "MANDO FINAL TRA.DER", "MANDO FINAL TRA.IZQ", "MASA DERECHA", "MASA IZQUIERDA",
    "MOTOR TRACCION IZQ", "MOTOR TRACCION DER", "DIFERENCIAL TRA"
]
componente = st.selectbox("Selecciona Componente:", componentes)

# Aceites Lubricantes asociados a los componentes
aceites_lubricantes = {
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
aceite_lubricante = aceites_lubricantes.get(componente, "No especificado")
st.write(f"Aceite Lubricante: {aceite_lubricante}")

# Generar valores automáticos
valores_generados = generar_valores_automaticos(equipo, componente, aceite_lubricante)
st.write("Valores Generados Automáticamente:")
st.json(valores_generados)

# Crear un DataFrame con los datos generados
input_data = pd.DataFrame({
    "Equipo": [equipo],
    "Componente": [componente],
    "Aceite Lubricante": [aceite_lubricante],
    **{k: [v] for k, v in valores_generados.items()}
})

# Botón para predecir
if st.button("Predecir"):
    prediccion = predecir_criticidad(input_data)
    st.success(f"Nivel de Criticidad Predicho: {prediccion[0]}")
######################################### Fin Modelo de ML ###################################


# Estilo personalizado para un diseño más elegante
st.markdown("""
<style>
.stApp {
    background-color: #FF6F00; /* Fondo naranja vibrante */
    color: #FFFFFF; /* Texto blanco para contraste */
}
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF; /* Texto blanco para los títulos */
    font-family: 'Arial', sans-serif; /* Fuente clara y profesional */
    font-weight: bold; /* Asegurar que los títulos sean prominentes */
}
p {
  color: #FFFFFF; /* Texto blanco */          
}
div.stButton > button {
    background-color: #FF6F00; /* Naranja vibrante */
    color: white; /* Texto blanco para contraste */
    border-radius: 5px; /* Bordes redondeados para un diseño moderno */
    border: none; /* Sin bordes adicionales */
    font-weight: bold; /* Texto en negrita para mayor visibilidad */
    transition: background-color 0.3s ease; /* Efecto suave al pasar el mouse */
}
div.stButton > button:hover {
    background-color: #E65C00; /* Un tono más oscuro de naranja al pasar el mouse */
}
[data-testid="stSidebar"] {
    background-color: #000000; /* Fondo negro para el sidebar */
    color: #FFFFFF; /* Texto blanco para contraste */
}
</style>
""", unsafe_allow_html=True)

# Título
st.title("📊 Dashboard de Monitoreo Análisis Tribológico")
st.title("Muestra Generada cada 2 hrs")

# Función para cargar datos
@st.cache_data(ttl=60)  # Actualiza los datos cada 60 segundos
def cargar_datos():
    try:
        return pd.read_csv("data/datos_generados.csv")
    except FileNotFoundError:
        st.error("El archivo 'datos_generados.csv' no existe. Asegúrate de que el script de generación de datos esté funcionando.")
        return pd.DataFrame()

# Cargar datos
df = cargar_datos()

# Verificar si el DataFrame está vacío
if df.empty:
    st.warning("No hay datos disponibles para mostrar.")
else:
    # Mostrar vista previa de los datos completos (colapsable)
    with st.expander("📋 Datos Completos"):
        st.dataframe(df)

    # Filtros
    st.sidebar.header("🔍 Filtros")
    equipo_seleccionado = st.sidebar.multiselect("Selecciona Equipo:", df["Equipo"].unique())
    componente_seleccionado = st.sidebar.multiselect("Selecciona Componente:", df["Componente"].unique())
    criticidad_seleccionada = st.sidebar.multiselect("Selecciona Nivel de Criticidad:", df["Criticidad"].unique())

    # Filtrar datos
    df_filtrado = df
    if equipo_seleccionado:
        df_filtrado = df_filtrado[df_filtrado["Equipo"].isin(equipo_seleccionado)]
    if componente_seleccionado:
        df_filtrado = df_filtrado[df_filtrado["Componente"].isin(componente_seleccionado)]
    if criticidad_seleccionada:
        df_filtrado = df_filtrado[df_filtrado["Criticidad"].isin(criticidad_seleccionada)]

    # Mostrar datos filtrados (colapsable)
    with st.expander("🎯 Datos Filtrados"):
        st.dataframe(df_filtrado)

    # Indicador de Semáforo
    st.markdown("#### 🚦 Indicador de Semáforo")
    nivel_residuo_ferroso = df_filtrado["Residuo Ferroso Total mg/kg"].mean()
    if nivel_residuo_ferroso < 200:
        st.success("🟢 Condiciones Normales")
    elif 200 <= nivel_residuo_ferroso < 400:
        st.warning("🟡 Nivel de Precaución")
    else:
        st.error("🔴 Nivel Crítico")

    # Visualizaciones
    st.subheader("📊 Visualizaciones Interactivas")
    col1, col2 = st.columns(2)

    # Gráfico de Barras: Desgaste por Hierro
    with col1:
        st.markdown("#### 📊 Desgaste por Hierro (ppm)")
        fig = px.bar(
            df_filtrado,
            x="Componente",
            y="Hierro (Fe) ppm",
            color="Componente",
            title="Desgaste Promedio por Hierro",
            labels={"Hierro (Fe) ppm": "Hierro (ppm)"},
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(size=10),
            xaxis_title="Componente",
            yaxis_title="Hierro (ppm)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Barras: Concentración de Silicio
    with col2:
        st.markdown("#### 📊 Concentración de Silicio (ppm)")
        fig = px.bar(
            df_filtrado,
            x="Componente",
            y="Silicio (Si) ppm",
            color="Componente",
            title="Concentración Promedio de Silicio",
            labels={"Silicio (Si) ppm": "Silicio (ppm)"},
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(size=10),
            xaxis_title="Componente",
            yaxis_title="Silicio (ppm)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

# Gráfico de Dispersión: Tendencia de Viscosidad
with col1:
    st.markdown("#### 📈 Dispersión de Viscosidad")
    df_filtrado['Fecha'] = pd.to_datetime(df_filtrado['Fecha'])
    df_agrupado = (
        df_filtrado.groupby([pd.Grouper(key="Fecha", freq="W"), "Componente"])
        .mean(numeric_only=True)
        .reset_index()
    )
    fig = px.scatter(
        df_agrupado,
        x="Fecha",
        y="Viscosidad 100°C cSt(mm2/s)",
        color="Componente",
        title="Dispersión de Viscosidad",
        labels={"Viscosidad 100°C cSt(mm2/s)": "Viscosidad"},
        template="plotly_dark",
        opacity=0.7,  # Transparencia para mejorar la visualización
        size_max=10   # Tamaño máximo de los puntos
    )
    fig.update_layout(
        font=dict(size=10),
        xaxis_title="Fecha",
        yaxis_title="Viscosidad",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# Gráfico de Distribución de Residuo Ferroso
with col2:
    st.markdown("#### 📊 Distribución de Residuo Ferroso")
    df_residuo = df_filtrado[df_filtrado["Residuo Ferroso Total mg/kg"] > 0]
    fig = px.box(
        df_residuo,
        x="Componente",
        y="Residuo Ferroso Total mg/kg",
        color="Componente",
        title="Distribución de Residuo Ferroso",
        labels={"Residuo Ferroso Total mg/kg": "Residuo Ferroso (mg/kg)"},
        template="plotly_dark"
    )
    fig.update_layout(
        font=dict(size=10),
        xaxis_title="Componente",
        yaxis_title="Residuo Ferroso (mg/kg)",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Proporción de Niveles de Criticidad
with col1:
    st.markdown("#### 📊 Proporción de Niveles de Criticidad")
    criticidad_counts = df_filtrado["Criticidad"].value_counts()
    fig = px.bar(
        x=criticidad_counts.values,
        y=criticidad_counts.index,
        orientation="h",
        title="Proporción de Criticidad",
        labels={"x": "Cantidad", "y": "Nivel de Criticidad"},
        color=criticidad_counts.index,
        color_discrete_sequence=["#2ca02c", "#ff7f0e", "#d62728"],
        template="plotly_dark"
    )
    fig.update_layout(
        font=dict(size=10),
        xaxis_title="Cantidad",
        yaxis_title="Nivel de Criticidad",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# Gráfico de Comparación de TAN y TBN
with col2:
    st.markdown("#### 📊 Comparación de TAN y TBN")
    fig = px.scatter(
        df_filtrado,
        x="TAN mg KOH/g",
        y="TBN mg KOH/g",
        color="Componente",
        title="Comparación de TAN y TBN",
        labels={"TAN mg KOH/g": "TAN (mg KOH/g)", "TBN mg KOH/g": "TBN (mg KOH/g)"},
        template="plotly_dark"
    )
    # Agregar línea de referencia (ejemplo: TAN = TBN)
    fig.add_shape(
        type="line",
        x0=df_filtrado["TAN mg KOH/g"].min(),
        y0=df_filtrado["TAN mg KOH/g"].min(),
        x1=df_filtrado["TAN mg KOH/g"].max(),
        y1=df_filtrado["TAN mg KOH/g"].max(),
        line=dict(color="white", width=2, dash="dash"),
        name="Línea de Referencia"
    )
    fig.update_layout(
        font=dict(size=10),
        xaxis_title="TAN (mg KOH/g)",
        yaxis_title="TBN (mg KOH/g)",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Contenido de Agua
    with col1:
        st.markdown("#### 📊 Distribución del Contenido de Agua")
        fig = px.box(
            df_filtrado,
            x="Componente",
            y="Contenido de agua %",
            color="Componente",
            title="Contenido de Agua",
            labels={"Contenido de agua %": "Agua (%)"},
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(size=10),
            xaxis_title="Componente",
            yaxis_title="Agua (%)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Criticidad por Equipo
    with col2:
        st.markdown("#### 📊 Criticidad por Equipo")
        criticidad_por_equipo = (
            df_filtrado.groupby(["Equipo", "Criticidad"]).size().unstack(fill_value=0)
        )
        fig = px.bar(
            criticidad_por_equipo,
            x=criticidad_por_equipo.index,
            y=criticidad_por_equipo.columns,
            title="Criticidad por Equipo",
            labels={"value": "Cantidad"},
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(size=10),
            xaxis_title="Equipo",
            yaxis_title="Cantidad",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Criticidad por Aceite Lubricante
    with col1:
        st.markdown("#### 📊 Criticidad por Aceite Lubricante")
        criticidad_por_aceite = (
            df_filtrado.groupby(["Aceite Lubricante", "Criticidad"]).size().unstack(fill_value=0)
        )
        fig = px.bar(
            criticidad_por_aceite,
            x=criticidad_por_aceite.index,
            y=criticidad_por_aceite.columns,
            title="Criticidad por Aceite Lubricante",
            labels={"value": "Cantidad"},
            template="plotly_dark"
        )
        fig.update_layout(
            font=dict(size=10),
            xaxis_title="Aceite Lubricante",
            yaxis_title="Cantidad",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)