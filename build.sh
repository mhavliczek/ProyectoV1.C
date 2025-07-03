#!/bin/bash

# Forzar Python 3.11
export PYTHON_VERSION=3.11.7

# Actualizar pip y setuptools primero
python -m pip install --upgrade pip setuptools wheel

# Instalar dependencias
pip install -r requirements.txt

# Verificar la versión de Python
python --version

echo "Build completado exitosamente" 