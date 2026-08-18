FROM python:3.11-slim

WORKDIR /app

# Устанавливаем и обновляем системные зависимости (включая Node.js и npm)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    git \
    nodejs \
    npm \
    libsecret-1-0 \
    && rm -rf /var/lib/apt/lists/*

# Глобально предустанавливаем MCP-серверы, чтобы npx стартовал за 0.1 сек без скачивания по сети
RUN npm install -g @modelcontextprotocol/server-google-maps @presto-ai/google-workspace-mcp

# Копируем requirements & устанавливаем/обновляем python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Копируем файлы приложения
COPY . .

# Environment setup
ENV PORT=8080
EXPOSE 8080

# Run ADK Web UI bound to 0.0.0.0:$PORT
CMD ["sh", "-c", "adk web --host 0.0.0.0 --port ${PORT} ."]
