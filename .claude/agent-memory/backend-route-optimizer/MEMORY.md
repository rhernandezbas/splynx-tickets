# Backend Route Optimizer Memory

## Key Patterns & Conventions

### Database-First Configuration
- All configuration stored in database (`system_config`, `operator_config`, `operator_schedule`)
- Use `ConfigHelper` to read config values, never hardcode
- Only credentials and static IDs in `constants.py`

### Date Handling Patterns
- CSV/webhook dates from Gestión Real: DD-MM-YYYY HH:MM:SS → `parse_gestion_real_date()` in `date_utils.py`
- Splynx API dates: YYYY-MM-DD HH:MM:SS → `parse_splynx_date()` in `date_utils.py`
- Internal DB datetime: naive datetime (no timezone)
- Always use Argentina timezone (pytz): `America/Argentina/Buenos_Aires`
- When comparing naive with aware datetimes: localize with `ensure_argentina_tz()`

### Interface Layer Pattern
- All DB operations through interface layer (`app/interface/interfaces.py`)
- IntegrityError on duplicate = expected behavior (log as info, not error)
- Return None on error, never raise exceptions
- Always commit after updates
- `TicketResponseMetricsInterface` is DEPRECATED (stub only) — data now lives in `IncidentsDetection`

### Thread Pattern
- Long-running operations use `threading.Thread` with app context
- Always pass `current_app._get_current_object()` as arg to threads needing DB access
- Use `with app.app_context():` inside the thread function
- Exception: `thread_close_tickets` has no app context (currently broken — see known issues)

### Webhook Pipeline (post Selenium migration, 2026-03)
- External system POSTs to `/api/hooks/nuevo-ticket` → stored in `hook_nuevo_ticket` table (raw)
- Scheduler calls `/api/tickets/process_webhooks` every 3 min
- `thread_process_webhooks` calls `process_pending_webhooks()` then `TicketManager.create_ticket()`
- Duplicate detection uses `Fecha_Creacion` unique constraint in `IncidentsDetection`
- After processing (success or duplicate), webhook is marked `processed=True`
- Hooks endpoints have no auth (intentional — called by external system via trusted network)

## Known Issues & Anti-Patterns

### CRITICAL: `clean_closed_ticket()` is missing
- `thread_close_tickets()` in `thread_functions.py:59` calls `tk.clean_closed_ticket()`
- This method does NOT exist in `TicketManager` — calling `/api/tickets/close` raises `AttributeError`
- The `/api/tickets/close` endpoint and scheduler job were removed but the thread function was not cleaned up

### Stale import in `views.py:204`
- `from app import create_app` imported inside `sync_tickets_status_endpoint()` but never used

### `TicketResponseMetrics` still queried directly in `admin_routes.py:839`
- Direct model query bypasses interface layer; returns data from old table (may be stale/unmigrated)
- Comment at line 752 says "Usar IncidentsDetection" but line 839 still queries TicketResponseMetrics

### `HookNuevoTicket` has no unique constraint on `numero_ticket`
- Same webhook can be received twice (retry from external system) → stored twice → both processed
- `Fecha_Creacion` unique constraint in `IncidentsDetection` prevents incident duplicates,
  but `hook_nuevo_ticket` grows unbounded with duplicates

### Scheduler weekday hours hardcoded
- `scheduler.py:43`: `if not (8 <= current_hour < 23)` is hardcoded
- Weekend hours use ConfigHelper correctly — weekday hours do not (inconsistency)

### N+1 / full-table scan pattern in `ticket_manager.py`
- `_check_ticket_bd()` (line 155) and `create_ticket()` (lines 303, 379) call `IncidentsInterface.get_all()`
  then filter in Python — loads entire table on every scheduler run
- Should use: `IncidentsDetection.query.filter_by(is_created_splynx=False).all()`

### `datetime.utcnow()` in `webhook_interface.py:68`
- Inconsistent timezone: rest of app uses naive datetimes; `processed_at` uses utcnow
- Should use `datetime.now()` for consistency

### Direct `OperatorConfig.query` in `ticket_manager.py` (lines 749, 1160)
- Bypasses interface layer — should use `OperatorConfigInterface`

## Post-Selenium Migration Status (reviewed 2026-03)
- thread_close_tickets / clean_closed_ticket / all_flow / thread_download_csv: ALL GONE - migration is clean
- No broken imports from removed modules found anywhere in app/
- `is_from_gestion_real` and `ultimo_contacto_gr` dropped from DB by migration `b2c3d4e5f6a7`
- Migration chain: eb1116c82879 → a8c2d4e6f0b1 → f0fb571414ca → a1b2c3d4e5f6 → b2c3d4e5f6a7
- All scheduler jobs reference valid endpoints: /api/tickets/process_webhooks, assign_unassigned, alert_overdue, end_of_shift_notifications, auto_unassign_after_shift, sync_status, import_existing

## New Issues Found (2026-03 review)

### `import_existing_tickets.py` has its own `parse_splynx_date` (duplicate)
- `app/utils/import_existing_tickets.py:15-23` defines `parse_splynx_date` locally
- `app/utils/date_utils.py` already has the canonical `parse_splynx_date`
- Should import from `date_utils` instead of redeclaring

### `import_existing_tickets.py` uses `import logging` not centralized logger
- Line 11: `import logging` + `logger = logging.getLogger(__name__)`
- Should use `from app.utils.logger import get_logger`; `logger = get_logger(__name__)`

### `sync_tickets_status.py` uses `import logging` not centralized logger
- Same anti-pattern as above, line 15-17

### `auto_unassign_after_shift` uses wrong Splynx field name
- `ticket_manager.py:1044`: `ticket.get('assigned_to')` — Splynx API returns `assign_to`
- The same function at line 477 correctly uses `ticket.get('assign_to', 0)`
- This causes `assigned_to` to always be `None` → schedules never fetched → no desassignment

### ConfigHelper has in-process cache — cache never invalidates between requests
- `config_helper.py:14`: `_cache = {}` is a class-level dict (shared singleton across threads)
- Config changes via admin panel won't take effect until process restart
- Consider adding TTL or invalidating cache when `config/<key>` PUT succeeds

### `constants.py` has hardcoded DB password fallback
- `constants.py:94`: `DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')`
- Hardcoded default credential is a security concern; should use `None` as default

### Direct model access in admin_routes.py (acceptable pattern there)
- `admin_routes.py` uses `IncidentsDetection.query` directly in many places — this is by design
- The admin layer is NOT going through the interface layer — it's using SQLAlchemy directly
- This is a tradeoff; not critical but inconsistent with pattern elsewhere

## Common Routes/Files Reference
- Routes: `app/routes/` (views.py, admin_routes.py, hooks_routes.py, whatsapp_routes.py, auth_routes.py)
- Auth decorators: `login_required`, `admin_required` defined in `auth_routes.py`, used in `whatsapp_routes.py`
- Thread functions: `app/routes/thread_functions.py` (all background work goes here)
- Webhook entry: `app/routes/hooks_routes.py`
- Webhook processing: `app/services/webhook_processor.py`
- Date utilities: `app/utils/date_utils.py`
- `parse_gestion_real_date` still used in `sync_tickets_status.py` as fallback for `Fecha_Creacion`
- Duplicate `parse_splynx_date` in `import_existing_tickets.py` (should use `date_utils` version)
