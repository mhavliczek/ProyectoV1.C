import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import time

# ==============================
# ARCHIVOS DE SALIDA PRINCIPALES
# ==============================
# - ARCHIVO_DATOS: contiene todos los datos generados (CSV y Parquet)
#   Ejemplo: data/datos_generados_completos.csv, data/datos_generados_completos.parquet
# - ARCHIVO_METRICAS: contiene todas las métricas calculadas (CSV y Parquet)
#   Ejemplo: data/metricas_completas.csv, data/metricas_completas.parquet
# ==============================

# ==============================
# CONFIGURACIÓN PRINCIPAL
# ==============================
num_komatsu = 68
num_caterpillar = 39
num_registros = num_komatsu + num_caterpillar

# Porcentaje de efectividad de alertas (puede ser ajustado)
EFECTIVIDAD_ALERTAS = 0.7  # 70% por defecto
# Costo mensual por fallas tribológicas (CLP)
COSTO_MENSUAL_TRIBOLOGICAS = 132_000_000  # 165 h x $800.000
# Costo por hora de camión detenido (CLP)
COSTO_HORA_CAMION_DETENIDO = 800_000
# Costo estimado por falla evitada (puede ser ajustado o calculado)
# Por defecto, se puede estimar como el costo por hora de camión detenido multiplicado por el tiempo promedio de parada de una falla crítica
# Este valor puede ser recalculado dinámicamente si se desea
COSTO_FALLA_EVITADA = COSTO_HORA_CAMION_DETENIDO * 12  # Ejemplo: 12 horas promedio por falla crítica

# Rango de flotas por marca
flota_caterpillar = list(range(900, 940))  # Caterpillar: 900-939
flota_komatsu = list(range(500, 569))      # Komatsu: 500-568

# Distribución de modelos por marca
modelos_komatsu = ["KOMATSU 930 E3"] * 23 + ["KOMATSU 930 E4"] * 22 + ["KOMATSU 930 E4SE"] * 11 + ["KOMATSU 930 E5"] * 12
modelos_caterpillar = ["CATERPILLAR 797F"] * 13 + ["CATERPILLAR 798AC-A"] * 13 + ["CATERPILLAR 798AC-P"] * 13

# Probabilidades de criticidad por marca
prob_criticidad = {
    "CATERPILLAR": {"Critico": 0.1, "Atencion": 0.12, "Normal": 0.78},
    "KOMATSU": {"Critico": 0.13, "Atencion": 0.14, "Normal": 0.73}
}

# Tiempos de parada por marca (horas)
tiempos_parada = {
    "CATERPILLAR": (4, 7),
    "KOMATSU": (5, 6)
}

# Componentes y aceites lubricantes asociados
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

# Tipos de muestreo
cambioLubricanate = ["Muestreo", "Cambio Aceite"]

# Variables globales para mantener el estado correlativo
NUM_MUESTRA_LETRAS = "ABCDE"
NUM_MUESTRA_DIGITOS = 0
NUM_REGISTRO = 0

# Nombres de archivos de salida (puedes cambiarlos aquí)
ARCHIVO_DATOS = "data/datos_generados_completos.csv"
ARCHIVO_METRICAS = "data/metricas_completas.csv"

# ==============================
# FUNCIONES DE APOYO
# ==============================
def cargar_estado():
    """Carga el estado previo de números de muestra y registro desde un archivo"""
    global NUM_MUESTRA_DIGITOS, NUM_REGISTRO
    try:
        with open("data/estado_generador.txt", "r") as f:
            lineas = f.readlines()
            if len(lineas) >= 2:
                NUM_MUESTRA_DIGITOS = int(lineas[0].strip())
                NUM_REGISTRO = int(lineas[1].strip())
    except FileNotFoundError:
        pass

def guardar_estado():
    """Guarda el estado actual de números de muestra y registro en un archivo"""
    os.makedirs("data", exist_ok=True)
    with open("data/estado_generador.txt", "w") as f:
        #f.write(f"{NUM_MUESTRA_DIGITOS}\n{NUM_REGISTRO}\n")
        f.write(f"{NUM_MUESTRA_DIGITOS}{NUM_REGISTRO}\n")

def generar_criticidad(marca):
    """Genera criticidad basada en probabilidades ajustadas por marca"""
    opciones = list(prob_criticidad[marca].keys())
    pesos = list(prob_criticidad[marca].values())
    return random.choices(opciones, weights=pesos, k=1)[0]


