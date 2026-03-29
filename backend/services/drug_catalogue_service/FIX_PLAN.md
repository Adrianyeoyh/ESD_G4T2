# Drug Catalogue Service - Fix Plan

**Service:** `backend/services/drug_catalogue_service/`
**Date:** 2026-03-29
**Status:** Pending execution

---

## Fix Checklist

### Critical

- [ ] **FIX-1: Syntax error in `run.py:5`**
  - File: `run.py`
  - Issue: Extra closing parenthesis causes `SyntaxError` — service cannot start
  - Action: Remove the trailing `)` from `uvicorn.run(...))`
  - Verify: `python -c "import py_compile; py_compile.compile('run.py', doraise=True)"`

### High

- [ ] **FIX-2: Add `GET /drug/{drug_id}` endpoint**
  - File: `app/routers/drug_router.py`
  - Issue: `DrugService.get_drug()` exists but has no route — single drug lookup is unreachable via HTTP
  - Action: Add `@router.get("/{drug_id}", response_model=DrugResponse)` route calling `service.get_drug(drug_id)`
  - Verify: Route exists returning a single `DrugResponse`

- [ ] **FIX-3: Rename update route to PATCH and add full update schema**
  - File: `app/routers/drug_router.py`, `app/schemas/drug_schema.py`
  - Issue: `PUT /{drug_id}` only updates quantity — misleading HTTP method for partial update
  - Action: Change `@router.put` to `@router.patch` for quantity-only update. Optionally add a `DrugUpdate` schema with all optional fields (`drug_name`, `quantity`, `price`) and a `PUT` route for full replacement
  - Verify: PATCH route exists for partial update

### Medium

- [ ] **FIX-4: Remove unused imports in `app/__init__.py`**
  - File: `app/__init__.py`
  - Issue: `asynccontextmanager`, `APIRouter`, `Depends`, `status` imported but never used
  - Action: Remove unused imports, keep only `FastAPI`, `Request`, `JSONResponse`, `text`, `SQLAlchemyError` (if used), router, Base, engine, drug_model, AppError
  - Verify: `python -c "from app import create_app"` succeeds with no warnings

- [ ] **FIX-5: Add `DrugUpdateQuantity` camelCase config**
  - File: `app/schemas/drug_schema.py`
  - Issue: `DrugUpdateQuantity` lacks `ConfigDict(alias_generator=to_camel, populate_by_name=True)` — inconsistent API casing with other schemas
  - Action: Add `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)` to `DrugUpdateQuantity`
  - Verify: Class has `model_config` with `alias_generator`

- [ ] **FIX-6: Add pagination to list endpoint**
  - Files: `app/routers/drug_router.py`, `app/repositories/drug_repository.py`
  - Issue: `GET /drug` returns all records with no limit — will degrade with scale
  - Action: Add `skip: int = 0, limit: int = 100` query params to `get_all_drugs`, pass to repo `list_all(skip, limit)` using `.offset(skip).limit(limit)`
  - Verify: Route accepts `skip` and `limit` query parameters

### Low

- [ ] **FIX-7: Remove redundant `save()` method or clarify intent**
  - File: `app/repositories/drug_repository.py`
  - Issue: `save()` calls `db.add()` on already-tracked objects — no-op that misleads readers
  - Action: Remove `save()` and `self.repo.save(drug)` call in `drug_service.py:46` since SQLAlchemy tracks dirty attributes automatically via session. The `commit()` on the next line is sufficient.
  - Verify: `save` method removed from repository, not called from service

- [ ] **FIX-8: Remove `.env` from version control**
  - File: `.env`, `.gitignore`
  - Issue: `.env` contains credentials and is tracked in git
  - Action: Add `*.env` or `.env` to the service's `.gitignore` (or project root), then `git rm --cached .env`
  - Verify: `git ls-files .env` returns empty

---

## Execution Order

1. FIX-1 (unblocks service startup)
2. FIX-4 (quick cleanup)
3. FIX-2, FIX-5 (API completeness)
4. FIX-3, FIX-6 (API improvements)
5. FIX-7, FIX-8 (cleanup)

---

*Generated from code review of drug_catalogue_service on 2026-03-29*
