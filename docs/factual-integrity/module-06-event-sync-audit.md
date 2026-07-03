# Module 6 — Event sync interval audit

**Baseline:** `f0553ac5e87a00de49efdff30ef3ed9e317c8650`  
**Audit date:** 2026-07-03

## Defect table (before fix)

| Уровень | Текущее значение | Требуемое | Дефект |
|---------|------------------|-----------|--------|
| Config default (`config.py:121`) | 12 | 4 | Да |
| `.env.example` | 12 | 4 | Да |
| `docker-compose.prod.yml` | 0 (disabled) | 4 | Да — in-app scheduler выключен |
| Production env (runtime) | Cannot be verified до deploy | 4 | Ожидался 0 из compose |
| Scheduler sleep | `EVENT_SYNC_INTERVAL_HOURS * 3600` | 14400 | Да при hours≠4 |
| UI Афиши (`EventsStatsRibbon`) | кино 8 ч / полная 24 ч (hardcoded API) | 4 ч event sync | Да — не event interval |
| Map sync (`MAP_AUTO_SYNC_HOURS`) | 6 default / prod 0 + cron 6 ч | без изменений | OK |

## Scheduler flow (after fix)

1. `lifespan` → `start_background_tasks(settings)` once per worker process.
2. If `EVENT_SYNC_INTERVAL_HOURS > 0` → one `periodic:Event sync` task.
3. `run_periodic`: immediate `work()`, then `sleep(interval_seconds)`, loop; errors logged, loop continues.
4. Shutdown → `stop_background_tasks` cancels all tasks.
5. Duplicate registration in same process guarded by `_background_tasks_started`.

## Map sync

Unchanged: `MAP_AUTO_SYNC_HOURS=0` in prod compose; VPS cron map every 6 h; `MapStatsRibbon` still shows map interval.

## Module 7

**NOT STARTED.**
