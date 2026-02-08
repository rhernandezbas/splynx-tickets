# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

App Splynx is an automated ticket management system that integrates with Splynx ISP management platform and Gestión Real ticketing system. The system automatically assigns tickets to operators using fair distribution algorithms, sends WhatsApp notifications, and tracks response times.

## Architecture

### Technology Stack
- **Backend**: Flask (Python 3.10+) with SQLAlchemy ORM
- **Database**: MySQL (remote, hosted at 190.7.234.37:3025)
- **Task Scheduling**: APScheduler for periodic jobs
- **Web Scraping**: Selenium with Chromium for Gestión Real integration
- **Notifications**: Evolution API for WhatsApp integration
- **Deployment**: Docker Compose with multi-stage builds

### Key Components

#### 1. Data Layer (`app/models/`)
- **models.py**: All database models including:
  - `IncidentsDetection`: Ticket storage with metrics and audit fields
  - `AssignmentTracker`: Fair distribution tracking per operator
  - `TicketResponseMetrics`: Response time tracking and alerts
  - `OperatorConfig`: Dynamic operator configuration (active status, WhatsApp numbers)
  - `OperatorSchedule`: Work, assignment, and alert schedules per operator
  - `SystemConfig`: Global configuration stored in database
  - `User`: Authentication with role-based access (admin/operator)
  - `DeviceAnalysis`: Network device analysis with AI feedback

#### 2. Interface Layer (`app/interface/`)
- **interfaces.py**: CRUD operations for all models with error handling
- **message_templates.py**: WhatsApp message template management
- **reassignment_history.py**: Ticket reassignment tracking
- **users.py**: User management operations
- Follows repository pattern with BaseInterface for common operations

#### 3. Services Layer (`app/services/`)
- **splynx_services.py**: API integration with Splynx (tickets, customers)
- **selenium_multi_departamentos.py**: Web scraping from Gestión Real using Selenium
- **ticket_manager.py**: Business logic for ticket assignment and management
- **evolution_api.py**: WhatsApp API integration
- **whatsapp_service.py**: WhatsApp message formatting and delivery

#### 4. Routes Layer (`app/routes/`)
- **views.py**: Main ticket endpoints (download, create, assign, close)
- **admin_routes.py**: Admin panel endpoints (operators, schedules, config)
- **auth_routes.py**: Authentication endpoints
- **messages_routes.py**: Message template management
- **device_analysis_routes.py**: Network device analysis proxy
- **logs_routes.py**: Audit log endpoints
- **whatsapp_routes.py**: WhatsApp messaging endpoints (REST API for WhatsApp service)
- **thread_functions.py**: Background thread implementations

#### 5. Utilities (`app/utils/`)
- **config.py**: Flask and database configuration
- **constants.py**: Centralized constants (credentials, URLs, IDs)
- **config_helper.py**: Database-driven configuration helper
- **schedule_helper.py**: Operator schedule validation
- **scheduler.py**: APScheduler setup with periodic jobs
- **system_control.py**: System pause/resume control
- **logger.py**: Centralized logging configuration

### Configuration Philosophy

**IMPORTANT**: Most configuration is now stored in the database, not in code:
- Operator info: `operator_config` table (names, WhatsApp numbers, pause status)
- Schedules: `operator_schedule` table (work hours, assignment times, alert times)
- System settings: `system_config` table (thresholds, intervals, toggles)

Use the admin panel or `ConfigHelper` methods to read/modify configuration.

**SECURITY - Environment Variables**: Sensitive credentials are stored in environment variables (`.env` file):
- Database credentials: `DB_HOST`, `DB_USER`, `DB_PASSWORD`
- Splynx API: `SPLYNX_USER`, `SPLYNX_PASSWORD`, `SPLYNX_SSL_VERIFY`
- Gestión Real: `GESTION_REAL_USERNAME`, `GESTION_REAL_PASSWORD`
- Evolution API: `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`
- Flask: `SECRET_KEY`, `SESSION_COOKIE_SECURE`

To configure, copy `.env.template` to `.env` and set appropriate values. The `.env` file is gitignored and should never be committed.

## Development Commands

### Local Development
```bash
# Install dependencies
poetry install

# Create .env file from template
cp .env.template .env
# Edit .env and set your credentials

# Validate environment variables
poetry run python validate_env.py

# Run migrations (first time or after model changes)
poetry run python -m flask db upgrade

# Run application locally
poetry run python -m flask run --host=0.0.0.0 --port=5605

# Access application
# Backend: http://localhost:5605
```

### Docker Commands
```bash
# Build and run with Docker Compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose up -d --build

# Stop containers
docker-compose down

# Access backend container
docker exec -it splynx-backend bash
```

### Database Operations
```bash
# Create new migration after model changes
poetry run python -m flask db migrate -m "Description of changes"

# Apply migrations
poetry run python -m flask db upgrade

# Rollback migration
poetry run python -m flask db downgrade
```

