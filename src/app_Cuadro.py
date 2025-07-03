import pandas as pd
import streamlit as st
import plotly.express as px
import os
import numpy as np

st.set_page_config(page_title="Dashboard de Métricas Clave", layout="wide")

# Ruta de los datos
ARCHIVO_CSV = "data/datos_generados_completos.csv"
ARCHIVO_PARQUET = "data/datos_generados_completos.parquet"

# Leer datos
if os.path.exists(ARCHIVO_PARQUET):
    df = pd.read_parquet(ARCHIVO_PARQUET)
else:
    df = pd.read_csv(ARCHIVO_CSV)

# Procesar fechas
if "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df[df["Fecha"].notnull()]
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
else:
    st.error("No se encontró columna 'Fecha' en los datos.")
    st.stop()

# Filtros en la barra lateral
with st.sidebar:
    st.header("Filtros")
    limpiar = st.button("Limpiar filtros")
    meses_disponibles = df["Mes"].unique()
    marcas_disponibles = ["Todos"] + sorted(df["Marca"].dropna().unique()) if "Marca" in df.columns else ["Todos"]
    if limpiar:
        mes_seleccionado = meses_disponibles[0]
        dia_seleccionado = "Todos"
        marca_seleccionada = "Todos"
    else:
        mes_seleccionado = st.selectbox("Selecciona el mes a visualizar:", sorted(meses_disponibles, reverse=True))
        df_mes = df[df["Mes"] == mes_seleccionado]
        dias_disponibles = df_mes["Fecha"].dt.date.unique()
        dia_seleccionado = st.selectbox("Selecciona el día a visualizar (opcional):", ["Todos"] + [str(d) for d in sorted(dias_disponibles, reverse=True)])
        marca_seleccionada = st.selectbox("Selecciona la marca (opcional):", marcas_disponibles)

    # Aplicar filtros
    df_mes = df[df["Mes"] == mes_seleccionado]
    if dia_seleccionado != "Todos":
        df_mes = df_mes[df_mes["Fecha"].dt.date == pd.to_datetime(dia_seleccionado).date()]
    if "Marca" in df_mes.columns and marca_seleccionada != "Todos":
        df_mes = df_mes[df_mes["Marca"] == marca_seleccionada]

# =====================
# FUNCIONES DE MÉTRICAS
# =====================
def calcular_disponibilidad_promedio(df):
    return round(df["Disponibilidad"].mean(), 2)

def calcular_reduccion_fallas_no_planificadas(df):
    if "Criticidad" not in df.columns:
        return None
    df = df.copy()
    df["EsFallaNoPlanificada"] = df["Criticidad"].str.lower().str.contains("critico")
    fallas_por_dia = df.groupby(df["Fecha"].dt.date)["EsFallaNoPlanificada"].sum()
    if len(fallas_por_dia) < 2:
        return None
    anterior, actual = fallas_por_dia.iloc[-2], fallas_por_dia.iloc[-1]
    if anterior == 0:
        return None
    return round(((anterior - actual) / anterior) * 100, 2)

def calcular_reduccion_paradas_criticas(df):
    if "Criticidad" not in df.columns:
        return None
    df = df.copy()
    df["EsParadaCritica"] = df["Criticidad"].str.lower().str.contains("critico")
    paradas_por_dia = df.groupby(df["Fecha"].dt.date)["EsParadaCritica"].sum()
    if len(paradas_por_dia) < 2:
        return None
    anterior, actual = paradas_por_dia.iloc[-2], paradas_por_dia.iloc[-1]
    if anterior == 0:
        return None
    return round(((anterior - actual) / anterior) * 100, 2)

def calcular_incremento_tbf_general(df):
    if "TBF" not in df.columns:
        return None
    tbf_por_dia = df.groupby(df["Fecha"].dt.date)["TBF"].mean()
    if len(tbf_por_dia) < 2:
        return None
    anterior, actual = tbf_por_dia.iloc[-2], tbf_por_dia.iloc[-1]
    if anterior == 0:
        return None
    return round(((actual - anterior) / anterior) * 100, 2)

