#!/bin/bash

# Script de inicialización para Render
echo "Inicializando aplicación..."

# Crear directorio de datos si no existe
mkdir -p data

# Copiar archivos de datos si existen
if [ -f "src/data/datos_generados_completos.parquet" ]; then
    cp src/data/datos_generados_completos.parquet data/
    echo "Archivo de datos copiado exitosamente"
else
    echo "Advertencia: No se encontró el archivo de datos"
fi

# Verificar que los archivos estén en su lugar
ls -la data/

echo "Inicialización completada" 