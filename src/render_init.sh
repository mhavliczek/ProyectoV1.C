#!/bin/bash

# Crear directorio data dentro de src si no existe
mkdir -p src/data

# Generar datos iniciales
python data_generator.py

# Iniciar la aplicación
streamlit run app.py 