## Key Endpoints

### Ticket Operations
- `POST /api/tickets/download` - Download CSV from Gestión Real
- `POST /api/tickets/create` - Create tickets in Splynx
- `POST /api/tickets/close` - Mark closed tickets
- `POST /api/tickets/all_flow` - Full workflow (download → create → assign)
- `POST /api/tickets/assign_unassigned` - Assign unassigned tickets
- `POST /api/tickets/alert_overdue` - Alert operators about tickets > 45 min
- `POST /api/tickets/end_of_shift_notifications` - End-of-shift reminders
- `POST /api/tickets/auto_unassign_after_shift` - Unassign after shift ends
- `POST /api/tickets/sync_status` - Sync ticket status with Splynx
- `POST /api/tickets/import_existing` - Import existing tickets from Splynx

### Admin Operations
- `GET/POST /api/admin/operators` - Manage operators
- `GET/POST /api/admin/schedules` - Manage schedules
- `GET/POST /api/admin/config` - System configuration
- `POST /api/admin/operators/{id}/pause` - Pause operator
- `POST /api/admin/operators/{id}/resume` - Resume operator
- `POST /api/admin/system/pause` - Pause entire system
- `POST /api/admin/system/resume` - Resume system

### WhatsApp Operations
- `POST /api/whatsapp/send/text` - Send text message to a phone number (admin only)
- `POST /api/whatsapp/send/overdue-alert` - Send grouped overdue tickets alert to operator (admin only)
- `POST /api/whatsapp/send/shift-summary` - Send end-of-shift summary to operator (admin only)
- `POST /api/whatsapp/send/assignment` - Send ticket assignment notification to operator (admin only)
- `POST /api/whatsapp/send/custom` - Send custom message to operator (admin only)
- `POST /api/whatsapp/send/bulk` - Send same message to multiple operators, max 50 (admin only)
- `GET /api/whatsapp/operators/{person_id}/validate` - Validate operator WhatsApp configuration (authenticated)
- `GET /api/whatsapp/operators/config` - Get WhatsApp configuration for all operators (authenticated)
- `GET /api/whatsapp/health` - Health check for WhatsApp service (public)

**Authentication**: All send endpoints require admin role. Read endpoints require authentication. Use existing session-based auth.

**Usage Example**:
```python
# From services/routes
whatsapp_service = WhatsAppService()
result = whatsapp_service.send_custom_message(person_id=10, message="Hello")
```

## Scheduled Jobs

The scheduler (`app/utils/scheduler.py`) runs these jobs automatically:

- **Every 3 minutes**: Full ticket flow (download, create, assign)
- **Every 3 minutes**: Alert overdue tickets (>45 min)
- **Every hour**: End-of-shift notifications
- **Every 40 minutes**: Auto-unassign after shift
- **Every 5 minutes**: Sync ticket status with Splynx
- **Every 5 minutes**: Import existing tickets

Jobs only run during work hours:
- Weekdays: 8 AM - 11 PM (Argentina time)
- Weekends: 9 AM - 9 PM (configurable in DB)

## Ticket Assignment Logic

### Fair Distribution Algorithm
1. Check if weekend (assign to on-duty operator: ID 10 by default)
2. Check ticket note for shift tags:
   - `[TT]` = Turno Tarde (afternoon shift) → IDs 27, 38
   - `[TD]` = Turno Día (day shift) → IDs 10, 37
3. Query `operator_schedule` with `schedule_type='assignment'`
4. Filter operators available at current time
5. Exclude paused operators (`is_paused=True` or `assignment_paused=True`)
6. Assign to operator with least tickets (tracked in `assignment_tracker`)
7. Fallback to round-robin if no one is in assignment schedule

### Operator Pause States
- `is_paused`: Full pause (no assignments, no notifications)
- `assignment_paused`: No new assignments, but keeps current tickets
- `notifications_enabled`: Control WhatsApp notifications independently

## WhatsApp Notifications

Uses Evolution API with three schedule types in `operator_schedule`:

1. **Work Schedule** (`schedule_type='work'`): General work hours
2. **Assignment Schedule** (`schedule_type='assignment'`): When to assign new tickets
3. **Alert Schedule** (`schedule_type='alert'`): When to send WhatsApp notifications

### Alert Types
- **Overdue alerts**: Tickets >45 min without update (threshold in DB)
- **End-of-shift**: 1 hour before shift ends (time in DB)
- **Grouped messages**: One message per operator with all overdue tickets

## Important Patterns

### Database-First Configuration
Always check if a value is in the database before hardcoding:
```python
# ❌ DON'T
THRESHOLD = 45

# ✅ DO
threshold = ConfigHelper.get_int('TICKET_ALERT_THRESHOLD_MINUTES', 45)
```

