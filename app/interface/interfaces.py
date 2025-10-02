"""
This module provides interfaces for CRUD operations on models.
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy.exc import SQLAlchemyError

from app.utils.config import db
from app.models.models import IncidentsDetection


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
                Asunto=data.get('Asunto'),
                Fecha_Creacion=data.get('Fecha_Creacion'),
                Ticket_ID=data.get('Ticket_ID'),
                Estado=data.get('Estado'),
                Prioridad=data.get('Prioridad'),
                is_created_splynx=data.get('is_created_splynx', False)
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