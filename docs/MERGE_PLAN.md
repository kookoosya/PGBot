# План мержа PR #37 в main

Ветка: `cursor/literary-site-cohesion-771b`  
PR: https://github.com/kookoosya/PGBot/pull/37

## Что входит в PR

- Дизайн-система «Пушкиногорский альбом» (публичный фронтенд)
- Восстановление киноафиши (backend enrichment + фильтр `isRealCinemaEvent`)
- Миграции Alembic `018_event_genre`, `019_event_poster`
- Fallback `alembic stamp head` в `scripts/remote-deploy.sh`

Относительно `main`: ~101 файл, +9k / −1.4k строк.

---

## PR: что закрыть, что оставить

### Закрыть как superseded (уже в #37)

| PR | Ветка |
|----|-------|
| #31 | `cursor/literary-album-style-771b` |
| #32 | `cursor/literary-pages-style-771b` |
| #33 | `cursor/landing-hero-polish-771b` |
| #34 | `cursor/literary-remaining-pages-771b` |
| #35 | `cursor/literary-atmosphere-polish-771b` |
| #36 | `cursor/cinema-afisha-fix-771b` |
| #29 | `cursor/restore-landing-features-771b` (функции landing восстановлены в #37) |

Комментарий при закрытии: `Superseded by #37`.

### Оставить на потом (не мержить вместе с #37)

| PR | Причина |
|----|---------|
| #24–#28 | Рефакторинги модулей — отдельное ревью |
| #21 | JWT httpOnly cookies — breaking change auth |
| #27 | Redis rate limit — инфраструктура |
| #19–#20, #23 | AI tiers, VK DB — продуктовые фичи |
| #30 | Map polish — rebase после мержа #37 |

---

## Перед мержем

1. **Убедиться, что CI/сборка зелёная**
   ```bash
   cd frontend && npm run build
   ```

2. **Локальный smoke (опционально)**
   ```bash
   bash scripts/smoke-public.sh http://localhost:5173
   ```

3. **Rebase на актуальный main** (если main ушёл вперёд)
   ```bash
   git fetch origin main
   git rebase origin/main
   # при конфликтах — разрешить, npm run build, git rebase --continue
   ```

4. **Проверить, что на проде нет незакоммиченных hotfix** вне main.

---

## Мерж

Рекомендуется **merge commit** (сохраняет историю этапов) или **squash** (один коммит в main — проще откатить визуально).

```bash
# На GitHub: Merge pull request #37 → main
# Или локально:
git checkout main
git pull origin main
git merge --no-ff cursor/literary-site-cohesion-771b -m "feat: Пушкиногорский альбом + киноафиша (#37)"
git push origin main
```

После мержа: закрыть PR #31–#36, #29 как superseded.

---

## Сразу после мержа

### 1. Деплой

```bash
BRANCH=main bash scripts/remote-deploy.sh
```

Скрипт выполняет: `git pull`, `docker compose up -d --build`, `alembic upgrade head || alembic stamp head`, `seed_events.py`.

### 2. Smoke на проде

```bash
bash scripts/smoke-public.sh https://192-210-213-135.sslip.io
# или
bash scripts/smoke-public.sh https://pushkinskie-gory.ru
```

Проверяются: главная, `/events`, `/classifieds`, `/map`, `/api/v1/public/today`, статические ассеты.

### 3. Ручная проверка (5 мин)

| URL | Ожидание |
|-----|----------|
| `/` | Literary hero, блок «Сегодня», афиша, кино |
| `/events` | Literary layout, кино с постерами (если есть данные) |
| `/classifieds` | Карточки с датой, literary empty state |
| `/map` | Карта, literary header |
| `/register` | Literary hub |
| `/events` → фильм | Постер, жанр, сеансы |

### 4. Синхронизация афиши (если кино-блок пуст)

```bash
docker compose -f docker-compose.prod.yml exec -T backend python scripts/enrich_events.py
# или источники kinopskov/mirage/silver по cron
```

---

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Alembic 018/019 уже на проде | Средняя | `upgrade \|\| stamp head` в deploy |
| Пустой блок кино | Средняя | Запуск enrichment после деплоя |
| Откат стиля | Низкая | CSS подключён в `main.tsx`, один атомарный PR |
| Сломанные lazy-роуты | Низкая | `npm run build` + smoke URLs |
| Конфликт с #30 map | Низкая | Rebase #30 после мержа #37 |

---

## Откат (если что-то пошло не так)

```bash
git revert -m 1 <merge-commit-sha>   # откат merge commit
git push origin main
BRANCH=main bash scripts/remote-deploy.sh
```

Для отката только фронта без backend: не рекомендуется — кино-фильтр зависит от полей `genre`/`poster_url`.
