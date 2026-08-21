FROM python:3.11-slim

WORKDIR /app

# Устанавливаем и обновляем базовые системные зависимости
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

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
