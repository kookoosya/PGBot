# Stage 02 — Pushkin quotes audit

## Removed / corrected

| Text | Status | Action |
|------|--------|--------|
| «Здесь любил я первый жизни глас» | UNVERIFIED | Replaced in hero |
| «Ученье — свет, а неученье — тьма» | NOT_PUSHKIN | Removed from AI quotes |
| «Труд — вот лучшая зарядка для юности!» | UNVERIFIED | Removed from AI quotes |

## Verified set (`shared/pushkin_quotes.json`)

| Text | Work | Year | Source |
|------|------|-----:|--------|
| Приют спокойствия, трудов и вдохновенья | Деревня | 1819 | [RVB](https://rvb.ru/pushkin/01text/01versus/0217_22/1819/0046.htm) |
| Друзья мои, прекрасен наш союз! | 19 октября | 1825 | [RVB](https://rvb.ru/pushkin/01text/01versus/0423_36/1825/0386.htm) |
| Да здравствуют музы, да здравствует разум! | Вакхическая песня | 1825 | [RVB](https://rvb.ru/pushkin/01text/01versus/0423_36/1825/0382.htm) |
| И долго буду тем любезен я народу… | Я памятник себе воздвиг нерукотворный… | 1836 | [RVB](https://rvb.ru/pushkin/01text/01versus/0627_41/1836/0001.htm) |

## AI behaviour

- Random quote append removed (`PUSHKIN_QUOTES` deleted).
- Quotes appended only when user asks about poetry/Pushkin (`maybe_append_verified_quote`).
- System prompt forbids inventing Pushkin quotes.

## Афиша (read-only)

No production code changes. Event sources use automated sync; expired events filtered in `event/public.py`. No proven parser defect on this pass.
