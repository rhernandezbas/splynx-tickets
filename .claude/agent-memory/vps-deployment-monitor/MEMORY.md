# VPS Deployment Monitor - Memory

## VPS Connection Details
- **Host**: 190.7.234.37
- **User**: root
- **Application Path**: /opt/splynx-tickets
- **Container Name**: splynx-backend
- **Application Port**: 5605 (mapped from internal 7842)

## Database Configuration
- **Host**: 190.7.234.37
- **Port**: 3025
- **Database**: ipnext
- **User**: mysql
- **Connection**: Remote MySQL, accessible from container

## Docker Commands
- **Build and Start**: `docker compose up -d --build`
- **View Logs**: `docker logs splynx-backend --tail=50`
- **Check Status**: `docker compose ps`
- **Execute Commands**: `docker exec splynx-backend <command>`

## Migration Process
1. SSH to VPS: `ssh root@190.7.234.37`
2. Navigate to app: `cd /opt/splynx-tickets`
3. Pull changes: `git pull`
4. Rebuild containers: `docker compose up -d --build`
5. **Wait 10 seconds** before running migrations (important for DB connection stability)
6. Run migration: `docker exec splynx-backend flask db upgrade`

## Common Issues

### Database Connection Timeout on Migration
- **Symptom**: `(2013, 'Lost connection to MySQL server during query')`
- **Cause**: Flask app initializing while migration tries to connect
- **Solution**: Wait 10 seconds after container start before running migration
- **Verification**: Test connection with `docker exec splynx-backend python -c 'import pymysql; ...'`

### Container Not Running
- **Check**: `docker compose ps` shows nothing
- **Solution**: Start with `docker compose up -d --build`
- **Verify**: Container should show "Up X seconds (health: starting)"

### Application Health Check
- **Test**: `curl http://localhost:5605/`
- **Expected**: `{"message":"Application is running","service":"splynx-tickets","status":"healthy"}`

## Recent Deployments

### 2026-02-08: NOC Permissions Migration
- **Migration**: `a8c2d4e6f0b1_add_noc_permissions_to_users.py`
- **Changes**: Added `can_access_noc_dashboard` and `can_access_noc_control` columns to `users` table
- **Status**: Successful
- **Verification**: All 5 users have new columns with default value 0 (False)
- **Note**: Initial connection timeout resolved by waiting 10 seconds

## Verification Queries

### Check Migration Status
```bash
docker exec splynx-backend flask db current
```

### Verify Users Table Structure
```bash
docker exec splynx-backend python -c 'import pymysql; conn = pymysql.connect(host="190.7.234.37", port=3025, user="mysql", password="1234", database="ipnext"); cursor = conn.cursor(); cursor.execute("DESCRIBE users"); print(cursor.fetchall()); conn.close()'
```

### Check NOC Permissions
```bash
docker exec splynx-backend python -c 'import pymysql; conn = pymysql.connect(host="190.7.234.37", port=3025, user="mysql", password="1234", database="ipnext"); cursor = conn.cursor(); cursor.execute("SELECT username, can_access_noc_dashboard, can_access_noc_control FROM users"); print(cursor.fetchall()); conn.close()'
```
