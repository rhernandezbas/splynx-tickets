import csv
import os
from app.utils.constants import DEPARTAMENTOS

# Mapeo de prioridades a formato Splynx
PRIORITY_MAP = {
    "baja": "low",
    "media": "medium", 
    "alta": "high",
    "urgente": "urgent"
}

def procesar_departamento(dept_key, dept_name):
    """Procesar CSV de un departamento específico"""
    print(f"\n*** Procesando departamento: {dept_name} ***")
    print("-" * 50)
    
    # Obtener directorios
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, '..', 'archivos'))
    dept_dir = os.path.join(base_dir, dept_key)
    
    # Archivos de entrada y salida
    csv_file = os.path.join(dept_dir, "casos_recientes.csv")
    output_file = os.path.join(dept_dir, "clientes_extraidos.txt")
    
    print(f"*** Directorio: {dept_dir}")
    print(f"*** CSV de entrada: casos_recientes.csv")
    print(f"*** Archivo de salida: clientes_extraidos.txt")
    
    # Verificar que existe el CSV
    if not os.path.exists(csv_file):
        print(f"*** No se encontró el archivo CSV en {dept_key}")
        print("*** Ejecuta primero selenium_multi_departamentos.py")
        return False
    
    try:
        # Crear archivo de salida
        with open(output_file, "w", encoding="utf-8") as f_out:
            # Escribir encabezados
            f_out.write("Cliente\tAsunto\tFecha_Creacion\tPrioridad\n")
            
            # Procesar CSV
            with open(csv_file, newline="", encoding="latin-1") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=";")
                
                clientes_procesados = 0
                for fila in reader:
                    cliente = fila.get("Cliente", "").strip()
                    asunto_original = fila.get("Asunto", "").strip()
                    fecha_creacion = fila.get("Fecha Creacion", "").strip()
                    prioridad_raw = fila.get("Prioridad", "").strip().lower()
                    contrato = fila.get("Contrato", "").strip()
                    
                    # Convertir prioridad usando el mapeo
                    prioridad = PRIORITY_MAP.get(prioridad_raw, "medium")
                    
                    # Lógica para determinar el asunto basado en FO en el contrato
                    if "FO" in contrato.upper() or "FTTH" in contrato.upper():
                        asunto = "Ticket-FO"
                    else:
                        asunto = "Ticket-WIRELESS"
                    
                    if cliente:  # Solo guardar si hay cliente
                        f_out.write(f"{cliente}\t{asunto}\t{fecha_creacion}\t{prioridad}\n")
                        clientes_procesados += 1
                
                print(f"*** {clientes_procesados} clientes procesados para {dept_name} ***")
                return True
                
    except Exception as e:
        print(f"*** Error procesando {dept_name}: {e} ***")
        return False

def main():
    """Función principal para procesar departamentos automáticamente"""
    print("*** Sistema Multi-Departamental de Procesamiento de Clientes ***")
    print("=" * 65)
    print("*** MODO AUTOMATICO - Sin verificaciones ***")
    
    # Procesar automáticamente solo los departamentos habilitados
    departamentos_a_procesar = [(key, name) for key, name in DEPARTAMENTOS.items()]
    
    print(f"*** Procesando automaticamente: {', '.join([name for _, name in departamentos_a_procesar])} ***")
    
    # Procesar departamentos seleccionados
    resultados = {}
    for dept_key, dept_name in departamentos_a_procesar:
        success = procesar_departamento(dept_key, dept_name)
        resultados[dept_key] = success
    
    # Mostrar resumen
    print(f"\n{'=' * 65}")
    print("*** RESUMEN DE PROCESAMIENTO ***")
    print("=" * 65)
    
    exitosos = 0
    for dept_key, success in resultados.items():
        dept_name = DEPARTAMENTOS[dept_key]
        if success:
            print(f"*** {dept_name}: Clientes extraídos correctamente ***")
            exitosos += 1
        else:
            print(f"*** {dept_name}: Error en el procesamiento ***")
    
    print(f"\n*** Total exitosos: {exitosos}/{len(resultados)} ***")
    
    if exitosos > 0:
        print("*** Proceso completado! ***")
        print("*** Continuando con la creación de tickets... ***")
    else:
        print("*** No se procesaron departamentos exitosamente ***")

if __name__ == "__main__":
    main()
