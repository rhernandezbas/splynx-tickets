"""Sistema Multi-Departamental de Descarga de Tickets"""

import os
import time
import glob
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from app.utils.constants import USUARIO, CONTRASENA, LOGIN_URL, CASOS_URL, DEPARTAMENTOS_SELENIUM
from app.interface.interfaces import IncidentsInterface
from flask import current_app
from app import create_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SeleniumMultiDepartamentos:
    def __init__(self):
        """Inicializar el sistema multi-departamental"""
        self.departamentos = DEPARTAMENTOS_SELENIUM

    @staticmethod
    def setup_chrome_driver(dept_key:str):

        archivos_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archivos")
        specific_download_dir = os.path.join(archivos_root, dept_key)
        os.makedirs(specific_download_dir, exist_ok=True)
        download_dir = specific_download_dir

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Configurar directorio de descargas
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        # Usar ChromeDriver del sistema si existe (Docker)
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
            return webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback a la instalación automática de Selenium
            return webdriver.Chrome(options=chrome_options)

    @staticmethod
    def login_sistema( driver):
        """Realizar login en el sistema"""
        logger.info("*** Abriendo página de login...")
        driver.get(LOGIN_URL)
        time.sleep(2)

        logger.info("*** Ingresando usuario y contraseña...")
        driver.find_element(By.NAME, "myusername").send_keys(USUARIO)
        driver.find_element(By.NAME, "mypassword").send_keys(CONTRASENA)

        logger.info("*** Haciendo clic en 'Ingresar'...")
        driver.find_element(By.ID, "submit").click()

        # Verificación de login
        try:
            WebDriverWait(driver, 10).until(
                EC.url_contains("index.php")
            )
            logger.info("*** Login exitoso")
            return True
        except TimeoutException:
            logger.error("*** Login fallido")
            return False

    def descargar_csv_departamento(self,dept_key):
        """Descargar CSV para un departamento específico"""

        driver = self.setup_chrome_driver(dept_key)
        login = self.login_sistema(driver)

        if not login:
            logger.error("*** Login fallido. No se puede descargar el CSV")
            return False

        departamento_info = self.departamentos.get(f"{dept_key}")
        driver = driver
        archivos_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archivos")
        specific_download_dir = os.path.join(archivos_root, dept_key)
        os.makedirs(specific_download_dir, exist_ok=True)

        download_dir = specific_download_dir

        if not departamento_info:
            logger.error(f"*** Departamento no encontrado: {dept_key}")
            return False

        logger.info(f"*** Procesando departamento: {departamento_info['nombre_display']}")

        # Ir a módulo Casos
        logger.info("*** Abriendo módulo 'Reclamos / Casos'...")
        driver.get(CASOS_URL)
        time.sleep(3)

        # Seleccionar Grupo específico
        try:
            logger.info(f"*** Seleccionando grupo '{departamento_info['nombre_display']}'...")
            dropdown_grupo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "bus_caso_grupo_chosen"))
            )
            dropdown_grupo.click()

            opcion_grupo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, departamento_info['xpath_grupo']))
            )
            opcion_grupo.click()
            logger.info(f"*** Grupo '{departamento_info['nombre_display']}' seleccionado")
        except TimeoutException:
            logger.warning(f"*** No se encontró el grupo '{departamento_info['nombre_display']}'. Continuando...")

        # Seleccionar Estado: Asignado
        try:
            logger.info("*** Seleccionando estado 'Asignado'...")
            dropdown_estado = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "bus_caso_estado_chosen"))
            )
            dropdown_estado.click()

            opcion_estado = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'Asignado')]"))
            )
            opcion_estado.click()
            logger.info("*** Estado 'Asignado' seleccionado")
        except TimeoutException:
            logger.warning("*** No se encontró el estado 'Asignado'. Continuando...")

        time.sleep(1)

        # Hacer clic en Buscar
        logger.info("*** Haciendo clic en 'Buscar'...")
        try:
            buscar_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@title='Buscar']"))
            )
            buscar_btn.click()
            time.sleep(3)
        except TimeoutException:
            logger.warning("*** No se encontró el botón 'Buscar'. Continuando...")

        # Cambiar filas por página a 100
        try:
            logger.info("*** Ajustando filas por página a 100...")
            select_lpp = Select(WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "lpp"))
            ))
            select_lpp.select_by_value("100")
            time.sleep(2)
            logger.info("*** Filas por página ajustadas a 100")
        except TimeoutException:
            logger.warning("*** No se encontró el dropdown de filas por página")

        # Descargar CSV
        logger.info("*** Descargando CSV...")
        main_window = driver.current_window_handle
        try:
            # Obtener lista de archivos antes de la descarga
            files_before = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()

            csv_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//img[contains(@src,'fil_csv.png')]"))
            )
            csv_btn.click()
            time.sleep(2)

            # Cambiar a nueva pestaña si se abre
            all_windows = driver.window_handles
            for handle in all_windows:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    break

            # Esperar que termine la descarga
            timeout = 60
            start_time = time.time()
            new_file = None

            while time.time() - start_time < timeout:
                # Verificar archivos.crdownload (descarga en progreso)
                crdownload_files = glob.glob(os.path.join(download_dir, "*.crdownload"))
                if crdownload_files:
                    time.sleep(1)
                    continue

                # Buscar nuevos archivos CSV
                current_files = set(os.listdir(download_dir)) if os.path.exists(download_dir) else set()
                new_files = current_files - files_before
                csv_new_files = [f for f in new_files if f.endswith('.csv')]

                if csv_new_files:
                    new_file = csv_new_files[0]  # Tomar el primer archivo CSV nuevo
                    break

                time.sleep(1)

            if new_file:
                # Renombrar el archivo descargado
                source_path = os.path.join(download_dir, new_file)
                target_path = os.path.join(download_dir, "casos_recientes.csv")

                # Eliminar archivo existente si existe
                if os.path.exists(target_path):
                    os.remove(target_path)

                # Renombrar
                os.rename(source_path, target_path)
                logger.info(f"*** CSV descargado para {departamento_info['nombre_display']}: casos_recientes.csv")

                self.guardar_en_base_datos(dept_key)
                return True
            else:
                # Verificar si ya existe el archivo con el nombre correcto
                target_path = os.path.join(download_dir, "casos_recientes.csv")
                if os.path.exists(target_path):
                    logger.info(f"*** CSV ya existe para {departamento_info['nombre_display']}: casos_recientes.csv")
                    return True
                else:
                    logger.warning(f"*** No se descargó CSV para {departamento_info['nombre_display']} - Timeout")
                    return False

        except TimeoutException:
            logger.error(f"*** Error descargando CSV para {departamento_info['nombre_display']}")
            return False

    def guardar_en_base_datos(self, dept_key):
        """
        Guarda los datos del CSV del departamento directamente en la base de datos
        sin crear archivos de texto intermedios.

        Args:
            dept_key: Clave del departamento (ej: 'Soporte_Tecnico')

        Returns:
            dict: Resumen de la operación con estadísticas
        """
        logger.info(f"*** Guardando datos de {dept_key} directamente en la base de datos...")

        # Crear contexto de aplicación Flask
        from app import create_app
        app = create_app()
        app.app_context().push()

        # Preparar resultado
        resultado = {
            "total_procesados": 0,
            "guardados_exitosamente": 0,
            "errores": 0,
            "detalles": []
        }

        # Obtener rutas de archivos
        archivos_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archivos")
        specific_dir = os.path.join(archivos_root, dept_key)
        csv_file = os.path.join(specific_dir, "casos_recientes.csv")

        # Verificación detallada del CSV
        logger.info(f"*** Verificando CSV en: {csv_file}")
        logger.info(f"*** El directorio existe: {os.path.exists(specific_dir)}")
        logger.info(f"*** El CSV existe: {os.path.exists(csv_file)}")

        # Verificar que existe el CSV
        if not os.path.exists(csv_file):
            error_msg = f"No se encontró el archivo CSV en {dept_key}"
            logger.error(f"*** {error_msg}")
            resultado["detalles"].append({"error": error_msg})

            # Verificar contenido del directorio
            logger.info(f"*** Contenido del directorio {specific_dir}:")
            try:
                dir_content = os.listdir(specific_dir)
                for item in dir_content:
                    logger.info(f"***   - {item}")
            except Exception as e:
                logger.error(f"*** Error al listar directorio: {str(e)}")

            return resultado

        try:
            # Verificar tamaño y contenido del CSV antes de procesarlo
            file_size = os.path.getsize(csv_file)
            logger.info(f"*** Tamaño del archivo CSV: {file_size} bytes")

            if file_size == 0:
                error_msg = f"El archivo CSV está vacío"
                logger.error(f"*** {error_msg}")
                resultado["detalles"].append({"error": error_msg})
                return resultado

            # Procesar CSV
            logger.info(f"*** Abriendo CSV para procesar...")
            with open(csv_file, newline="", encoding="latin-1") as csvfile:
                # Verificar primeras líneas del CSV
                logger.debug(f"*** Primeras líneas del CSV:")
                csvfile.seek(0)
                for i in range(3):
                    line = csvfile.readline().strip()
                    logger.debug(f"***   Línea {i+1}: {line}")

                # Volver al inicio del archivo
                csvfile.seek(0)

                # Intentar leer el CSV con DictReader
                logger.info(f"*** Intentando leer con DictReader (delimitador: ';')...")
                reader = csv.DictReader(csvfile, delimiter=";")

                # Verificar las columnas detectadas
                logger.info(f"*** Columnas detectadas: {reader.fieldnames}")

                # Procesar filas
                logger.info(f"*** Procesando filas del CSV...")
                row_count = 0

                for fila in reader:
                    row_count += 1
                    resultado["total_procesados"] += 1

                    try:
                        logger.debug(f"*** Procesando fila {row_count}: {str(fila)[:100]}...")
                        cliente = fila.get("Cliente", "").strip()
                        cliente_nombre = fila.get("Nombre", "").strip()  # Capturar nombre del cliente
                        asunto_original = fila.get("Asunto", "").strip()
                        fecha_creacion = fila.get("Fecha Creacion", "").strip()
                        prioridad_raw = fila.get("Prioridad", "").strip().lower()
                        contrato = fila.get("Contrato", "").strip()

                        logger.debug(f"***   Cliente: '{cliente}', Nombre: '{cliente_nombre}', Asunto: '{asunto_original}', Fecha: '{fecha_creacion}'")
                        logger.debug(f"***   Prioridad: '{prioridad_raw}', Contrato: '{contrato}'")

                        # Lógica para determinar el asunto basado en FO en el contrato
                        if "FO" in contrato.upper() or "FTTH" in contrato.upper():
                            asunto = "Ticket-FO"
                        else:
                            asunto = "Ticket-WIRELESS"

                        # Mapeo de prioridades
                        prioridad_map = {
                            "baja": "low",
                            "media": "medium",
                            "alta": "high",
                            "urgente": "urgent"
                        }
                        prioridad = prioridad_map.get(prioridad_raw, "medium")

                        logger.debug(f"***   Asunto final: '{asunto}', Prioridad final: '{prioridad}'")

                        # Solo procesar si hay cliente
                        if cliente:
                            # Crear objeto para la base de datos
                            incident_data = {
                                "Cliente": cliente,
                                "Cliente_Nombre": cliente_nombre,  # Agregar nombre del cliente
                                "Asunto": asunto,
                                "Fecha_Creacion": f"{fecha_creacion}",  # Usar True en lugar de la cadena de fecha
                                "Ticket_ID": "",  # Se llenará cuando se cree el ticket
                                "Estado": "PENDING",  # Estado inicial
                                "Prioridad": prioridad,
                                "is_created_splynx": False  # Inicialmente no creado
                            }

                            try:
                                # Guardar en la base de datos usando la interfaz
                                incident = IncidentsInterface.create(incident_data)

                                if incident:
                                    resultado["guardados_exitosamente"] += 1
                                    resultado["detalles"].append({
                                        "cliente": cliente,
                                        "asunto": asunto,
                                        "estado": "GUARDADO",
                                        "id": incident.id
                                    })
                                    logger.info(f"*** Guardado exitoso: {cliente} - {asunto}")
                                else:
                                    # Si incident es None, probablemente es un duplicado (ya manejado en IncidentsInterface)
                                    # No contar como error, solo como duplicado omitido
                                    logger.info(f"*** Ticket duplicado omitido: {cliente} - {asunto}")
                            except Exception as e:
                                # Solo errores reales (no IntegrityError que ya se maneja en IncidentsInterface)
                                resultado["errores"] += 1
                                resultado["detalles"].append({
                                    "cliente": cliente,
                                    "asunto": asunto,
                                    "estado": "ERROR",
                                    "error": f"Error creating incident: {str(e)}"
                                })
                                logger.error(f"Error creating incident: {str(e)}")
                                logger.error(f"*** Error al guardar: {cliente} - {asunto}")

                    except Exception as e:
                        resultado["errores"] += 1
                        resultado["detalles"].append({
                            "error": f"Error procesando fila: {str(e)}",
                            "fila": str(fila)
                        })
                        logger.error(f"*** Error procesando fila: {str(e)}")

            logger.info(f"*** Resumen: {resultado['guardados_exitosamente']} guardados de {resultado['total_procesados']} procesados")
            return resultado

        except Exception as e:
            logger.error(f"*** Error procesando datos: {str(e)}")
            resultado["detalles"].append({"error": f"Error general: {str(e)}"})
            return resultado

    def descargar_y_guardar_soporte_tecnico(self):
        """
        Descarga los datos de Soporte Técnico y los guarda en la base de datos

        Returns:
            dict: Resumen de la operación
        """
        dept_key = "Soporte_Tecnico"

        # Verificar directorios antes de comenzar
        archivos_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archivos")
        specific_dir = os.path.join(archivos_root, dept_key)
        csv_file = os.path.join(specific_dir, "casos_recientes.csv")

        logger.info(f"*** VERIFICACIÓN INICIAL ***")
        logger.info(f"*** Directorio de archivos: {specific_dir}")
        logger.info(f"*** Ruta del CSV esperado: {csv_file}")
        logger.info(f"*** El directorio existe: {os.path.exists(specific_dir)}")
        logger.info(f"*** El CSV existe antes de descargar: {os.path.exists(csv_file)}")

        # Paso 1: Descargar CSV
        logger.info(f"*** INICIANDO DESCARGA DEL CSV ***")
        descarga_exitosa = self.descargar_csv_departamento(dept_key)

        # Verificar después de la descarga
        logger.info(f"*** VERIFICACIÓN POST-DESCARGA ***")
        logger.info(f"*** Descarga reportada como exitosa: {descarga_exitosa}")
        logger.info(f"*** El CSV existe después de descargar: {os.path.exists(csv_file)}")

        if os.path.exists(csv_file):
            try:
                # Verificar tamaño y contenido del CSV
                file_size = os.path.getsize(csv_file)
                logger.info(f"*** Tamaño del archivo CSV: {file_size} bytes")

                # Leer primeras líneas para verificar contenido
                with open(csv_file, 'r', encoding='latin-1') as f:
                    first_lines = [next(f) for _ in range(3)]
                logger.info(f"*** Primeras líneas del CSV:")
                for i, line in enumerate(first_lines):
                    logger.info(f"***   Línea {i+1}: {line.strip()}")
            except Exception as e:
                logger.error(f"*** Error al verificar el CSV: {str(e)}")

        if not descarga_exitosa:
            return {
                "estado": "ERROR",
                "mensaje": "No se pudo descargar el CSV de Soporte Técnico",
                "db_guardado": False
            }

        # Paso 2: Guardar en la base de datos
        logger.info(f"*** INICIANDO GUARDADO EN BASE DE DATOS ***")
        resultado_db = self.guardar_en_base_datos(dept_key)

        return {
            "estado": "EXITOSO" if resultado_db["guardados_exitosamente"] > 0 else "ERROR",
            "mensaje": f"Se guardaron {resultado_db['guardados_exitosamente']} de {resultado_db['total_procesados']} registros",
            "db_guardado": resultado_db["guardados_exitosamente"] > 0,
            "detalles": resultado_db
        }
