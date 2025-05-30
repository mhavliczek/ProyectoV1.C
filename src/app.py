import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import os

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(page_title="📊 Dashboard Tribológico CAEX", layout="wide")
st.title("📊 Dashboard de Análisis Predictivo Tribológico")
st.markdown("### Flota de Camiones CAEX - División Radomiro Tomic")

# Rutas
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
        df_datos = pd.read_parquet(DATA_PATH)
        return df_datos
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {e}")
        return pd.DataFrame()

@st.cache_resource
def cargar_modelo():
    if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
        try:
            modelo = joblib.load(MODEL_PATH)
            feature_names = joblib.load(FEATURES_PATH)
            return modelo, feature_names
        except Exception as e:
            st.warning(f"⚠️ No se pudo cargar el modelo: {e}")
    else:
        st.warning("⚠️ Archivos del modelo no encontrados.")
    return None, None

# Cargar datos y modelo
df_datos = cargar_datos()
modelo, feature_names = cargar_modelo()
modelo_disponible = modelo is not None

# ==============================
# FILTROS INTERACTIVOS
# ==============================
st.sidebar.header("🔎 Filtros de Datos")

marca_filtro = st.sidebar.multiselect(
    "Marca",
    options=df_datos["Marca"].unique() if not df_datos.empty else [],
    default=df_datos["Marca"].unique() if not df_datos.empty else []
)

componente_filtro = st.sidebar.multiselect(
    "Componente",
    options=df_datos["Componente"].unique() if not df_datos.empty else [],
    default=df_datos["Componente"].unique() if not df_datos.empty else []
)

criticidad_filtro = st.sidebar.multiselect(
    "Nivel de Criticidad",
    options=["Critico", "Atencion", "Normal"],
    default=["Critico", "Atencion", "Normal"]
)

# Aplicar filtros
if not df_datos.empty:
    df_filtrado = df_datos[
        df_datos["Marca"].isin(marca_filtro) &
        df_datos["Componente"].isin(componente_filtro) &
        df_datos["Criticidad"].isin(criticidad_filtro)
    ]
else:
    df_filtrado = pd.DataFrame()

# Verificar si hay datos
if df_filtrado.empty:
    st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================
# INDICADORES CLAVE
# ==============================
st.markdown("## 🔑 Indicadores Clave")

