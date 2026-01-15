"""
This module provides interfaces for CRUD operations on models.
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy.exc import SQLAlchemyError

from app.utils.config import db
from app.models.models import IncidentsDetection, AssignmentTracker, TicketResponseMetrics, OperatorConfig, OperatorSchedule, SystemConfig, AuditLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseInterface:
    """Base interface with common CRUD operations."""
    
    @staticmethod
    def commit_changes() -> bool:
        """Commit changes to database."""
        try:
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error: {str(e)}")
            return False
    
    @staticmethod
    def add_item(item: db.Model) -> bool:
        """Add item to database."""
        try:
            db.session.add(item)
            return BaseInterface.commit_changes()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error adding item: {str(e)}")
            return False


class IncidentsInterface(BaseInterface):
    """Interface for IncidentsDetection model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[IncidentsDetection]:
        """
        Create a new incident.
        
        Args:
            data: Dictionary with incident data
            
        Returns:
            Created incident or None if error
        """
        try:
            incident = IncidentsDetection(
                Cliente=data.get('Cliente'),
                Cliente_Nombre=data.get('Cliente_Nombre'),
                Asunto=data.get('Asunto'),
                Fecha_Creacion=data.get('Fecha_Creacion'),
                Ticket_ID=data.get('Ticket_ID'),
                Estado=data.get('Estado'),
                Prioridad=data.get('Prioridad'),
                is_created_splynx=data.get('is_created_splynx', False),
                assigned_to=data.get('assigned_to')
            )
            
            if BaseInterface.add_item(incident):
                return incident
            return None
        except Exception as e:
            logger.error(f"Error creating incident: {str(e)}")
            return None
    
    @staticmethod
    def get_by_id(incident_id: int) -> Optional[IncidentsDetection]:
        """
        Get incident by ID.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Incident or None if not found
        """
        try:
            return IncidentsDetection.query.get(incident_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting incident by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_all() -> List[IncidentsDetection]:
        """
        Get all incidents.
        
        Returns:
            List of incidents
        """
        try:
            return IncidentsDetection.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all incidents: {str(e)}")
            return []
    
    @staticmethod
    def update(incident_id: int, data: Dict[str, Any]) -> Optional[IncidentsDetection]:
        """
        Update an incident.
        
        Args:
            incident_id: ID of the incident to update
            data: Dictionary with updated data
            
        Returns:
            Updated incident or None if error
        """
        try:
            incident = IncidentsInterface.get_by_id(incident_id)
            if not incident:
                return None
            
            # Update fields if they exist in data
            if 'Cliente' in data:
                incident.Cliente = data['Cliente']
            if 'Cliente_Nombre' in data:
                incident.Cliente_Nombre = data['Cliente_Nombre']
            if 'Asunto' in data:
                incident.Asunto = data['Asunto']
            if 'Fecha_Creacion' in data:
                incident.Fecha_Creacion = data['Fecha_Creacion']
            if 'Ticket_ID' in data:
                incident.Ticket_ID = data['Ticket_ID']
            if 'Estado' in data:
                incident.Estado = data['Estado']
            if 'Prioridad' in data:
                incident.Prioridad = data['Prioridad']
            if 'is_created_splynx' in data:
                incident.is_created_splynx = data['is_created_splynx']
            if 'assigned_to' in data:
                incident.assigned_to = data['assigned_to']
            
            if BaseInterface.commit_changes():
                return incident
            return None
        except Exception as e:
            logger.error(f"Error updating incident: {str(e)}")
            return None
    
    @staticmethod
    def delete(incident_id: int) -> bool:
        """
        Delete an incident.
        
        Args:
            incident_id: ID of the incident to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            incident = IncidentsInterface.get_by_id(incident_id)
            if not incident:
                return False
            
            db.session.delete(incident)
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error deleting incident: {str(e)}")
            return False
    
    @staticmethod
    def find_by_ticket_id(ticket_id: str) -> Optional[IncidentsDetection]:
        """
        Find incident by Ticket_ID.
        
        Args:
            ticket_id: Ticket ID to search for
            
        Returns:
            Incident or None if not found
        """
        try:
            return IncidentsDetection.query.filter_by(Ticket_ID=ticket_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding incident by ticket ID: {str(e)}")
            return None
    
    @staticmethod
    def find_by_client(client_name: str) -> List[IncidentsDetection]:
        """
        Find incidents by client name.
        
        Args:
            client_name: Client name to search for
            
        Returns:
            List of incidents for the client
        """
        try:
            return IncidentsDetection.query.filter_by(Cliente=client_name).all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding incidents by client: {str(e)}")
            return []
    
    @staticmethod
    def find_by_status(status: str) -> List[IncidentsDetection]:
        """
        Find incidents by status.
        
        Args:
            status: Status to search for
            
        Returns:
            List of incidents with the specified status
        """
        try:
            return IncidentsDetection.query.filter_by(Estado=status).all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding incidents by status: {str(e)}")
            return []


class AssignmentTrackerInterface(BaseInterface):
    """Interface for AssignmentTracker model."""
    
    @staticmethod
    def create(person_id: int) -> Optional[AssignmentTracker]:
        """Create a new assignment tracker for a person."""
        try:
            from datetime import datetime
            tracker = AssignmentTracker(
                person_id=person_id,
                ticket_count=0,
                last_assigned=datetime.now()
            )
            if BaseInterface.add_item(tracker):
                return tracker
            return None
        except Exception as e:
            logger.error(f"Error creating assignment tracker: {str(e)}")
            return None
    
    @staticmethod
    def get_by_person_id(person_id: int) -> Optional[AssignmentTracker]:
        """Get tracker by person ID."""
        try:
            return AssignmentTracker.query.filter_by(person_id=person_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting tracker by person ID: {str(e)}")
            return None
    
    @staticmethod
    def get_all() -> List[AssignmentTracker]:
        """Get all trackers."""
        try:
            return AssignmentTracker.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all trackers: {str(e)}")
            return []
    
    @staticmethod
    def increment_count(person_id: int) -> bool:
        """Increment ticket count for a person."""
        try:
            from datetime import datetime
            tracker = AssignmentTrackerInterface.get_by_person_id(person_id)
            if not tracker:
                tracker = AssignmentTrackerInterface.create(person_id)
                if not tracker:
                    return False
            
            tracker.ticket_count += 1
            tracker.last_assigned = datetime.now()
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error incrementing count: {str(e)}")
            return False
    
    @staticmethod
    def get_person_with_least_tickets(person_ids: List[int]) -> int:
        """Get person ID with least assigned tickets."""
        try:
            trackers = {}
            for person_id in person_ids:
                tracker = AssignmentTrackerInterface.get_by_person_id(person_id)
                if tracker:
                    trackers[person_id] = tracker.ticket_count
                else:
                    trackers[person_id] = 0
            
            return min(trackers, key=trackers.get)
        except Exception as e:
            logger.error(f"Error getting person with least tickets: {str(e)}")
            return person_ids[0]
    
    @staticmethod
    def reset_all_counts() -> bool:
        """Reset all ticket counts to 0."""
        try:
            trackers = AssignmentTrackerInterface.get_all()
            for tracker in trackers:
                tracker.ticket_count = 0
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error resetting counts: {str(e)}")
            return False


class TicketResponseMetricsInterface(BaseInterface):
    """Interface for TicketResponseMetrics model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[TicketResponseMetrics]:
        """Create a new ticket response metric."""
        try:
            from datetime import datetime
            metric = TicketResponseMetrics(
                ticket_id=data.get('ticket_id'),
                assigned_to=data.get('assigned_to'),
                customer_id=data.get('customer_id'),
                customer_name=data.get('customer_name'),
                subject=data.get('subject'),
                created_at=data.get('created_at'),
                first_alert_sent_at=data.get('first_alert_sent_at'),
                last_alert_sent_at=data.get('last_alert_sent_at'),
                response_time_minutes=data.get('response_time_minutes'),
                alert_count=data.get('alert_count', 0),
                resolved_at=data.get('resolved_at'),
                exceeded_threshold=data.get('exceeded_threshold', True)
            )
            if BaseInterface.add_item(metric):
                return metric
            return None
        except Exception as e:
            logger.error(f"Error creating ticket metric: {str(e)}")
            return None
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> Optional[TicketResponseMetrics]:
        """Get metric by ticket ID."""
        try:
            return TicketResponseMetrics.query.filter_by(ticket_id=ticket_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting metric by ticket ID: {str(e)}")
            return None
    
    @staticmethod
    def update_alert_sent(ticket_id: str, response_time_minutes: int, assigned_to: int = None, 
                         customer_id: str = None, customer_name: str = None, 
                         subject: str = None, created_at = None) -> bool:
        """Update alert sent timestamp and increment alert count. Creates metric if doesn't exist."""
        try:
            from datetime import datetime
            import pytz
            metric = TicketResponseMetricsInterface.get_by_ticket_id(ticket_id)
            # Usar timezone de Argentina para evitar problemas de comparación
            tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz_argentina)
            
            if metric:
                # Actualizar métrica existente
                metric.last_alert_sent_at = now
                metric.alert_count += 1
                metric.response_time_minutes = response_time_minutes
                logger.debug(f"      📝 Actualizando ticket {ticket_id}: last_alert={now}, count={metric.alert_count}")
            else:
                # Crear métrica nueva si no existe
                logger.debug(f"      🆕 Creando nueva métrica para ticket {ticket_id}")
                metric = TicketResponseMetrics(
                    ticket_id=ticket_id,
                    assigned_to=assigned_to,
                    customer_id=customer_id,
                    customer_name=customer_name,
                    subject=subject,
                    created_at=created_at or now,
                    first_alert_sent_at=now,
                    last_alert_sent_at=now,
                    response_time_minutes=response_time_minutes,
                    alert_count=1,
                    exceeded_threshold=True
                )
                from app.utils.config import db
                db.session.add(metric)
            
            commit_result = BaseInterface.commit_changes()
            if not commit_result:
                logger.error(f"      ❌ Commit falló para ticket {ticket_id}")
            return commit_result
        except Exception as e:
            logger.error(f"      ❌ Error updating alert sent para ticket {ticket_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def add_assignment_to_history(ticket_id: str, assigned_to: int, reason: str = "assigned") -> bool:
        """Add assignment entry to history."""
        try:
            from datetime import datetime
            metric = TicketResponseMetricsInterface.get_by_ticket_id(ticket_id)
            if metric:
                # Inicializar historial si es None o vacío
                if metric.assignment_history is None:
                    metric.assignment_history = []
                
                # Agregar nueva entrada al historial
                assignment_entry = {
                    "assigned_to": assigned_to,
                    "assigned_at": datetime.now().isoformat(),
                    "reason": reason
                }
                metric.assignment_history.append(assignment_entry)
                
                # Actualizar assigned_to actual
                metric.assigned_to = assigned_to
                
                logger.debug(f"      📋 Historial actualizado: {len(metric.assignment_history)} asignaciones para ticket {ticket_id}")
                return BaseInterface.commit_changes()
            return False
        except Exception as e:
            logger.error(f"Error adding assignment to history: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def mark_resolved(ticket_id: str) -> bool:
        """Mark ticket as resolved."""
        try:
            from datetime import datetime
            metric = TicketResponseMetricsInterface.get_by_ticket_id(ticket_id)
            if metric:
                metric.resolved_at = datetime.now()
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error marking ticket as resolved: {str(e)}")
            return False
    
    @staticmethod
    def get_metrics_by_person(person_id: int) -> List[TicketResponseMetrics]:
        """Get all metrics for a specific person."""
        try:
            return TicketResponseMetrics.query.filter_by(assigned_to=person_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting metrics by person: {str(e)}")
            return []
    
    @staticmethod
    def get_unresolved_metrics() -> List[TicketResponseMetrics]:
        """Get all unresolved ticket metrics."""
        try:
            return TicketResponseMetrics.query.filter_by(resolved_at=None).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting unresolved metrics: {str(e)}")
            return []


class OperatorConfigInterface(BaseInterface):
    """Interface for OperatorConfig model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[OperatorConfig]:
        """Create a new operator configuration."""
        try:
            operator = OperatorConfig(
                person_id=data.get('person_id'),
                name=data.get('name'),
                whatsapp_number=data.get('whatsapp_number'),
                is_active=data.get('is_active', True),
                is_paused=data.get('is_paused', False),
                notifications_enabled=data.get('notifications_enabled', True)
            )
            if BaseInterface.add_item(operator):
                return operator
            return None
        except Exception as e:
            logger.error(f"Error creating operator config: {str(e)}")
            return None
    
    @staticmethod
    def get_by_person_id(person_id: int) -> Optional[OperatorConfig]:
        """Get operator config by person ID."""
        try:
            return OperatorConfig.query.filter_by(person_id=person_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting operator config: {str(e)}")
            return None
    
    @staticmethod
    def get_all() -> List[OperatorConfig]:
        """Get all operator configurations."""
        try:
            return OperatorConfig.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all operator configs: {str(e)}")
            return []
    
    @staticmethod
    def get_active_operators() -> List[OperatorConfig]:
        """Get all active operators."""
        try:
            return OperatorConfig.query.filter_by(is_active=True, is_paused=False).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active operators: {str(e)}")
            return []
    
    @staticmethod
    def update(person_id: int, data: Dict[str, Any]) -> Optional[OperatorConfig]:
        """Update operator configuration."""
        try:
            operator = OperatorConfigInterface.get_by_person_id(person_id)
            if not operator:
                return None
            
            for key, value in data.items():
                if hasattr(operator, key):
                    setattr(operator, key, value)
            
            if BaseInterface.commit_changes():
                return operator
            return None
        except Exception as e:
            logger.error(f"Error updating operator config: {str(e)}")
            return None
    
    @staticmethod
    def pause_operator(person_id: int, reason: str, paused_by: str) -> bool:
        """Pause an operator."""
        try:
            from datetime import datetime
            operator = OperatorConfigInterface.get_by_person_id(person_id)
            if not operator:
                return False
            
            operator.is_paused = True
            operator.paused_reason = reason
            operator.paused_at = datetime.now()
            operator.paused_by = paused_by
            
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error pausing operator: {str(e)}")
            return False
    
    @staticmethod
    def resume_operator(person_id: int) -> bool:
        """Resume an operator."""
        try:
            operator = OperatorConfigInterface.get_by_person_id(person_id)
            if not operator:
                return False
            
            operator.is_paused = False
            operator.paused_reason = None
            operator.paused_at = None
            operator.paused_by = None
            
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error resuming operator: {str(e)}")
            return False


class OperatorScheduleInterface(BaseInterface):
    """Interface for OperatorSchedule model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[OperatorSchedule]:
        """Create a new operator schedule."""
        try:
            schedule = OperatorSchedule(
                person_id=data.get('person_id'),
                day_of_week=data.get('day_of_week'),
                start_time=data.get('start_time'),
                end_time=data.get('end_time'),
                is_active=data.get('is_active', True)
            )
            if BaseInterface.add_item(schedule):
                return schedule
            return None
        except Exception as e:
            logger.error(f"Error creating operator schedule: {str(e)}")
            return None
    
    @staticmethod
    def get_by_person_id(person_id: int) -> List[OperatorSchedule]:
        """Get all schedules for a person."""
        try:
            return OperatorSchedule.query.filter_by(person_id=person_id, is_active=True).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting schedules by person: {str(e)}")
            return []
    
    @staticmethod
    def get_by_id(schedule_id: int) -> Optional[OperatorSchedule]:
        """Get schedule by ID."""
        try:
            return OperatorSchedule.query.get(schedule_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting schedule by ID: {str(e)}")
            return None
    
    @staticmethod
    def update(schedule_id: int, data: Dict[str, Any]) -> Optional[OperatorSchedule]:
        """Update operator schedule."""
        try:
            schedule = OperatorScheduleInterface.get_by_id(schedule_id)
            if not schedule:
                return None
            
            for key, value in data.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            if BaseInterface.commit_changes():
                return schedule
            return None
        except Exception as e:
            logger.error(f"Error updating schedule: {str(e)}")
            return None
    
    @staticmethod
    def delete(schedule_id: int) -> bool:
        """Delete operator schedule."""
        try:
            schedule = OperatorScheduleInterface.get_by_id(schedule_id)
            if not schedule:
                return False
            
            db.session.delete(schedule)
            return BaseInterface.commit_changes()
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return False


class SystemConfigInterface(BaseInterface):
    """Interface for SystemConfig model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[SystemConfig]:
        """Create a new system configuration."""
        try:
            config = SystemConfig(
                key=data.get('key'),
                value=data.get('value'),
                value_type=data.get('value_type', 'string'),
                description=data.get('description'),
                category=data.get('category'),
                updated_by=data.get('updated_by')
            )
            if BaseInterface.add_item(config):
                return config
            return None
        except Exception as e:
            logger.error(f"Error creating system config: {str(e)}")
            return None
    
    @staticmethod
    def get_by_key(key: str) -> Optional[SystemConfig]:
        """Get config by key."""
        try:
            return SystemConfig.query.filter_by(key=key).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting config by key: {str(e)}")
            return None
    
    @staticmethod
    def get_by_category(category: str) -> List[SystemConfig]:
        """Get all configs by category."""
        try:
            return SystemConfig.query.filter_by(category=category).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting configs by category: {str(e)}")
            return []
    
    @staticmethod
    def get_all() -> List[SystemConfig]:
        """Get all system configurations."""
        try:
            return SystemConfig.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all system configs: {str(e)}")
            return []
    
    @staticmethod
    def update_or_create(key: str, value: str, updated_by: str = None, **kwargs) -> Optional[SystemConfig]:
        """Update existing config or create new one."""
        try:
            config = SystemConfigInterface.get_by_key(key)
            if config:
                config.value = value
                config.updated_by = updated_by
                for k, v in kwargs.items():
                    if hasattr(config, k):
                        setattr(config, k, v)
            else:
                config = SystemConfig(
                    key=key,
                    value=value,
                    updated_by=updated_by,
                    **kwargs
                )
                db.session.add(config)
            
            if BaseInterface.commit_changes():
                return config
            return None
        except Exception as e:
            logger.error(f"Error updating or creating config: {str(e)}")
            return None
    
    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """Get config value with type conversion."""
        try:
            config = SystemConfigInterface.get_by_key(key)
            if not config:
                return default
            
            value = config.value
            value_type = config.value_type
            
            if value_type == 'int':
                return int(value)
            elif value_type == 'bool':
                return value.lower() in ('true', '1', 'yes')
            elif value_type == 'json':
                import json
                return json.loads(value)
            else:
                return value
        except Exception as e:
            logger.error(f"Error getting config value: {str(e)}")
            return default


class AuditLogInterface(BaseInterface):
    """Interface for AuditLog model."""
    
    @staticmethod
    def create(data: Dict[str, Any]) -> Optional[AuditLog]:
        """Create a new audit log entry."""
        try:
            log = AuditLog(
                action=data.get('action'),
                entity_type=data.get('entity_type'),
                entity_id=data.get('entity_id'),
                old_value=data.get('old_value'),
                new_value=data.get('new_value'),
                performed_by=data.get('performed_by'),
                ip_address=data.get('ip_address'),
                notes=data.get('notes')
            )
            if BaseInterface.add_item(log):
                return log
            return None
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            return None
    
    @staticmethod
    def log_action(action: str, entity_type: str, entity_id: str = None, 
                   old_value: Dict = None, new_value: Dict = None,
                   performed_by: str = None, ip_address: str = None, notes: str = None) -> bool:
        """Helper method to log an action."""
        try:
            data = {
                'action': action,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'old_value': old_value,
                'new_value': new_value,
                'performed_by': performed_by,
                'ip_address': ip_address,
                'notes': notes
            }
            return AuditLogInterface.create(data) is not None
        except Exception as e:
            logger.error(f"Error logging action: {str(e)}")
            return False
    
    @staticmethod
    def get_recent(limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs."""
        try:
            return AuditLog.query.order_by(AuditLog.performed_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent audit logs: {str(e)}")
            return []
    
    @staticmethod
    def get_by_entity(entity_type: str, entity_id: str) -> List[AuditLog]:
        """Get audit logs for specific entity."""
        try:
            return AuditLog.query.filter_by(entity_type=entity_type, entity_id=entity_id).order_by(AuditLog.performed_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting audit logs by entity: {str(e)}")
            return []
    
    @staticmethod
    def get_by_action(action: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs by action type."""
        try:
            return AuditLog.query.filter_by(action=action).order_by(AuditLog.performed_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting audit logs by action: {str(e)}")
            return []