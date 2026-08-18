# 🚀 Blogger Agent MCP & AI Content Generation Engine

**Blogger Agent MCP** — это автономная мультиагентная система на базе **Google Agent Development Kit (ADK)** и **Gemini 3.5 Flash**, предназначенная для глубокого анализа трендов, живого поиска актуальных фактов в вебе, автоматического построения многоточечных маршрутов путешествий в **Google Maps**, написания экспертных лонгридов, публикации документов в **Google Docs** и рассылки по **Gmail**.

---

## 🌟 Ключевые возможности

* 🧠 **Мультиагентный пайплайн (Google ADK & Gemini 3.5 Flash):** Использование специализированных субагентов `BlogPlanner` и `BlogWriter` под управлением единого оркестратора `Root Agent`.
* 🌐 **Живой веб-поиск в реальном времени (`search_web`):** Заземление фактов (Grounding) на текущую дату для предотвращения галлюцинаций и устаревания данных LLM.
* 🗺 **Гранд-Тур маршрутизатор (`get_scenic_travel_route`):** Построение сложных автопутешествий **Точка А ➔ Б ➔ В ➔ Г** с генерацией кликабельных интерактивных карт в Google Maps.
* 📈 **Google Trends Integration:** Автоматический сбор восходящих ключевых трендов аудитории.
* 🔒 **Делегированная OAuth 2.0 авторизация:** Создание файлов прямо на **вашем личном Google Диске** (Google Docs API) и отправка сообщений от **вашего личного Gmail** (Gmail API).
* ☁️ **Cloud Native & Docker Ready:** Готов к моментальному развертыванию в **Google Cloud Run**, **Docker** и **Dokploy**.

---

## 🏗 Архитектура пайплайна

```
[Пользовательский Запрос]
        │
        ▼
[Root Agent (Blogger)]
        │
        ├──> 1. Trends Analysis (get_google_trends / pytrends)
        │
        ├──> 2. Live Web Search (search_web / DDGS Grounding)
        │
        ├──> 3. Scenic Route Planner (get_scenic_travel_route / Places & Routes API)
        │
        ├──> 4. Outline Generation (Sub-Agent: BlogPlanner)
        │
        ├──> 5. Full Article Generation (Sub-Agent: BlogWriter)
        │
        └──> 6. Export & Delivery
                 ├── Google Drive / Docs API (save_to_google_drive)
                 ├── Google Cloud Storage Backup (save_to_cloud_storage)
                 └── Gmail API Dispatch (send_article_email)
```

---

## ⚙️ Переменные окружения (`.env`)

Создайте файл `.env` в корневом каталоге проекта:

```env
# Модель и регион Google Cloud Vertex AI
MODEL=gemini-3.5-flash
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Ключ Google Maps Platform API
GOOGLE_MAPS_API_KEY=AIzaSyYourGoogleMapsApiKeyHere12345

# Хранилище Google Cloud Storage
GCS_BUCKET_NAME=your-gcs-bucket-name

# OAuth 2.0 Desktop Credentials (для личного Google Диска и Gmail)
OAUTH_CLIENT_ID=123456789012-yourclientid.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=GOCSPX-yourClientSecretHere123456
OAUTH_REFRESH_TOKEN=1//04yourRefreshTokenHere_abcdefghijklmnopqrstuvwxyz

# Email для уведомлений
NOTIFICATION_EMAIL=your_email@gmail.com
```

---

## 📦 Быстрая установка и локальный запуск

### 1. Клонирование репозитория и создание venv
```bash
git clone https://github.com/your-username/bloggeragentmcp.git
cd bloggeragentmcp

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Авторизация OAuth 2.0 (Однократный запуск)
Для получения своего долговечного `OAUTH_REFRESH_TOKEN` запустите скрипт авторизации:
```bash
python generate_oauth_token.py
```
Авторизуйтесь в открывшемся браузере под своим Google-аккаунтом и скопируйте полученный `refresh_token` в `.env`.

### 4. Локальный запуск агента
```bash
python agent.py
```

---

## 🐳 Развертывание в Docker / Dokploy / Cloud Run

### 1. Запуск через Docker Compose
Создайте `docker-compose.yml`:
```yaml
version: '3.8'

services:
  blogger-agent:
    build: .
    container_name: blogger_agent
    restart: always
    ports:
      - "8080:8080"
    env_file:
      - .env
```

Запустите контейнер:
```bash
docker compose up -d
```

---

### 2. Деплой в Google Cloud Run
```bash
gcloud run deploy bloggeragentmcpv03 \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-secrets="OAUTH_REFRESH_TOKEN=oauth-refresh-token:latest" \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,MODEL="gemini-3.5-flash",GOOGLE_CLOUD_LOCATION="global",GCS_BUCKET_NAME="your-gcs-bucket-name",NOTIFICATION_EMAIL="your_email@gmail.com"
```

---

### 3. Деплой в Dokploy
1. Создайте **Application** в панели Dokploy.
2. В **Build Type** выберите `Dockerfile`.
3. Заполните переменные во вкладке **Environment**.
4. Нажмите **Deploy**.

---

## 📝 Лицензия
MIT License © 2026 Blogger Agent MCP Team.
