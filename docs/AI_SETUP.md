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

## Альтернатива: прямой Gemini

```env
GEMINI_API_KEY=AIza...   # из aistudio.google.com/apikey
```

Работает чат. Для картинок всё равно лучше Pollinations.

## Проверка

```bash
curl -s https://192-210-213-135.sslip.io/api/v1/ai/status | python3 -m json.tool
```

`"ready": true` — всё настроено.