def calcular_disponibilidad(marca, criticidad):
    """Calcula disponibilidad y tiempo de parada con variabilidad realista"""
    tiempo_total = 24  # Horas en un día
    tmb_horas = random.randint(0, 90) / 30  
    
    if criticidad == "Critico":
        tiempo_parada = random.randint(12, 24)
        return 0.0, tiempo_parada  # Disponibilidad 0 si es crítico
    elif criticidad == "Atencion":
        tiempo_parada = random.randint(6, 12)
    else:
        tiempo_parada = random.randint(1, 6)

    # Calcular disponibilidad para los otros casos
    disponibilidad = round((tiempo_total - tiempo_parada) / tiempo_total, 4)
    return disponibilidad, tiempo_parada
def calcular_confiabilidad(df):
    """Calcula métricas de confiabilidad diaria"""
    df_criticos = df[df["Criticidad"] == "Critico"]
    total_fallas = len(df_criticos)
    camiones_disponibles = num_registros - total_fallas
    camiones_disponibles = max(camiones_disponibles, 1)  # Evitar división por cero
    
    mttr = df_criticos["Tiempo Parada"].mean() if not df_criticos.empty else 0
    tasa_fallas = total_fallas / num_registros  # Usar número inicial de camiones
    total_tbf = df["TBF"].sum()
    mtbf = total_tbf / total_fallas if total_fallas > 0 else 0
    confiabilidad_promedio = df["Confiabilidad"].mean() if not df.empty else 0

    return {
        "Total Fallas": total_fallas,
        "Camiones Disponibles": camiones_disponibles,
        "MTTR (horas)": round(mttr, 2),
        "Tasa de Fallas": round(tasa_fallas, 4),
        "TBF Total (horas)": total_tbf,
        "MTBF (horas)": round(mtbf, 2),
        "Confiabilidad (%)": round(confiabilidad_promedio,2)
    }

def calcular_reduccion_fallas_no_planificadas(df):
    """Calcula la reducción porcentual de fallas no planificadas (criticidad 'Critico') entre los dos últimos días."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    # Agrupar por día y contar fallas críticas
    fallas_por_dia = df[df['Criticidad'] == 'Critico'].groupby(df['Fecha'].dt.date).size().sort_index()
    if len(fallas_por_dia) < 2:
        return None  # No hay suficientes días para comparar
    fallas_anterior = fallas_por_dia.iloc[-2]
    fallas_actual = fallas_por_dia.iloc[-1]
    if fallas_anterior == 0:
        return None  # Evitar división por cero
    reduccion = ((fallas_anterior - fallas_actual) / fallas_anterior) * 100
    return round(reduccion, 2)

def calcular_reduccion_paradas_criticas(df):
    """Calcula la reducción porcentual de paradas críticas (Criticidad 'Critico') entre los dos últimos días."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    paradas_por_dia = df[df['Criticidad'] == 'Critico'].groupby(df['Fecha'].dt.date).size().sort_index()
    if len(paradas_por_dia) < 2:
        return None
    paradas_antes = paradas_por_dia.iloc[-2]
    paradas_despues = paradas_por_dia.iloc[-1]
    if paradas_antes == 0:
        return None
    reduccion = ((paradas_antes - paradas_despues) / paradas_antes) * 100
    return round(reduccion, 2)

def calcular_incremento_tbf_general(df):
    """Calcula el incremento porcentual del TBF promedio general entre los dos últimos días."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    tbf_por_dia = df.groupby(df['Fecha'].dt.date)['TBF'].mean().sort_index()
    if len(tbf_por_dia) < 2:
        return None
    tbf_anterior = tbf_por_dia.iloc[-2]
    tbf_nuevo = tbf_por_dia.iloc[-1]
    if tbf_anterior == 0:
        return None
    incremento = ((tbf_nuevo - tbf_anterior) / tbf_anterior) * 100
    return round(incremento, 2)

def calcular_incremento_tbf_por_equipo(df):
    """Calcula el incremento porcentual del TBF promedio por equipo entre los dos últimos días. Devuelve un diccionario flota: incremento."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    incrementos = {}
    for flota, grupo in df.groupby('flota'):
        tbf_por_dia = grupo.groupby(grupo['Fecha'].dt.date)['TBF'].mean().sort_index()
        if len(tbf_por_dia) < 2:
            continue
        tbf_anterior = tbf_por_dia.iloc[-2]
        tbf_nuevo = tbf_por_dia.iloc[-1]
        if tbf_anterior == 0:
            continue
        incremento = ((tbf_nuevo - tbf_anterior) / tbf_anterior) * 100
        incrementos[flota] = round(incremento, 2)
    return incrementos

