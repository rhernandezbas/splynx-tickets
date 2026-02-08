# Backend Route Optimizer Memory

## Key Patterns & Conventions

### Database-First Configuration
- All configuration stored in database (`system_config`, `operator_config`, `operator_schedule`)
- Use `ConfigHelper` to read config values, never hardcode
- Only credentials and static IDs in `constants.py`

### Date Handling Patterns
- CSV dates from Gestión Real: DD-MM-YYYY HH:MM:SS format
- Splynx API dates: YYYY-MM-DD HH:MM:SS format (ISO-ish)
- Internal DB datetime: naive datetime (no timezone info)
- Always use Argentina timezone (pytz) for comparisons: `America/Argentina/Buenos_Aires`
- When comparing naive with aware datetimes: localize naive first with ARGENTINA_TZ

### Ticket Source Differentiation
- **GR Tickets**: `is_from_gestion_real=True` → Use `ultimo_contacto_gr` for last_update
- **Splynx Tickets**: `is_from_gestion_real=False/None` → Use `updated_at` from API for last_update
- Field `last_update` in DB stores the appropriate timestamp based on source
- Sync logic in `sync_tickets_status.py` handles differentiation (lines 87-112)

### Interface Layer Pattern
- All DB operations through interface layer (`app/interface/interfaces.py`)
- IntegrityError on duplicate = expected behavior (log as info, not error)
- On duplicate GR tickets: update `ultimo_contacto_gr` and `last_update` if changed
- Return None on error, never raise exceptions
- Always commit after updates

## Common Anti-Patterns to Watch For

1. **Mixing date formats**: CSV parsing must handle DD-MM-YYYY, not YYYY-MM-DD
2. **Timezone-naive comparisons**: Always localize datetime before comparing with now()
3. **Direct model access**: Must go through interface layer
4. **Hardcoded config**: Check if value exists in `system_config` table first
5. **Missing null checks**: Always check if datetime field exists before using it

## Recent Implementations (2026-02-08)

### Differentiated Last Update Tracking
- Added `is_from_gestion_real` (Boolean) and `ultimo_contacto_gr` (DateTime) to `IncidentsDetection`
- CSV parsing extracts "Ultimo Contacto" column (line 409 in selenium_multi_departamentos.py)
- Date parsing handles DD-MM-YYYY HH:MM:SS format with explicit component extraction
- On duplicate tickets from GR: update ultimo_contacto_gr if present (interfaces.py:88-104)
- Sync logic differentiates between GR and Splynx tickets for last_update source

### CSV Date Parsing Strategy
```python
# Split date string: "08-02-2026 14:30:45"
parts = ultimo_contacto.split(' ')
date_parts = parts[0].split('-')  # ['08', '02', '2026']
time_part = parts[1] if len(parts) > 1 else '00:00:00'
year = date_parts[2]
month = date_parts[1]
day = date_parts[0]
dt = datetime.strptime(f'{year}-{month}-{day} {time_part}', '%Y-%m-%d %H:%M:%S')
```

## Optimization Opportunities Found

- Date parsing logic repeated (in selenium and sync_tickets_status) → could extract to utility
- Manual date component extraction fragile → consider dateutil.parser for robustness
- No index on `is_from_gestion_real` field → consider adding if querying frequently
