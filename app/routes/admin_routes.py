"""
Admin API Routes - Panel de administración para gestión de operadores, horarios y configuraciones
"""

from flask import Blueprint, jsonify, request, current_app
from app.interface.interfaces import (
    OperatorConfigInterface, 
    OperatorScheduleInterface, 
    SystemConfigInterface,
    AuditLogInterface,
    AssignmentTrackerInterface,
    TicketResponseMetricsInterface
)
from app.interface.message_templates import MessageTemplateInterface
from app.utils.logger import get_logger
from datetime import datetime, timedelta
import pytz
from sqlalchemy import func
from app.utils.config import db
from app.models.models import TicketResponseMetrics, IncidentsDetection

logger = get_logger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def get_client_ip():
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


def log_audit(action: str, entity_type: str, entity_id: str = None, 
              old_value: dict = None, new_value: dict = None, notes: str = None):
    """Helper to log audit actions."""
    try:
        AuditLogInterface.log_action(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            performed_by=request.json.get('performed_by', 'admin') if request.json else 'admin',
            ip_address=get_client_ip(),
            notes=notes
        )
    except Exception as e:
        logger.error(f"Error logging audit: {e}")


@admin_bp.route('/operators', methods=['GET'])
def get_operators():
    """Get all operators with their configurations."""
    try:
        operators = OperatorConfigInterface.get_all()
        
        result = []
        for op in operators:
            tracker = AssignmentTrackerInterface.get_by_person_id(op.person_id)
            schedules = OperatorScheduleInterface.get_by_person_id(op.person_id)
            
            result.append({
                'person_id': op.person_id,
                'name': op.name,
                'whatsapp_number': op.whatsapp_number,
                'is_active': op.is_active,
                'is_paused': op.is_paused,
                'assignment_paused': op.assignment_paused,
                'paused_reason': op.paused_reason,
                'paused_at': op.paused_at.isoformat() if op.paused_at else None,
                'paused_by': op.paused_by,
                'notifications_enabled': op.notifications_enabled,
                'ticket_count': tracker.ticket_count if tracker else 0,
                'last_assigned': tracker.last_assigned.isoformat() if tracker and tracker.last_assigned else None,
                'schedules': [{
                    'id': s.id,
                    'day_of_week': s.day_of_week,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'schedule_type': s.schedule_type,
                    'is_active': s.is_active
                } for s in schedules]
            })
        
        return jsonify({
            'success': True,
            'operators': result
        }), 200
    except Exception as e:
        logger.error(f"Error getting operators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/<int:person_id>', methods=['GET'])
def get_operator(person_id):
    """Get specific operator details."""
    try:
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        tracker = AssignmentTrackerInterface.get_by_person_id(person_id)
        schedules = OperatorScheduleInterface.get_by_person_id(person_id)
        metrics = TicketResponseMetricsInterface.get_metrics_by_person(person_id)
        
        return jsonify({
            'success': True,
            'operator': {
                'person_id': operator.person_id,
                'name': operator.name,
                'whatsapp_number': operator.whatsapp_number,
                'is_active': operator.is_active,
                'is_paused': operator.is_paused,
                'paused_reason': operator.paused_reason,
                'paused_at': operator.paused_at.isoformat() if operator.paused_at else None,
                'paused_by': operator.paused_by,
                'notifications_enabled': operator.notifications_enabled,
                'ticket_count': tracker.ticket_count if tracker else 0,
                'last_assigned': tracker.last_assigned.isoformat() if tracker and tracker.last_assigned else None,
                'total_tickets_handled': len(metrics),
                'schedules': [{
                    'id': s.id,
                    'day_of_week': s.day_of_week,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'is_active': s.is_active
                } for s in schedules]
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting operator: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/<int:person_id>', methods=['PUT'])
def update_operator(person_id):
    """Update operator configuration."""
    try:
        data = request.get_json()
        
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        old_value = {
            'name': operator.name,
            'whatsapp_number': operator.whatsapp_number,
            'is_active': operator.is_active,
            'notifications_enabled': operator.notifications_enabled
        }
        
        updated = OperatorConfigInterface.update(person_id, data)
        if updated:
            log_audit(
                action='update_operator',
                entity_type='operator',
                entity_id=str(person_id),
                old_value=old_value,
                new_value=data,
                notes=f"Updated operator {operator.name}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Operator updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update operator'
            }), 500
    except Exception as e:
        logger.error(f"Error updating operator: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/<int:person_id>/pause', methods=['POST'])
def pause_operator(person_id):
    """Pause an operator."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Pausa manual')
        paused_by = data.get('paused_by', 'admin')
        
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        success = OperatorConfigInterface.pause_operator(person_id, reason, paused_by)
        if success:
            log_audit(
                action='pause_operator',
                entity_type='operator',
                entity_id=str(person_id),
                new_value={'paused': True, 'reason': reason},
                notes=f"Paused operator {operator.name}"
            )
            
            return jsonify({
                'success': True,
                'message': f'Operator {operator.name} paused successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to pause operator'
            }), 500
    except Exception as e:
        logger.error(f"Error pausing operator: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/<int:person_id>/resume', methods=['POST'])
def resume_operator(person_id):
    """Resume a paused operator."""
    try:
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        success = OperatorConfigInterface.resume_operator(person_id)
        if success:
            log_audit(
                action='resume_operator',
                entity_type='operator',
                entity_id=str(person_id),
                new_value={'paused': False},
                notes=f"Resumed operator {operator.name}"
            )
            
            return jsonify({
                'success': True,
                'message': f'Operator {operator.name} resumed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to resume operator'
            }), 500
    except Exception as e:
        logger.error(f"Error resuming operator: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/<int:person_id>/config', methods=['PATCH'])
def update_operator_config(person_id):
    """Update operator configuration (pausas granulares, número de WhatsApp, etc)."""
    try:
        data = request.get_json()
        
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        old_values = {
            'is_paused': operator.is_paused,
            'assignment_paused': operator.assignment_paused,
            'notifications_enabled': operator.notifications_enabled,
            'whatsapp_number': operator.whatsapp_number
        }
        
        # Actualizar campos según lo enviado
        if 'is_paused' in data:
            operator.is_paused = data['is_paused']
            if data['is_paused']:
                operator.paused_at = datetime.now()
                operator.paused_reason = data.get('paused_reason', 'Pausa manual')
                operator.paused_by = data.get('paused_by', 'admin')
        
        if 'assignment_paused' in data:
            operator.assignment_paused = data['assignment_paused']
        
        if 'notifications_enabled' in data:
            operator.notifications_enabled = data['notifications_enabled']
        
        if 'whatsapp_number' in data:
            operator.whatsapp_number = data['whatsapp_number']
        
        db.session.commit()
        
        new_values = {
            'is_paused': operator.is_paused,
            'assignment_paused': operator.assignment_paused,
            'notifications_enabled': operator.notifications_enabled,
            'whatsapp_number': operator.whatsapp_number
        }
        
        log_audit(
            action='update_operator_config',
            entity_type='operator',
            entity_id=str(person_id),
            old_value=old_values,
            new_value=new_values,
            notes=f"Updated config for operator {operator.name}"
        )
        
        return jsonify({
            'success': True,
            'message': f'Operator {operator.name} config updated successfully',
            'operator': {
                'person_id': operator.person_id,
                'name': operator.name,
                'is_paused': operator.is_paused,
                'assignment_paused': operator.assignment_paused,
                'notifications_enabled': operator.notifications_enabled,
                'whatsapp_number': operator.whatsapp_number
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating operator config: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/operators/create', methods=['POST'])
def create_operator():
    """Create a new operator."""
    try:
        data = request.get_json()
        
        existing = OperatorConfigInterface.get_by_person_id(data.get('person_id'))
        if existing:
            return jsonify({
                'success': False,
                'error': 'Operator with this person_id already exists'
            }), 400
        
        operator = OperatorConfigInterface.create(data)
        if operator:
            log_audit(
                action='create_operator',
                entity_type='operator',
                entity_id=str(operator.person_id),
                new_value=data,
                notes=f"Created operator {operator.name}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Operator created successfully',
                'operator_id': operator.person_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create operator'
            }), 500
    except Exception as e:
        logger.error(f"Error creating operator: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/schedules', methods=['POST'])
def create_schedule():
    """Create a new operator schedule."""
    try:
        data = request.get_json()
        
        schedule = OperatorScheduleInterface.create(data)
        if schedule:
            log_audit(
                action='create_schedule',
                entity_type='schedule',
                entity_id=str(schedule.id),
                new_value=data,
                notes=f"Created schedule for operator {data.get('person_id')}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Schedule created successfully',
                'schedule_id': schedule.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create schedule'
            }), 500
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an operator schedule."""
    try:
        data = request.get_json()
        
        schedule = OperatorScheduleInterface.get_by_id(schedule_id)
        if not schedule:
            return jsonify({
                'success': False,
                'error': 'Schedule not found'
            }), 404
        
        old_value = {
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'is_active': schedule.is_active
        }
        
        updated = OperatorScheduleInterface.update(schedule_id, data)
        if updated:
            log_audit(
                action='update_schedule',
                entity_type='schedule',
                entity_id=str(schedule_id),
                old_value=old_value,
                new_value=data,
                notes=f"Updated schedule {schedule_id}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Schedule updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update schedule'
            }), 500
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete an operator schedule."""
    try:
        schedule = OperatorScheduleInterface.get_by_id(schedule_id)
        if not schedule:
            return jsonify({
                'success': False,
                'error': 'Schedule not found'
            }), 404
        
        old_value = {
            'person_id': schedule.person_id,
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time
        }
        
        success = OperatorScheduleInterface.delete(schedule_id)
        if success:
            log_audit(
                action='delete_schedule',
                entity_type='schedule',
                entity_id=str(schedule_id),
                old_value=old_value,
                notes=f"Deleted schedule {schedule_id}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Schedule deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete schedule'
            }), 500
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/assignment/reset', methods=['POST'])
def reset_assignment_counters():
    """Reset all assignment counters (round-robin)."""
    try:
        data = request.get_json() or {}
        
        trackers = AssignmentTrackerInterface.get_all()
        old_values = {str(t.person_id): t.ticket_count for t in trackers}
        
        success = AssignmentTrackerInterface.reset_all_counts()
        if success:
            log_audit(
                action='reset_counters',
                entity_type='assignment',
                old_value=old_values,
                new_value={'all_counters': 0},
                notes='Reset all assignment counters'
            )
            
            return jsonify({
                'success': True,
                'message': 'Assignment counters reset successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset counters'
            }), 500
    except Exception as e:
        logger.error(f"Error resetting counters: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/assignment/stats', methods=['GET'])
def get_assignment_stats():
    """Get assignment statistics."""
    try:
        trackers = AssignmentTrackerInterface.get_all()
        
        stats = []
        for tracker in trackers:
            operator = OperatorConfigInterface.get_by_person_id(tracker.person_id)
            stats.append({
                'person_id': tracker.person_id,
                'name': operator.name if operator else f'Operator {tracker.person_id}',
                'ticket_count': tracker.ticket_count,
                'last_assigned': tracker.last_assigned.isoformat() if tracker.last_assigned else None
            })
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting assignment stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/config', methods=['GET'])
def get_system_config():
    """Get all system configurations."""
    try:
        category = request.args.get('category')
        
        if category:
            configs = SystemConfigInterface.get_by_category(category)
        else:
            configs = SystemConfigInterface.get_all()
        
        result = [{
            'key': c.key,
            'value': c.value,
            'value_type': c.value_type,
            'description': c.description,
            'category': c.category,
            'updated_at': c.updated_at.isoformat() if c.updated_at else None,
            'updated_by': c.updated_by
        } for c in configs]
        
        return jsonify({
            'success': True,
            'configs': result
        }), 200
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/config/<key>', methods=['GET'])
def get_config_value(key):
    """Get specific configuration value."""
    try:
        config = SystemConfigInterface.get_by_key(key)
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        return jsonify({
            'success': True,
            'config': {
                'key': config.key,
                'value': config.value,
                'value_type': config.value_type,
                'description': config.description,
                'category': config.category
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting config value: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/config/<key>', methods=['PUT'])
def update_config(key):
    """Update or create system configuration."""
    try:
        from app.utils.config_helper import ConfigHelper
        
        data = request.get_json()
        value = data.get('value')
        updated_by = data.get('updated_by', 'admin')
        
        old_config = SystemConfigInterface.get_by_key(key)
        old_value = old_config.value if old_config else None
        
        config = SystemConfigInterface.update_or_create(
            key=key,
            value=value,
            updated_by=updated_by,
            value_type=data.get('value_type', 'string'),
            description=data.get('description'),
            category=data.get('category')
        )
        
        if config:
            # Limpiar caché de configuración para que se lea el nuevo valor
            ConfigHelper.clear_cache()
            logger.info(f"✅ Configuración '{key}' actualizada y caché limpiado")
            
            log_audit(
                action='update_config',
                entity_type='config',
                entity_id=key,
                old_value={'value': old_value},
                new_value={'value': value},
                notes=f"Updated config {key}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update configuration'
            }), 500
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/audit', methods=['GET'])
def get_audit_logs():
    """Get audit logs."""
    try:
        limit = int(request.args.get('limit', 100))
        action = request.args.get('action')
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        
        if action:
            logs = AuditLogInterface.get_by_action(action, limit)
        elif entity_type and entity_id:
            logs = AuditLogInterface.get_by_entity(entity_type, entity_id)
        else:
            logs = AuditLogInterface.get_recent(limit)
        
        result = [{
            'id': log.id,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'performed_by': log.performed_by,
            'performed_at': log.performed_at.isoformat() if log.performed_at else None,
            'ip_address': log.ip_address,
            'notes': log.notes
        } for log in logs]
        
        return jsonify({
            'success': True,
            'logs': result
        }), 200
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz_argentina)
        
        operators = OperatorConfigInterface.get_all()
        active_operators = len([o for o in operators if o.is_active and not o.is_paused])
        paused_operators = len([o for o in operators if o.is_paused])
        
        trackers = AssignmentTrackerInterface.get_all()
        total_assignments = sum(t.ticket_count for t in trackers)
        
        # Usar IncidentsDetection en lugar de TicketResponseMetrics
        unresolved_tickets = IncidentsDetection.query.filter_by(is_closed=False).all()
        overdue_tickets = len([t for t in unresolved_tickets if t.exceeded_threshold])
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.Fecha_Creacion >= today_start
        ).all()
        
        avg_response_time = 0
        if today_tickets:
            response_times = [t.response_time_minutes for t in today_tickets if t.response_time_minutes]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        operator_stats = []
        for tracker in trackers:
            operator = OperatorConfigInterface.get_by_person_id(tracker.person_id)
            if operator:
                # Obtener tickets del operador desde IncidentsDetection
                operator_tickets = IncidentsDetection.query.filter_by(assigned_to=tracker.person_id).all()
                unresolved = [t for t in operator_tickets if not t.is_closed]
                
                operator_stats.append({
                    'person_id': tracker.person_id,
                    'name': operator.name,
                    'is_active': operator.is_active,
                    'is_paused': operator.is_paused,
                    'current_assignments': tracker.ticket_count,
                    'total_handled': len(operator_tickets),
                    'unresolved': len(unresolved),
                    'avg_response_time': sum(t.response_time_minutes for t in operator_tickets if t.response_time_minutes) / len(operator_tickets) if operator_tickets else 0
                })
        
        from app.utils.system_control import SystemControl
        system_status = SystemControl.get_status()
        
        return jsonify({
            'success': True,
            'stats': {
                'system': {
                    'status': system_status.get('status'),
                    'paused': system_status.get('paused'),
                    'paused_reason': system_status.get('reason')
                },
                'operators': {
                    'total': len(operators),
                    'active': active_operators,
                    'paused': paused_operators
                },
                'assignments': {
                    'total': total_assignments,
                    'today': len(today_tickets)
                },
                'tickets': {
                    'unresolved': len(unresolved_tickets),
                    'overdue': overdue_tickets,
                    'avg_response_time_minutes': round(avg_response_time, 2)
                },
                'operator_stats': operator_stats
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/metrics/operator/<int:person_id>', methods=['GET'])
def get_operator_metrics(person_id):
    """Get detailed metrics for an operator."""
    try:
        days = int(request.args.get('days', 7))
        
        operator = OperatorConfigInterface.get_by_person_id(person_id)
        if not operator:
            return jsonify({
                'success': False,
                'error': 'Operator not found'
            }), 404
        
        tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz_argentina)
        start_date = now - timedelta(days=days)
        
        metrics = db.session.query(TicketResponseMetrics).filter(
            TicketResponseMetrics.assigned_to == person_id,
            TicketResponseMetrics.created_at >= start_date
        ).all()
        
        total_tickets = len(metrics)
        resolved_tickets = len([m for m in metrics if m.is_closed])
        unresolved_tickets = total_tickets - resolved_tickets
        exceeded_threshold = len([m for m in metrics if m.exceeded_threshold])
        
        response_times = [m.response_time_minutes for m in metrics if m.response_time_minutes]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        daily_stats = {}
        for metric in metrics:
            date_key = metric.created_at.strftime('%Y-%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {'total': 0, 'resolved': 0, 'exceeded': 0}
            daily_stats[date_key]['total'] += 1
            if metric.is_closed:
                daily_stats[date_key]['resolved'] += 1
            if metric.exceeded_threshold:
                daily_stats[date_key]['exceeded'] += 1
        
        return jsonify({
            'success': True,
            'metrics': {
                'operator': {
                    'person_id': person_id,
                    'name': operator.name
                },
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': now.isoformat()
                },
                'summary': {
                    'total_tickets': total_tickets,
                    'resolved': resolved_tickets,
                    'unresolved': unresolved_tickets,
                    'exceeded_threshold': exceeded_threshold,
                    'avg_response_time_minutes': round(avg_response_time, 2)
                },
                'daily_stats': daily_stats
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting operator metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get general system metrics."""
    try:
        from app.models.models import IncidentsDetection
        
        # Obtener estadísticas generales de tickets_detection
        total_tickets = IncidentsDetection.query.count()
        
        # Usar is_closed como fuente única de verdad
        open_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.is_closed == False
        ).count()
        
        closed_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.is_closed == True
        ).count()
        
        # Calcular tiempo promedio de respuesta desde incidents_detection
        avg_response = db.session.query(func.avg(IncidentsDetection.response_time_minutes)).filter(
            IncidentsDetection.response_time_minutes.isnot(None)
        ).scalar()
        
        # Tickets vencidos (exceeded_threshold=True Y is_closed=False)
        overdue_tickets = IncidentsDetection.query.filter(
            IncidentsDetection.exceeded_threshold == True,
            IncidentsDetection.is_closed == False
        ).count()
        
        # Distribución por operador - obtener nombres de operadores
        from app.interface.interfaces import OperatorConfigInterface
        operators = OperatorConfigInterface.get_all()
        operator_map = {op.person_id: op.name for op in operators}
        
        # Distribución por operador con SLA
        operator_stats = db.session.query(
            IncidentsDetection.assigned_to,
            func.count(IncidentsDetection.id).label('assigned')
        ).filter(
            IncidentsDetection.assigned_to.isnot(None)
        ).group_by(
            IncidentsDetection.assigned_to
        ).all()
        
        operator_distribution = []
        for stat in operator_stats:
            # Contar tickets completados (cerrados)
            completed = IncidentsDetection.query.filter(
                IncidentsDetection.assigned_to == stat.assigned_to,
                IncidentsDetection.is_closed == True
            ).count()
            
            # Calcular SLA: tickets que excedieron el umbral
            total_operator_tickets = stat.assigned
            exceeded = IncidentsDetection.query.filter(
                IncidentsDetection.assigned_to == stat.assigned_to,
                IncidentsDetection.exceeded_threshold == True
            ).count()
            
            # SLA = (total - excedidos) / total * 100
            sla_percentage = ((total_operator_tickets - exceeded) / total_operator_tickets * 100) if total_operator_tickets > 0 else 100
            
            operator_distribution.append({
                'person_id': stat.assigned_to,
                'name': operator_map.get(stat.assigned_to, f'Operador {stat.assigned_to}'),
                'assigned': stat.assigned,
                'completed': completed,
                'exceeded_threshold': exceeded,
                'sla_percentage': round(sla_percentage, 2)
            })
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'closed_tickets': closed_tickets,
                'overdue_tickets': overdue_tickets,
                'average_response_time': round(avg_response, 2) if avg_response else 0,
                'operator_distribution': operator_distribution
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/incidents', methods=['GET'])
def get_incidents():
    """Get all incidents/tickets with optional filters."""
    try:
        from app.models.models import IncidentsDetection
        
        # Obtener parámetros de filtro
        start_date_str = request.args.get('start_date')  # Formato: YYYY-MM-DD
        end_date_str = request.args.get('end_date')      # Formato: YYYY-MM-DD
        status = request.args.get('status')
        assigned_to = request.args.get('assigned_to')
        ticket_status = request.args.get('ticket_status')  # 'open', 'closed', o 'all'
        
        # Construir query base
        query = IncidentsDetection.query
        
        # Obtener nombres de operadores
        from app.interface.interfaces import OperatorConfigInterface
        operators = OperatorConfigInterface.get_all()
        operator_map = {op.person_id: op.name for op in operators}
        
        # Aplicar filtros de fecha (convertir formato YYYY-MM-DD a DD-MM-YYYY)
        if start_date_str:
            try:
                # Convertir "2026-01-12" a "12-01-2026 00:00:00"
                start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d')
                start_date_formatted = start_date_obj.strftime('%d-%m-%Y')
                # Filtrar tickets >= fecha inicio
                query = query.filter(IncidentsDetection.Fecha_Creacion >= start_date_formatted)
            except ValueError:
                logger.warning(f"Formato de start_date inválido: {start_date_str}")
        
        if end_date_str:
            try:
                # Convertir "2026-01-15" a "15-01-2026 23:59:59"
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date_formatted = end_date_obj.strftime('%d-%m-%Y 23:59:59')
                # Filtrar tickets <= fecha fin
                query = query.filter(IncidentsDetection.Fecha_Creacion <= end_date_formatted)
            except ValueError:
                logger.warning(f"Formato de end_date inválido: {end_date_str}")
        
        if status:
            query = query.filter(IncidentsDetection.Estado == status)
        if assigned_to:
            query = query.filter(IncidentsDetection.assigned_to == int(assigned_to))
        
        # Filtro de estado abierto/cerrado usando is_closed (fuente de verdad)
        if ticket_status == 'open':
            query = query.filter(IncidentsDetection.is_closed == False)
        elif ticket_status == 'closed':
            query = query.filter(IncidentsDetection.is_closed == True)
        
        # Ordenar por ID descendente (más recientes primero)
        incidents = query.order_by(IncidentsDetection.id.desc()).all()
        
        # Transformar a diccionarios
        incidents_data = []
        for incident in incidents:
            incident_dict = {
                'id': incident.id,
                'ticket_id': incident.Ticket_ID,
                'customer_name': incident.Cliente_Nombre or incident.Cliente,
                'subject': incident.Asunto,
                'status_name': incident.Estado,
                'priority_name': incident.Prioridad,
                'assigned_to': incident.assigned_to,
                'operator_name': operator_map.get(incident.assigned_to, 'Sin asignar') if incident.assigned_to else 'Sin asignar',
                'created_at': incident.Fecha_Creacion,
                'closed_at': incident.closed_at.isoformat() if incident.closed_at else None,
                'is_closed': incident.is_closed,
                'last_update': (
                    incident.last_update.isoformat()
                    if incident.last_update and isinstance(incident.last_update, datetime)
                    else None
                ),
                'response_time_minutes': incident.response_time_minutes,
                'exceeded_threshold': incident.exceeded_threshold or False,
                'audit_requested': incident.audit_requested or False,
                'audit_status': incident.audit_status,
                'audit_notified': incident.audit_notified or False,
                'audit_requested_at': incident.audit_requested_at.isoformat() if incident.audit_requested_at else None,
                'audit_requested_by': incident.audit_requested_by,
                'recreado': incident.recreado or 0,
                'is_from_gestion_real': bool(incident.is_from_gestion_real),
                'ultimo_contacto_gr': (
                    incident.ultimo_contacto_gr.isoformat()
                    if incident.ultimo_contacto_gr and isinstance(incident.ultimo_contacto_gr, datetime)
                    else None
                )
            }
            
            incidents_data.append(incident_dict)
        
        return jsonify({
            'success': True,
            'incidents': incidents_data,
            'total': len(incidents_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting incidents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/threshold', methods=['PUT'])
def update_ticket_threshold(ticket_id):
    """Update exceeded_threshold status for a ticket in incidents_detection."""
    try:
        data = request.get_json()
        exceeded_threshold = data.get('exceeded_threshold', False)
        
        # Buscar el ticket en incidents_detection
        incident = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not incident:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # Actualizar exceeded_threshold
        incident.exceeded_threshold = exceeded_threshold
        
        db.session.commit()
        
        log_audit(
            action='update_threshold',
            entity_type='ticket',
            entity_id=ticket_id,
            old_value={'exceeded_threshold': not exceeded_threshold},
            new_value={'exceeded_threshold': exceeded_threshold},
            notes=f"Threshold actualizado para ticket {ticket_id}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Estado de vencimiento actualizado',
            'ticket_id': ticket_id,
            'exceeded_threshold': exceeded_threshold
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating ticket threshold: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket from incidents_detection."""
    try:
        from app.models.models import IncidentsDetection
        
        # Buscar el ticket
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # Eliminar el ticket
        db.session.delete(ticket)
        db.session.commit()
        
        log_audit(
            action='delete',
            entity_type='ticket',
            entity_id=ticket_id,
            notes=f"Ticket {ticket_id} eliminado"
        )
        
        return jsonify({
            'success': True,
            'message': 'Ticket eliminado correctamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting ticket: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/reassignment-history', methods=['GET'])
def get_reassignment_history():
    """Get ticket reassignment history with optional filters."""
    try:
        from app.interface.reassignment_history import ReassignmentHistoryInterface
        
        # Obtener parámetros de filtro
        ticket_id = request.args.get('ticket_id')
        operator_id = request.args.get('operator_id')
        limit = int(request.args.get('limit', 100))
        
        # Obtener historial según filtros
        if ticket_id:
            history = ReassignmentHistoryInterface.get_by_ticket(ticket_id)
        elif operator_id:
            history = ReassignmentHistoryInterface.get_by_operator(int(operator_id), limit)
        else:
            history = ReassignmentHistoryInterface.get_recent(limit)
        
        # Convertir a diccionarios
        history_data = [ReassignmentHistoryInterface.to_dict(h) for h in history]
        
        return jsonify({
            'success': True,
            'history': history_data,
            'total': len(history_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting reassignment history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/request-audit', methods=['POST'])
def request_ticket_audit(ticket_id):
    """Mark a ticket for audit by operator."""
    try:
        from datetime import datetime
        
        data = request.get_json()
        person_id = data.get('person_id')
        
        # Buscar el ticket
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # Marcar como solicitado para auditoría
        ticket.audit_requested = True
        ticket.audit_requested_at = datetime.now()
        ticket.audit_requested_by = person_id
        ticket.audit_status = 'pending'  # Establecer estado como pendiente
        ticket.audit_notified = False  # Resetear notificación
        
        db.session.commit()
        
        log_audit(
            action='request_audit',
            entity_type='ticket',
            entity_id=ticket_id,
            notes=f"Operador {person_id} solicitó auditoría para ticket {ticket_id}"
        )
        
        logger.info(f"✅ Ticket {ticket_id} marcado para auditoría por operador {person_id}")
        
        return jsonify({
            'success': True,
            'message': 'Ticket marcado para auditoría'
        }), 200
        
    except Exception as e:
        logger.error(f"Error requesting audit for ticket {ticket_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/audit-tickets', methods=['GET'])
def get_audit_tickets():
    """Get tickets marked for audit."""
    try:
        # Obtener tickets marcados para auditoría
        audit_tickets = IncidentsDetection.query.filter_by(
            audit_requested=True
        ).order_by(IncidentsDetection.audit_requested_at.desc()).all()
        
        tickets_data = []
        for ticket in audit_tickets:
            tickets_data.append({
                'id': ticket.id,
                'ticket_id': ticket.Ticket_ID,
                'customer_id': ticket.Cliente,
                'customer_name': ticket.Cliente_Nombre,
                'subject': ticket.Asunto,
                'created_at': ticket.Fecha_Creacion,
                'priority': ticket.Prioridad,
                'status': ticket.Estado,
                'assigned_to': ticket.assigned_to,
                'is_closed': ticket.is_closed,
                'exceeded_threshold': ticket.exceeded_threshold,
                'response_time_minutes': ticket.response_time_minutes,
                'audit_requested_at': ticket.audit_requested_at.isoformat() if ticket.audit_requested_at else None,
                'audit_requested_by': ticket.audit_requested_by,
                'audit_notified': ticket.audit_notified,
                'audit_status': ticket.audit_status,
                'audit_reviewed_at': ticket.audit_reviewed_at.isoformat() if ticket.audit_reviewed_at else None,
                'audit_reviewed_by': ticket.audit_reviewed_by
            })
        
        return jsonify({
            'success': True,
            'tickets': tickets_data,
            'total': len(tickets_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting audit tickets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/mark-audit-notified', methods=['POST'])
def mark_audit_notified(ticket_id):
    """Mark that admin has been notified about audit request."""
    try:
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        ticket.audit_notified = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ticket marcado como notificado'
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking audit notified for ticket {ticket_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/approve-audit', methods=['POST'])
def approve_audit(ticket_id):
    """Approve audit request for a ticket and reset exceeded_threshold counters."""
    try:
        from datetime import datetime
        from flask import session
        
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # Marcar como aprobado
        ticket.audit_status = 'approved'
        ticket.audit_reviewed_at = datetime.now()
        ticket.audit_reviewed_by = session.get('user_id')
        ticket.audit_notified = True
        
        # NUEVO: Resetear exceeded_threshold y contadores de alertas
        ticket.exceeded_threshold = False
        ticket.first_alert_sent_at = None
        ticket.last_alert_sent_at = None
        
        db.session.commit()
        
        log_audit(
            action='approve_audit',
            entity_type='ticket',
            entity_id=ticket_id,
            notes=f"Admin aprobó auditoría para ticket {ticket_id} - Contadores reseteados"
        )
        
        logger.info(f"✅ Auditoría aprobada para ticket {ticket_id} - Contadores reseteados")
        
        return jsonify({
            'success': True,
            'message': 'Auditoría aprobada y contadores reseteados'
        }), 200
        
    except Exception as e:
        logger.error(f"Error approving audit for ticket {ticket_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/reject-audit', methods=['POST'])
def reject_audit(ticket_id):
    """Reject audit request for a ticket - No hace cambios, solo marca como rechazado."""
    try:
        from datetime import datetime
        from flask import session
        
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # MODIFICADO: Solo marcar como rechazado, NO resetear contadores
        ticket.audit_status = 'rejected'
        ticket.audit_reviewed_at = datetime.now()
        ticket.audit_reviewed_by = session.get('user_id')
        ticket.audit_notified = True
        # NO se modifica exceeded_threshold ni alertas
        
        db.session.commit()
        
        log_audit(
            action='reject_audit',
            entity_type='ticket',
            entity_id=ticket_id,
            notes=f"Admin rechazó auditoría para ticket {ticket_id} - Sin cambios en contadores"
        )
        
        logger.info(f"⚠️ Auditoría rechazada para ticket {ticket_id} - Sin cambios")
        
        return jsonify({
            'success': True,
            'message': 'Auditoría rechazada'
        }), 200
        
    except Exception as e:
        logger.error(f"Error rejecting audit for ticket {ticket_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/tickets/<ticket_id>/delete-audit', methods=['DELETE'])
def delete_audit(ticket_id):
    """Oculta ticket de auditoría - Requiere que esté aprobado o rechazado previamente."""
    try:
        ticket = IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket no encontrado'
            }), 404
        
        # NUEVO: Verificar que el ticket esté aprobado o rechazado
        if ticket.audit_status not in ['approved', 'rejected']:
            return jsonify({
                'success': False,
                'error': 'Debe aprobar o rechazar el ticket antes de eliminarlo de la vista de auditoría'
            }), 400
        
        # MODIFICADO: Marcar como eliminado de auditoría (no resetear campos)
        # Agregar flag para ocultar de la vista de auditoría
        ticket.audit_requested = False  # Ocultar de la lista de auditoría
        # Mantener audit_status, audit_reviewed_at, audit_reviewed_by para historial
        # NO resetear exceeded_threshold - se mantiene el estado
        
        db.session.commit()
        
        log_audit(
            action='hide_from_audit',
            entity_type='ticket',
            entity_id=ticket_id,
            notes=f"Admin ocultó ticket {ticket_id} de la vista de auditoría (estado: {ticket.audit_status})"
        )
        
        logger.info(f"👁️ Ticket {ticket_id}: ocultado de auditoría (estado mantenido: {ticket.audit_status})")
        
        return jsonify({
            'success': True,
            'message': 'Ticket eliminado de la vista de auditoría'
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting audit for ticket {ticket_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