def calcular_efectividad_alertas(df):
    if "Alerta Emitida" not in df.columns or "Alerta Evitó Falla" not in df.columns:
        return None
    total_alertas = df["Alerta Emitida"].sum()
    alertas_efectivas = df["Alerta Evitó Falla"].sum()
    if total_alertas == 0:
        return None
    return round((alertas_efectivas / total_alertas) * 100, 2)

def calcular_ahorro_total(df, costo_hora=800000):
    if "Alerta Evitó Falla" not in df.columns or "Tiempo Parada" not in df.columns:
        return None
    return int((df["Alerta Evitó Falla"] * df["Tiempo Parada"] * costo_hora).sum())

# =====================
# CÁLCULO DE MÉTRICAS
# =====================
metricas = {
    "Disponibilidad Promedio (%)": calcular_disponibilidad_promedio(df_mes),
    "Reducción Fallas No Planificadas (%)": calcular_reduccion_fallas_no_planificadas(df_mes),
    "Reducción Paradas Críticas (%)": calcular_reduccion_paradas_criticas(df_mes),
    "Incremento TBF General (%)": calcular_incremento_tbf_general(df_mes),
    "Efectividad de Alertas (%)": calcular_efectividad_alertas(df_mes),
    "Ahorro Total (CLP)": calcular_ahorro_total(df_mes)
}

# =====================
# DASHBOARD VISUAL
# =====================
st.title(":bar_chart: Cuadro Tablero Metricas Mas importantes")

# KPIs en una sola línea
for k, key in zip(st.columns(6), [
    "Disponibilidad Promedio (%)",
    "Reducción Fallas No Planificadas (%)",
    "Reducción Paradas Críticas (%)",
    "Incremento TBF General (%)",
    "Efectividad de Alertas (%)",
    "Ahorro Total (CLP)"
]):
    k.metric(key, metricas[key] if metricas[key] is not None else "N/A")

# Gráficos organizados en filas de 4
#st.subheader(":bar_chart: Evolución de Disponibilidad Operacional")
disp_diaria = df_mes.groupby(df_mes["Fecha"].dt.date)["Disponibilidad"].mean().reset_index()
fig_disp = px.line(disp_diaria, x="Fecha", y="Disponibilidad", markers=True, title="Evolución de Disponibilidad Operacional", color_discrete_sequence=px.colors.sequential.Viridis)

#st.subheader(":bar_chart: Evolución de TBF General")
tbf_diaria = df_mes.groupby(df_mes["Fecha"].dt.date)["TBF"].mean().reset_index()
fig_tbf = px.line(tbf_diaria, x="Fecha", y="TBF", markers=True, title="Evolución de TBF General", color_discrete_sequence=px.colors.sequential.Cividis)

#st.subheader(":bar_chart: Efectividad de Alertas por Día")
if "Alerta Emitida" in df_mes.columns and "Alerta Evitó Falla" in df_mes.columns:
    alertas_diaria = df_mes.groupby(df_mes["Fecha"].dt.date).agg({"Alerta Emitida": "sum", "Alerta Evitó Falla": "sum"}).reset_index()
    alertas_diaria["Efectividad (%)"] = (alertas_diaria["Alerta Evitó Falla"] / alertas_diaria["Alerta Emitida"]).fillna(0) * 100
    fig_alertas = px.bar(alertas_diaria, x="Fecha", y="Efectividad (%)", title="Efectividad de Alertas por Día", color="Efectividad (%)", color_continuous_scale="Plasma")
else:
    fig_alertas = None

#st.subheader(":bar_chart: Ahorro Total por Día")
if "Alerta Evitó Falla" in df_mes.columns and "Tiempo Parada" in df_mes.columns:
    ahorro_diario = df_mes.copy()
    ahorro_diario["Ahorro"] = ahorro_diario["Alerta Evitó Falla"] * ahorro_diario["Tiempo Parada"] * 800000
    ahorro_diario = ahorro_diario.groupby(ahorro_diario["Fecha"].dt.date)["Ahorro"].sum().reset_index()
    fig_ahorro = px.bar(ahorro_diario, x="Fecha", y="Ahorro", title="Ahorro Total por Día", color="Ahorro", color_continuous_scale="Rainbow")
else:
    fig_ahorro = None

