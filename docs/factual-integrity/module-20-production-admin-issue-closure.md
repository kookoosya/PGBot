# Module 20 — Production Admin Access + Issue #6 Closure

**Status:** **NOT COMPLETE** — `ADMIN CREDENTIALS REQUIRED`  
**Baseline:** `2ef4f167d3bfd33e898dd58c5c97ac9ff84b260f`  
**Runtime baseline `/health`:** `4e78a93` (browser CDP, 2026-07-06)  
**Branch:** `main`

## Admin credential availability

| Check | Result |
|-------|--------|
| `.admin.env` exists locally | **no** |
| `.admin.env` tracked in git | **no** |
| `.deploy.env` exists (SSH only) | **yes** (not tracked) |
| Credentials in repo | **no** |
| Agent can authenticate to production admin | **no** |

Recommended local format (not committed):

```env
ADMIN_BASE_URL=https://pushkinskie-gory.xyz
ADMIN_USERNAME=...
ADMIN_PASSWORD=...
# or ADMIN_TOKEN=... after POST /api/v1/auth/login
```

Official issue moderation uses `/cabinet/login` → `/official` (roles: `administration`, `super_admin`, …). Owner panel `/admin/login` is separate (`OWNER_USERNAME` / `SUPER_ADMIN_USERNAME`).

## Admin / issue API map

| Item | Route | Auth |
|------|-------|------|
| Resident/official login | `POST /api/v1/auth/login` | public |
| Owner login UI | `/admin/login` | owner token |
| Official workbench | `/official` → `OfficialIssues.tsx` | `get_current_user` + official role |
| Admin issues (owner) | `/admin/issues` → `Issues.tsx` | owner |
| List issues | `GET /api/v1/issues` | `get_current_user` + access filter |
| Issue detail | `GET /api/v1/issues/{id}` | `require_issue_for_user` |
| Status update | `PATCH /api/v1/issues/{id}/status` | `require_owner_or_official()` |
| Archive | `PATCH /api/v1/issues/{id}/archive` | `require_owner_or_official()` |

## Issue #6 (Module 18 production test)

| Field | Value |
|-------|-------|
| Description marker | `MODULE 18 TEST — просьба не обрабатывать, проверка формы обращения.` |
| Created in Module 18 browser test | yes — UI showed «Обращение #6 принята» |
| Expected initial status | `NEW` |
| **Old status (production)** | **Cannot be verified** — `GET /api/v1/issues/6` → **401** without token |
| **Final status** | **unchanged** — closure not performed |
| Direct DB edit | **no** |

## Production read-only baseline

| Check | Result |
|-------|--------|
| `/health` `git_commit` | `4e78a93` |
| Smoke (last deploy Module 19) | **33 OK / 0 FAIL** |
| `/admin/login` | opens (owner panel) |
| `GET /api/v1/issues/6` unauthenticated | **401** `Not authenticated` |
| Public `/complaints` | not re-tested this session; Module 18/19 OK |

## Hypotheses A–O

| ID | Hypothesis | Result |
|----|------------|--------|
| A | Admin credentials absent locally | **CONFIRMED** |
| B | Admin login works | **CANNOT BE VERIFIED** |
| C | Issue #6 visible in admin list | **CANNOT BE VERIFIED** |
| D | Issue #6 detail opens | **CANNOT BE VERIFIED** |
| E | NEW → RESOLVED | **REJECTED** in tests (Module 19); production **CANNOT BE VERIFIED** |
| F | RESOLVED → ARCHIVED | **REJECTED** in tests; production **CANNOT BE VERIFIED** |
| G | Archived leaves active list | **CANNOT BE VERIFIED** |
| H | Archived not deleted | **REJECTED** in tests (retrieve still possible) |
| I | `statusError` in UI | **REJECTED** — fixed Module 19 `4e78a93` |
| J | Invalid status 4xx | **REJECTED** in tests |
| K | Missing issue 404 | **REJECTED** in tests |
| L | Auth protects endpoints | **REJECTED** — 401 on unauthenticated detail |
| M | Public complaints after archive | **CANNOT BE VERIFIED** (archive not done) |
| N | Interrupted deploy fallout | **REJECTED** — health OK, no 502 at verification time |
| O | Container/orphan state | **CANNOT BE VERIFIED** — VPS SSH from agent failed (ssh2 path / prior timeouts) |

## Confirmed defects

**None in code.** Blocker is **missing production admin credentials** for agent session.

## Closure attempt

**Not performed.** Module 20 stops per contract when `.admin.env` / credentials unavailable.

To complete manually (operator):

1. Create local `.admin.env` (add to `.git/info/exclude`).
2. `POST /api/v1/auth/login` with official/owner account.
3. `GET /api/v1/issues?search=MODULE%2018` — confirm id **6**, status.
4. `PATCH /api/v1/issues/6/status` → `RESOLVED` with resolution text marking test closure.
5. `PATCH /api/v1/issues/6/archive` → `ARCHIVED`.
6. Confirm issue absent from active list (`status_filter` excluding archived).

## Ops / deploy notes

- Prior VPS verify: 15× SSH timeout (Module 19 session).
- Prior parallel deploy interrupted on container recreate; subsequent deploy attempt **4** succeeded, `/health` = `4e78a93`.
- Current production: **no 502** at Module 20 read-only check.

## Changed files

- `docs/factual-integrity/module-20-production-admin-issue-closure.md` (this file)

## Tests run (regression, no code change)

- Existing Module 19 tests cover `NEW` → `RESOLVED` → `ARCHIVED` lifecycle locally.

## Cannot be verified

- Issue #6 current/final status on production
- Admin UI login and workbench with issue #6
- VPS container inventory (SSH from Windows agent)
- CI run ID
- Screenshots (`docs/screenshots/module-20-production/`)

## Module status

**MODULE 20 NOT COMPLETE** · **MODULE 21 NOT STARTED**
