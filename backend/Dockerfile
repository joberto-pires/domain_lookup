FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar uv para gerenciar dependências do projeto
RUN pip install --no-cache-dir uv

# Copiar arquivos de dependências primeiro (melhor cache)
COPY pyproject.toml uv.lock* ./

# Instalar dependências do projeto sem instalar o projeto em si
# (o código será montado via volume em desenvolvimento)
RUN uv sync --no-install-project --no-dev

# Adicionar o venv ao PATH para que os comandos do Compose funcionem
ENV PATH="/app/.venv/bin:$PATH"

# Copiar código (em dev, sobrescrito pelo volume)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