# Nueva fila de 4 gráficos
#st.subheader(":bar_chart: Disponibilidad de Camiones % por Flota")
if "Disponibilidad" in df_mes.columns and "flota" in df_mes.columns:
    disp_flota = df_mes.groupby("flota")["Disponibilidad"].mean().reset_index()
    fig_disp_flota = px.bar(disp_flota, x="flota", y="Disponibilidad", title="Disponibilidad de Camiones % por Flota", color="Disponibilidad", color_continuous_scale="Viridis")
else:
    fig_disp_flota = None

#st.subheader(":bar_chart: Confiabilidad de Camiones por Flota")
if "Confiabilidad" in df_mes.columns and "flota" in df_mes.columns:
    conf_flota = df_mes.groupby("flota")["Confiabilidad"].mean().reset_index()
    fig_conf_flota = px.bar(conf_flota, x="flota", y="Confiabilidad", title="Confiabilidad de Camiones por Flota", color="Confiabilidad", color_continuous_scale="Cividis")
else:
    fig_conf_flota = None

#st.subheader(":bar_chart: Alertas por Marca")
if "Marca" in df_mes.columns and "Alerta Emitida" in df_mes.columns and "Alerta Evitó Falla" in df_mes.columns:
    alertas_marca = df_mes.groupby("Marca").agg({"Alerta Emitida": "sum", "Alerta Evitó Falla": "sum"}).reset_index()
    alertas_marca["Alertas de Falla"] = alertas_marca["Alerta Emitida"] - alertas_marca["Alerta Evitó Falla"]
    fig_alertas_marca = px.bar(alertas_marca.melt(id_vars="Marca", value_vars=["Alerta Emitida", "Alertas de Falla", "Alerta Evitó Falla"]),
                               x="Marca", y="value", color="variable", barmode="group",
                               title="Alertas Emitidas, de Falla y Evitadas por Marca")
else:
    fig_alertas_marca = None

# Mostrar los gráficos en filas de 4
#st.subheader(":bar_chart: Visualizaciones Principales")
row1 = st.columns(4)
with row1[0]:
    st.plotly_chart(fig_disp, use_container_width=True)
with row1[1]:
    st.plotly_chart(fig_tbf, use_container_width=True)
