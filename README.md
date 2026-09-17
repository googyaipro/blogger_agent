# 🚀 Blogger Agent MCP & AI Universal Content Generation Engine

**Blogger Agent MCP** — это автономная мультиагентная система на базе **Google Agent Development Kit (ADK)** и флагманской модели **Gemini 3.8 Flash** (Vertex AI Global Endpoint), предназначенная для глубокого аналитического исследования трендов через **Google BigQuery**, живого поиска актуальных фактов в вебе, автоматического построения многоточечных маршрутов в **Google Maps**, написания экспертных лонгридов по любым профильным и междисциплинарным темам, публикации документов в **Google Docs** и рассылки по **Gmail**.

---

## 🌟 Ключевые возможности

* 🧠 **Мультиагентный универсальный пайплайн (Google ADK & Gemini 3.8 Flash):** Использование профильных субагентов `BlogPlanner` *(Senior Content Strategist & Structural Editor)* и `BlogWriter` под управлением оркестратора `Root Agent`. Подключение к Vertex AI через глобальный динамический балансировщик (`GOOGLE_CLOUD_LOCATION="global"`).
* 🎯 **Умный селектор масштаба темы (Smart Topic Scope):**
  * 📍 **`scope="local"` (Гиперлокальный):** Для региональной традиционной продукции, локальных ремесел, кулинарии и путеводителей. Запрашиваются только тренды выбранной страны (`geo`), а мировой инфошум полностью отсекается (`global_trends = []`).
  * 🌍 **`scope="global"` (Мировой):** Для глобальных тем (AI, квантовые вычисления, облачные архитектуры).
  * 🌐 **`scope="both"` (Гибридный):** Для вопросов экспорта, международной торговли и транзитного туризма.
* 📊 **Официальный BigQuery Engine (Dual-Scope Trend Synthesis):** Замена неофициального парсинга на **прямые SQL-запросы к датасету `bigquery-public-data.google_trends.international_top_terms`**. Точная фильтрация по ISO-кодам стран без прокси и без блокировок 429/403!
* 🌐 **Живой веб-поиск в реальном времени (`search_web`):** Заземление фактов (Grounding) на текущую дату для гарантированной актуальности цен, законов и правил 2026 года.
* 🗺 **Гранд-Тур маршрутизатор (`get_scenic_travel_route`):** Построение сложных автопутешествий **Точка А ➔ Б ➔ В ➔ Г** через Google Places & Routes API с безопасным экранированием кириллицы (`urllib.parse.urlencode`) и генерацией интерактивных карт.
* 🔒 **Бессрочная OAuth 2.0 авторизация & Fallback Storage:** Режим **In production** с параметром `access_type="offline"` гарантирует вечную жизнь токенов. При любых временных сбоях Google Drive статья автоматически сохраняется в **Google Cloud Storage (GCS)** (нулевой риск потери контента).
* 🐳 **Облегченный Docker-образ:** Удален лишний стек Node.js/npm, контейнер уменьшен на **~350 МБ** (чистый Python 3.11-slim, быстрая сборка).

---

## 🏗 Архитектура пайплайна

```
[Пользовательский Запрос (Любая профильная или смежная тема)]
        │
        ▼
[Root Agent (Blogger Orchestrator)]
        │
        ├──> 1. Smart Topic Scope Selector (prompts.py)
        │        ├──> scope="local"  -> Только региональные тренды выбранной страны
        │        ├──> scope="global" -> Только мировые глобальные тренды
        │        └──> scope="both"   -> Синтез локальных и мировых трендов
        │
        ├──> 2. Official BigQuery Trends Engine (get_google_trends)
        │        └──> `bigquery-public-data.google_trends.international_top_terms`
        │
        ├──> 3. Live Web Search (search_web / DDGS 2026 Grounding)
        │
        ├──> 4. Scenic Route Planner (get_scenic_travel_route / Places & Routes API)
        │
        ├──> 5. Outline Generation (Sub-Agent: BlogPlanner - Senior Content Strategist)
        │
        ├──> 6. Full Article Generation (Sub-Agent: BlogWriter - Master Writer)
        │
        └──> 7. Export & Delivery
                 ├── Google Drive / Docs API (save_to_google_drive)
                 ├── 🛡 Fallback: Google Cloud Storage (save_to_cloud_storage)
                 └── Gmail API Dispatch (send_article_email)
```

---

## ⚙️ Переменные окружения (`.env`)

Создайте файл `.env` в корневом каталоге проекта:

```env
# Модель и регион Google Cloud Vertex AI
MODEL=gemini-3.8-flash
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
git clone -b bigquery https://github.com/googyaipro/blogger_agent.git
cd blogger_agent

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Авторизация OAuth 2.0 (Однократный запуск)
Для получения своего бессрочного `OAUTH_REFRESH_TOKEN` запустите скрипт авторизации:
```bash
python generate_oauth_token.py
```
Авторизуйтесь в открывшемся браузере под своим Google-аккаунтом и скопируйте полученный `refresh_token` в `.env` и в Google Cloud Secret Manager.

### 4. Локальный запуск агента
```bash
python agent.py
```

---

## 🐳 Развертывание в Docker / Cloud Run / Dokploy

### 1. Деплой в Google Cloud Run (Рекомендуемый способ)
```bash
gcloud run deploy bloggeragentmcpv03 \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --service-account="blogger-sa@your-gcp-project.iam.gserviceaccount.com" \
  --set-secrets="OAUTH_REFRESH_TOKEN=oauth-refresh-token:latest" \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,MODEL="gemini-3.8-flash",GOOGLE_CLOUD_LOCATION="global",GCS_BUCKET_NAME="your-gcs-bucket-name",NOTIFICATION_EMAIL="your_email@gmail.com",GOOGLE_MAPS_API_KEY="AIzaSyYourGoogleMapsApiKeyHere12345"
```

---

### 2. Запуск через Docker Compose
```bash
docker compose up -d
```

---

### 3. Деплой в Dokploy (VPS)
1. Создайте **Application** в панели Dokploy.
2. В **Build Type** выберите `Dockerfile`.
3. Заполните переменные во вкладке **Environment**.
4. Загрузите файл сервисного аккаунта `/app/gcp-key.json` во вкладку **File Mounts** для Vertex AI & BigQuery.
5. Нажмите **Deploy**.

---

## 📚 Дополнительная документация проекта

* 📑 [**Итоговая ретроспектива проекта**](PROJECT_RETROSPECTIVE.md) — детальный разбор проблем, решений и результатов.
* 🛠 [**Шпаргалка по командам gcloud**](gcloud_cheatsheet.md) — справочник команд для управления инфраструктурой, Secret Manager и Cloud Run.
* 📊 [**Интерактивный Pitch Deck**](blogger_agent_pitch_deck.html) — презентационный мокап для печати в PDF.

---

## 📝 Лицензия
MIT License © 2026 Blogger Agent MCP Team.
