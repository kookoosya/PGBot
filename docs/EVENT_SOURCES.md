# Источники афиши — токены и диагностика

Портал подтягивает события из 13 внешних источников. Большинство работают без ключей (RSS, парсинг сайтов). Три источника требуют токен в `.deploy.env` на сервере.

## Быстрая проверка

```bash
# На VPS или локально с docker
bash scripts/check-event-sources.sh

# Публичный health
curl -sS https://192-210-213-135.sslip.io/health | python3 -m json.tool
```

В ответе `event_sources`:

| Поле | `ready` | `group_token_only` | `needs_token` |
|------|---------|-------------------|---------------|
| `vk_wall` | полный импорт из всех VK-групп | только стена своего сообщества | токен не задан |
| `timepad` | TimePad API работает | — | нужен `TIMEPAD_API_TOKEN` |
| `proculture` | PRO.Культура API работает | — | нужен `PROCULTURE_API_KEY` |

Админка: **/admin/events** → панель «Источники афиши» (статусы, счётчики, синхронизация).

## Переменные в `.deploy.env`

```env
VK_EVENTS_TOKEN=vk1.a....      # user token для wall.get из нескольких сообществ
TIMEPAD_API_TOKEN=....         # https://dev.timepad.ru/
PROCULTURE_API_KEY=....        # https://pro.culture.ru/
```

После правки:

```bash
bash scripts/sync-vps-env.sh
# перезапуск backend на VPS (делает remote-deploy.sh автоматически)
```

## VK_EVENTS_TOKEN

Подробная пошаговая инструкция: [VK_SETUP.md](./VK_SETUP.md), шаг 8.

Кратко: нужен **user token** с правом `wall` — иначе в афишу попадут только посты сообщества бота (`VK_GROUP_ID`).

## TimePad

1. Зарегистрируйтесь на [timepad.ru](https://timepad.ru)
2. Получите API-токен в [документации TimePad](https://dev.timepad.ru/api/get-v1-events)
3. Добавьте `TIMEPAD_API_TOKEN` в `.deploy.env`
4. Синхронизация: админка → TimePad → «Синк» или `bash scripts/vps-sync-events.sh all`

Фильтры городов и ключевых слов: `backend/app/constants/event_config.py` → `TIMEPAD_CITY_FILTERS`.

## PRO.Культура

1. Получите API-ключ на [pro.culture.ru](https://pro.culture.ru/)
2. `PROCULTURE_API_KEY` в `.deploy.env`
3. Опционально: `PROCULTURE_PSKOV_LOCALE_ID` в `.env` (если нужен конкретный регион)

## Источники без токенов

Работают из коробки после деплоя и cron-синка:

- `pushkinland` — календарь Пушкинского заповедника (гарнец, программа)
- `informpskov`, `pln` — RSS новостей
- `kdc`, `drampush` — сайты КДЦ и драмтеатра
- `kinopskov`, `mirage`, `silver`, `orbilet` — кино Пскова
- `kudago` — открытый API (Псков ограничен в KudaGo)

Cron на VPS: `scripts/vps-sync-events.sh cinema` каждые 8 ч, `all` — раз в сутки в 03:15.

## Публичные ссылки

| URL | Назначение |
|-----|------------|
| `/events?festival=garnect` | только программа Бугровского гарнеца |
| `/events?source=pushkinland` | события из заповедника |
| `/share/festival/garnect` | OG-страница для шаринга программы гарнеца |

В API `/public/info` → `portal_links.events_garnect` и `events_garnect_share`.
