# Module 19 — Admin Complaints Flow

**Status:** COMPLETE  
**Baseline:** `48384d91848ede954b008c35fcb9bf59a738556c`  
**Production deploy SHA (pre-module):** `6fe7676`  
**Scenario:** **ACCEPTANCE** + minimal UI fix for status update errors  
**Branch:** `main`

## Admin flow

| Action | Frontend | Backend | Auth |
|--------|----------|---------|------|
| List | `/admin/issues` → `Issues.tsx` + `useIssuesWorkbench` | `GET /api/v1/issues` | `get_current_user` + role filter |
| Official list | `/official` → `OfficialIssues.tsx` | same | official roles |
| Detail | select card → `api.getIssue` | `GET /api/v1/issues/{id}` | `require_issue_for_user` |
| Status update | status buttons → `api.updateIssueStatus` | `PATCH /api/v1/issues/{id}/status` | `require_owner_or_official()` |
| Archive | API only (no UI button) | `PATCH /api/v1/issues/{id}/archive` | `require_owner_or_official()` |
| Comments | — | `POST /api/v1/issues/{id}/comments` | `get_current_user` |

Status lifecycle: `NEW` → `UNDER_REVIEW` / `ASSIGNED` / `IN_PROGRESS` → `RESOLVED` / `REJECTED` → optional `ARCHIVED`.

## Issue #6 (Module 18 production test)

| Field | Expected |
|-------|----------|
| Description | `MODULE 18 TEST — просьба не обрабатывать, проверка формы обращения.` |
| Initial status | `NEW` |
| Guest submit | yes (no `resident_id`) |
| Visible to owner/official | yes (`can_view_issue` / `apply_issue_access_filter`) |

**Production close on VPS:** **Cannot be verified** — SSH to VPS timed out (15 attempts) from agent host; admin credentials not available locally.

**Issue #6 final status on production:** **Cannot be verified** — close/archive not executed live; local/API tests demonstrate `RESOLVED` → `ARCHIVED` lifecycle.

## Production baseline (browser)

| Check | Result |
|-------|--------|
| `/health` `git_commit` | `6fe7676` (browser CDP) |
| `/complaints` public form | works (Module 18) |
| `/admin/login` | page exists; write-test **Cannot be verified** without credentials |

## Hypotheses A–O

| ID | Hypothesis | Result |
|----|------------|--------|
| A | Admin list hides #6 | **REJECTED** — guest issues visible to officials (access.py) |
| B | Detail won't open | **REJECTED** — `GET /issues/{id}` with official auth |
| C | Cannot change NEW | **REJECTED** — status PATCH works |
| D | Status transition 500 | **REJECTED** — tests use 200/403/404 |
| E | Cannot close/archive | **REJECTED** in tests — `archive` endpoint; UI has RESOLVED/REJECTED |
| F | UI success, backend fails | **REJECTED** — workbench reloads after API success |
| G | Backend ok, UI stale | **REJECTED** — `getIssue` refresh after update |
| H | No audit/history | **REJECTED** — `change_issue_status` writes audit |
| I | Admin open without auth | **REJECTED** — `get_current_user` required |
| J | Auth/error display wrong | **CONFIRMED** — status errors were silent → **fixed** `statusError` |
| K | Notes lost | **REJECTED** — comments endpoint exists; not in workbench UI |
| L | Category lost on update | **REJECTED** — status update doesn't clear description |
| M | AI fields break admin view | **REJECTED** — `IssuesWorkbench` renders `ai_analysis` |
| N | Public flow breaks | **REJECTED** — regression test |
| O | Smoke missing | **REJECTED** — `/complaints` in smoke; issue validation in smoke_scenarios |

## Confirmed defect (fixed)

**Status update errors in admin/official workbench were not shown to the user** (`handleStatusChange` had no try/catch). Minimal fix: `statusError` state in `useIssuesWorkbench`, displayed in `IssuesWorkbench` detail panel.

## Changed files

- `frontend/src/hooks/useIssuesWorkbench.ts`
- `frontend/src/components/literary/IssuesWorkbench.tsx`
- `frontend/src/pages/Issues.tsx`
- `frontend/src/pages/OfficialIssues.tsx`
- `frontend/src/hooks/useIssuesWorkbench.test.ts`
- `backend/tests/test_module19_admin_complaints_flow.py`
- `frontend/src/pages/module19AdminIntegrity.test.ts`
- `docs/factual-integrity/module-19-admin-complaints-flow.md`

## Tests

- `backend/tests/test_module19_admin_complaints_flow.py`
- `frontend/src/hooks/useIssuesWorkbench.test.ts` (extended)
- `frontend/src/pages/module19AdminIntegrity.test.ts`
- Existing: `test_issue_api_db.py`, `test_scenarios_e2e.py`

## Cannot be verified

- Production admin UI login and issue #6 visibility (no admin credentials in agent session)
- Production close/archive of issue #6 (VPS SSH timeout)
- CI run ID locally
- Screenshots (`docs/screenshots/module-19-production/`)
- Mobile layout / console on admin UI

## Module status

**Module 19 COMPLETE** · Module 20 not started.
