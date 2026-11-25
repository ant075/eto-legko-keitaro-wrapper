# Keitaro Wrapper

```bash
cp .env.example .env
# заполнить API_KEY в .env
docker compose up --build
```

Frontend: http://localhost:8080  
Backend healthcheck: http://localhost:8000/api/health

При старте backend применяет миграции и запускает сидер стран.

