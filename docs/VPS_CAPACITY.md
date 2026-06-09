# VPS: два проекта без конфликтов

## Текущая схема на вашем сервере

| Проект | Порт | Папка |
|--------|------|-------|
| BetMasterAI (торговый бот) | 80 → 8080 | /opt/BetMasterAI |
| Народный Контроль (VK + сайт) | 8088 | /opt/pgbot |

Проекты **изолированы**: разные Docker Compose, разные базы данных, разные порты.

## Выдержит ли VPS наплыв на VK-бота?

**Да, для поселка — обычно да.** Типичный VPS (2–4 GB RAM) справляется с:

- BetMasterAI на 8080
- PGBot на 8088 (FastAPI + PostgreSQL + nginx)
- Сотни одновременных обращений VK в час

### Если жителей станет очень много

1. Увеличить workers в `docker-compose.prod.yml`:
   ```
   uvicorn app.main:app --workers 4
   ```
2. Добавить RAM на VPS (4 → 8 GB)
3. VK Callback API сам по себе лёгкий — основная нагрузка это Gemini AI

### Мониторинг

```bash
docker stats                    # нагрузка контейнеров
free -h                         # память
docker logs pgbot-backend-1 -f  # логи VK
```

## Правила — не мешать друг другу

- **Не трогать** порт 80 и 8080 (BetMasterAI)
- PGBot только на **8088**
- Обновлять только: `cd /opt/pgbot && git pull && docker compose -f docker-compose.prod.yml up -d --build`
- BetMasterAI обновлять отдельно в `/opt/BetMasterAI`

## Домен

Когда привяжете домен к VPS — добавьте отдельный `server_name` в nginx, проксирующий на `127.0.0.1:8088`. BetMasterAI останется на основном домене или поддомене.
