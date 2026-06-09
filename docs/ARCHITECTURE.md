# Архитектура

## Поток данных

```
Житель → ВКонтакте → VK Callback API → FastAPI Backend
                                              ↓
                                         Gemini API (анализ)
                                              ↓
                                         PostgreSQL
                                              ↓
                                    Admin Panel (React)
                                              ↓
                                    Telegram (уведомления)
```

## Компоненты

### Backend (FastAPI)

- **VK Webhook** (`/api/v1/vk/callback`) — приём сообщений от жителей
- **Issue Processor** — обработка обращений: AI-анализ, дедупликация, назначение отдела
- **REST API** — CRUD для админ-панели
- **Telegram Service** — отправка уведомлений

### Frontend (React)

Админ-панель с разделами: Dashboard, Issues, Residents, Departments, Analytics, Audit, Settings.

### База данных

PostgreSQL с таблицами: users, roles, issues, issue_photos, issue_comments, issue_duplicates, departments, notifications, audit_logs, ai_analysis.

## Роли

| Роль | Доступ |
|------|--------|
| Resident | Отправка обращений через VK |
| Moderator | Модерация, объединение дубликатов |
| Administration | Управление обращениями, статусы |
| SocialService | Социальные обращения |
| SuperAdmin | Полный доступ |

## AI-анализ (Gemini)

На каждое обращение возвращается JSON:

```json
{
  "is_valid": true,
  "category": "Освещение",
  "priority": "medium",
  "summary": "Не работает фонарь возле дома",
  "duplicate_probability": 0.85,
  "suggested_department": "ЖКХ"
}
```

При недоступности Gemini используется rule-based fallback.

## Дедупликация

Если `duplicate_probability > 0.80`, обращение связывается с существующим, счётчик подтверждений увеличивается.

## Уведомления

- **Высокий приоритет** — немедленная отправка в Telegram
- **Обычный** — добавление в очередь (`notifications` table)
