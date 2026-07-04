# Module 13 — public complaints flow

**Baseline SHA:** `e856efd78a7cf203b1c1b71d52bb109c0589ab20`  
**Scope:** public web complaints (`/complaints` → `POST /api/v1/issues`).  
**Module 14:** not started.

## Flow summary

| Step | Behavior |
|------|----------|
| User fields | `description` (required, min 5), optional `address`, `category`, guest `full_name`+`phone`, honeypot `website_url` |
| Frontend validation | HTML5 `required`, `minLength={5}`, guest name/phone required; submit disabled while `loading`; `submittingRef` blocks double submit |
| API | `POST /api/v1/issues` (optional auth) |
| Backend schema | `IssueCreate`: description 5–5000 chars; honeypot → 400 |
| Service | `create_issue_from_web` → `process_web_complaint` → Gemini analysis + rule fallback → dedup → persist |
| Initial status | `NEW` when accepted; spam path `REJECTED` / `is_spam=true` (not returned to user) |
| User response | `201` + `IssueResponse` (`id`, `status`, …) |
| Resident history | `GET /api/v1/issues/my` (auth) |
| Official list | `GET /api/v1/issues` (auth + role filter) |
| Dedup | `duplicate_probability >= DUPLICATE_THRESHOLD` links to open parent, increments `confirmation_count` |

## Production baseline (pre-fix, SHA `e856efd`)

| # | Request | Status | Result |
|---|---------|--------|--------|
| 1 | `POST /issues` `{"description":"abc"}` | **422** | Pydantic `string_too_short` |
| 2 | `POST /issues` description only, no contact | **400** | «Укажите имя и телефон или войдите в кабинет» |
| 3 | `POST /issues` with `website_url` honeypot | **400** | «Не удалось отправить форму…» |
| 4 | `POST /issues` test text + guest contact | **400** | «Обращение не принято…» (Gemini/failure path) |
| 5 | `POST /issues` realistic lighting/roads text | **400** | same — **all live creates rejected** |
| 6 | `GET /complaints` page | **200** | smoke OK |
| 7 | `GET /complaints?new=1` | **200** | smoke OK |

**Production test issue ID (pre-fix):** none — creates rejected before user-visible `201`.

## Hypothesis matrix

| ID | Hypothesis | Result |
|----|------------|--------|
| A | Double submit creates two issues | **REJECTED** — `loading` + `submittingRef` guard on form |
| B | Frontend validation weaker than backend | **REJECTED** — both min 5 chars; 422 messages were opaque (**see fix I**) |
| C | Backend accepts empty/garbage | **REJECTED** — 422/400 on bad input |
| D | Backend returns 500 on bad input | **REJECTED** — 422/400 observed |
| E | UI success on API failure | **REJECTED** — success only in `try` after `createIssue` |
| F | Created issue not in admin/API | **CANNOT BE VERIFIED** pre-fix (no successful create) |
| G | Status/department not assigned | **REJECTED** in tests — `NEW` + optional `department_id` from AI |
| H | Dedup incorrect | **REJECTED** — covered by `test_business_rules_db` + Module 13 duplicate test |
| I | Error message unclear on 422 | **CONFIRMED** — `error.detail` array rendered poorly → **fixed** `formatApiErrorDetail` |
| J | Attachments break web flow | **REJECTED** — web form has no photo upload |

## Confirmed defect (fixed)

**Gemini outage / false-negative blocked all public complaints on production.**

- `run_gemini_with_retry` returned `is_valid=false` on API failure instead of rule-based `_fallback_analysis`.
- Valid village complaints (lighting, roads) received **400** «Обращение не принято…».
- **Fix:** on Gemini failure use `_fallback_analysis`; when Gemini rejects but rules accept, override in `analyze_issue_with_context`.

## Changes in this module

| File | Change |
|------|--------|
| `backend/app/services/issue/gemini_analysis.py` | Rule fallback on Gemini failure + false-negative override |
| `frontend/src/lib/api/client.ts` | `formatApiErrorDetail` for 422 arrays |
| `frontend/src/pages/Complaints.tsx` | `submittingRef` anti double-submit |
| `backend/tests/test_module13_public_complaints.py` | Module 13 targeted tests |
| `frontend/src/lib/api/client.test.ts` | API error formatting test |
| `docs/factual-integrity/module-13-public-complaints-flow.md` | this audit |

Map, inventory, Афиша, VK bot, admin UI: **unchanged**.

## Tests

- `backend/tests/test_module13_public_complaints.py`
- `frontend/src/lib/api/client.test.ts`
- Existing: `test_public_api.py`, `test_business_rules_db.py`, `test_scenarios_e2e.py`

## Cannot be verified (pre-deploy)

- Live `201` create on production before fix (all attempts returned 400).
- Admin UI visibility of test issue (no issue created pre-fix).

Post-deploy verification required for Module 13 COMPLETE.

## Module status

Pending deploy + production re-test.
