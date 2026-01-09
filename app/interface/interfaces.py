"""
This module provides interfaces for CRUD operations on models.
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy.exc import SQLAlchemyError

from app.utils.config import db
from app.models.models import IncidentsDetection, AssignmentTracker, TicketResponseMetrics


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
            print(f"Database error: {str(e)}")
            return False
    
    @staticmethod
    def add_item(item: db.Model) -> bool:
        """Add item to database."""
        try:
            db.session.add(item)
            return BaseInterface.commit_changes()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error adding item: {str(e)}")
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
            print(f"Error creating incident: {str(e)}")
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
            print(f"Error getting incident by ID: {str(e)}")
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
            print(f"Error getting all incidents: {str(e)}")
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
            print(f"Error updating incident: {str(e)}")
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
            print(f"Error deleting incident: {str(e)}")
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
            print(f"Error finding incident by ticket ID: {str(e)}")
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
            print(f"Error finding incidents by client: {str(e)}")
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
            print(f"Error finding incidents by status: {str(e)}")
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
            print(f"Error creating assignment tracker: {str(e)}")
            return None
    
    @staticmethod
    def get_by_person_id(person_id: int) -> Optional[AssignmentTracker]:
        """Get tracker by person ID."""
        try:
            return AssignmentTracker.query.filter_by(person_id=person_id).first()
        except SQLAlchemyError as e:
            print(f"Error getting tracker by person ID: {str(e)}")
            return None
    
    @staticmethod
    def get_all() -> List[AssignmentTracker]:
        """Get all trackers."""
        try:
            return AssignmentTracker.query.all()
        except SQLAlchemyError as e:
            print(f"Error getting all trackers: {str(e)}")
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
            print(f"Error incrementing count: {str(e)}")
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
            print(f"Error getting person with least tickets: {str(e)}")
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
            print(f"Error resetting counts: {str(e)}")
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
            print(f"Error creating ticket metric: {str(e)}")
            return None
    
    @staticmethod
    def get_by_ticket_id(ticket_id: str) -> Optional[TicketResponseMetrics]:
        """Get metric by ticket ID."""
        try:
            return TicketResponseMetrics.query.filter_by(ticket_id=ticket_id).first()
        except SQLAlchemyError as e:
            print(f"Error getting metric by ticket ID: {str(e)}")
            return None
    
    @staticmethod
    def update_alert_sent(ticket_id: str, response_time_minutes: int) -> bool:
        """Update alert sent timestamp and increment alert count."""
        try:
            from datetime import datetime
            metric = TicketResponseMetricsInterface.get_by_ticket_id(ticket_id)
            if metric:
                metric.last_alert_sent_at = datetime.now()
                metric.alert_count += 1
                metric.response_time_minutes = response_time_minutes
            return BaseInterface.commit_changes()
        except Exception as e:
            print(f"Error updating alert sent: {str(e)}")
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
            print(f"Error marking ticket as resolved: {str(e)}")
            return False
    
    @staticmethod
    def get_metrics_by_person(person_id: int) -> List[TicketResponseMetrics]:
        """Get all metrics for a specific person."""
        try:
            return TicketResponseMetrics.query.filter_by(assigned_to=person_id).all()
        except SQLAlchemyError as e:
            print(f"Error getting metrics by person: {str(e)}")
            return []
    
    @staticmethod
    def get_unresolved_metrics() -> List[TicketResponseMetrics]:
        """Get all unresolved ticket metrics."""
        try:
            return TicketResponseMetrics.query.filter_by(resolved_at=None).all()
        except SQLAlchemyError as e:
            print(f"Error getting unresolved metrics: {str(e)}")
            return []