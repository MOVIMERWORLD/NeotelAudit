#!/usr/bin/env python3
"""
Script de debugging con ESPERAS MEJORADAS para contenido dinámico
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time
from pathlib import Path

# Crear carpeta para screenshots
debug_dir = Path("debug_screenshots")
debug_dir.mkdir(exist_ok=True)

print("=" * 80)
print("🔍 DEBUGGING CON ESPERAS MEJORADAS")
print("=" * 80)
print()

# Configurar Chrome
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

def wait_and_scroll(seconds=10):
    """Esperar y hacer scroll para forzar carga"""
    print(f"⏳ Esperando {seconds} segundos y haciendo scroll...")
    
    for i in range(seconds):
        if i % 2 == 0:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        else:
            # Scroll up
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
    
    print("✅ Espera completada")

def find_visible_tables():
    """Buscar solo tablas VISIBLES"""
    all_tables = driver.find_elements(By.CSS_SELECTOR, 'table')
    visible_tables = [t for t in all_tables if t.is_displayed()]
    return visible_tables

try:
    # ========================================================================
    # PASO 1: LOGIN
    # ========================================================================
    print("=" * 80)
    print("PASO 1: LOGIN")
    print("=" * 80)
    
    driver.get("https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server")
    
    wait = WebDriverWait(driver, 30)
    
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
    password = driver.find_element(By.CSS_SELECTOR, '#password')
    
    username.send_keys("movimerworld")
    password.send_keys("movimer_92")
    
    driver.find_element(By.CSS_SELECTOR, '#kc-login').click()
    
    print("⏳ Esperando login...")
    time.sleep(8)
    
    print(f"✅ Login OK - URL: {driver.current_url}")
    driver.save_screenshot(str(debug_dir / "01_login_ok.png"))
    print()
    
    # ========================================================================
    # PASO 2: IR A EXTENSIONES CON ESPERAS MEJORADAS
    # ========================================================================
    print("=" * 80)
    print("PASO 2: EXTENSIONES - VERSIÓN MEJORADA")
    print("=" * 80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/ivr/extension/search")
    print("📄 Página de extensiones cargada")
    
    # ESTRATEGIA 1: Esperar y hacer scroll
    wait_and_scroll(10)
    driver.save_screenshot(str(debug_dir / "02_extensiones_scroll.png"))
    
    # ESTRATEGIA 2: Intentar buscar tabla específica con espera explícita
    print("\n🔍 Buscando tabla de extensiones con espera explícita...")
    
    try:
        # Esperar a que aparezca UNA tabla visible
        wait.until(lambda d: len([t for t in d.find_elements(By.CSS_SELECTOR, 'table') if t.is_displayed()]) > 0)
        print("✅ Tabla visible detectada!")
    except:
        print("⚠️  No se detectó tabla visible automáticamente")
    
    # Esperar 5 segundos adicionales por si acaso
    time.sleep(5)
    
    # ESTRATEGIA 3: Buscar solo tablas VISIBLES
    visible_tables = find_visible_tables()
    
    print(f"\n📊 Tablas VISIBLES encontradas: {len(visible_tables)}")
    driver.save_screenshot(str(debug_dir / "03_extensiones_final.png"))
    
    if len(visible_tables) == 0:
        print("\n❌ ¡PROBLEMA! No hay tablas visibles")
        print("Vamos a intentar estrategias alternativas...\n")
        
        # ESTRATEGIA ALTERNATIVA 1: Buscar por otros selectores
        print("🔍 Buscando con selectores alternativos...")
        
        alternative_selectors = [
            'table.table',
            'table[class*="table"]',
            '.table-responsive table',
            'div[class*="table"] table',
            'table.table-striped',
            'table.table-hover'
        ]
        
        for sel in alternative_selectors:
            try:
                tables = driver.find_elements(By.CSS_SELECTOR, sel)
                visible = [t for t in tables if t.is_displayed()]
                if visible:
                    print(f"  ✓ Encontradas {len(visible)} con: {sel}")
            except:
                pass
        
        # ESTRATEGIA ALTERNATIVA 2: Ver el HTML crudo
        print("\n📝 HTML de la página (primeros 5000 caracteres):")
        page_source = driver.page_source[:5000]
        print(page_source)
        print("\n... (truncado)")
        
    else:
        # ANALIZAR CADA TABLA VISIBLE
        for i, table in enumerate(visible_tables):
            print(f"\n{'='*60}")
            print(f"TABLA VISIBLE {i+1} de {len(visible_tables)}")
            print(f"{'='*60}")
            
            try:
                table_class = table.get_attribute('class')
                table_id = table.get_attribute('id')
                
                print(f"  ID: {table_id if table_id else '(sin id)'}")
                print(f"  Class: {table_class if table_class else '(sin class)'}")
                
                # Headers
                theads = table.find_elements(By.TAG_NAME, 'thead')
                if theads:
                    headers = theads[0].find_elements(By.TAG_NAME, 'th')
                    print(f"  📋 Headers ({len(headers)}):")
                    for j, header in enumerate(headers):
                        text = header.text.strip()
                        if text:
                            print(f"    [{j}] {text}")
                
                # Filas
                tbodies = table.find_elements(By.TAG_NAME, 'tbody')
                if tbodies:
                    rows = tbodies[0].find_elements(By.TAG_NAME, 'tr')
                    print(f"  📊 Filas: {len(rows)}")
                    
                    if len(rows) > 0:
                        print(f"\n  🔍 PRIMERA FILA:")
                        first_row = rows[0]
                        cells = first_row.find_elements(By.TAG_NAME, 'td')
                        print(f"    Celdas: {len(cells)}")
                        
                        for k, cell in enumerate(cells):
                            text = cell.text.strip()
                            if text:
                                print(f"      [{k}] {text[:80]}")
                            else:
                                print(f"      [{k}] (vacío)")
                        
                        # Segunda fila
                        if len(rows) > 1:
                            print(f"\n  🔍 SEGUNDA FILA:")
                            cells2 = rows[1].find_elements(By.TAG_NAME, 'td')
                            for k, cell in enumerate(cells2[:8]):
                                text = cell.text.strip()
                                if text:
                                    print(f"      [{k}] {text[:80]}")
                        
                        # Tercera fila
                        if len(rows) > 2:
                            print(f"\n  🔍 TERCERA FILA:")
                            cells3 = rows[2].find_elements(By.TAG_NAME, 'td')
                            for k, cell in enumerate(cells3[:8]):
                                text = cell.text.strip()
                                if text:
                                    print(f"      [{k}] {text[:80]}")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
    
    # ========================================================================
    # PASO 3: DIDs CON ESPERAS MEJORADAS
    # ========================================================================
    print("\n" + "="*80)
    print("PASO 3: DIDs - VERSIÓN MEJORADA")
    print("="*80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/ivr/did")
    print("📄 Página de DIDs cargada")
    
    wait_and_scroll(10)
    driver.save_screenshot(str(debug_dir / "04_dids_scroll.png"))
    
    # Esperar a que aparezca el SELECT
    print("\n🔍 Esperando SELECT de DIDs...")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'select')))
        print("✅ SELECT encontrado!")
    except:
        print("⚠️  SELECT no encontrado con espera")
    
    time.sleep(5)
    
    # Buscar SELECTs visibles
    all_selects = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects = [s for s in all_selects if s.is_displayed()]
    
    print(f"\n📋 SELECT visibles: {len(visible_selects)}")
    driver.save_screenshot(str(debug_dir / "05_dids_final.png"))
    
    for i, select_elem in enumerate(visible_selects):
        try:
            select_id = select_elem.get_attribute('id')
            select_name = select_elem.get_attribute('name')
            
            print(f"\n  SELECT {i+1}:")
            print(f"    ID: {select_id if select_id else '(sin id)'}")
            print(f"    Name: {select_name if select_name else '(sin name)'}")
            
            select = Select(select_elem)
            options = select.options
            print(f"    Opciones: {len(options)}")
            
            if len(options) > 0:
                print(f"    Primeras 10 opciones:")
                for j, option in enumerate(options[:10]):
                    print(f"      [{j}] {option.text}")
                
                # ¿Parece el de DIDs?
                if len(options) > 50:
                    print(f"    ⭐ ¡Probablemente es el SELECT de DIDs! (tiene {len(options)} opciones)")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    # ========================================================================
    # PASO 4: COLAS CON ESPERAS MEJORADAS
    # ========================================================================
    print("\n" + "="*80)
    print("PASO 4: COLAS - VERSIÓN MEJORADA")
    print("="*80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/queue")
    print("📄 Página de Colas cargada")
    
    wait_and_scroll(10)
    driver.save_screenshot(str(debug_dir / "06_colas_scroll.png"))
    
    time.sleep(5)
    
    # Buscar SELECTs visibles
    all_selects_colas = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects_colas = [s for s in all_selects_colas if s.is_displayed()]
    
    print(f"\n📋 SELECT visibles: {len(visible_selects_colas)}")
    driver.save_screenshot(str(debug_dir / "07_colas_final.png"))
    
    for i, select_elem in enumerate(visible_selects_colas):
        try:
            select_id = select_elem.get_attribute('id')
            
            print(f"\n  SELECT {i+1}:")
            print(f"    ID: {select_id if select_id else '(sin id)'}")
            
            select = Select(select_elem)
            options = select.options
            print(f"    Opciones: {len(options)}")
            
            if len(options) > 0:
                print(f"    Primeras 10 opciones:")
                for j, option in enumerate(options[:10]):
                    print(f"      [{j}] {option.text}")
                
                if len(options) > 20:
                    print(f"    ⭐ ¡Probablemente es el SELECT de COLAS! (tiene {len(options)} opciones)")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    # Buscar elementos de miembros
    print("\n📋 Buscando elementos de MIEMBROS...")
    
    member_search_results = []
    
    # Buscar por texto "Extensión:"
    try:
        ext_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Extensión:')]")
        member_search_results.append(('XPATH con texto "Extensión:"', len(ext_elements)))
        
        if ext_elements:
            print(f"  ✓ Encontrados {len(ext_elements)} elementos con 'Extensión:'")
            print(f"\n  Muestra de los primeros 3:")
            for i, elem in enumerate(ext_elements[:3]):
                print(f"    {i+1}. {elem.text[:100]}")
    except Exception as e:
        print(f"  ✗ Error buscando por texto: {str(e)}")
    
    # Buscar por clases comunes
    common_classes = [
        '.member', '.miembro', '.member-item', '.miembro-item',
        '[class*="member"]', '[class*="miembro"]'
    ]
    
    for css_class in common_classes:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, css_class)
            visible = [e for e in elements if e.is_displayed()]
            if visible:
                member_search_results.append((css_class, len(visible)))
                print(f"  ✓ {css_class}: {len(visible)} visibles")
        except:
            pass
    
    print("\n" + "="*80)
    print("✅ DEBUGGING COMPLETADO CON ESPERAS MEJORADAS")
    print("="*80)
    print()
    print("📁 Screenshots en: debug_screenshots/")
    print()
    print("🔍 REVISA LA SALIDA Y DIME:")
    print("  1. ¿Cuántas tablas VISIBLES encontró en Extensiones?")
    print("  2. ¿Cuál tabla tiene los datos correctos?")
    print("  3. ¿Qué SELECT tiene los DIDs?")
    print("  4. ¿Qué SELECT tiene las Colas?")
    print()
    
    input("Presiona Enter para cerrar...")
    
except Exception as e:
    print(f"\n❌ ERROR CRÍTICO: {str(e)}")
    import traceback
    traceback.print_exc()
    input("Presiona Enter para cerrar...")

finally:
    driver.quit()
    print("\n✅ Navegador cerrado")