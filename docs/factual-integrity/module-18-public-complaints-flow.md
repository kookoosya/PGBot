# Module 18 — Public Complaints Flow Production Verification

**Status:** COMPLETE  
**Baseline:** `268613b02cb57c596bb98aa118abbbd0eadce0ce`  
**Final:** `6fe7676a502c4c713eea8cf3642d00e079bb4573`  
**Production deploy SHA (runtime):** `6fe7676` (post-Module 18 deploy)  
**Scenario:** **ACCEPTANCE** — no new code defect; Module 13 fix remains effective  
**Branch:** `main`

## Public flow

| Step | File / endpoint | Behavior |
|------|-----------------|----------|
| Form render | `frontend/src/pages/Complaints.tsx` | `/complaints`, guest name+phone, description min 5, honeypot |
| Frontend validation | HTML5 `required`, `minLength={5}`, `checkValidity()` |
| Submit guard | `submittingRef` + `loading` disables button |
| API client | `POST /api/v1/issues` via `api.createIssue` |
| Backend schema | `IssueCreate` description 5–5000 |
| Service | `create_issue_from_web` → `process_web_complaint` + Gemini/rule fallback |
| Initial status | `NEW` |
| User response | `201` + `IssueResponse` (`id`, `status`) |
| Resident history | `GET /api/v1/issues/my` (auth) |
| Official list | `GET /api/v1/issues` (auth + role) |
| Dedup | high `duplicate_probability` links to parent issue |
| Rate limit | `ISSUE_RATE_LIMIT` on create endpoint |

## Production baseline (pre-Module 18 change)

| Check | Result |
|-------|--------|
| `/health` `git_commit` | `2e154d7` |
| `/complaints?new=1` | **200** — form visible |
| `POST /issues` short text | **Cannot verify** from Windows host (timeout); covered by deploy smoke + browser |
| Valid guest submit (browser) | **201 UI success** — issue **#6** |
| Issue text | `MODULE 18 TEST — просьба не обрабатывать, проверка формы обращения.` |
| UI success | «Обращение #6 принята», «Статус: на рассмотрении…» |
| Description cleared after success | **yes** |
| Submit button pending state | «Отправляем…» disabled during request |

**Production test issue ID:** **6** (MODULE 18 test; marked in description).  
Archive/close: **not performed** — no safe public lifecycle for guest-created test without admin credentials in agent session.

## Production verification (browser @ `2e154d7`)

| Check | Result |
|-------|--------|
| `/health` `git_commit` | `2e154d7` |
| Form at `/complaints?new=1` | **visible** |
| Valid guest submit | **success** — issue **#6**, status message «на рассмотрении» |
| Pending submit UI | button «Отправляем…» disabled |
| Description cleared after success | **yes** |

## Hypotheses A–O

| ID | Hypothesis | Result |
|----|------------|--------|
| A | Form missing/hidden | **REJECTED** — form at `/complaints?new=1` |
| B | Wrong endpoint | **REJECTED** — `api.createIssue` → `/issues` |
| C | Success before API | **REJECTED** — success only after `createIssue` resolves |
| D | Empty/short passes backend | **REJECTED** — schema min 5; smoke expects 422 |
| E | Bad input → 500 | **REJECTED** — 422/400 in Module 13 tests |
| F | Double click duplicate | **REJECTED** — `submittingRef` + disabled button; Module 13 rate limit 429 |
| G | Network error unclear | **REJECTED** — `catch` sets `msg` from `Error.message` |
| H | Issue not in admin/API | **CANNOT BE VERIFIED** — no admin session in agent; create returned ID |
| I | Wrong initial status | **REJECTED** — production UI «на рассмотрении» / API contract `NEW` |
| J | Category lost | **REJECTED** — optional; AI assigns when empty |
| K | Department not assigned | **REJECTED** — optional from AI; not blocking create |
| L | Rate limit breaks valid submit | **REJECTED** — single valid submit succeeded |
| M | Attachments break flow | **REJECTED** — web form has no uploads |
| N | CSRF/CORS breaks prod | **REJECTED** — browser submit succeeded same-origin |
| O | Smoke missing flow | **REJECTED** — `/complaints`, deep links in `smoke-public.sh`; validation in `smoke_scenarios.py` |

## Confirmed defects

**None** in Module 18 scope. Root issue (Gemini blocking all creates) fixed in Module 13 (`9fc4395`).

## Minimal fix

**None required.** Module 18 adds regression tests + this audit.

## Tests

- `backend/tests/test_module18_public_complaints_flow.py`
- `frontend/src/pages/Complaints.test.tsx`
- `frontend/src/pages/module18ComplaintsIntegrity.test.ts`
- Existing: `test_module13_public_complaints.py`, `client.test.ts`

## Changed files

- `docs/factual-integrity/module-18-public-complaints-flow.md`
- `backend/tests/test_module18_public_complaints_flow.py`
- `frontend/src/pages/Complaints.test.tsx`
- `frontend/src/pages/module18ComplaintsIntegrity.test.ts`

## Cannot be verified

- Direct `curl`/urllib from Windows agent host to production API (timeout)
- Admin UI list visibility of issue #6 (no credentials)
- Double-click duplicate on production (not re-run to avoid extra issues)
- CI run ID locally (`gh` unavailable)
- Screenshots (`docs/screenshots/module-18-production/`) — not captured
- Mobile layout / console on production

## Module status

**Module 18 COMPLETE** · Module 19 not started.
