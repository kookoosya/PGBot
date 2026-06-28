# Cloudflare — полная инструкция с нуля

**Домен:** `pushkinskie-gory.xyz` (лежит в Porkbun)  
**Сервер (VPS):** `192.210.213.135` — сайт PGBot уже там  
**Цель:** чтобы `https://pushkinskie-gory.xyz` открывался в России **без VPN**

Cloudflare — бесплатный «прокси» перед сайтом. Люди в РФ ходят на IP Cloudflare, а не напрямую на US-сервер.

---

## Часть 1. Регистрация в Cloudflare

1. Открой в браузере: **https://dash.cloudflare.com/sign-up**
2. Введи **email** и **пароль** → **Sign up**
3. Подтверди почту (письмо от Cloudflare → ссылка **Verify email**)
4. Войди: **https://dash.cloudflare.com/login**

---

## Часть 2. Добавить домен в Cloudflare

1. На главной Cloudflare нажми синюю кнопку **Add a site** (или **Add site**)
2. В поле введи **точно**:

   ```
   pushkinskie-gory.xyz
   ```

   Без `https://`, без `www`, без слэша в конце.

3. Нажми **Continue**
4. Выбери план **Free** → **Continue**
5. Cloudflare просканирует DNS — нажми **Continue**

---

## Часть 3. DNS-записи в Cloudflare (важно!)

На шаге **Review your DNS records** (или позже: домен → **DNS** → **Records**):

### Удали лишнее

- Если есть записи с **серым облачком** на IP Porkbun (`44.227.x.x` и т.п.) — удали или замени
- Если включён **URL Forwarding** в Porkbun — его отключим в части 4

### Добавь или измени две A-записи

| Type | Name (имя) | IPv4 address (значение) | Proxy status |
|------|------------|-------------------------|--------------|
| **A** | `@` | `192.210.213.135` | **Proxied** (оранжевое облако ☁️) |
| **A** | `www` | `192.210.213.135` | **Proxied** (оранжевое облако ☁️) |

> **Отдельный поддомен `api` не нужен.** REST API на том же домене:  
> `https://pushkinskie-gory.xyz/api/v1/...`  
> Если при импорте DNS появилась запись `api` — удали (если не используешь `api.домен` отдельно).

**Как добавить запись:**

1. **Add record**
2. Type: **A**
3. Name: `@` (для корня домена) или `www` (для www.)
4. IPv4 address: `192.210.213.135`
5. **Proxy status** — кликни на облако, чтобы было **оранжевым** (надпись **Proxied**)
6. **Save**

> Серое облако (**DNS only**) — **не подходит**. Нужно только **оранжевое Proxied**.

Нажми **Continue** / **Save** в мастере настройки.

---

## Часть 4. Nameservers — переключить домен с Porkbun на Cloudflare

Cloudflare покажет экран **Change your nameservers** с **двумя** nameserver, например:

```
ada.ns.cloudflare.com
bob.ns.cloudflare.com
```

(У тебя будут **свои** два адреса — скопируй их из Cloudflare, не эти примеры.)

### В Porkbun

1. Открой **https://porkbun.com** → войди в аккаунт
2. **Domain Management** → кликни на **pushkinskie-gory.xyz**
3. Найди раздел **Authoritative Nameservers** (или **DNS / Nameservers**)
4. Выбери **Use custom nameservers** (свои NS, не Porkbun default)
5. Вставь **оба** nameserver от Cloudflare (Host 1 и Host 2)
6. **Save** / **Update**

### Отключи parking / forwarding (если есть)

В той же панели Porkbun:

- **URL Forwarding** — **Off** / удалить
- **Parking** — выключить, если включён

### В Cloudflare

Вернись в Cloudflare → нажми **Done, check nameservers** (или **Continue**)

Статус домена станет **Active** (зелёный) через **10 минут — 24 часа**. Обычно **30–60 минут**.

Пока **Pending** — это нормально, жди.

---

## Часть 5. SSL в Cloudflare

Когда домен **Active**:

1. Cloudflare → **pushkinskie-gory.xyz** → слева **SSL/TLS**
2. **Overview** → режим **Full (strict)**

   | Режим | Когда |
   |-------|--------|
   | **Full (strict)** | основной (у нас на VPS есть Let's Encrypt) |
   | Full | только если strict выдаёт ошибку — временно для проверки |

3. **SSL/TLS** → **Edge Certificates**:
   - **Always Use HTTPS** → **On**
   - **Automatic HTTPS Rewrites** → **On** (можно)

---

## Часть 6. Проверка

### В браузере (лучше с телефона без VPN, мобильный интернет)

```
https://pushkinskie-gory.xyz
```

Должен открыться портал Пушкинских Гор.

```
https://pushkinskie-gory.xyz/health
```

Должно быть:

```json
{"status":"ok",...}
```

### Если не открывается

| Симптом | Что проверить |
|---------|----------------|
| «Сайт не найден» | NS в Porkbun ещё не обновились — подожди 1–2 часа |
| Ошибка SSL | Cloudflare SSL → попробуй **Full** вместо strict |
| 522 / 523 | VPS не отвечает — напиши мне, проверю сервер |
| Открывается только с VPN | Облако должно быть **оранжевым** (Proxied) |

---

## Часть 7. Что делает агент на VPS (тебе не трогать)

После того как Cloudflare станет **Active**, на сервере уже настроено:

- nginx + HTTPS (Let's Encrypt)
- скрипт `setup-cloudflare-origin.sh` — правильные IP клиентов через Cloudflare
- деплой через git / GitHub Actions

**VK Callback** (если спросят):  
`https://pushkinskie-gory.xyz/api/v1/vk/callback`

---

## Краткий чеклист

- [ ] Аккаунт Cloudflare создан
- [ ] Домен `pushkinskie-gory.xyz` добавлен (план Free)
- [ ] A `@` → `192.210.213.135` — **Proxied** (оранжевое)
- [ ] A `www` → `192.210.213.135` — **Proxied** (оранжевое)
- [ ] В Porkbun NS заменены на Cloudflare (2 штуки)
- [ ] URL Forwarding в Porkbun выключен
- [ ] Cloudflare статус **Active**
- [ ] SSL **Full (strict)** + **Always Use HTTPS**
- [ ] Сайт открывается без VPN

---

## Чего НЕ нужно

- Покупать `.ru` — **не нужен**
- Переносить домен на Cloudflare Registrar — **не нужен**, достаточно NS
- Платный план Cloudflare — **не нужен**, хватит Free
- Трогать VPS / git — **делает агент**

---

## Если застрял

Напиши на каком шаге и что видишь на экране (или скрин). Чаще всего проблема:

1. Облако **серое** вместо оранжевого  
2. NS в Porkbun **не сохранились**  
3. Ещё не прошло время после смены NS  
