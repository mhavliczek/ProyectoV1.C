# Dashboard de Mantenimiento Predictivo

Sistema de monitoreo y análisis predictivo para mantenimiento de flotas.

## Instalación

1. Clonar el repositorio
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución

Para ejecutar la aplicación localmente:
```bash
streamlit run src/app.py
```

Para ejecutar las diferentes vistas:
- Dashboard Ejecutivo: `streamlit run src/app_ejecutivo.py`
- Dashboard Técnico: `streamlit run src/app_tecnico.py`
- Dashboard Económico: `streamlit run src/app_economico.py`

## Estructura del Proyecto

- `src/`: Código fuente de la aplicación
  - `app.py`: Dashboard principal
  - `app_ejecutivo.py`: Vista ejecutiva
  - `app_tecnico.py`: Vista técnica
  - `app_economico.py`: Vista económica
- `data/`: Archivos de datos y modelos
- `requirements.txt`: Dependencias del proyecto
