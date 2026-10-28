# Usamos una imagen oficial de Python ligera
FROM python:3.12-slim

# Configuraciones de entorno para evitar problemas de memoria con PyTorch
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/tmp/hf_cache
ENV TOKENIZERS_PARALLELISM=false
ENV TORCH_DISABLE_META=1

# Instalamos dependencias del sistema necesarias (ej. para psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces ejecuta los contenedores con el usuario 1000
# Creamos un usuario para evitar problemas de permisos
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Establecemos el directorio de trabajo
WORKDIR $HOME/app

# Copiamos e instalamos los requerimientos primero (para aprovechar la caché de Docker)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY --chown=user . .

# Exponemos el puerto por defecto de Hugging Face
EXPOSE 7860

# Comando para arrancar FastAPI. 
# Usamos 6_agente_orquestado:app porque es tu archivo del agente
CMD ["uvicorn", "6_agente_orquestado:app", "--host", "0.0.0.0", "--port", "7860"]