# ==============================
# GENERACIÓN DE DATOS
# ==============================
def generar_datos_historicos(fecha_inicio, fecha_fin):
    """Genera datos históricos entre las fechas especificadas"""
    global NUM_MUESTRA_DIGITOS, NUM_REGISTRO
    cargar_estado()
    datos_totales = []
    delta_dias = (fecha_fin - fecha_inicio).days + 1
    
    for dia in range(delta_dias):
        fecha_base = fecha_inicio + timedelta(days=dia)
        
        # Generar flotas aleatorias para este día
        flotas = (
            random.sample(flota_caterpillar, num_caterpillar) + 
            random.sample(flota_komatsu, num_komatsu)
        )
        random.shuffle(flotas)
        
        # Registrar flotas con falla crítica en el día actual
        flotas_con_falla_critica = set()
        
        # Inicializar datos para este día como listas vacías
        datos = {
            "Fecha": [(fecha_base + timedelta(minutes=5 * i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(num_registros)],
            "flota": flotas,
            "Modelo": [],
            "Marca": [],
            "Componente": [],
            "Aceite Lubricante": [],
            "cambioLubricanate": [],
            "Contenido de agua %": [],
            "Punto de inflamacion °C": [],
            "Glicol %": [],
            "Nitracion A/cm": [],
            "Oxidación A/cm": [],
            "Hollín %": [],
            "Sulfatacion A/cm": [],
            "Diesel %": [],
            "N de part >4µm": [],
            "N° de part >6µm": [],
            "N° de part>14µm": [],
            "Código ISO 4406": [],
            "Viscosidad 100°C cSt(mm2/s)": [],
            "Viscosidad 40°C cSt(mm2/s)": [],
            "TAN mg KOH/g": [],
            "TBN mg KOH/g": [],
            "Plata (Ag) ppm": [],
            "Aluminio (Al) ppm": [],
            "Bario (Ba) ppm": [],
            "Boro (B) ppm": [],
            "Calcio (Ca) ppm": [],
            "Cromo (Cr) ppm": [],
            "Cobre (Cu) ppm": [],
            "Hierro (Fe) ppm": [],
            "Potasio (K) ppm": [],
            "Magnesio (Mg) ppm": [],
            "Molibdeno (Mo) ppm": [],
            "Sodio (Na) ppm": [],
            "Níquel (Ni) ppm": [],
            "Plomo (Pb) ppm": [],
            "Fósforo (P) ppm": [],
            "Silicio (Si) ppm": [],
            "Estaño (Sn) ppm": [],
            "Titanio (Ti) ppm": [],
            "Vanadio (V) ppm": [],
            "Zinc (Zn) ppm": [],
            "Residuo Ferroso Total mg/kg": [],
            "Numero Muestra": [],
            "Numero Registro": [],
            "Numero Serie Equipo": [],
            "Criticidad": [],
            "Disponibilidad": [],
            "Tiempo Parada": [],
            "TRR": [],
            "TMP": [],
            "TBF": [],
            "Confiabilidad": [],
            "Alerta Emitida": [],
            "Alerta Evitó Falla": []
        }
        
        # Generar datos para cada registro
        for i in range(num_registros):
            flota = flotas[i]
            marca = "CATERPILLAR" if 900 <= flota <= 939 else "KOMATSU"
            modelo = random.choice(modelos_caterpillar if marca == "CATERPILLAR" else modelos_komatsu)
            
            # Evitar múltiples fallas críticas por flota por día
            if flota in flotas_con_falla_critica:
                criticidad = "Normal"
                disponibilidad, tiempo_parada = calcular_disponibilidad(marca, "Normal")
            else:
                criticidad = generar_criticidad(marca)
                disponibilidad, tiempo_parada = calcular_disponibilidad(marca, criticidad)
                if criticidad == "Critico":
                    flotas_con_falla_critica.add(flota)
                    
            # Calcular TRR y TMP
            trr = random.randint(0, 6)
            tmp = random.randint(0, 90) / 30
            
            # Calcular TBF y confiabilidad
            tbf = 24 - tiempo_parada if criticidad != "Critico" else 0
            if criticidad == "Critico":
                confiabilidad = 0.0
            else:
                if tbf > 0:
                    confiabilidad = ((tbf - trr) / tbf) * 100
                    confiabilidad = max(round(confiabilidad, 1), 0)
                else:
                    confiabilidad = 100.0
            
            # Seleccionar componente y aceite lubricante
            componente_seleccionado = random.choice(list(componentes_aceites.keys()))
            aceite_lubricante = componentes_aceites[componente_seleccionado]
            
            # Generar valores según criticidad
            if criticidad == "Normal":
                silicio = random.randint(0, 15)
                hierro = random.randint(0, 100)
            elif criticidad == "Atencion":
                silicio = random.randint(15, 25)
                hierro = random.randint(100, 200)
            else:
                silicio = random.randint(25, 50)
                hierro = random.randint(200, 300)
            
            # Generar números de muestra y registro
            letra_muestra = random.choice(NUM_MUESTRA_LETRAS)
            NUM_MUESTRA_DIGITOS += 1
            NUM_REGISTRO += 1
            
            # Agregar datos al diccionario
            datos["Marca"].append(marca)
            datos["Modelo"].append(modelo)
            datos["Criticidad"].append(criticidad)
            datos["Disponibilidad"].append(disponibilidad * 100)
            datos["Tiempo Parada"].append(tiempo_parada)
            datos["TRR"].append(trr)
            datos["TMP"].append(tmp)
            datos["TBF"].append(tbf)
            datos["Confiabilidad"].append(confiabilidad)
            datos["Componente"].append(componente_seleccionado)
            datos["Aceite Lubricante"].append(aceite_lubricante)
            datos["Numero Muestra"].append(f"{letra_muestra}{NUM_MUESTRA_DIGITOS:05d}")
            datos["Numero Registro"].append(f"{NUM_REGISTRO:07d}")
            datos["Numero Serie Equipo"].append(f"LAJ{random.randint(0, 999):03d}")
            datos["cambioLubricanate"].append(random.choice(cambioLubricanate))
            datos["Contenido de agua %"].append(round(np.random.uniform(0, 1), 2))
            datos["Punto de inflamacion °C"].append(np.random.randint(180, 250))
            datos["Glicol %"].append(round(np.random.uniform(0, 0.5), 2))
            datos["Nitracion A/cm"].append(np.random.randint(0, 5))
            datos["Oxidación A/cm"].append(np.random.randint(0, 5))
            datos["Hollín %"].append(round(np.random.uniform(0, 2), 2))
            datos["Sulfatacion A/cm"].append(np.random.randint(0, 5))
            datos["Diesel %"].append(round(np.random.uniform(0, 1), 2))
            datos["N de part >4µm"].append(np.random.randint(1000, 10000))
            datos["N° de part >6µm"].append(np.random.randint(500, 5000))
            datos["N° de part>14µm"].append(np.random.randint(100, 1000))
            datos["Código ISO 4406"].append(f"{np.random.randint(18, 22)}/{np.random.randint(16, 20)}/{np.random.randint(13, 17)}")
            datos["Viscosidad 100°C cSt(mm2/s)"].append(round(np.random.uniform(10, 20), 2))
            datos["Viscosidad 40°C cSt(mm2/s)"].append(round(np.random.uniform(80, 120), 2))
            datos["TAN mg KOH/g"].append(round(np.random.uniform(0, 3), 2))
            datos["TBN mg KOH/g"].append(np.random.randint(0, 10))
            datos["Plata (Ag) ppm"].append(np.random.randint(0, 5))
            datos["Aluminio (Al) ppm"].append(np.random.randint(0, 30))
            datos["Bario (Ba) ppm"].append(np.random.randint(0, 10))
            datos["Boro (B) ppm"].append(np.random.randint(0, 10))
            datos["Calcio (Ca) ppm"].append(np.random.randint(0, 1000))
            datos["Cromo (Cr) ppm"].append(np.random.randint(0, 10))
            datos["Cobre (Cu) ppm"].append(np.random.randint(0, 50))
            datos["Potasio (K) ppm"].append(np.random.randint(0, 10))
            datos["Magnesio (Mg) ppm"].append(np.random.randint(0, 10))
            datos["Molibdeno (Mo) ppm"].append(np.random.randint(0, 10))
            datos["Sodio (Na) ppm"].append(np.random.randint(0, 30))
            datos["Níquel (Ni) ppm"].append(np.random.randint(0, 10))
            datos["Plomo (Pb) ppm"].append(np.random.randint(0, 10))
            datos["Fósforo (P) ppm"].append(np.random.randint(0, 10))
            datos["Silicio (Si) ppm"].append(silicio)
            datos["Estaño (Sn) ppm"].append(np.random.randint(0, 10))
            datos["Titanio (Ti) ppm"].append(np.random.randint(0, 10))
            datos["Vanadio (V) ppm"].append(np.random.randint(0, 10))
            datos["Zinc (Zn) ppm"].append(np.random.randint(0, 100))
            datos["Hierro (Fe) ppm"].append(hierro)
            datos["Residuo Ferroso Total mg/kg"].append(np.random.randint(0, 600))
            # Simulación de alertas
            alerta_emitida = 1 if criticidad in ["Atencion", "Critico"] else 0
            # Simulación: porcentaje parametrizado de las alertas emitidas evitan una falla si no es crítico
            if alerta_emitida and criticidad == "Atencion":
                alerta_evito_falla = 1 if random.random() < EFECTIVIDAD_ALERTAS else 0
            else:
                alerta_evito_falla = 0
            datos.setdefault("Alerta Emitida", []).append(alerta_emitida)
            datos.setdefault("Alerta Evitó Falla", []).append(alerta_evito_falla)
        
        # Verificar longitudes antes de crear el DataFrame
        for key, value in datos.items():
            if len(value) != num_registros:
                raise ValueError(f"Longitud incorrecta en '{key}': {len(value)}")
        
        # Crear el DataFrame una sola vez por día
        df_dia = pd.DataFrame(datos)
        datos_totales.append(df_dia)
        guardar_datos(df_dia, fecha_dia=fecha_base.date())
    
    df = pd.concat(datos_totales, ignore_index=True)
    metricas = calcular_confiabilidad(df)
    guardar_estado()
    return df, metricas

# ==============================
# GUARDADO DE DATOS
# ==============================
def guardar_datos(df_nuevos, fecha_dia, archivo=ARCHIVO_DATOS):
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    # Definir tipos explícitos para evitar errores
    tipos_de_columnas = {
        "Numero Registro": str,
        "Numero Muestra": str,
        "Numero Serie Equipo": str,
    }

    # Guardar datos principales
    try:
        df_existente = pd.read_csv(archivo)
        df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
    except FileNotFoundError:
        df_final = df_nuevos

    # Convertir columnas específicas a string
    for col, dtype in tipos_de_columnas.items():
        if col in df_final.columns:
            df_final[col] = df_final[col].astype(dtype)

    # Guardar en CSV
    df_final.to_csv(archivo, index=False)

    # Opcional: Guardar en Parquet
    archivo_parquet = archivo.replace(".csv", ".parquet")
    df_final.to_parquet(archivo_parquet, engine='pyarrow', index=False)

    # Guardar métricas usando solo datos del día actual
    metricas_hoy = calcular_confiabilidad(df_nuevos)
    metricas_diarias = {
        "Fecha": [str(fecha_dia)],
        "Fallas Totales": [int(metricas_hoy["Total Fallas"])],
        "Camiones Disponibles": [int(metricas_hoy["Camiones Disponibles"])],
        "MTTR (horas)": [float(metricas_hoy["MTTR (horas)"])],
        "Tasa Fallas": [float(metricas_hoy["Tasa de Fallas"])],
        "TBF Total (horas)": [int(metricas_hoy["TBF Total (horas)"])],
        "MTBF (horas)": [float(metricas_hoy["MTBF (horas)"])],
        "Confiabilidad (%)": [float(metricas_hoy["Confiabilidad (%)"])]
    }
    df_metricas = pd.DataFrame(metricas_diarias)
    try:
        df_metricas_ant = pd.read_csv(ARCHIVO_METRICAS)
        df_metricas_ant = df_metricas_ant.astype(str)
        df_metricas = pd.concat([df_metricas_ant, df_metricas], ignore_index=True)
    except FileNotFoundError:
        pass
    df_metricas = df_metricas.drop_duplicates()
    df_metricas.to_csv(ARCHIVO_METRICAS, index=False)
    # Guardar métricas en parquet también (opcional)
    archivo_metricas_parquet = ARCHIVO_METRICAS.replace(".csv", ".parquet")
    df_metricas.astype({
        "Fallas Totales": "int64",
        "Camiones Disponibles": "int64",
        "MTTR (horas)": "float64",
        "Tasa Fallas": "float64",
        "TBF Total (horas)": "int64",
        "MTBF (horas)": "float64",
        "Confiabilidad (%)": "float64"
    }).to_parquet(archivo_metricas_parquet, engine='pyarrow', index=False)

def calcular_efectividad_alertas(df):
    """Calcula la efectividad de alertas (%) según la fórmula: (Alertas que evitaron fallas / Total de alertas emitidas) * 100"""
    total_alertas = df['Alerta Emitida'].sum()
    alertas_efectivas = df['Alerta Evitó Falla'].sum()
    if total_alertas == 0:
        return None
    return round((alertas_efectivas / total_alertas) * 100, 2)

def calcular_ahorro_total(df, costo_falla_evita=COSTO_FALLA_EVITADA):
    """Calcula el ahorro total como la suma del costo estimado por cada falla evitada."""
    n_fallas_evitadas = df['Alerta Evitó Falla'].sum()
    return n_fallas_evitadas * costo_falla_evita

def calcular_metricas_completas(df):
    """Calcula todas las métricas clave del sistema y retorna un diccionario con los resultados."""
    metricas = {}
    # Disponibilidad promedio
    metricas['Disponibilidad Promedio (%)'] = round(df['Disponibilidad'].mean(), 2)
    # Reducción de fallas no planificadas
    reduccion_fallas = calcular_reduccion_fallas_no_planificadas(df)
    metricas['Reducción Fallas No Planificadas (%)'] = reduccion_fallas if reduccion_fallas is not None else 'N/A'
    # Reducción de paradas críticas
    reduccion_paradas = calcular_reduccion_paradas_criticas(df)
    metricas['Reducción Paradas Críticas (%)'] = reduccion_paradas if reduccion_paradas is not None else 'N/A'
    # Incremento TBF general
    incremento_tbf = calcular_incremento_tbf_general(df)
    metricas['Incremento TBF General (%)'] = incremento_tbf if incremento_tbf is not None else 'N/A'
    # Incremento TBF por equipo
    incremento_tbf_equipos = calcular_incremento_tbf_por_equipo(df)
    metricas['Incremento TBF por Equipo (%)'] = incremento_tbf_equipos if incremento_tbf_equipos else 'N/A'
    # Efectividad de alertas
    efectividad_alertas = calcular_efectividad_alertas(df)
    metricas['Efectividad de Alertas (%)'] = efectividad_alertas if efectividad_alertas is not None else 'N/A'
    # Ahorro total
    ahorro_total = calcular_ahorro_total(df)
    metricas['Ahorro Total (CLP)'] = ahorro_total
    # Parámetros relevantes
    metricas['Costo Falla Evitada (CLP)'] = COSTO_FALLA_EVITADA
    metricas['Costo Hora Camión Detenido (CLP)'] = COSTO_HORA_CAMION_DETENIDO
    metricas['Costo Mensual Fallas Tribológicas (CLP)'] = COSTO_MENSUAL_TRIBOLOGICAS
    metricas['Efectividad Alertas Parametrizada'] = EFECTIVIDAD_ALERTAS
    return metricas

# ==============================
# BUCLE PRINCIPAL
# ==============================
if __name__ == "__main__":
    # Generar datos históricos desde 2025-01-01 hasta hoy
    fecha_inicio = datetime(2025, 4, 1)
    fecha_fin = datetime.now()
    
    print(f"Generando datos históricos desde {fecha_inicio.date()} hasta {fecha_fin.date()}...")
    
    try:
        df_historicos, metricas_nuevas = generar_datos_historicos(fecha_inicio, fecha_fin)
        guardar_datos(df_historicos, metricas_nuevas)
        print("Datos históricos generados y guardados.")
        
        # Bucle diario (opcional)
        while True:
            print("Generando nuevos registros diarios...")
            fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = fecha_inicio + timedelta(days=1)
            df_diarios, metricas_diarias = generar_datos_historicos(fecha_inicio, fecha_fin)
            guardar_datos(df_diarios, metricas_diarias)
            print("Datos diarios guardados. Esperando 24 horas...")
            time.sleep(86400)
            
    except KeyboardInterrupt:
        print("\nGeneración de datos interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError en la generación de datos: {str(e)}")