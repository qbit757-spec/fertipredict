# Usa la imagen oficial de Python 3.9
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala libgomp1 requerido por LightGBM
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos e instala las dependencias
COPY Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt
RUN pip install --no-cache-dir uvicorn

# Copia el resto de los archivos de la aplicación
COPY . .

# Expone el puerto donde se ejecutará la API
EXPOSE 8000

# Comando para iniciar el backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
