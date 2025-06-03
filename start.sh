#!/bin/bash
export PATH="/usr/local/bin:$PATH"

# Generar datos de ejemplo
python src/data_generator.py

# Iniciar la aplicación
streamlit run src/app.py --server.port=$PORT --server.address=127.0.0.1 