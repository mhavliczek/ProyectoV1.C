#!/bin/bash

# Crear directorio data si no existe
mkdir -p data

# Generar datos iniciales
python src/data_generator.py

# Iniciar la aplicación
streamlit run src/app.py 