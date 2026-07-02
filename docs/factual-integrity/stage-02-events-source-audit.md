# Stage 2 — Events source audit (read-only)

**Date:** 2026-06-27  
**No parser or import changes on this stage.**

## Sources (`event_sources/coordinator.py`)

| Source | URL | Region | Code status |
|--------|-----|--------|-------------|
| vk | VK API | Pushkinogorie, Pskov | active |
| timepad | timepad.ru | Pskov | active |
| orbilet | orbilet.ru | Pskov cinema | active |
| kinopskov | kinopskov.ru | Pskov | active |
| mirage | mirage cinema | Pskov | active |
| silver | silver cinema | Pskov | active |
| proculture | pro.culture.ru | filtered | active |
| kudago | kudago.com | Pskov | active |
| kdc | kdc-pushgory.ru | Pushkin Gory | active |
| pushkinland | pushkinland.ru | museum | active |
| informpskov | informpskov.ru | oblast | active |
| pln | pln-pskov.ru | Pskov | active |
| drampush | drampush.ru | Pskov theater | active |

## Checks

- Past events: `unpublish_past_external_events` in coordinator (unchanged).
- Tests assert `source_url` on pushkinland and drampush parsers.
- Production `/api/v1/events` unreachable from research host during audit.

## Defects

None proven without live DB. No afisha fixes applied.
