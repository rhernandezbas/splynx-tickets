# Database Query Optimizer Memory

## Database Schema

### Table: tickets_detection
Main table for ticket storage. Key columns:
- `Cliente`: Customer ID (string)
- `Cliente_Nombre`: Customer name
- `Asunto`: Ticket subject
- `Fecha_Creacion`: Creation date (unique, used to prevent duplicates)
- `Ticket_ID`: Splynx ticket ID (populated after creation)
- `Estado`: Ticket status
- `is_created_splynx`: Boolean flag - FALSE means pending creation in Splynx
- `assigned_to`: Operator person_id
- `is_closed`: Boolean for closed tickets
- `recreado`: Counter for ticket recreations
- `is_from_gestion_real`: Identifies tickets from Gestión Real vs Splynx

### Common Query Patterns

1. **Find pending tickets for Splynx creation**:
```sql
SELECT * FROM tickets_detection
WHERE is_created_splynx = 0
ORDER BY Fecha_Creacion DESC
```

2. **Avoid duplicate insertion by date**:
- `Fecha_Creacion` has UNIQUE constraint
- Duplicate key errors are logged as INFO (expected behavior)

## Known Issues

### Issue: Tickets stuck with is_created_splynx = False
**Status**: Investigating (2026-02-09)
**Findings**:
- Found 5 tickets with `is_created_splynx = False`
- All have Ticket_ID = 'N/A' (not created in Splynx)
- All are unassigned (assigned_to = NULL)
- All have Estado = 'PENDING'
- Date range: 2026-02-07 to 2026-02-09

**Next Steps**:
- Check ticket creation service logic
- Verify Splynx API connectivity
- Review logs for creation failures