metricas_actuales = {
    "Fallas Totales": len(df_filtrado[df_filtrado["Criticidad"] != "Normal"]),
    "Camiones Disponibles": len(df_filtrado[df_filtrado["Disponibilidad"] > 0.9]),
    "MTTR (horas)": round(df_filtrado["Tiempo Parada"].mean(), 2),
    "Tasa de Fallas": round(len(df_filtrado[df_filtrado["Criticidad"] == "Critico"]) / len(df_filtrado), 4),
    "MTBF (horas)": round(df_filtrado["TBF"].mean(), 2),
    "Confiabilidad (%)": round(df_filtrado["Confiabilidad"].mean(), 2)
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Fallas Totales", metricas_actuales["Fallas Totales"])
with col2:
    st.metric("Camiones Disponibles", metricas_actuales["Camiones Disponibles"])
with col3:
    st.metric("Tasa de Fallas", f"{metricas_actuales['Tasa de Fallas']:.4f}")
with col4:
    st.metric("Confiabilidad", f"{metricas_actuales['Confiabilidad (%)']:.2f}%")

# ==============================
# GRÁFICOS INTERACTIVOS
# ==============================
st.markdown("### 📉 Disponibilidad por Camión")
fig = px.line(
    df_filtrado.sort_values(by="flota"),
    x="flota",
    y="Disponibilidad",
    color="Marca",
    title="Disponibilidad por Número de Flota"
)
st.plotly_chart(fig, use_container_width=True)


st.markdown("### 📅 Tendencia Diaria de Fallas")
df_filtrado["Fecha"] = pd.to_datetime(df_filtrado["Fecha"])
fallas_diarias = (
    df_filtrado[df_filtrado["Criticidad"] != "Normal"]
    .groupby(df_filtrado["Fecha"].dt.date)
    .size()
)
fig = px.line(
    x=fallas_diarias.index,
    y=fallas_diarias.values,
    title="Fallas Diarias",
    labels={"x": "Fecha", "y": "Número de Fallas"}
)
st.plotly_chart(fig, use_container_width=True)


st.markdown("## 📈 Gráficos de Análisis")

# Distribución de criticidad
st.markdown("### 📊 Distribución de Criticidad")
criticidad_counts = df_filtrado["Criticidad"].value_counts()
color_map = {"Critico": "#d62728", "Atencion": "#ff7f0e", "Normal": "#2ca02c"}
fig = px.pie(
    names=criticidad_counts.index,
    values=criticidad_counts.values,
    title="Distribución de Criticidad",
    color=criticidad_counts.index,
    color_discrete_map=color_map,
    hole=0.4
)
st.plotly_chart(fig, use_container_width=True)

# Hierro vs Viscosidad
st.markdown("### 🧪 Hierro (ppm) vs Viscosidad")
fig = px.scatter(
    df_filtrado,
    x="Viscosidad 100°C cSt(mm2/s)",
    y="Hierro (Fe) ppm",
    color="Criticidad",
    hover_data=["Marca", "Componente"],
    title="Hierro vs Viscosidad por Criticidad"
)
st.plotly_chart(fig, use_container_width=True)

# Disponibilidad por marca
st.markdown("### 🚛 Disponibilidad Promedio por Marca")
fig = px.bar(
    df_filtrado.groupby("Marca")["Disponibilidad"].mean().reset_index(),
    x="Marca",
    y="Disponibilidad",
    color="Marca",
    title="Disponibilidad Promedio por Marca",
    range_y=[0, 1]
)
st.plotly_chart(fig, use_container_width=True)

# TBF por componente
st.markdown("### ⏳ TBF (Tiempo Entre Fallas) por Componente")
fig = px.box(
    df_filtrado,
    x="Componente",
    y="TBF",
    color="Marca",
    title="TBF por Componente y Marca"
)
st.plotly_chart(fig, use_container_width=True)

# ==============================
# PREDICCIÓN ML - INTERFAZ MEJORADA
# ==============================
if modelo_disponible:
    st.sidebar.header("🧠 Predicción Automática")

    # Seleccionar Equipo
    equipos = ["CATERPILLAR 797F", "KOMATSU 930 E3", "KOMATSU 930 E4", "KOMATSU 930 E4SE", "KOMATSU 930 E5"]
    equipo_seleccionado = st.sidebar.selectbox("Selecciona Equipo:", equipos)

    # Seleccionar Componente
    componentes = list(componentes_aceites.keys())
    componente_seleccionado = st.sidebar.selectbox("Selecciona Componente:", componentes)

    # Obtener aceite basado en componente
    aceite_seleccionado = componentes_aceites.get(componente_seleccionado, "MOBIL DELVAC 15W40")
    st.sidebar.markdown(f"**Aceite Lubricante:** {aceite_seleccionado}")

    # Función para generar valores típicos aleatorios
    def generar_valores_automaticos(marca, componente):
        """Genera valores típicos según componente"""
        return {
            "Viscosidad 100°C cSt(mm2/s)": round(np.random.uniform(10, 20), 2),
            "Hierro (Fe) ppm": np.random.randint(0, 300),
            "Conten ido de agua %": round(np.random.uniform(0, 1), 2),
            "Silicio (Si) ppm": np.random.randint(0, 50),
            "Aluminio (Al) ppm": np.random.randint(0, 30),
            "Cobre (Cu) ppm": np.random.randint(0, 50),
            "Cromo (Cr) ppm": np.random.randint(0, 10),
            "Níquel (Ni) ppm": np.random.randint(0, 10),
            "TAN mg KOH/g": round(np.random.uniform(0, 3), 2),
            "TBN mg KOH/g": np.random.randint(0, 10),
            "Residuo Ferroso Total mg/kg": np.random.randint(0, 600)
        }

    # Generar valores automáticos
    #valores_generados = generar_valores_automaticos(equipo_seleccionado, componente_seleccionado)
    valores_generados = generar_valores_automaticos(equipo_seleccionado.split()[0], componente_seleccionado)

    # Mostrar valores generados
    st.sidebar.markdown("### Valores Generados:")
    for key, value in valores_generados.items():
        st.sidebar.write(f"{key}: `{value}`")

    if st.sidebar.button("🔍 Predecir Criticidad"):
        # Crear DataFrame de entrada
        input_df = pd.DataFrame([{
            "Marca": equipo_seleccionado.split()[0],  # Extraer marca del nombre del equipo
            "Componente": componente_seleccionado,
            "Aceite Lubricante": aceite_seleccionado,
            **valores_generados
        }])

        # Aplicar get_dummies y reindexar
        input_encoded = pd.get_dummies(input_df)
        input_encoded = input_encoded.reindex(columns=feature_names, fill_value=0)

        # Hacer predicción
        try:
            prediccion = modelo.predict(input_encoded)
            st.sidebar.success(f"🚨 Nivel de Criticidad Predicho: **{prediccion[0]}**")
        except Exception as e:
            st.sidebar.error(f"❌ Error al hacer predicción: {e}")

# ==============================
# DATOS COMPLETOS (Colapsable)
# ==============================
with st.expander("📋 Ver Datos Completos"):
    st.dataframe(df_filtrado)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("📌 *Datos simulados basados en información real operacional de Codelco - División Radomiro Tomic*")