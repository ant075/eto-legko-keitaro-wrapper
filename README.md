# Keitaro Wrapper

```bash
cp backend/.env.example backend/.env
# заполнить API_KEY в backend/.env
docker compose up -d --build
```

Frontend: http://localhost:8080  
Backend healthcheck: http://localhost:8000/api/health

При старте backend применяет миграции и запускает сидер стран.

## Запуск в dev-режиме

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

В dev-режиме frontend доступен по адресу http://localhost:8080, backend — по адресу http://localhost:8000. Изменения исходников frontend и backend подхватываются автоматически. Dev- и production-конфигурации используют один volume PostgreSQL `postgres_data`.

### Запуск тестов в dev-режиме

Dev-образ содержит тестовые зависимости. После сборки dev-контейнеров запустите feature-тесты из корня проекта:

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps backend pytest
```

Тесты используют изолированную SQLite-базу и fake API Keitaro, поэтому для их запуска не требуется подключение к реальному API.

Для запуска отдельного файла или теста:

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps backend \
  pytest tests/features/test_offer_publication_canceling.py

docker compose -f docker-compose.dev.yml run --rm --no-deps backend \
  pytest tests/features/test_campaigns.py::test_create_campaign_creates_external_resources_and_initial_snapshot
```

Локальный запуск из virtualenv:

```bash
cd backend
source ../.venv/bin/activate
python -m pip install --no-cache-dir ".[test]"
python -m pytest
```

