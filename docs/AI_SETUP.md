# Настройка ИИ (чат + картинки)

## Проблема «ИИ не работает»

На VPS в `/opt/pgbot/.env` часто остаётся **заглушка** `GEMINI_API_KEY=your-gemini-api-key` из примера — это **не настоящий ключ**.

Pollinations (Flux, картинки + чат) требует отдельный ключ: `POLLINATIONS_API_KEY`.

## Быстрая настройка (рекомендуется)

1. Зарегистрируйтесь на [enter.pollinations.ai](https://enter.pollinations.ai)
2. Создайте **Secret key** (`sk_...`)
3. Добавьте в `.deploy.env` в корне репозитория:

```env
POLLINATIONS_API_KEY=sk_ваш_ключ
```

4. Задеплойте: `bash scripts/remote-deploy.sh`

Ключ автоматически попадёт в `/opt/pgbot/.env` на сервере.

## Gemini (Google) — где взять ключ

1. Откройте **https://aistudio.google.com/apikey**
2. Войдите в Google-аккаунт
3. Нажмите **«Create API key»** / «Создать ключ API»
4. Скопируйте ключ — он начинается с **`AIza...`** (длина ~39 символов)

Бесплатный тариф: есть лимиты на запросы в минуту/день — для портала обычно хватает.

### Куда вставить ключ

**Вариант А** — Cursor → Settings → Cloud Agents → **Secrets**:
```env
GEMINI_API_KEY=AIzaSy...
```

**Вариант Б** — файл `.deploy.env` в корне проекта:
```env
GEMINI_API_KEY=AIzaSy...
```

Затем деплой: `bash scripts/remote-deploy.sh` — ключ попадёт в `/opt/pgbot/.env`.

Приоритет провайдеров: Pollinations → OpenRouter → **Gemini** → локальный справочник.

### Лимиты

| Уровень | Что ограничено |
|---------|----------------|
| **Портал** | 30 сообщений/картинок в день на человека (обновление в полночь) |
| **Gemini** | Квота Google: запросов в минуту и в день; при 429 — подождите или включите биллинг |
| **OpenRouter** | Баланс кредитов на аккаунте |
| **Pollinations** | Pollen на аккаунте (enter.pollinations.ai) |

**Важно:** чужие «бесплатные ключи из интернета» использовать нельзя — это нарушение правил и риск блокировки. Легальные бесплатные варианты: [aistudio.google.com](https://aistudio.google.com/apikey), [enter.pollinations.ai](https://enter.pollinations.ai), [openrouter.ai](https://openrouter.ai).

## Проверка

```bash
curl -s https://192-210-213-135.sslip.io/api/v1/ai/status | python3 -m json.tool
```

`"ready": true` — всё настроено.
