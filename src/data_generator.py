import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ==============================
# CONFIGURACIÓN PRINCIPAL
# ==============================
num_komatsu = 68
num_caterpillar = 39
num_registros = num_komatsu + num_caterpillar

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

# ==============================
# FUNCIONES DE APOYO
# ==============================
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

def generar_datos_disponibilidad():
    """Genera datos de disponibilidad para un período"""
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    datos = []
    for dia in range(31):
        fecha_base = fecha_inicio + timedelta(days=dia)
        
        # Generar flotas aleatorias para este día
        flotas = (
            random.sample(flota_caterpillar, num_caterpillar) + 
            random.sample(flota_komatsu, num_komatsu)
        )
        random.shuffle(flotas)
        
        # Registrar flotas con falla crítica en el día actual
        flotas_con_falla_critica = set()
        
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
            
            # Seleccionar componente y aceite lubricante
            componente = random.choice(list(componentes_aceites.keys()))
            aceite = componentes_aceites[componente]
            
            # Generar valores según criticidad
            if criticidad == "Normal":
                silicio = random.randint(0, 15)
                hierro = random.randint(0, 100)
                cobre = random.randint(0, 30)
                aluminio = random.randint(0, 15)
            elif criticidad == "Atencion":
                silicio = random.randint(15, 25)
                hierro = random.randint(100, 200)
                cobre = random.randint(30, 45)
                aluminio = random.randint(15, 25)
            else:
                silicio = random.randint(25, 40)
                hierro = random.randint(200, 300)
                cobre = random.randint(45, 60)
                aluminio = random.randint(25, 35)
            
            # Calcular TBF y confiabilidad
            tbf = 24 - tiempo_parada if criticidad != "Critico" else 0
            confiabilidad = 0.0 if criticidad == "Critico" else round(((tbf - random.randint(0, 6)) / tbf) * 100 if tbf > 0 else 100.0, 1)
            
            datos.append({
                'Fecha': fecha_base + timedelta(minutes=5 * i),
                'flota': f'CAEX_{flota}',
                'Marca': marca,
                'Modelo': modelo,
                'Componente': componente,
                'Aceite Lubricante': aceite,
                'Criticidad': criticidad,
                'Disponibilidad': disponibilidad,
                'Tiempo Parada': tiempo_parada,
                'TBF': tbf,
                'Confiabilidad': confiabilidad,
                'Hierro (Fe) ppm': hierro,
                'Cobre (Cu) ppm': cobre,
                'Silicio (Si) ppm': silicio,
                'Aluminio (Al) ppm': aluminio,
                'Viscosidad 100°C cSt(mm2/s)': random.uniform(12, 16),
                'Contaminación (ppm)': random.uniform(0, 100),
                'Temperatura (°C)': random.uniform(80, 95)
            })
    
    return pd.DataFrame(datos)

def generar_datos_confiabilidad():
    """Genera datos de confiabilidad para cada equipo"""
    df_disp = generar_datos_disponibilidad()
    equipos = df_disp[['Marca', 'Modelo', 'flota']].drop_duplicates()
    
    data = []
    for _, equipo in equipos.iterrows():
        mtbf = random.uniform(300, 500)  # Tiempo medio entre fallas (horas)
        mttr = random.uniform(4, 16)     # Tiempo medio de reparación (horas)
        disponibilidad = mtbf / (mtbf + mttr)
        
        data.append({
            'Marca': equipo['Marca'],
            'Modelo': equipo['Modelo'],
            'flota': equipo['flota'],
            'MTBF': mtbf,
            'MTTR': mttr,
            'Disponibilidad': disponibilidad
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Generar datos
    df_disponibilidad = generar_datos_disponibilidad()
    df_confiabilidad = generar_datos_confiabilidad()
    
    # Crear directorio data si no existe
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Guardar datos
    df_disponibilidad.to_parquet('data/datos_generados_Disponibilidad.parquet')
    df_confiabilidad.to_parquet('data/metricas_confiabilidad.parquet')
    
    print("Datos generados exitosamente") 