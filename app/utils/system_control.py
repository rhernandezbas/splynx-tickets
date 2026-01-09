"""
Control de estado del sistema
Permite pausar y reanudar la asignación automática y procesos
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Archivo para persistir el estado del sistema
STATE_FILE = Path(__file__).parent.parent.parent / "system_state.json"


class SystemControl:
    """Clase para controlar el estado del sistema"""
    
    @staticmethod
    def _load_state() -> dict:
        """Carga el estado desde el archivo"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando estado: {e}")
        
        return {
            "paused": False,
            "paused_at": None,
            "paused_by": None,
            "reason": None
        }
    
    @staticmethod
    def _save_state(state: dict):
        """Guarda el estado en el archivo"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error guardando estado: {e}")
    
    @staticmethod
    def is_paused() -> bool:
        """Verifica si el sistema está pausado"""
        state = SystemControl._load_state()
        return state.get("paused", False)
    
    @staticmethod
    def pause(reason: str = None, paused_by: str = "manual") -> dict:
        """
        Pausa el sistema
        
        Args:
            reason: Razón de la pausa
            paused_by: Quién pausó el sistema
            
        Returns:
            dict: Estado actualizado
        """
        state = {
            "paused": True,
            "paused_at": datetime.now().isoformat(),
            "paused_by": paused_by,
            "reason": reason or "Pausa manual"
        }
        
        SystemControl._save_state(state)
        print(f"⏸️  Sistema PAUSADO - {reason or 'Pausa manual'}")
        
        return state
    
    @staticmethod
    def resume(resumed_by: str = "manual") -> dict:
        """
        Reanuda el sistema
        
        Args:
            resumed_by: Quién reanudó el sistema
            
        Returns:
            dict: Estado actualizado
        """
        state = {
            "paused": False,
            "resumed_at": datetime.now().isoformat(),
            "resumed_by": resumed_by,
            "reason": None
        }
        
        SystemControl._save_state(state)
        print(f"▶️  Sistema REANUDADO")
        
        return state
    
    @staticmethod
    def get_status() -> dict:
        """
        Obtiene el estado actual del sistema
        
        Returns:
            dict: Estado completo del sistema
        """
        state = SystemControl._load_state()
        
        return {
            "paused": state.get("paused", False),
            "status": "PAUSADO" if state.get("paused", False) else "ACTIVO",
            "paused_at": state.get("paused_at"),
            "paused_by": state.get("paused_by"),
            "reason": state.get("reason"),
            "resumed_at": state.get("resumed_at"),
            "resumed_by": state.get("resumed_by")
        }