with row1[2]:
    if fig_alertas:
        st.plotly_chart(fig_alertas, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la efectividad de alertas.")
with row1[3]:
    if fig_ahorro:
        st.plotly_chart(fig_ahorro, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar el ahorro total.")

row2 = st.columns(4)
with row2[0]:
    if fig_disp_flota:
        st.plotly_chart(fig_disp_flota, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la disponibilidad por flota.")
with row2[1]:
    if fig_conf_flota:
        st.plotly_chart(fig_conf_flota, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la confiabilidad por flota.")
with row2[2]:
    if fig_alertas_marca:
        st.plotly_chart(fig_alertas_marca, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar las alertas por marca.")
with row2[3]:
    st.empty()

# =====================
# GRÁFICOS ADICIONALES SOLICITADOS
# =====================
row3 = st.columns(3)

# 1. Reducción de paradas críticas por flota
def reduccion_paradas_criticas_por_flota(df):
    if "Criticidad" not in df.columns or "flota" not in df.columns:
        return None
    resultados = []
    for flota, grupo in df.groupby("flota"):
        grupo = grupo.copy()
        grupo["EsParadaCritica"] = grupo["Criticidad"].str.lower().str.contains("critico")
        paradas_por_dia = grupo.groupby(grupo["Fecha"].dt.date)["EsParadaCritica"].sum()
        if len(paradas_por_dia) < 2:
            continue
        anterior, actual = paradas_por_dia.iloc[-2], paradas_por_dia.iloc[-1]
        if anterior == 0:
            continue
        reduccion = ((anterior - actual) / anterior) * 100
        resultados.append({"flota": flota, "Reducción Paradas Críticas (%)": round(reduccion, 2)})
    return pd.DataFrame(resultados) if resultados else None

with row3[0]:
    df_red_paradas = reduccion_paradas_criticas_por_flota(df_mes)
    if df_red_paradas is not None and not df_red_paradas.empty:
        fig_red_paradas = px.bar(df_red_paradas, x="flota", y="Reducción Paradas Críticas (%)", color="Reducción Paradas Críticas (%)", color_continuous_scale="Plasma", title="Reducción de Paradas Críticas por Flota")
        st.plotly_chart(fig_red_paradas, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la reducción de paradas críticas por flota.")

# 2. Reducción de fallas no planificadas por flota
def reduccion_fallas_no_planificadas_por_flota(df):
    if "Criticidad" not in df.columns or "flota" not in df.columns:
        return None
    resultados = []
    for flota, grupo in df.groupby("flota"):
        grupo = grupo.copy()
        grupo["EsFallaNoPlanificada"] = grupo["Criticidad"].str.lower().str.contains("critico")
        fallas_por_dia = grupo.groupby(grupo["Fecha"].dt.date)["EsFallaNoPlanificada"].sum()
        if len(fallas_por_dia) < 2:
            continue
        anterior, actual = fallas_por_dia.iloc[-2], fallas_por_dia.iloc[-1]
        if anterior == 0:
            continue
        reduccion = ((anterior - actual) / anterior) * 100
        resultados.append({"flota": flota, "Reducción Fallas No Planificadas (%)": round(reduccion, 2)})
    return pd.DataFrame(resultados) if resultados else None

with row3[1]:
    df_red_fallas = reduccion_fallas_no_planificadas_por_flota(df_mes)
    if df_red_fallas is not None and not df_red_fallas.empty:
        fig_red_fallas = px.bar(df_red_fallas, x="flota", y="Reducción Fallas No Planificadas (%)", color="Reducción Fallas No Planificadas (%)", color_continuous_scale="Viridis", title="Reducción de Fallas No Planificadas por Flota")
        st.plotly_chart(fig_red_fallas, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la reducción de fallas no planificadas por flota.")

# 3. Gráfico de torta de criticidad
def grafico_criticidad(df):
    if "Criticidad" not in df.columns:
        return None
    crit_counts = df["Criticidad"].value_counts().reset_index()
    crit_counts.columns = ["Criticidad", "Cantidad"]
    if crit_counts.empty:
        return None
    fig = px.pie(crit_counts, names="Criticidad", values="Cantidad", title="Distribución de Criticidad", hole=0.3, color_discrete_sequence=px.colors.sequential.RdBu)
    return fig

with row3[2]:
    fig_crit = grafico_criticidad(df_mes)
    if fig_crit:
        st.plotly_chart(fig_crit, use_container_width=True)
    else:
        st.info("No hay datos suficientes para graficar la criticidad.")

# =====================
# FÓRMULAS UTILIZADAS
# =====================
st.markdown("""
---
### Fórmulas Utilizadas
""")

st.latex(r"\text{Disponibilidad} = \left( \frac{\text{Tiempo Operativo}}{\text{Tiempo Total}} \right) \times 100")
st.latex(r"\text{Disponibilidad} = \frac{\text{Total horas} - \text{Tiempo Parada}}{\text{Total horas}} \times 100")
st.latex(r"\text{Reducción de paradas no planificadas (\%)} = \left( \frac{\text{Paradas Antes} - \text{Paradas Después}}{\text{Paradas Antes}} \right) \times 100")
st.latex(r"\text{Incremento (\%)} = \left( \frac{\text{TBF nuevo} - \text{TBF anterior}}{\text{TBF anterior}} \right) \times 100")
st.latex(r"\text{TBF} = \frac{\text{Tiempo Total Operativo}}{\text{Número de Fallas}}")
st.latex(r"\text{Ahorro Total} = \sum (\text{Costo estimado por falla evitada} \times \text{N° de fallas evitadas})")

st.markdown("""
Dashboard actualizado con KPIs reales, fórmulas visualizadas con st.latex y visualizaciones compactas - Julio 2025
""")

# Definición de los KPIs más importantes
kpi_tabla = pd.DataFrame([
    {
        "Nombre": "Disponibilidad Promedio (%)",
        "Objetivo": "Maximizar el tiempo operativo de la flota",
        "Fórmula / Ratio": r"Disponibilidad = \left( \frac{\text{Tiempo Operativo}}{\text{Tiempo Total}} \right) \times 100",
        "Meta": "≥ 85%",
        "Periodicidad": "Diaria/Mensual",
        "Responsable": "Jefe de Mantenimiento"
    },
    {
        "Nombre": "Reducción Fallas No Planificadas (%)",
        "Objetivo": "Disminuir las fallas inesperadas en la operación",
        "Fórmula / Ratio": r"Reducción = \left( \frac{\text{Paradas Antes} - \text{Paradas Después}}{\text{Paradas Antes}} \right) \times 100",
        "Meta": "≥ 10% reducción mensual",
        "Periodicidad": "Mensual",
        "Responsable": "Jefe de Operaciones"
    },
    {
        "Nombre": "Reducción Paradas Críticas (%)",
        "Objetivo": "Reducir la cantidad de paradas críticas",
        "Fórmula / Ratio": r"Reducción = \left( \frac{\text{Paradas Críticas Antes} - \text{Paradas Críticas Después}}{\text{Paradas Críticas Antes}} \right) \times 100",
        "Meta": "≥ 10% reducción mensual",
        "Periodicidad": "Mensual",
        "Responsable": "Supervisor de Flota"
    },
    {
        "Nombre": "Incremento TBF General (%)",
        "Objetivo": "Aumentar el tiempo medio entre fallas",
        "Fórmula / Ratio": r"Incremento = \left( \frac{\text{TBF nuevo} - \text{TBF anterior}}{\text{TBF anterior}} \right) \times 100",
        "Meta": "≥ 5% incremento mensual",
        "Periodicidad": "Mensual",
        "Responsable": "Analista de Confiabilidad"
    },
    {
        "Nombre": "Efectividad de Alertas (%)",
        "Objetivo": "Maximizar la cantidad de alertas que evitan fallas",
        "Fórmula / Ratio": r"Efectividad = \left( \frac{\text{Alertas que evitaron fallas}}{\text{Total de alertas emitidas}} \right) \times 100",
        "Meta": "≥ 70%",
        "Periodicidad": "Mensual",
        "Responsable": "Ingeniero Predictivo"
    },
    {
        "Nombre": "Ahorro Total (CLP)",
        "Objetivo": "Cuantificar el ahorro por fallas evitadas",
        "Fórmula / Ratio": r"Ahorro = \sum (\text{Costo estimado por falla evitada} \times \text{N° de fallas evitadas})",
        "Meta": "Maximizar",
        "Periodicidad": "Mensual",
        "Responsable": "Gerente de Mantenimiento"
    }
])

st.markdown("### Cuadro Resumen de KPIs Clave")
st.dataframe(kpi_tabla, use_container_width=True)

# Ejemplo de DataFrame
df_kpis = pd.DataFrame({
    "KPI": [
        "Disponibilidad",
        "Reducción de fallas no planificadas",
        "Reducción de paradas críticas",
        "Incremento TBF",
        "Efectividad de alertas",
        "Ahorro total"
    ],
    "Fórmula / Ratio": [
        "Tiempo Operativo / Tiempo Total x 100",
        "(Fallas Antes - Fallas Después) / Fallas Antes x 100",
        "(Paradas Críticas Antes - Paradas Críticas Después) / Paradas Críticas Antes x 100",
        "(TBF nuevo - TBF anterior) / TBF anterior x 100",
        "Alertas que evitaron fallas / Total de alertas emitidas x 100",
        "Costo estimado por falla evitada x N° de fallas evitadas"
    ],
    "Meta": [
        "≥ 95%",
        "≥ 20%",
        "≥ 15%",
        "≥ 10%",
        "≥ 80%",
        "≥ Maximizar"
    ],
    "Periodicidad": [
        "Mensual",
        "Mensual",
        "Mensual",
        "Mensual",
        "Mensual",
        "Mensual"
    ],
    "Responsable": [
        "Jefe de Mantenimiento",
        "Jefe de Mantenimiento",
        "Jefe de Mantenimiento",
        "Jefe de Mantenimiento",
        "Jefe de Mantenimiento",
        "Jefe de Mantenimiento"
    ]
})

st.dataframe(df_kpis, use_container_width=True)
