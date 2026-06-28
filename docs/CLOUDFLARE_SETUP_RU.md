# Cloudflare и доступ из России (актуально 2026)

**Домен:** `pushkinskie-gory.xyz`  
**VPS:** `192.210.213.135`

---

## Важно: оранжевое облако в РФ не работает

С июня 2025 провайдеры в России **режут сайты за Cloudflare Proxied** (~16 КБ на соединение). Сайт не в реестре РКН — **ломается весь Cloudflare**.

**Для жителей России:** DNS-записи должны быть **DNS only (серое облако)**, не Proxied.

Подробно: [RU_ACCESS_FIX.md](./RU_ACCESS_FIX.md)

---

## Настройка Cloudflare (DNS only)

### 1. Домен Active, NS на Cloudflare

Nameservers в Porkbun → два NS от Cloudflare (как раньше).

### 2. DNS → Records

| Type | Name | IPv4 | Proxy |
|------|------|------|-------|
| A | `@` | `192.210.213.135` | **DNS only** (серое) |
| A | `www` | `192.210.213.135` | **DNS only** (серое) |

Поддомен `api` **не нужен** — API по пути `/api/v1/`.

### 3. Проверка

```bash
dig +short pushkinskie-gory.xyz A
```

Должно быть **`192.210.213.135`**. Если видишь `104.21.x` или `172.67.x` — облако всё ещё **оранжевое**, переключи на серое.

### 4. С телефона без VPN

- https://pushkinskie-gory.xyz  
- https://pushkinskie-gory.xyz/health  

---

## Регистрация / NS (если ещё не сделано)

1. https://dash.cloudflare.com → Add site → `pushkinskie-gory.xyz` → Free  
2. DNS-записи как выше (**серое** облако)  
3. Porkbun → custom NS → два nameserver от Cloudflare  
4. Отключить URL Forwarding / parking в Porkbun  

---

## VPS (делает агент)

- Let's Encrypt для `@` и `www`  
- `bash scripts/setup-cloudflare-origin.sh` — real IP (полезно, если позже снова включишь Proxied)  
- Деплой: `git pull && bash scripts/vps-deploy.sh`  

---

## Если после серого облака всё равно не открывается

IP `192.210.213.135` (US) могут резать отдельно. Нужен **VPS в России** — см. [RU_ACCESS_FIX.md](./RU_ACCESS_FIX.md), решение 2.

---

## VK Callback

`https://pushkinskie-gory.xyz/api/v1/vk/callback`
