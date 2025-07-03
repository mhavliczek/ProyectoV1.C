# Dashboard de Métricas Clave - Proyecto V1.C

## Descripción
Dashboard interactivo para visualizar métricas clave de mantenimiento predictivo y confiabilidad de flota de camiones.

## Características
- 📊 KPIs en tiempo real
- 📈 Gráficos interactivos con Plotly
- 🔍 Filtros por mes, día y marca
- 💾 Optimizado con archivos Parquet
- 🚀 Despliegue automático en Render

## Despliegue en Render

### Configuración Automática
El proyecto está configurado para desplegarse automáticamente en Render con:
- Python 3.10.12
- Streamlit 1.25.0+
- Dependencias mínimas optimizadas

### Pasos para el Despliegue

1. **Fork o Clone el repositorio**
   ```bash
   git clone https://github.com/mhavliczek/ProyectoV1.C.git
   cd ProyectoV1.C
   ```

2. **Conectar con Render**
   - Ve a [Render Dashboard](https://dashboard.render.com)
   - Crea un nuevo "Web Service"
   - Conecta tu repositorio de GitHub
   - Render detectará automáticamente la configuración

3. **Configuración Automática**
   - El archivo `render.yaml` contiene toda la configuración necesaria
   - Python 3.10.12 se instalará automáticamente
   - Las dependencias se instalarán desde `requirements-minimal.txt`
   - El script `render_init.sh` preparará el entorno

4. **Despliegue**
   - Render construirá automáticamente la aplicación
   - La URL estará disponible en el dashboard de Render

### Estructura del Proyecto
```
ProyectoV1.C/
├── src/
│   ├── app_Cuadro.py          # Aplicación principal
│   ├── render.yaml            # Configuración de Render
│   ├── requirements-minimal.txt # Dependencias mínimas
│   ├── render_init.sh         # Script de inicialización
│   └── data/                  # Archivos de datos
├── data/                      # Datos optimizados
└── README.md
```

### Solución de Problemas

#### Error: "Could not fetch Python version 3.11.5"
- **Solución**: El proyecto está configurado para usar Python 3.10.12
- Verifica que `runtime.txt` y `render.yaml` usen la misma versión

#### Error: "No se encontró el archivo de datos"
- **Solución**: Asegúrate de que los archivos `.parquet` estén en `src/data/`
- El script `render_init.sh` los copiará automáticamente

#### Error de dependencias
- **Solución**: Usa `requirements-minimal.txt` que contiene solo las dependencias esenciales

### Desarrollo Local

1. **Instalar dependencias**
   ```bash
   pip install -r src/requirements.txt
   ```

2. **Ejecutar aplicación**
   ```bash
   cd src
   streamlit run app_Cuadro.py
   ```

### KPIs Incluidos
- Disponibilidad Promedio (%)
- Reducción de Fallas No Planificadas (%)
- Reducción de Paradas Críticas (%)
- Incremento TBF General (%)
- Efectividad de Alertas (%)
- Ahorro Total (CLP)

### Tecnologías Utilizadas
- **Frontend**: Streamlit
- **Visualización**: Plotly
- **Datos**: Pandas, PyArrow (Parquet)
- **Despliegue**: Render
- **Lenguaje**: Python 3.10

## Soporte
Para problemas de despliegue, verifica:
1. La versión de Python en `runtime.txt` y `render.yaml`
2. Que los archivos de datos estén presentes
3. Los logs de construcción en Render Dashboard

---
*Actualizado: Julio 2025*
