"""
Sistema Multi-Departamental de Creación de Tickets para Splynx
"""

import os

# Configuración de departamentos
DEPARTAMENTOS = {
    "Soporte_Tecnico": "Soporte Técnico",
    "administracion": "administracion", 
    "Facturacion": "Facturación"
}

class MultiDepartmentTicketCreator:
    def __init__(self, max_workers=5):
        """
        Inicializar el creador multi-departamental
        
        Args:
            max_workers (int): Número máximo de workers concurrentes por departamento
        """
        self.max_workers = max_workers
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.resultados_departamentos = {}
    
    def procesar_departamento(self, dept_key, dept_name):
        """Procesar tickets para un departamento específico"""
        print(f"\n🏢 Procesando tickets para: {dept_name}")
        print("=" * 60)
        
        # Verificar que existe la carpeta del departamento en app/archivos
        base_dir = os.path.abspath(os.path.join(self.script_dir, '..', 'archivos'))
        dept_dir = os.path.join(base_dir, dept_key)
        if not os.path.exists(dept_dir):
            print(f"❌ No existe la carpeta {dept_key}")
            return {"success": False, "error": "Carpeta no encontrada"}
        
        # Verificar que existe el archivo de clientes
        clientes_file = os.path.join(dept_dir, "clientes_extraidos.txt")
        if not os.path.exists(clientes_file):
            print(f"❌ No existe clientes_extraidos.txt en {dept_key}")
            print("💡 Ejecuta primero tickets_process.py")
            return {"success": False, "error": "Archivo clientes_extraidos.txt no encontrado"}

    
    def procesar_departamentos_seleccionados(self, departamentos_a_procesar):
        """Procesar una lista de departamentos"""
        print("🚀 Iniciando creación de tickets multi-departamental...")
        
        for dept_key, dept_name in departamentos_a_procesar:
            resultado = self.procesar_departamento(dept_key, dept_name)
            self.resultados_departamentos[dept_key] = resultado
        
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Mostrar resumen final de todos los departamentos procesados"""
        print(f"\n{'=' * 70}")
        print("📊 RESUMEN FINAL - CREACIÓN DE TICKETS MULTI-DEPARTAMENTAL")
        print("=" * 70)
        
        total_exitosos = 0
        total_tickets_nuevos = 0
        total_tiempo = 0
        
        for dept_key, resultado in self.resultados_departamentos.items():
            dept_name = DEPARTAMENTOS[dept_key]
            
            if resultado["success"]:
                stats = resultado["stats"]
                duration = resultado["duration"]
                new_tickets = resultado["new_tickets"]
                
                print(f"\n✅ {dept_name}:")
                print(f"   - Tickets nuevos creados: {new_tickets}")
                print(f"   - Total exitosos: {stats['success']}")
                print(f"   - Total con Ticket ID: {stats['with_ticket_id']}")
                print(f"   - Tiempo: {duration:.2f} segundos")
                
                total_exitosos += 1
                total_tickets_nuevos += new_tickets
                total_tiempo += duration
            else:
                print(f"\n❌ {dept_name}:")
                print(f"   - Error: {resultado['error']}")
        
        print(f"\n{'=' * 70}")
        print(f"📈 TOTALES GENERALES:")
        print(f"   - Departamentos exitosos: {total_exitosos}/{len(self.resultados_departamentos)}")
        print(f"   - Total tickets nuevos: {total_tickets_nuevos}")
        print(f"   - Tiempo total: {total_tiempo:.2f} segundos")
        print("🎉 Proceso multi-departamental completado!")