#!/usr/bin/env python3
"""
Auditor de Configuración Neotel - VERSIÓN COMPLETA
Extrae DIDs, Extensiones y Colas con configuración detallada
"""

import json
import logging
import os
import sys
import time
import tempfile
import threading
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Importar módulos propios
from config_audit import ConfigAudit
from email_sender import EmailSender

try:
    import psutil
except ImportError:
    psutil = None

class NeotelConfigExtractor:
    """Extractor completo de configuración Neotel"""
    
    def __init__(self):
        """Inicializar el extractor"""
        self.logger = self._setup_logging()
        self.driver = None
        self.temp_dir = None
        self.email_sender = EmailSender(ConfigAudit.EMAIL_CONFIG)
        
        ConfigAudit.create_directories()
        
        if not ConfigAudit.validate_config():
            raise Exception("Error en la configuración")
        
        self.logger.info("=" * 80)
        self.logger.info("🔍 AUDITOR DE CONFIGURACIÓN NEOTEL - VERSIÓN COMPLETA")
        self.logger.info("=" * 80)
    
    def select_chosen_option_by_text(self, select_id, option_text):
        """
        Seleccionar una opción en un dropdown de Chosen.js por su texto
        
        Args:
            select_id: ID del select original (sin #)
            option_text: Texto de la opción a seleccionar
        """
        try:
            chosen_container_id = f"{select_id}_chosen"
            
            wait = WebDriverWait(self.driver, 10)
            chosen_container = wait.until(
                EC.presence_of_element_located((By.ID, chosen_container_id))
            )
            
            # Scroll hacia arriba para evitar el header
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # Scroll al contenedor
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_container)
            time.sleep(0.5)
            
            # Buscar y hacer click en el enlace
            chosen_link = chosen_container.find_element(By.CSS_SELECTOR, 'a.chosen-single')
            
            try:
                chosen_link.click()
            except:
                self.driver.execute_script("arguments[0].click();", chosen_link)
            
            time.sleep(1)
            
            # Buscar la opción en el dropdown
            dropdown = chosen_container.find_element(By.CSS_SELECTOR, 'ul.chosen-results')
            options = dropdown.find_elements(By.TAG_NAME, 'li')
            
            for option in options:
                if option.text.strip() == option_text:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", option)
                    time.sleep(0.3)
                    
                    try:
                        option.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", option)
                    
                    time.sleep(1)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"    Error seleccionando opción en Chosen: {str(e)}")
            return False

    def click_view_button(self, button_id):
        """
        Hacer click en el botón "Ver"
        
        Args:
            button_id: ID del botón (sin #)
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            button = wait.until(
                EC.element_to_be_clickable((By.ID, button_id))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)
            
            try:
                button.click()
            except:
                self.driver.execute_script("arguments[0].click();", button)
            
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"    Error haciendo click en botón Ver: {str(e)}")
            return False

    def _setup_logging(self):
        """Configurar logging"""
        log_file = ConfigAudit.get_log_filename()
        
        logging.basicConfig(
            level=getattr(logging, ConfigAudit.LOG_LEVEL),
            format=ConfigAudit.LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return logging.getLogger(__name__)
    
    def setup_driver(self):
        """Configurar Chrome WebDriver"""
        try:
            self.logger.info("⚙️  Configurando Chrome WebDriver...")
            
            self._apply_chrome_fixes()
            
            chrome_options = Options()
            
            temp_dir = self._create_ultra_unique_dir()
            if temp_dir:
                self.temp_dir = temp_dir
                chrome_options.add_argument(f'--user-data-dir={self.temp_dir}')
            
            if ConfigAudit.HEADLESS_BROWSER:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            
            prefs = {
                "download.default_directory": str(ConfigAudit.DOWNLOAD_DIR),
                "download.prompt_for_download": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    service = Service()
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.driver.implicitly_wait(10)
                    
                    self.logger.info(f"✅ Chrome WebDriver creado (intento {attempt + 1})")
                    break
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        self._cleanup_failed_attempt()
                        time.sleep(5)
                        temp_dir = self._create_ultra_unique_dir()
                        if temp_dir:
                            self.temp_dir = temp_dir
                    else:
                        raise retry_error
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando driver: {str(e)}")
            raise
    
    def _apply_chrome_fixes(self):
        """Aplicar fixes preventivos"""
        try:
            self._kill_chrome_processes()
            self._clean_temp_directories()
            time.sleep(2)
        except Exception as e:
            self.logger.warning(f"⚠️  Error aplicando fixes: {str(e)}")
    
    def _kill_chrome_processes(self):
        """Eliminar procesos Chrome existentes"""
        if not psutil:
            return
        try:
            killed_count = 0
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if 'chrome' in process.info['name'].lower():
                        process.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed_count > 0:
                time.sleep(3)
        except:
            pass
    
    def _clean_temp_directories(self):
        """Limpiar directorios temporales"""
        try:
            temp_base = Path(tempfile.gettempdir())
            patterns = ['chrome_movimer_*', 'chrome_selenium_*', 'scoped_dir*']
            for pattern in patterns:
                for old_dir in temp_base.glob(pattern):
                    try:
                        if old_dir.is_dir():
                            shutil.rmtree(old_dir, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def _create_ultra_unique_dir(self):
        """Crear directorio único para Chrome"""
        try:
            timestamp = int(time.time() * 1000)
            unique_id = str(uuid.uuid4()).replace('-', '')[:12]
            process_id = os.getpid()
            
            dir_name = f"chrome_movimer_{timestamp}_{unique_id}_{process_id}"
            temp_dir = Path(tempfile.gettempdir()) / dir_name
            
            temp_dir.mkdir(parents=True, exist_ok=False)
            if os.name != 'nt':
                os.chmod(temp_dir, 0o700)
            
            return temp_dir
        except:
            return None
    
    def _cleanup_failed_attempt(self):
        """Limpiar después de intento fallido"""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self._kill_chrome_processes()
        except:
            pass
    
    def login_to_neotel(self):
        """Realizar login en Neotel"""
        try:
            self.logger.info("🔐 Iniciando login en Neotel...")
            
            self.driver.get(ConfigAudit.LOGIN_URL)
            wait = WebDriverWait(self.driver, ConfigAudit.PAGE_LOAD_TIMEOUT)
            
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['username_field']))
            )
            password_field = self.driver.find_element(By.CSS_SELECTOR, ConfigAudit.SELECTORES['password_field'])
            
            username_field.clear()
            username_field.send_keys(ConfigAudit.NEOTEL_USERNAME)
            
            password_field.clear()
            password_field.send_keys(ConfigAudit.NEOTEL_PASSWORD)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, ConfigAudit.SELECTORES['login_button'])
            login_button.click()
            
            wait.until(lambda driver: "pbx.neotel2000.com" in driver.current_url and "auth" not in driver.current_url)
            
            self.logger.info("✅ Login completado exitosamente")
            time.sleep(5)
            
        except Exception as e:
            self.logger.error(f"❌ Error durante el login: {str(e)}")
            raise
    
    def click_menu_item(self, text, wait_time=3):
        """Buscar y hacer click en elemento del menú"""
        try:
            selectors = [
                f"//a[contains(text(), '{text}')]",
                f"//div[contains(text(), '{text}')]",
                f"//span[contains(text(), '{text}')]",
                f"//*[contains(text(), '{text}')]"
            ]
            
            element = None
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                element = elem
                                break
                        except:
                            continue
                    if element:
                        break
                except:
                    continue
            
            if not element:
                return False
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            try:
                element.click()
            except:
                self.driver.execute_script("arguments[0].click();", element)
            
            time.sleep(wait_time)
            return True
            
        except:
            return False
        
    def extract_extensions(self):
        """
        Extraer configuración de extensiones
        Retorna: Lista de diccionarios con info de extensiones
        """
        try:
            self.logger.info("📞 Extrayendo configuración de extensiones...")
            
            # Navegar con clicks en menú
            self.click_menu_item("Configuración", wait_time=2)
            self.click_menu_item("Extensiones", wait_time=3)
            
            time.sleep(15)  # Esperar carga de tabla
            
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.table')))
            
            extensions = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, ConfigAudit.SELECTORES['extensions_table'])
            
            self.logger.info(f"📊 Encontradas {len(rows)} extensiones")
            
            for idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    
                    if len(cells) < 10:
                        continue
                    
                    extension_code = cells[0].text.strip()
                    name = cells[1].text.strip()
                    group = cells[2].text.strip()
                    agente_asignado = cells[3].text.strip()  # ⭐ NUEVO CAMPO
                    numero_saliente = cells[4].text.strip()
                    
                    # Detectar estado de colas mirando las CLASES CSS de los botones
                    action_cell = cells[9]
                    
                    # Buscar botones por ID
                    reanudar_habilitado = False
                    pausar_habilitado = False
                    
                    try:
                        # Buscar botón de Reanudar
                        reanudar_button = action_cell.find_element(By.ID, f'play_queue_{extension_code}')
                        button_classes = reanudar_button.get_attribute('class')
                        # Habilitado = tiene clase 'btn-success' (verde)
                        reanudar_habilitado = 'btn-success' in button_classes
                    except:
                        pass
                    
                    try:
                        # Buscar botón de Pausar
                        pausar_button = action_cell.find_element(By.ID, f'pause_queue_{extension_code}')
                        button_classes = pausar_button.get_attribute('class')
                        # Habilitado = tiene clase 'btn-danger' (rojo)
                        pausar_habilitado = 'btn-danger' in button_classes
                    except:
                        pass
                    
                    # Determinar estado según combinación de botones
                    if reanudar_habilitado and pausar_habilitado:
                        queue_status = "mixto"
                    elif reanudar_habilitado and not pausar_habilitado:
                        queue_status = "todas_pausadas"
                    elif not reanudar_habilitado and pausar_habilitado:
                        queue_status = "todas_activas"
                    else:
                        queue_status = "sin_colas"
                    
                    extension = {
                        'extension': extension_code,
                        'nombre': name,
                        'grupo': group,
                        'agente_asignado': agente_asignado,  # ⭐ NUEVO CAMPO
                        'numero_saliente': numero_saliente,
                        'estado_colas': queue_status
                    }
                    
                    extensions.append(extension)
                    
                    # Log cada 20 extensiones
                    if (idx + 1) % 20 == 0:
                        self.logger.info(f"  Procesadas {idx + 1}/{len(rows)} extensiones...")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando extensión en fila {idx + 1}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Extraídas {len(extensions)} extensiones")
            return extensions
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo extensiones: {str(e)}")
            raise

    def extract_dids(self):
        """
        Extraer configuración completa de DIDs
        Incluye locución y acciones 1–5
        """
        try:
            self.logger.info("📱 Extrayendo configuración detallada de DIDs...")

            # Navegar a sección de DIDs
            for did_text in ["DIDs", "DID", "dids"]:
                if self.click_menu_item(did_text, wait_time=3):
                    self.logger.info(f"✅ Navegación a {did_text}")
                    break

            time.sleep(10)

            dids = []

            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            
            self.logger.info(f"🔍 Buscando select: {ConfigAudit.SELECTORES['dids_select']}")
            
            try:
                select_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['dids_select']))
                )
                self.logger.info("✅ Select de DIDs encontrado")
            except TimeoutException:
                self.logger.error(f"❌ TIMEOUT buscando select de DIDs")
                self.logger.error(f"   URL actual: {self.driver.current_url}")
                self.logger.error(f"   Título: {self.driver.title}")
                raise
            
            select = Select(select_element)
            options = select.options

            self.logger.info(f"📊 Encontrados {len(options)} DIDs en el selector")

            for idx, option in enumerate(options):
                try:
                    did_numero = option.text.strip() or option.get_attribute('textContent').strip()
                    did_id_interno = option.get_attribute('value')

                    if not did_numero or not did_id_interno:
                        continue

                    # USAR CHOSEN.JS en lugar de select.select_by_value()
                    if not self.select_chosen_option_by_text('configuration_dids_view_did_list_dids', did_numero):
                        self.logger.warning(f"  ⚠️  No se pudo seleccionar DID {did_numero}")
                        continue
                    
                    # HACER CLICK EN BOTÓN "VER"
                    if not self.click_view_button('configuration_dids_view_did_list_button_view'):
                        self.logger.warning(f"  ⚠️  No se pudo hacer click en botón Ver para DID {did_numero}")
                        continue

                    # Esperar a que cargue el panel de detalle
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['did_detail_panel']))
                    )

                    def safe_get_text(selector, field_name="campo"):
                        try:
                            el = self.driver.find_element(By.CSS_SELECTOR, selector)
                            text = el.text.strip()
                            if not text:
                                try:
                                    text = el.find_element(By.TAG_NAME, 'i').text.strip()
                                except:
                                    pass
                            return text if text else "N/D"
                        except:
                            return "N/D"

                    # Extraer campos del panel de detalle
                    locucion = safe_get_text(ConfigAudit.SELECTORES['did_locucion'], 'Locución')
                    accion1 = safe_get_text(ConfigAudit.SELECTORES['did_accion1'], 'Acción 1')
                    accion2 = safe_get_text(ConfigAudit.SELECTORES['did_accion2'], 'Acción 2')
                    accion3 = safe_get_text(ConfigAudit.SELECTORES['did_accion3'], 'Acción 3')
                    accion4 = safe_get_text(ConfigAudit.SELECTORES['did_accion4'], 'Acción 4')
                    accion5 = safe_get_text(ConfigAudit.SELECTORES['did_accion5'], 'Acción 5')

                    did = {
                        'numero': did_numero,
                        'id_interno': did_id_interno,
                        'locucion': locucion,
                        'accion1': accion1,
                        'accion2': accion2,
                        'accion3': accion3,
                        'accion4': accion4,
                        'accion5': accion5,
                    }
                    dids.append(did)

                    # Log cada 20 DIDs
                    if (idx + 1) % 20 == 0:
                        self.logger.info(f"  Procesados {idx + 1}/{len(options)} DIDs...")
                    
                    # Cerrar modal con ESC
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(1)
                    except:
                        pass

                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando DID en índice {idx + 1}: {str(e)}")
                    # Intentar cerrar modal antes de continuar
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass
                    continue

            self.logger.info(f"✅ Extraídos {len(dids)} DIDs con configuración detallada")
            return dids

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo DIDs: {str(e)}")
            import traceback
            self.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            raise

    def extract_colas(self):
        """
        Extraer configuración completa de colas y miembros
        Incluye número de extensión y estado (activo/pausado)
        """
        try:
            self.logger.info("📋 Extrayendo configuración detallada de colas...")

            # Navegar a sección de Colas
            for cola_text in ["Colas", "Cola"]:
                if self.click_menu_item(cola_text, wait_time=3):
                    self.logger.info(f"✅ Navegación a {cola_text}")
                    break

            time.sleep(10)

            colas = []

            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            
            select_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['colas_select']))
            )
            self.logger.info("✅ Select de Colas encontrado")
            
            select = Select(select_element)
            options = select.options

            self.logger.info(f"📊 Encontradas {len(options)} colas en el selector")

            for idx, option in enumerate(options):
                try:
                    cola_nombre = option.text.strip() or option.get_attribute('textContent').strip()
                    cola_id_interno = option.get_attribute('value')

                    if not cola_nombre or not cola_id_interno:
                        continue

                    # Asegurar que no hay modales abiertos
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Scroll hacia arriba
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)

                    # USAR CHOSEN.JS para seleccionar
                    if not self.select_chosen_option_by_text('configuration_queues_view_queue_list_queues', cola_nombre):
                        self.logger.warning(f"  ⚠️  No se pudo seleccionar cola {cola_nombre}")
                        continue
                    
                    # HACER CLICK EN BOTÓN "VER"
                    if not self.click_view_button('configuration_queues_view_queue_list_button_view'):
                        self.logger.warning(f"  ⚠️  No se pudo hacer click en botón Ver para cola {cola_nombre}")
                        continue
                    
                    time.sleep(2)

                    # Esperar el detalle
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['colas_detalle']))
                    )

                    # Buscar miembros
                    miembros = []
                    try:
                        miembros_container = self.driver.find_element(By.CSS_SELECTOR, ConfigAudit.SELECTORES['colas_miembros'])
                        miembros_divs = miembros_container.find_elements(By.CSS_SELECTOR, 'div[data-extension]')

                        for div in miembros_divs:
                            try:
                                ext = div.get_attribute('data-extension')
                                texto = div.text.strip()

                                estado = "desconocido"
                                try:
                                    svg = div.find_element(By.TAG_NAME, 'svg')
                                    svg_class = svg.get_attribute('class')
                                    if 'fa-play' in svg_class:
                                        estado = "activo"
                                    elif 'fa-pause' in svg_class:
                                        estado = "pausado"
                                except:
                                    pass

                                miembros.append({
                                    'extension': ext,
                                    'texto': texto,
                                    'estado': estado
                                })
                            except:
                                continue
                    except:
                        pass

                    colas.append({
                        'nombre': cola_nombre,
                        'id_interno': cola_id_interno,
                        'miembros': miembros
                    })

                    # Log cada 10 colas
                    if (idx + 1) % 10 == 0:
                        self.logger.info(f"  Procesadas {idx + 1}/{len(options)} colas...")
                    
                    # Cerrar modal con ESC
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass

                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando cola en índice {idx + 1}: {str(e)}")
                    # Intentar cerrar modales
                    try:
                        for _ in range(3):
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                            time.sleep(0.3)
                    except:
                        pass
                    continue

            self.logger.info(f"✅ Extraídas {len(colas)} colas con sus miembros")
            return colas

        except Exception as e:
            self.logger.error(f"❌ Error extrayendo colas: {str(e)}")
            raise

    def save_snapshot(self, config_data, date=None):
        """Guardar snapshot de configuración"""
        try:
            snapshot_file = ConfigAudit.get_snapshot_filename(date)
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'date': (date or datetime.now().date()).isoformat(),
                'config': config_data
            }
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"💾 Snapshot guardado: {snapshot_file}")
            return snapshot_file
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando snapshot: {str(e)}")
            raise
    
    def load_snapshot(self, date):
        """Cargar snapshot de una fecha específica"""
        try:
            snapshot_file = ConfigAudit.get_snapshot_filename(date)
            
            if not snapshot_file.exists():
                return None
            
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)
            
            return snapshot.get('config')
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error cargando snapshot de {date}: {str(e)}")
            return None
    
    def compare_configs(self, current_config, previous_config):
        """Comparar dos configuraciones y detectar cambios"""
        if previous_config is None:
            self.logger.info("ℹ️  No hay configuración anterior para comparar")
            return {
                'has_changes': False,
                'is_first_run': True,
                'message': 'Primera ejecución - no hay datos previos'
            }
        
        self.logger.info("🔍 Comparando configuraciones...")
        
        changes = {
            'has_changes': False,
            'is_first_run': False,
            'dids_added': [],
            'dids_removed': [],
            'dids_modified': [],
            'extensions_added': [],
            'extensions_removed': [],
            'extensions_modified': [],
            'colas_added': [],
            'colas_removed': [],
            'colas_modified': []
        }
        
        # Comparar DIDs
        current_dids = {d['numero']: d for d in current_config.get('dids', [])}
        previous_dids = {d['numero']: d for d in previous_config.get('dids', [])}
        
        for did_num, did_data in current_dids.items():
            if did_num not in previous_dids:
                changes['dids_added'].append(did_data)
            elif did_data != previous_dids[did_num]:
                changes['dids_modified'].append({
                    'numero': did_num,
                    'anterior': previous_dids[did_num],
                    'actual': did_data
                })
        
        for did_num in previous_dids:
            if did_num not in current_dids:
                changes['dids_removed'].append(previous_dids[did_num])
        
        # Comparar Extensiones
        current_exts = {e['extension']: e for e in current_config.get('extensiones', [])}
        previous_exts = {e['extension']: e for e in previous_config.get('extensiones', [])}
        
        for ext_num, ext_data in current_exts.items():
            if ext_num not in previous_exts:
                changes['extensions_added'].append(ext_data)
            elif ext_data != previous_exts[ext_num]:
                changes['extensions_modified'].append({
                    'extension': ext_num,
                    'anterior': previous_exts[ext_num],
                    'actual': ext_data
                })
        
        for ext_num in previous_exts:
            if ext_num not in current_exts:
                changes['extensions_removed'].append(previous_exts[ext_num])
        
        # Comparar Colas
        current_colas = {c['nombre']: c for c in current_config.get('colas', [])}
        previous_colas = {c['nombre']: c for c in previous_config.get('colas', [])}
        
        for cola_name, cola_data in current_colas.items():
            if cola_name not in previous_colas:
                changes['colas_added'].append(cola_data)
            elif cola_data != previous_colas[cola_name]:
                changes['colas_modified'].append({
                    'nombre': cola_name,
                    'anterior': previous_colas[cola_name],
                    'actual': cola_data
                })
        
        for cola_name in previous_colas:
            if cola_name not in current_colas:
                changes['colas_removed'].append(previous_colas[cola_name])
        
        # Determinar si hay cambios
        changes['has_changes'] = any([
            changes['dids_added'],
            changes['dids_removed'],
            changes['dids_modified'],
            changes['extensions_added'],
            changes['extensions_removed'],
            changes['extensions_modified'],
            changes['colas_added'],
            changes['colas_removed'],
            changes['colas_modified']
        ])
        
        if changes['has_changes']:
            total = sum([
                len(changes['dids_added']),
                len(changes['dids_removed']),
                len(changes['dids_modified']),
                len(changes['extensions_added']),
                len(changes['extensions_removed']),
                len(changes['extensions_modified']),
                len(changes['colas_added']),
                len(changes['colas_removed']),
                len(changes['colas_modified'])
            ])
            self.logger.info(f"⚠️  CAMBIOS DETECTADOS: {total} modificaciones")
        else:
            self.logger.info("✅ No se detectaron cambios")
        
        return changes
    
    def generate_html_report(self, changes, report_date):
        """Generar reporte HTML profesional con cambios"""
        try:
            report_file = ConfigAudit.get_report_filename(report_date)
            
            # Calcular totales
            total_changes = sum([
                len(changes.get('dids_added', [])),
                len(changes.get('dids_removed', [])),
                len(changes.get('dids_modified', [])),
                len(changes.get('extensions_added', [])),
                len(changes.get('extensions_removed', [])),
                len(changes.get('extensions_modified', [])),
                len(changes.get('colas_added', [])),
                len(changes.get('colas_removed', [])),
                len(changes.get('colas_modified', []))
            ])
            
            html = f"""<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Cambios - Neotel</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            :root {{
                --primary: #2c3e50;
                --accent: #3498db;
                --success: #27ae60;
                --warning: #f39c12;
                --danger: #e74c3c;
                --background: #f8f9fa;
                --surface: #ffffff;
                --border: #dee2e6;
                --text-primary: #2c3e50;
                --text-secondary: #7f8c8d;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: var(--background);
                padding: 20px;
                color: var(--text-primary);
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: var(--surface);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            /* Header */
            .header {{
                background: var(--primary);
                color: white;
                padding: 30px 40px;
                border-bottom: 3px solid var(--accent);
            }}
            
            .header h1 {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            
            .header .date {{
                font-size: 14px;
                opacity: 0.9;
            }}
            
            /* Summary Box */
            .summary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 40px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}
            
            .summary-card {{
                text-align: center;
            }}
            
            .summary-card .number {{
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            .summary-card .label {{
                font-size: 12px;
                text-transform: uppercase;
                opacity: 0.9;
                letter-spacing: 0.5px;
            }}
            
            /* Tabs */
            .tabs {{
                display: flex;
                background: var(--surface);
                border-bottom: 1px solid var(--border);
                padding: 0 40px;
                gap: 8px;
                overflow-x: auto;
            }}
            
            .tab {{
                padding: 14px 20px;
                background: transparent;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
                border-bottom: 2px solid transparent;
                white-space: nowrap;
            }}
            
            .tab:hover {{
                color: var(--primary);
                background: rgba(52, 73, 94, 0.04);
            }}
            
            .tab.active {{
                color: var(--primary);
                border-bottom-color: var(--accent);
            }}
            
            /* Content */
            .content {{
                padding: 40px;
            }}
            
            .tab-content {{
                display: none;
            }}
            
            .tab-content.active {{
                display: block;
                animation: fadeIn 0.2s ease;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(4px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            /* Change Sections */
            .change-section {{
                margin-bottom: 30px;
            }}
            
            .change-section h3 {{
                font-size: 16px;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 15px;
                padding-left: 10px;
                border-left: 4px solid var(--primary);
            }}
            
            .change-section.added h3 {{
                border-left-color: var(--success);
                color: var(--success);
            }}
            
            .change-section.removed h3 {{
                border-left-color: var(--danger);
                color: var(--danger);
            }}
            
            .change-section.modified h3 {{
                border-left-color: var(--warning);
                color: var(--warning);
            }}
            
            .change-list {{
                list-style: none;
            }}
            
            .change-item {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 10px;
                transition: box-shadow 0.2s ease;
            }}
            
            .change-item:hover {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            .change-item.added {{
                border-left: 3px solid var(--success);
                background: #f0f9f4;
            }}
            
            .change-item.removed {{
                border-left: 3px solid var(--danger);
                background: #fef3f2;
            }}
            
            .change-item.modified {{
                border-left: 3px solid var(--warning);
                background: #fefbf3;
            }}
            
            .change-item-header {{
                font-weight: 600;
                font-size: 14px;
                color: var(--text-primary);
                margin-bottom: 8px;
            }}
            
            .change-item-details {{
                font-size: 13px;
                color: var(--text-secondary);
                line-height: 1.6;
            }}
            
            .change-detail {{
                display: flex;
                align-items: center;
                margin: 5px 0;
                gap: 8px;
            }}
            
            .change-detail .field {{
                font-weight: 500;
                color: var(--text-primary);
                min-width: 120px;
            }}
            
            .change-detail .arrow {{
                color: var(--warning);
                font-weight: bold;
            }}
            
            .change-detail .value {{
                color: var(--text-secondary);
            }}
            
            .change-detail .value.old {{
                text-decoration: line-through;
                opacity: 0.7;
            }}
            
            .change-detail .value.new {{
                color: var(--success);
                font-weight: 500;
            }}
            
            .empty-state {{
                text-align: center;
                padding: 40px;
                color: var(--text-secondary);
            }}
            
            .empty-state .icon {{
                font-size: 48px;
                margin-bottom: 10px;
                opacity: 0.3;
            }}
            
            /* No changes message */
            .no-changes {{
                background: #e8f5e9;
                border: 1px solid #c8e6c9;
                border-radius: 6px;
                padding: 20px;
                text-align: center;
                color: #2e7d32;
            }}
            
            .no-changes .icon {{
                font-size: 32px;
                margin-bottom: 10px;
            }}
            
            /* Footer */
            .footer {{
                background: var(--background);
                padding: 20px 40px;
                text-align: center;
                font-size: 12px;
                color: var(--text-secondary);
                border-top: 1px solid var(--border);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>🔍 Reporte de Cambios - Configuración Neotel</h1>
                <div class="date">
                    📅 {report_date.strftime('%d/%m/%Y')} | 
                    🕐 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            
            <!-- Summary -->
            <div class="summary">
                <div class="summary-card">
                    <div class="number">{total_changes}</div>
                    <div class="label">Cambios Totales</div>
                </div>
                <div class="summary-card">
                    <div class="number">{len(changes.get('extensions_added', [])) + len(changes.get('extensions_removed', [])) + len(changes.get('extensions_modified', []))}</div>
                    <div class="label">📞 Extensiones</div>
                </div>
                <div class="summary-card">
                    <div class="number">{len(changes.get('dids_added', [])) + len(changes.get('dids_removed', [])) + len(changes.get('dids_modified', []))}</div>
                    <div class="label">📱 DIDs</div>
                </div>
                <div class="summary-card">
                    <div class="number">{len(changes.get('colas_added', [])) + len(changes.get('colas_removed', [])) + len(changes.get('colas_modified', []))}</div>
                    <div class="label">📋 Colas</div>
                </div>
            </div>
            
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" onclick="showTab('extensiones')">📞 Extensiones</button>
                <button class="tab" onclick="showTab('dids')">📱 DIDs</button>
                <button class="tab" onclick="showTab('colas')">📋 Colas</button>
            </div>
            
            <!-- Content -->
            <div class="content">
                <!-- Extensiones Tab -->
                <div id="extensiones" class="tab-content active">
                    {self._generate_extensions_changes_html(changes)}
                </div>
                
                <!-- DIDs Tab -->
                <div id="dids" class="tab-content">
                    {self._generate_dids_changes_html(changes)}
                </div>
                
                <!-- Colas Tab -->
                <div id="colas" class="tab-content">
                    {self._generate_colas_changes_html(changes)}
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                Reporte automático generado por el Sistema de Auditoría Neotel
            </div>
        </div>
        
        <script>
            function showTab(tabName) {{
                // Hide all tabs
                const tabs = document.querySelectorAll('.tab-content');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Remove active from buttons
                const buttons = document.querySelectorAll('.tab');
                buttons.forEach(btn => btn.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(tabName).classList.add('active');
                
                // Activate button
                event.target.classList.add('active');
            }}
        </script>
    </body>
    </html>"""
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"✅ Reporte HTML generado: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte HTML: {str(e)}")
            return None

    def _generate_changes_html(self, items, title, change_type):
        """Helper para generar HTML de cambios"""
        if not items:
            return ""
        
        html = f'<div class="change {change_type}"><h4>{title} ({len(items)})</h4><ul>'
        for item in items[:20]:  # Máximo 20 por tipo
            # Convertir dict a string legible
            item_str = str(item) if not isinstance(item, dict) else ', '.join([f"{k}: {v}" for k, v in list(item.items())[:3]])
            html += f'<li>{item_str}</li>'
        if len(items) > 20:
            html += f'<li>... y {len(items) - 20} más</li>'
        html += '</ul></div>'
        return html
    
    def cleanup_old_snapshots(self):
        """Limpiar snapshots antiguos"""
        try:
            self.logger.info(f"🧹 Limpiando snapshots antiguos (>{ConfigAudit.RETENTION_DAYS} días)...")
            
            cutoff_date = datetime.now() - timedelta(days=ConfigAudit.RETENTION_DAYS)
            deleted_count = 0
            
            for snapshot_file in ConfigAudit.SNAPSHOTS_DIR.glob("*.json"):
                try:
                    date_str = snapshot_file.stem.split('_')[0]
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        snapshot_file.unlink()
                        deleted_count += 1
                
                except:
                    continue
            
            if deleted_count > 0:
                self.logger.info(f"✅ Eliminados {deleted_count} snapshots antiguos")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error limpiando snapshots: {str(e)}")
    
    def run_audit(self):
        """Ejecutar auditoría completa"""
        try:
            audit_date = datetime.now().date()
            previous_date = audit_date - timedelta(days=1)
            
            self.logger.info(f"📅 Fecha de auditoría: {audit_date}")
            
            # Setup
            self.setup_driver()
            self.login_to_neotel()
            
            # Extraer configuración
            self.logger.info("=" * 80)
            self.logger.info("📥 EXTRAYENDO CONFIGURACIÓN ACTUAL")
            self.logger.info("=" * 80)
            
            current_config = {
                'extensiones': self.extract_extensions(),
                'dids': self.extract_dids(),
                'colas': self.extract_colas()
            }
            
            # Guardar snapshot
            self.save_snapshot(current_config, audit_date)
            
            # Cargar snapshot anterior
            previous_config = self.load_snapshot(previous_date)
            
            # Comparar
            self.logger.info("=" * 80)
            self.logger.info("🔍 COMPARANDO CONFIGURACIONES")
            self.logger.info("=" * 80)
            
            changes = self.compare_configs(current_config, previous_config)
            
            # Generar reporte y enviar email
            if changes.get('is_first_run'):
                self.logger.info("ℹ️  Primera ejecución - no se envía email")
            elif changes.get('has_changes'):
                report_file = self.generate_html_report(changes, audit_date)
                self.email_sender.send_change_report(report_file, changes, audit_date)
            else:
                self.email_sender.send_no_changes_notification(audit_date)
            
            # Limpieza
            self.cleanup_old_snapshots()
            
            self.logger.info("=" * 80)
            self.logger.info("✅ AUDITORÍA COMPLETADA EXITOSAMENTE")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ Error durante la auditoría: {str(e)}")
            self.email_sender.send_error_notification(str(e))
            raise
        finally:
            self.cleanup()
    
    def _generate_extensions_changes_html(self, changes):
        """Generar HTML de cambios en extensiones"""
        html = []
        
        # Añadidas
        if changes.get('extensions_added'):
            html.append('<div class="change-section added">')
            html.append(f'<h3>✅ AÑADIDAS ({len(changes["extensions_added"])})</h3>')
            html.append('<ul class="change-list">')
            for ext in changes['extensions_added']:
                html.append(f'''
                    <li class="change-item added">
                        <div class="change-item-header">📞 {ext.get("extension", "")} - {ext.get("nombre", "")}</div>
                        <div class="change-item-details">
                            Grupo: {ext.get("grupo", "-")} | 
                            Agente: {ext.get("agente_asignado", "-")} | 
                            Estado: {ext.get("estado_colas", "").replace("_", " ").title()}
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Eliminadas
        if changes.get('extensions_removed'):
            html.append('<div class="change-section removed">')
            html.append(f'<h3>❌ ELIMINADAS ({len(changes["extensions_removed"])})</h3>')
            html.append('<ul class="change-list">')
            for ext in changes['extensions_removed']:
                html.append(f'''
                    <li class="change-item removed">
                        <div class="change-item-header">📞 {ext.get("extension", "")} - {ext.get("nombre", "")}</div>
                        <div class="change-item-details">
                            Grupo: {ext.get("grupo", "-")} | 
                            Agente: {ext.get("agente_asignado", "-")}
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Modificadas
        if changes.get('extensions_modified'):
            html.append('<div class="change-section modified">')
            html.append(f'<h3>🔄 MODIFICADAS ({len(changes["extensions_modified"])})</h3>')
            html.append('<ul class="change-list">')
            for change in changes['extensions_modified']:
                ext_code = change.get('extension', '')
                anterior = change.get('anterior', {})
                actual = change.get('actual', {})
                
                html.append(f'''
                    <li class="change-item modified">
                        <div class="change-item-header">📞 {ext_code} - {actual.get("nombre", "")}</div>
                        <div class="change-item-details">
                ''')
                
                # Detectar qué cambió
                if anterior.get('nombre') != actual.get('nombre'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Nombre:</span>
                            <span class="value old">{anterior.get('nombre', '-')}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('nombre', '-')}</span>
                        </div>
                    ''')
                
                if anterior.get('grupo') != actual.get('grupo'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Grupo:</span>
                            <span class="value old">{anterior.get('grupo', '-')}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('grupo', '-')}</span>
                        </div>
                    ''')
                
                if anterior.get('agente_asignado') != actual.get('agente_asignado'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Agente:</span>
                            <span class="value old">{anterior.get('agente_asignado', '-')}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('agente_asignado', '-')}</span>
                        </div>
                    ''')
                
                if anterior.get('numero_saliente') != actual.get('numero_saliente'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Nº Saliente:</span>
                            <span class="value old">{anterior.get('numero_saliente', '-')}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('numero_saliente', '-')}</span>
                        </div>
                    ''')
                
                if anterior.get('estado_colas') != actual.get('estado_colas'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Estado Colas:</span>
                            <span class="value old">{anterior.get('estado_colas', '').replace('_', ' ').title()}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('estado_colas', '').replace('_', ' ').title()}</span>
                        </div>
                    ''')
                
                html.append('</div></li>')
            html.append('</ul></div>')
        
        # Sin cambios
        if not any([changes.get('extensions_added'), changes.get('extensions_removed'), changes.get('extensions_modified')]):
            html.append('<div class="no-changes"><div class="icon">✅</div><div>No hay cambios en extensiones</div></div>')
        
        return '\n'.join(html)

    def _generate_dids_changes_html(self, changes):
        """Generar HTML de cambios en DIDs"""
        html = []
        
        # Añadidos
        if changes.get('dids_added'):
            html.append('<div class="change-section added">')
            html.append(f'<h3>✅ AÑADIDOS ({len(changes["dids_added"])})</h3>')
            html.append('<ul class="change-list">')
            for did in changes['dids_added']:
                html.append(f'''
                    <li class="change-item added">
                        <div class="change-item-header">📱 {did.get("numero", "")}</div>
                        <div class="change-item-details">
                            Locución: {did.get("locucion", "-")} | 
                            Acción 1: {did.get("accion1", "-")[:50]}...
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Eliminados
        if changes.get('dids_removed'):
            html.append('<div class="change-section removed">')
            html.append(f'<h3>❌ ELIMINADOS ({len(changes["dids_removed"])})</h3>')
            html.append('<ul class="change-list">')
            for did in changes['dids_removed']:
                html.append(f'''
                    <li class="change-item removed">
                        <div class="change-item-header">📱 {did.get("numero", "")}</div>
                        <div class="change-item-details">
                            Locución: {did.get("locucion", "-")}
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Modificados
        if changes.get('dids_modified'):
            html.append('<div class="change-section modified">')
            html.append(f'<h3>🔄 MODIFICADOS ({len(changes["dids_modified"])})</h3>')
            html.append('<ul class="change-list">')
            for change in changes['dids_modified']:
                did_num = change.get('numero', '')
                anterior = change.get('anterior', {})
                actual = change.get('actual', {})
                
                html.append(f'''
                    <li class="change-item modified">
                        <div class="change-item-header">📱 {did_num}</div>
                        <div class="change-item-details">
                ''')
                
                # Detectar cambios
                if anterior.get('locucion') != actual.get('locucion'):
                    html.append(f'''
                        <div class="change-detail">
                            <span class="field">Locución:</span>
                            <span class="value old">{anterior.get('locucion', '-')}</span>
                            <span class="arrow">→</span>
                            <span class="value new">{actual.get('locucion', '-')}</span>
                        </div>
                    ''')
                
                for i in range(1, 6):
                    accion_key = f'accion{i}'
                    if anterior.get(accion_key) != actual.get(accion_key):
                        html.append(f'''
                            <div class="change-detail">
                                <span class="field">Acción {i}:</span>
                                <span class="value old">{anterior.get(accion_key, '-')[:40]}...</span>
                                <span class="arrow">→</span>
                                <span class="value new">{actual.get(accion_key, '-')[:40]}...</span>
                            </div>
                        ''')
                
                html.append('</div></li>')
            html.append('</ul></div>')
        
        # Sin cambios
        if not any([changes.get('dids_added'), changes.get('dids_removed'), changes.get('dids_modified')]):
            html.append('<div class="no-changes"><div class="icon">✅</div><div>No hay cambios en DIDs</div></div>')
        
        return '\n'.join(html)

    def _generate_colas_changes_html(self, changes):
        """Generar HTML de cambios en colas"""
        html = []
        
        # Añadidas
        if changes.get('colas_added'):
            html.append('<div class="change-section added">')
            html.append(f'<h3>✅ AÑADIDAS ({len(changes["colas_added"])})</h3>')
            html.append('<ul class="change-list">')
            for cola in changes['colas_added']:
                miembros_count = len(cola.get('miembros', []))
                html.append(f'''
                    <li class="change-item added">
                        <div class="change-item-header">📋 {cola.get("nombre", "")}</div>
                        <div class="change-item-details">
                            Miembros: {miembros_count}
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Eliminadas
        if changes.get('colas_removed'):
            html.append('<div class="change-section removed">')
            html.append(f'<h3>❌ ELIMINADAS ({len(changes["colas_removed"])})</h3>')
            html.append('<ul class="change-list">')
            for cola in changes['colas_removed']:
                miembros_count = len(cola.get('miembros', []))
                html.append(f'''
                    <li class="change-item removed">
                        <div class="change-item-header">📋 {cola.get("nombre", "")}</div>
                        <div class="change-item-details">
                            Tenía {miembros_count} miembros
                        </div>
                    </li>
                ''')
            html.append('</ul></div>')
        
        # Modificadas
        if changes.get('colas_modified'):
            html.append('<div class="change-section modified">')
            html.append(f'<h3>🔄 MODIFICADAS ({len(changes["colas_modified"])})</h3>')
            html.append('<ul class="change-list">')
            for change in changes['colas_modified']:
                cola_name = change.get('nombre', '')
                anterior = change.get('anterior', {})
                actual = change.get('actual', {})
                
                miembros_ant = {m['extension']: m for m in anterior.get('miembros', [])}
                miembros_act = {m['extension']: m for m in actual.get('miembros', [])}
                
                # Detectar miembros añadidos/eliminados
                added_members = set(miembros_act.keys()) - set(miembros_ant.keys())
                removed_members = set(miembros_ant.keys()) - set(miembros_act.keys())
                
                # Detectar cambios de estado
                estado_changes = []
                for ext in set(miembros_ant.keys()) & set(miembros_act.keys()):
                    if miembros_ant[ext].get('estado') != miembros_act[ext].get('estado'):
                        estado_changes.append((ext, miembros_ant[ext].get('estado'), miembros_act[ext].get('estado')))
                
                html.append(f'''
                    <li class="change-item modified">
                        <div class="change-item-header">📋 {cola_name}</div>
                        <div class="change-item-details">
                ''')
                
                if added_members:
                    html.append(f'<div class="change-detail"><span class="field">✅ Miembros añadidos:</span> {", ".join(added_members)}</div>')
                
                if removed_members:
                    html.append(f'<div class="change-detail"><span class="field">❌ Miembros eliminados:</span> {", ".join(removed_members)}</div>')
                
                if estado_changes:
                    for ext, old_state, new_state in estado_changes:
                        html.append(f'''
                            <div class="change-detail">
                                <span class="field">{ext}:</span>
                                <span class="value old">{old_state.title()}</span>
                                <span class="arrow">→</span>
                                <span class="value new">{new_state.title()}</span>
                            </div>
                        ''')
                
                html.append('</div></li>')
            html.append('</ul></div>')
        
        # Sin cambios
        if not any([changes.get('colas_added'), changes.get('colas_removed'), changes.get('colas_modified')]):
            html.append('<div class="no-changes"><div class="icon">✅</div><div>No hay cambios en colas</div></div>')
        
        return '\n'.join(html)
    
    def cleanup(self):
        """Limpiar recursos"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                    time.sleep(2)
                except:
                    pass
                finally:
                    self.driver = None
            
            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                        if not self.temp_dir.exists():
                            break
                    except:
                        time.sleep(1)
            
            self._kill_chrome_processes()
            
        except:
            pass

def main():
    """Función principal"""
    print("=" * 80)
    print("🔍 AUDITOR DE CONFIGURACIÓN NEOTEL")
    print("=" * 80)
    print()
    
    try:
        extractor = NeotelConfigExtractor()
        extractor.run_audit()
        
        print()
        print("=" * 80)
        print("✅ ¡AUDITORÍA COMPLETADA EXITOSAMENTE!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR DURANTE LA AUDITORÍA")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()