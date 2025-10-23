#!/usr/bin/env python3
"""
Auditor de Configuración Neotel - Extractor Principal
Detecta cambios diarios en DIDs, Extensiones y Colas
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
    """Extractor de configuración de Neotel"""
    
    def __init__(self):
        """Inicializar el extractor"""
        self.logger = self._setup_logging()
        self.driver = None
        self.temp_dir = None
        self.email_sender = EmailSender(ConfigAudit.EMAIL_CONFIG)
        
        # Crear directorios necesarios
        ConfigAudit.create_directories()
        
        # Validar configuración
        if not ConfigAudit.validate_config():
            raise Exception("Error en la configuración. Revisa config_audit.py")
        
        self.logger.info("=" * 80)
        self.logger.info("🔍 AUDITOR DE CONFIGURACIÓN NEOTEL - INICIADO")
        self.logger.info("=" * 80)
    
    def _setup_logging(self):
        """Configurar sistema de logging"""
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
        """Configurar el driver de Chrome (basado en script original)"""
        try:
            self.logger.info("⚙️  Configurando Chrome WebDriver...")
            
            # Aplicar fixes preventivos
            self._apply_chrome_fixes()
            
            chrome_options = Options()
            
            # Crear directorio único para Chrome
            temp_dir = self._create_ultra_unique_dir()
            
            if temp_dir:
                self.temp_dir = temp_dir
                chrome_options.add_argument(f'--user-data-dir={self.temp_dir}')
                self.logger.info(f"📁 Directorio Chrome: {self.temp_dir}")
            else:
                self.logger.info("📁 Ejecutando sin user-data-dir")
                self.temp_dir = None
            
            # Configurar opciones de Chrome
            if ConfigAudit.HEADLESS_BROWSER:
                chrome_options.add_argument('--headless')
                self.logger.info("🔇 Modo headless activado")
            
            # Opciones de estabilidad
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Configurar preferencias
            prefs = {
                "download.default_directory": str(ConfigAudit.DOWNLOAD_DIR),
                "download.prompt_for_download": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # Crear driver con reintentos
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    service = Service()
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.driver.implicitly_wait(10)
                    
                    self.logger.info(f"✅ Chrome WebDriver creado exitosamente (intento {attempt + 1})")
                    break
                    
                except Exception as retry_error:
                    self.logger.warning(f"⚠️  Intento {attempt + 1} falló: {str(retry_error)}")
                    
                    if attempt < max_retries - 1:
                        self._cleanup_failed_attempt()
                        time.sleep(5)
                        temp_dir = self._create_ultra_unique_dir()
                        if temp_dir:
                            self.temp_dir = temp_dir
                    else:
                        raise retry_error
            
            self.logger.info("✅ Driver Chrome configurado correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando driver: {str(e)}")
            # Intentar configuración de emergencia
            try:
                self.logger.info("🆘 Intentando configuración de emergencia...")
                chrome_options = self._get_emergency_chrome_options()
                self.driver = webdriver.Chrome(options=chrome_options)
                self.temp_dir = None
                self.logger.info("✅ Driver creado con configuración de emergencia")
            except Exception as emergency_error:
                self.logger.error(f"❌ Falló configuración de emergencia: {str(emergency_error)}")
                raise

    def _apply_chrome_fixes(self):
        """Aplicar fixes preventivos"""
        try:
            self.logger.info("🔧 Aplicando fixes preventivos...")
            self._kill_chrome_processes()
            self._clean_temp_directories()
            time.sleep(2)
            self.logger.info("✅ Fixes preventivos aplicados")
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
                self.logger.info(f"🔧 {killed_count} procesos Chrome eliminados")
        except Exception as e:
            self.logger.warning(f"⚠️  Error eliminando procesos Chrome: {str(e)}")
    
    def _clean_temp_directories(self):
        """Limpiar directorios temporales antiguos"""
        try:
            temp_base = Path(tempfile.gettempdir())
            cleaned_count = 0
            patterns = ['chrome_movimer_*', 'chrome_selenium_*', 'scoped_dir*']
            
            for pattern in patterns:
                for old_dir in temp_base.glob(pattern):
                    try:
                        if old_dir.is_dir():
                            shutil.rmtree(old_dir, ignore_errors=True)
                            cleaned_count += 1
                    except:
                        pass
            
            if cleaned_count > 0:
                self.logger.info(f"🧹 {cleaned_count} directorios temporales limpiados")
        except Exception as e:
            self.logger.warning(f"⚠️  Error limpiando directorios: {str(e)}")
    
    def _create_ultra_unique_dir(self):
        """Crear directorio único para Chrome"""
        try:
            timestamp = int(time.time() * 1000)
            unique_id = str(uuid.uuid4()).replace('-', '')[:12]
            process_id = os.getpid()
            thread_id = threading.get_ident() if hasattr(threading, 'get_ident') else 0
            
            dir_name = f"chrome_movimer_{timestamp}_{unique_id}_{process_id}_{thread_id}"
            temp_dir = Path(tempfile.gettempdir()) / dir_name
            
            temp_dir.mkdir(parents=True, exist_ok=False)
            if os.name != 'nt':
                os.chmod(temp_dir, 0o700)
            
            return temp_dir
        except Exception as e:
            self.logger.warning(f"⚠️  No se pudo crear directorio único: {str(e)}")
            return None
    
    def _cleanup_failed_attempt(self):
        """Limpiar después de un intento fallido"""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self._kill_chrome_processes()
        except:
            pass
    
    def _get_emergency_chrome_options(self):
        """Configuración de emergencia"""
        chrome_options = Options()
        
        if ConfigAudit.HEADLESS_BROWSER:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        return chrome_options
    
    def login_to_neotel(self):
        """Realizar login en Neotel"""
        try:
            self.logger.info("🔐 Iniciando login en Neotel...")
            
            self.driver.get(ConfigAudit.LOGIN_URL)
            self.logger.info(f"🌐 Navegando a: {ConfigAudit.LOGIN_URL}")
            
            wait = WebDriverWait(self.driver, ConfigAudit.PAGE_LOAD_TIMEOUT)
            
            # Buscar campos de login
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['username_field']))
            )
            password_field = self.driver.find_element(By.CSS_SELECTOR, ConfigAudit.SELECTORES['password_field'])
            
            # Introducir credenciales
            username_field.clear()
            username_field.send_keys(ConfigAudit.NEOTEL_USERNAME)
            self.logger.info(f"👤 Usuario introducido: {ConfigAudit.NEOTEL_USERNAME}")
            
            password_field.clear()
            password_field.send_keys(ConfigAudit.NEOTEL_PASSWORD)
            self.logger.info("🔑 Contraseña introducida")
            
            # Hacer clic en login
            login_button = self.driver.find_element(By.CSS_SELECTOR, ConfigAudit.SELECTORES['login_button'])
            login_button.click()
            self.logger.info("🖱️  Botón de login pulsado")
            
            # Esperar a completar login
            wait.until(lambda driver: "pbx.neotel2000.com" in driver.current_url and "auth" not in driver.current_url)
            
            self.logger.info("✅ Login completado exitosamente")
            time.sleep(3)  # Esperar estabilización
            
        except Exception as e:
            self.logger.error(f"❌ Error durante el login: {str(e)}")
            raise
    
    def extract_extensions(self):
        """
        Extraer configuración de extensiones
        Retorna: Lista de diccionarios con info de extensiones
        """
        try:
            self.logger.info("📞 Extrayendo configuración de extensiones...")
            
            self.driver.get(ConfigAudit.EXTENSIONS_URL)
            time.sleep(5)
            
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.table')))
            
            extensions = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, ConfigAudit.SELECTORES['extensions_table'])
            
            self.logger.info(f"📊 Encontradas {len(rows)} filas de extensiones")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    
                    if len(cells) < 10:
                        continue
                    
                    extension_code = cells[0].text.strip()
                    name = cells[1].text.strip()
                    group = cells[2].text.strip()
                    # Saltar columna 3 (agente asignado)
                    number_saliente = cells[4].text.strip()
                    
                    # Detectar estado de colas mirando botones en columna "Acción" (índice 9)
                    buttons = cells[9].find_elements(By.TAG_NAME, 'button')
                    
                    queue_status = "desconocido"
                    
                    # Analizar botones visibles
                    visible_buttons = []
                    for btn in buttons:
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.strip().lower()
                                btn_class = btn.get_attribute('class')
                                visible_buttons.append((btn_text, btn_class))
                        except:
                            continue
                    
                    # Lógica basada en las capturas:
                    # - Solo botón verde "Reanudar en todas las colas" = todas pausadas
                    # - Botón verde + botón rojo = algunas pausadas/activadas
                    # - Solo botón gris "Pausar en todas las colas" = todas activadas
                    
                    has_green = any('reanudar' in text for text, _ in visible_buttons)
                    has_red = any('pausar' in text and 'btn-danger' in cls for text, cls in visible_buttons)
                    
                    if has_green and has_red:
                        queue_status = "mixto"  # Algunas pausadas, algunas activas
                    elif has_green and not has_red:
                        queue_status = "todas_pausadas"
                    elif not has_green and has_red:
                        queue_status = "todas_activas"
                    else:
                        queue_status = "sin_colas"
                    
                    extension = {
                        'extension': extension_code,
                        'nombre': name,
                        'grupo': group,
                        'numero_saliente': number_saliente,
                        'estado_colas': queue_status
                    }
                    
                    extensions.append(extension)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando fila de extensión: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Extraídas {len(extensions)} extensiones")
            return extensions
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo extensiones: {str(e)}")
            raise
    
    def extract_dids(self):
        """
        Extraer configuración de DIDs
        Retorna: Lista de diccionarios con info de DIDs
        """
        try:
            self.logger.info("📱 Extrayendo configuración de DIDs...")
            
            self.driver.get(ConfigAudit.DIDS_URL)
            time.sleep(5)
            
            dids = []
            
            # Buscar el select de DIDs
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            select_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select')))
            
            select = Select(select_element)
            options = select.options
            
            self.logger.info(f"📊 Encontrados {len(options)} DIDs")
            
            for i, option in enumerate(options):
                try:
                    did_number = option.text.strip()
                    
                    if not did_number or did_number == '':
                        continue
                    
                    self.logger.info(f"  📞 Procesando DID {i+1}/{len(options)}: {did_number}")
                    
                    # Seleccionar el DID
                    select.select_by_visible_text(did_number)
                    time.sleep(2)
                    
                    # Extraer información del DID
                    # Locución
                    locucion = "<Sin locución>"
                    try:
                        locucion_field = self.driver.find_element(By.CSS_SELECTOR, 'input[id*="locucion"], input[name*="locucion"], select[id*="locucion"]')
                        locucion_value = locucion_field.get_attribute('value') or locucion_field.text
                        if locucion_value and locucion_value.strip():
                            locucion = locucion_value.strip()
                    except:
                        pass
                    
                    # Acciones (primeras 3)
                    acciones = []
                    for accion_num in range(1, 4):
                        try:
                            # Buscar campos de acción
                            accion_selects = self.driver.find_elements(By.CSS_SELECTOR, f'select[id*="accion{accion_num}"], select[name*="accion{accion_num}"], select[id*="action{accion_num}"]')
                            
                            if accion_selects:
                                accion_select = accion_selects[0]
                                selected_option = Select(accion_select).first_selected_option
                                accion_text = selected_option.text.strip() if selected_option else "Sin acción"
                            else:
                                # Buscar inputs de texto
                                accion_inputs = self.driver.find_elements(By.CSS_SELECTOR, f'input[id*="accion{accion_num}"], input[name*="accion{accion_num}"]')
                                if accion_inputs:
                                    accion_text = accion_inputs[0].get_attribute('value') or "Sin acción"
                                else:
                                    accion_text = "Sin acción"
                            
                            acciones.append(accion_text)
                            
                        except Exception as e:
                            self.logger.debug(f"    No se pudo obtener acción {accion_num}")
                            acciones.append("Sin acción")
                    
                    did = {
                        'numero': did_number,
                        'locucion': locucion,
                        'accion1': acciones[0] if len(acciones) > 0 else "Sin acción",
                        'accion2': acciones[1] if len(acciones) > 1 else "Sin acción",
                        'accion3': acciones[2] if len(acciones) > 2 else "Sin acción"
                    }
                    
                    dids.append(did)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando DID {did_number}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Extraídos {len(dids)} DIDs")
            return dids
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo DIDs: {str(e)}")
            raise
    
    def extract_colas(self):
        """
        Extraer configuración de colas
        Retorna: Lista de diccionarios con info de colas
        """
        try:
            self.logger.info("📋 Extrayendo configuración de colas...")
            
            self.driver.get(ConfigAudit.COLAS_URL)
            time.sleep(5)
            
            colas = []
            
            # Buscar el select de colas
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            select_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select')))
            
            select = Select(select_element)
            options = select.options
            
            self.logger.info(f"📊 Encontradas {len(options)} colas")
            
            for i, option in enumerate(options):
                try:
                    cola_name = option.text.strip()
                    
                    if not cola_name or cola_name == '':
                        continue
                    
                    self.logger.info(f"  📋 Procesando cola {i+1}/{len(options)}: {cola_name}")
                    
                    # Seleccionar la cola
                    select.select_by_visible_text(cola_name)
                    time.sleep(2)
                    
                    # Extraer miembros
                    miembros = []
                    
                    # Buscar sección de miembros
                    try:
                        # Buscar todos los elementos que contengan información de miembros
                        member_elements = self.driver.find_elements(By.CSS_SELECTOR, '.member-item, [class*="miembro"], [class*="member"]')
                        
                        if not member_elements:
                            # Método alternativo: buscar por texto
                            member_texts = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Est:') and contains(text(), 'Pen:') and contains(text(), 'Pri:') and contains(text(), 'Extensión:')]")
                            
                            for member_text in member_texts:
                                try:
                                    text = member_text.text
                                    
                                    # Extraer número de extensión
                                    if 'Extensión:' in text:
                                        ext_start = text.find('Extensión:') + len('Extensión:')
                                        ext_text = text[ext_start:].strip().split()[0]
                                        
                                        # Detectar estado por ícono (▶ = activo, ⏸ = pausado)
                                        estado = "activo" if "▶" in text else "pausado" if "⏸" in text else "desconocido"
                                        
                                        miembros.append({
                                            'extension': ext_text,
                                            'estado': estado
                                        })
                                except Exception as e:
                                    self.logger.debug(f"    Error parseando miembro: {str(e)}")
                                    continue
                        else:
                            # Procesar elementos encontrados
                            for member_elem in member_elements:
                                try:
                                    text = member_elem.text
                                    
                                    # Buscar número de extensión
                                    extension_num = None
                                    if 'Extensión:' in text:
                                        ext_start = text.find('Extensión:') + len('Extensión:')
                                        extension_num = text[ext_start:].strip().split()[0]
                                    else:
                                        # Buscar patrón de extensión (4 dígitos-3 dígitos)
                                        import re
                                        match = re.search(r'(\d{4}-\d{3})', text)
                                        if match:
                                            extension_num = match.group(1)
                                    
                                    if extension_num:
                                        # Detectar estado
                                        estado = "activo" if "▶" in text else "pausado" if "⏸" in text else "desconocido"
                                        
                                        miembros.append({
                                            'extension': extension_num,
                                            'estado': estado
                                        })
                                except Exception as e:
                                    self.logger.debug(f"    Error procesando miembro: {str(e)}")
                                    continue
                    
                    except Exception as e:
                        self.logger.warning(f"    ⚠️  Error extrayendo miembros de cola {cola_name}: {str(e)}")
                    
                    cola = {
                        'nombre': cola_name,
                        'miembros': miembros
                    }
                    
                    colas.append(cola)
                    self.logger.info(f"    ✓ Cola '{cola_name}': {len(miembros)} miembros")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando cola {cola_name}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Extraídas {len(colas)} colas")
            return colas
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo colas: {str(e)}")
            raise
    
    def save_snapshot(self, config_data, date=None):
        """
        Guardar snapshot de configuración
        
        Args:
            config_data: Diccionario con configuración completa
            date: Fecha del snapshot (default: hoy)
        """
        try:
            snapshot_file = ConfigAudit.get_snapshot_filename(date)
            
            # Añadir metadata
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
        """
        Cargar snapshot de una fecha específica
        
        Args:
            date: Fecha del snapshot a cargar
            
        Returns:
            Diccionario con configuración o None si no existe
        """
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
        """
        Comparar dos configuraciones y detectar cambios
        
        Args:
            current_config: Configuración actual
            previous_config: Configuración anterior
            
        Returns:
            Diccionario con resumen de cambios
        """
        if previous_config is None:
            self.logger.info("ℹ️  No hay configuración anterior para comparar")
            return {
                'has_changes': False,
                'is_first_run': True,
                'message': 'Primera ejecución - no hay datos previos para comparar'
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
        """
        Generar reporte HTML con los cambios detectados
        
        Args:
            changes: Diccionario con cambios
            report_date: Fecha del reporte
            
        Returns:
            Ruta al archivo HTML generado
        """
        try:
            self.logger.info("📄 Generando reporte HTML...")
            
            report_file = ConfigAudit.get_report_filename(report_date)
            
            # Aquí iría el código para generar HTML
            # Por brevedad, creo una versión simplificada
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reporte de Cambios Neotel - {report_date.strftime('%d/%m/%Y')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h1 {{ color: #1976d2; border-bottom: 3px solid #1976d2; padding-bottom: 10px; }}
                    h2 {{ color: #424242; margin-top: 30px; }}
                    .summary {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0; }}
                    .change-section {{ margin: 20px 0; }}
                    .added {{ background: #e8f5e9; border-left: 3px solid #4caf50; padding: 10px; margin: 10px 0; }}
                    .removed {{ background: #ffebee; border-left: 3px solid #f44336; padding: 10px; margin: 10px 0; }}
                    .modified {{ background: #fff3e0; border-left: 3px solid #ff9800; padding: 10px; margin: 10px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background: #f5f5f5; font-weight: bold; }}
                    .diff {{ display: flex; gap: 20px; }}
                    .diff-col {{ flex: 1; }}
                    .label {{ font-weight: bold; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔍 Reporte de Cambios - Configuración Neotel</h1>
                    <p><strong>Fecha:</strong> {report_date.strftime('%d/%m/%Y')}</p>
                    <p><strong>Generado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    
                    <div class="summary">
                        <h3>📊 Resumen de Cambios</h3>
                        <ul>
                            <li>DIDs: +{len(changes.get('dids_added', []))} | -{len(changes.get('dids_removed', []))} | ≠{len(changes.get('dids_modified', []))}</li>
                            <li>Extensiones: +{len(changes.get('extensions_added', []))} | -{len(changes.get('extensions_removed', []))} | ≠{len(changes.get('extensions_modified', []))}</li>
                            <li>Colas: +{len(changes.get('colas_added', []))} | -{len(changes.get('colas_removed', []))} | ≠{len(changes.get('colas_modified', []))}</li>
                        </ul>
                    </div>
                    
                    <!-- Aquí iría el resto del contenido detallado -->
                    
                    <hr style="margin: 40px 0;">
                    <p style="color: #666; font-size: 12px;">Reporte generado automáticamente por el Auditor de Configuración Neotel</p>
                </div>
            </body>
            </html>
            """
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"✅ Reporte HTML generado: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte HTML: {str(e)}")
            raise
    
    def cleanup_old_snapshots(self):
        """Limpiar snapshots antiguos según retención configurada"""
        try:
            self.logger.info(f"🧹 Limpiando snapshots antiguos (retención: {ConfigAudit.RETENTION_DAYS} días)...")
            
            cutoff_date = datetime.now() - timedelta(days=ConfigAudit.RETENTION_DAYS)
            deleted_count = 0
            
            for snapshot_file in ConfigAudit.SNAPSHOTS_DIR.glob("*.json"):
                try:
                    # Extraer fecha del nombre del archivo
                    date_str = snapshot_file.stem.split('_')[0]
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        snapshot_file.unlink()
                        deleted_count += 1
                        self.logger.info(f"  🗑️  Eliminado: {snapshot_file.name}")
                
                except Exception as e:
                    self.logger.warning(f"⚠️  Error procesando {snapshot_file.name}: {str(e)}")
                    continue
            
            if deleted_count > 0:
                self.logger.info(f"✅ Limpiados {deleted_count} snapshots antiguos")
            else:
                self.logger.info("ℹ️  No hay snapshots antiguos para limpiar")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Error limpiando snapshots: {str(e)}")
    
    def run_audit(self):
        """Ejecutar auditoría completa"""
        try:
            audit_date = datetime.now().date()
            previous_date = audit_date - timedelta(days=1)
            
            self.logger.info(f"📅 Fecha de auditoría: {audit_date}")
            
            # 1. Configurar driver
            self.setup_driver()
            
            # 2. Login
            self.login_to_neotel()
            
            # 3. Extraer configuración actual
            self.logger.info("=" * 80)
            self.logger.info("📥 EXTRAYENDO CONFIGURACIÓN ACTUAL")
            self.logger.info("=" * 80)
            
            current_config = {
                'dids': self.extract_dids(),
                'extensiones': self.extract_extensions(),
                'colas': self.extract_colas()
            }
            
            # 4. Guardar snapshot
            self.save_snapshot(current_config, audit_date)
            
            # 5. Cargar snapshot anterior
            previous_config = self.load_snapshot(previous_date)
            
            # 6. Comparar configuraciones
            self.logger.info("=" * 80)
            self.logger.info("🔍 COMPARANDO CONFIGURACIONES")
            self.logger.info("=" * 80)
            
            changes = self.compare_configs(current_config, previous_config)
            
            # 7. Generar reporte y enviar email según resultado
            if changes.get('is_first_run'):
                self.logger.info("ℹ️  Primera ejecución - no se envía email")
            elif changes.get('has_changes'):
                report_file = self.generate_html_report(changes, audit_date)
                self.email_sender.send_change_report(report_file, changes, audit_date)
            else:
                self.email_sender.send_no_changes_notification(audit_date)
            
            # 8. Limpiar snapshots antiguos
            self.cleanup_old_snapshots()
            
            self.logger.info("=" * 80)
            self.logger.info("✅ AUDITORÍA COMPLETADA EXITOSAMENTE")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ Error durante la auditoría: {str(e)}")
            # Enviar notificación de error
            self.email_sender.send_error_notification(str(e))
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpiar recursos"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                    time.sleep(2)
                    self.logger.info("🔒 Driver web cerrado")
                except:
                    pass
                finally:
                    self.driver = None
            
            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                        if not self.temp_dir.exists():
                            self.logger.info(f"🧹 Directorio temporal eliminado")
                            break
                    except:
                        time.sleep(1)
            
            self._kill_chrome_processes()
            
        except Exception as e:
            self.logger.debug(f"Info cleanup: {str(e)}")


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
        print()
        print("📧 Revisa tu email para ver el reporte de cambios")
        print("📁 Logs disponibles en:", ConfigAudit.LOG_DIR)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR DURANTE LA AUDITORÍA")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        print(f"\n📁 Revisa los logs en: {ConfigAudit.LOG_DIR}")
        sys.exit(1)


if __name__ == "__main__":
    main()