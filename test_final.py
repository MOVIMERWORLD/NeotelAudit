#!/usr/bin/env python3
"""
Script de Prueba de Producción - 10 registros por tipo
Valida el funcionamiento completo antes del lanzamiento
"""

import json
import logging
import sys
import time
from datetime import datetime
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

# Importar la clase principal
from neotel_config_extractor_v2 import NeotelConfigExtractor

class ProductionTester(NeotelConfigExtractor):
    """Tester de producción - hereda todo del extractor principal"""
    
    def __init__(self):
        """Inicializar tester"""
        super().__init__()
        self.logger.info("🧪 MODO PRUEBA: Extrayendo solo 10 registros por tipo")
    
    def extract_extensions_limited(self, limit=10):
        """Extraer solo las primeras N extensiones"""
        try:
            self.logger.info(f"📞 Extrayendo las primeras {limit} extensiones...")
            
            # Navegar
            self.click_menu_item("Configuración", wait_time=2)
            self.click_menu_item("Extensiones", wait_time=3)
            time.sleep(15)
            
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.table')))
            
            extensions = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, ConfigAudit.SELECTORES['extensions_table'])
            
            total_rows = len(rows)
            self.logger.info(f"📊 Total disponible: {total_rows} extensiones")
            self.logger.info(f"🎯 Procesando solo las primeras {limit}...")
            
            for idx, row in enumerate(rows[:limit]):  # LIMITAR AQUÍ
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    
                    if len(cells) < 10:
                        continue
                    
                    extension_code = cells[0].text.strip()
                    name = cells[1].text.strip()
                    group = cells[2].text.strip()
                    numero_saliente = cells[4].text.strip()
                    
                    action_cell = cells[9]
                    
                    reanudar_habilitado = False
                    pausar_habilitado = False
                    
                    try:
                        reanudar_button = action_cell.find_element(By.ID, f'play_queue_{extension_code}')
                        button_classes = reanudar_button.get_attribute('class')
                        reanudar_habilitado = 'btn-success' in button_classes
                    except:
                        pass
                    
                    try:
                        pausar_button = action_cell.find_element(By.ID, f'pause_queue_{extension_code}')
                        button_classes = pausar_button.get_attribute('class')
                        pausar_habilitado = 'btn-danger' in button_classes
                    except:
                        pass
                    
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
                        'numero_saliente': numero_saliente,
                        'estado_colas': queue_status
                    }
                    
                    extensions.append(extension)
                    self.logger.info(f"  ✅ [{idx + 1}/{limit}] Ext {extension_code}: {name} - {queue_status}")
                    
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error en fila {idx + 1}: {str(e)}")
                    continue
            
            self.logger.info(f"✅ Extraídas {len(extensions)} extensiones de prueba")
            return extensions
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo extensiones: {str(e)}")
            raise
    
    def extract_dids_limited(self, limit=10):
        """Extraer solo los primeros N DIDs"""
        try:
            self.logger.info(f"📱 Extrayendo los primeros {limit} DIDs...")
            
            # Navegar
            for did_text in ["DIDs", "DID", "dids"]:
                if self.click_menu_item(did_text, wait_time=3):
                    self.logger.info(f"✅ Navegación a {did_text}")
                    break
            
            time.sleep(10)
            
            dids = []
            wait = WebDriverWait(self.driver, ConfigAudit.ELEMENT_WAIT_TIMEOUT)
            
            try:
                select_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ConfigAudit.SELECTORES['dids_select']))
                )
                self.logger.info("✅ Select de DIDs encontrado")
            except TimeoutException:
                self.logger.error("❌ TIMEOUT buscando select de DIDs")
                raise
            
            select = Select(select_element)
            options = select.options
            
            total_options = len(options)
            self.logger.info(f"📊 Total disponible: {total_options} DIDs")
            self.logger.info(f"🎯 Procesando solo los primeros {limit}...")
            
            for idx, option in enumerate(options[:limit]):  # LIMITAR AQUÍ
                try:
                    did_numero = option.text.strip() or option.get_attribute('textContent').strip()
                    did_id_interno = option.get_attribute('value')
                    
                    if not did_numero or not did_id_interno:
                        continue
                    
                    self.logger.info(f"  [{idx + 1}/{limit}] Procesando DID: {did_numero}")
                    
                    if not self.select_chosen_option_by_text('configuration_dids_view_did_list_dids', did_numero):
                        self.logger.warning(f"    ⚠️  No se pudo seleccionar")
                        continue
                    
                    if not self.click_view_button('configuration_dids_view_did_list_button_view'):
                        self.logger.warning(f"    ⚠️  No se pudo hacer click en Ver")
                        continue
                    
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
                    
                    self.logger.info(f"    Locución: {locucion}")
                    self.logger.info(f"    Acción 1: {accion1}")
                    self.logger.info(f"  ✅ DID procesado correctamente")
                    
                    # Cerrar modal
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(1)
                    except:
                        pass
                    
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error en DID {idx + 1}: {str(e)}")
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass
                    continue
            
            self.logger.info(f"✅ Extraídos {len(dids)} DIDs de prueba")
            return dids
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo DIDs: {str(e)}")
            raise
    
    def extract_colas_limited(self, limit=10):
        """Extraer solo las primeras N colas"""
        try:
            self.logger.info(f"📋 Extrayendo las primeras {limit} colas...")
            
            # Navegar
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
            
            total_options = len(options)
            self.logger.info(f"📊 Total disponible: {total_options} colas")
            self.logger.info(f"🎯 Procesando solo las primeras {limit}...")
            
            for idx, option in enumerate(options[:limit]):  # LIMITAR AQUÍ
                try:
                    cola_nombre = option.text.strip() or option.get_attribute('textContent').strip()
                    cola_id_interno = option.get_attribute('value')
                    
                    if not cola_nombre or not cola_id_interno:
                        continue
                    
                    self.logger.info(f"  [{idx + 1}/{limit}] Procesando cola: {cola_nombre}")
                    
                    # Cerrar modales previos
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Scroll
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                    
                    if not self.select_chosen_option_by_text('configuration_queues_view_queue_list_queues', cola_nombre):
                        self.logger.warning(f"    ⚠️  No se pudo seleccionar")
                        continue
                    
                    if not self.click_view_button('configuration_queues_view_queue_list_button_view'):
                        self.logger.warning(f"    ⚠️  No se pudo hacer click en Ver")
                        continue
                    
                    time.sleep(2)
                    
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
                    
                    self.logger.info(f"    Miembros: {len(miembros)}")
                    self.logger.info(f"  ✅ Cola procesada correctamente")
                    
                    # Cerrar modal
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(1)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                    except:
                        pass
                    
                except Exception as e:
                    self.logger.warning(f"  ⚠️  Error en cola {idx + 1}: {str(e)}")
                    try:
                        for _ in range(3):
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                            time.sleep(0.3)
                    except:
                        pass
                    continue
            
            self.logger.info(f"✅ Extraídas {len(colas)} colas de prueba")
            return colas
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo colas: {str(e)}")
            raise
    
    def run_production_test(self):
        """Ejecutar prueba de producción con 10 registros"""
        try:
            self.logger.info("=" * 80)
            self.logger.info("🧪 INICIANDO PRUEBA DE PRODUCCIÓN")
            self.logger.info("=" * 80)
            
            # Setup
            self.setup_driver()
            self.login_to_neotel()
            
            # Extraer datos limitados
            self.logger.info("\n" + "=" * 80)
            self.logger.info("📥 EXTRAYENDO DATOS DE PRUEBA (10 por tipo)")
            self.logger.info("=" * 80)
            
            config_test = {
                'extensiones': self.extract_extensions_limited(limit=10),
                'dids': self.extract_dids_limited(limit=10),
                'colas': self.extract_colas_limited(limit=10)
            }
            
            # Guardar JSON de prueba
            test_file = ConfigAudit.LOG_DIR / f"production_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            test_snapshot = {
                'timestamp': datetime.now().isoformat(),
                'test_mode': True,
                'config': config_test
            }
            
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_snapshot, f, indent=2, ensure_ascii=False)
            
            # Resumen
            self.logger.info("\n" + "=" * 80)
            self.logger.info("📊 RESUMEN DE PRUEBA")
            self.logger.info("=" * 80)
            
            self.logger.info(f"\n✅ EXTENSIONES ({len(config_test['extensiones'])}):")
            for ext in config_test['extensiones'][:5]:
                self.logger.info(f"  - {ext['extension']}: {ext['nombre']} [{ext['estado_colas']}]")
            if len(config_test['extensiones']) > 5:
                self.logger.info(f"  ... y {len(config_test['extensiones']) - 5} más")
            
            self.logger.info(f"\n✅ DIDs ({len(config_test['dids'])}):")
            for did in config_test['dids'][:5]:
                self.logger.info(f"  - {did['numero']}: {did['accion1'][:50]}...")
            if len(config_test['dids']) > 5:
                self.logger.info(f"  ... y {len(config_test['dids']) - 5} más")
            
            self.logger.info(f"\n✅ COLAS ({len(config_test['colas'])}):")
            for cola in config_test['colas'][:5]:
                self.logger.info(f"  - {cola['nombre']} ({len(cola['miembros'])} miembros)")
            if len(config_test['colas']) > 5:
                self.logger.info(f"  ... y {len(config_test['colas']) - 5} más")
            
            self.logger.info(f"\n💾 Datos guardados en: {test_file}")
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("✅ ¡PRUEBA DE PRODUCCIÓN COMPLETADA!")
            self.logger.info("=" * 80)
            self.logger.info("\n💡 Si todo se ve correcto, ejecuta el script completo:")
            self.logger.info("   python neotel_extractor.py")
            
        except Exception as e:
            self.logger.error(f"\n❌ Error durante la prueba: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
        finally:
            self.cleanup()


def main():
    """Función principal"""
    print("=" * 80)
    print("🧪 PRUEBA DE PRODUCCIÓN - NEOTEL")
    print("=" * 80)
    print()
    print("Este script extraerá:")
    print("  • 10 primeras extensiones")
    print("  • 10 primeros DIDs")
    print("  • 10 primeras colas")
    print()
    
    try:
        tester = ProductionTester()
        tester.run_production_test()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()