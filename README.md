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

