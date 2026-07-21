# Usamos a imagem oficial do Python (versão slim para não ficar gigante)
FROM python:3.11-slim

# Define variáveis de ambiente para o Python não gerar arquivos .pyc e não reter buffers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define a pasta de trabalho dentro do container
WORKDIR /app

# INSTALAÇÃO DE DEPENDÊNCIAS DO SISTEMA (Crítico para OpenCV / psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências (salve aquela sua lista como requirements.txt)
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do backend
COPY . .

# Expõe a porta padrão do FastAPI/Uvicorn
EXPOSE 8000

# Comando para rodar o FastAPI com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]