### Schedule Validation
Use `ScheduleHelper` to check operator availability:
```python
from app.utils.schedule_helper import ScheduleHelper

available = ScheduleHelper.get_available_operators(
    person_ids=[10, 27, 37, 38],
    schedule_type='assignment',
    current_time=datetime.now()
)
```

### Error Handling
Interface layer handles database errors gracefully:
- Duplicate key errors are logged as info (expected behavior)
- SQLAlchemy errors rollback and log as errors
- Return `None` or `False` on error, never raise

### Logging
Use the centralized logger:
```python
from app.utils.logger import get_logger
logger = get_logger(__name__)

logger.info("✅ Success message")
logger.warning("⚠️  Warning message")
logger.error("❌ Error message")
```

### Thread Safety
Long-running operations use background threads:
- All ticket operations spawn threads to avoid blocking
- Pass `current_app._get_current_object()` to threads needing app context
- Use `threading.Thread(target=func, args=(app,)).start()`

## Security Notes

### Credentials Management
**ALL credentials are now stored in environment variables (`.env` file)**:
- **Splynx API**: `SPLYNX_USER`, `SPLYNX_PASSWORD`, `SPLYNX_BASE_URL`, `SPLYNX_SSL_VERIFY`
- **Gestión Real**: `GESTION_REAL_USERNAME`, `GESTION_REAL_PASSWORD`
- **Evolution API**: `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`, `EVOLUTION_API_BASE_URL`
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Flask**: `SECRET_KEY`, `SESSION_COOKIE_SECURE`

**IMPORTANT**:
- Never commit the `.env` file (already in `.gitignore`)
- Use `.env.template` as documentation for required variables
- Run `poetry run python validate_env.py` to verify configuration
- Set proper file permissions: `chmod 600 .env`

### Authentication
- Session-based authentication with role-based access control (RBAC)
- Roles: `admin` (full access) and `operator` (limited access)
- Operators linked to `person_id` for ticket assignment
- Page-level permissions stored in `users` table:
  - `can_access_operator_view` (default: true) - Vista de operador
  - `can_access_device_analysis` (default: true) - Análisis de dispositivos
  - `can_access_noc_dashboard` (default: false) - Ver NOC Dashboard (sites, eventos, métricas)
  - `can_access_noc_control` (default: false) - Control del NOC (polling, WhatsApp, post-mortems)
- If `role === 'admin'`: Frontend ignores individual permissions and grants full access
- Session security configured via `SESSION_COOKIE_SECURE` (enable in production with HTTPS)

## Selenium Configuration

Runs in Docker with Chromium in headless mode:
- Chrome binary: `/usr/bin/chromium`
- ChromeDriver: `/usr/bin/chromedriver`
- Headless mode enabled for Docker compatibility
- No sandbox mode (`--no-sandbox`, `--disable-dev-shm-usage`)

## Frontend (Removed)

**Note**: The frontend directory has been deleted from the repository. The system currently only exposes REST API endpoints. If frontend files are needed, restore from git history before the deletion commit.

## Deployment

### Automatic GitHub Actions
Configured in `.github/workflows/deploy.yml`:
1. Push to `main` branch triggers deployment
2. SSH to VPS at 190.7.234.37
3. Pull latest code to `/opt/splynx-tickets`
4. Build Docker images
5. Restart containers with `docker-compose up -d`

### Manual Deployment to VPS
```bash
# SSH to VPS
ssh root@190.7.234.37

# Navigate to app directory
cd /opt/splynx-tickets

# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

Application runs on **port 7842** (both locally and in production).

## Troubleshooting

### Database Connection Issues
- Verify VPS can reach 190.7.234.37:3025
- Check credentials in `app/utils/constants.py`
- Test connection: `poetry run python -c "from app.utils.config import db; print('OK')"`

### Scheduler Not Running
- Check if lock file exists: `/tmp/splynx_scheduler.lock`
- Verify APScheduler initialized in `app/__init__.py:init_scheduler()`
- Check logs for "⏰ SCHEDULER INICIADO" message

### WhatsApp Notifications Failing
- Verify Evolution API URL is accessible from server
- Check `EVOLUTION_API_KEY` and `EVOLUTION_INSTANCE_NAME` in constants
- Verify operator has WhatsApp number in `operator_config` table
- Check if notifications enabled: `notifications_enabled=True`

### Tickets Not Assigning
- Check if system is paused: `SystemControl.is_paused()`
- Verify operators have `schedule_type='assignment'` in schedules
- Check operator pause states in `operator_config`
- Review assignment tracker counts in `assignment_tracker` table

### Selenium Failures
- Verify Chromium and ChromeDriver are installed in container
- Check Gestión Real credentials in `constants.py`
- Ensure headless mode is enabled for Docker
- Review Selenium logs in backend container logs
