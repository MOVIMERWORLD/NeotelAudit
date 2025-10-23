#!/usr/bin/env python3
"""
Script de debugging con NAVEGACIÓN CORRECTA por menú
Secuencia: Dashboard → Click Configuración → Click Extensiones → Esperar carga
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import time
from pathlib import Path

# Crear carpeta para screenshots
debug_dir = Path("debug_screenshots")
debug_dir.mkdir(exist_ok=True)

print("=" * 80)
print("🔍 DEBUGGING CON NAVEGACIÓN POR MENÚ")
print("=" * 80)
print()

# Configurar Chrome
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

def click_menu_item(text, wait_time=3):
    """
    Buscar y hacer click en elemento del menú por texto
    """
    try:
        print(f"🔍 Buscando menú: '{text}'")
        
        # Intentar varios selectores
        selectors = [
            f"//a[contains(text(), '{text}')]",
            f"//div[contains(text(), '{text}')]",
            f"//span[contains(text(), '{text}')]",
            f"//li[contains(text(), '{text}')]",
            f"//*[contains(text(), '{text}')]"
        ]
        
        element = None
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                # Buscar el primero que sea visible y clickeable
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
            print(f"❌ No se encontró elemento con texto '{text}'")
            return False
        
        # Hacer scroll al elemento
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        # Intentar click
        try:
            element.click()
            print(f"✅ Click realizado en '{text}'")
        except:
            # Si falla, usar JavaScript
            driver.execute_script("arguments[0].click();", element)
            print(f"✅ Click realizado en '{text}' (con JavaScript)")
        
        time.sleep(wait_time)
        return True
        
    except Exception as e:
        print(f"❌ Error haciendo click en '{text}': {str(e)}")
        return False

def wait_for_content_load(seconds=10):
    """Esperar a que cargue contenido con indicador de progreso"""
    print(f"⏳ Esperando {seconds} segundos a que cargue contenido...")
    for i in range(seconds):
        time.sleep(1)
        if (i + 1) % 2 == 0:
            print(f"   {i + 1}/{seconds}...", end="\r")
    print(f"   {seconds}/{seconds} ✅")

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
    # PASO 2: DASHBOARD (PUNTO DE PARTIDA)
    # ========================================================================
    print("=" * 80)
    print("PASO 2: ESPERANDO EN DASHBOARD")
    print("=" * 80)
    
    # Esperar a estar en dashboard
    wait_for_content_load(5)
    driver.save_screenshot(str(debug_dir / "02_dashboard.png"))
    print(f"✅ En Dashboard - URL: {driver.current_url}")
    print()
    
    # ========================================================================
    # PASO 3: NAVEGACIÓN A EXTENSIONES (CON CLICKS)
    # ========================================================================
    print("=" * 80)
    print("PASO 3: NAVEGANDO A EXTENSIONES (CON CLICKS EN MENÚ)")
    print("=" * 80)
    
    # Paso 3.1: Click en "Configuración"
    print("\n📂 PASO 3.1: Expandir menú 'Configuración'")
    if click_menu_item("Configuración", wait_time=2):
        driver.save_screenshot(str(debug_dir / "03a_menu_config_expandido.png"))
        print("✅ Menú Configuración expandido")
    else:
        print("⚠️  No se pudo expandir Configuración - intentando continuar")
    
    # Paso 3.2: Click en "Extensiones"
    print("\n📂 PASO 3.2: Click en 'Extensiones'")
    if click_menu_item("Extensiones", wait_time=3):
        driver.save_screenshot(str(debug_dir / "03b_navegado_extensiones.png"))
        print(f"✅ Navegado a Extensiones - URL: {driver.current_url}")
    else:
        print("❌ No se pudo navegar a Extensiones")
    
    # Paso 3.3: ESPERAR A QUE CARGUE (esto es crítico)
    print("\n⏳ PASO 3.3: Esperando a que cargue la tabla de extensiones...")
    wait_for_content_load(15)  # 15 segundos de espera
    
    driver.save_screenshot(str(debug_dir / "03c_extensiones_cargado.png"))
    
    # Paso 3.4: ANALIZAR TABLAS VISIBLES
    print("\n📊 PASO 3.4: Analizando tablas de extensiones...")
    visible_tables = find_visible_tables()
    
    print(f"📊 Tablas VISIBLES encontradas: {len(visible_tables)}")
    
    if len(visible_tables) == 0:
        print("❌ ¡PROBLEMA! No hay tablas visibles aún")
        print("Vamos a esperar 10 segundos más...")
        wait_for_content_load(10)
        visible_tables = find_visible_tables()
        print(f"📊 Tablas VISIBLES (segundo intento): {len(visible_tables)}")
    
    # Analizar cada tabla visible
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
                    print(f"\n  🔍 PRIMERAS 3 FILAS:")
                    for row_idx in range(min(3, len(rows))):
                        print(f"\n    FILA {row_idx + 1}:")
                        row = rows[row_idx]
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        print(f"      Celdas: {len(cells)}")
                        
                        for k, cell in enumerate(cells[:12]):  # Máximo 12 celdas
                            text = cell.text.strip()
                            if text:
                                print(f"        [{k}] {text[:80]}")
                            else:
                                # Ver si tiene botones u otros elementos
                                buttons = cell.find_elements(By.TAG_NAME, 'button')
                                if buttons:
                                    print(f"        [{k}] (contiene {len(buttons)} botones)")
                                else:
                                    print(f"        [{k}] (vacío)")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "="*80)
    print("📋 RESUMEN EXTENSIONES")
    print("="*80)
    if visible_tables:
        print(f"✅ Se encontraron {len(visible_tables)} tabla(s) visible(s)")
        print("👉 Revisa cuál tiene los headers: Extensión, Nombre, Grupo, etc.")
    else:
        print("❌ No se encontraron tablas visibles")
        print("💡 Revisa los screenshots para ver qué se muestra en pantalla")
    print()
    
    # ========================================================================
    # PASO 4: NAVEGACIÓN A DIDs (CON CLICKS)
    # ========================================================================
    print("=" * 80)
    print("PASO 4: NAVEGANDO A DIDs (CON CLICKS EN MENÚ)")
    print("=" * 80)
    
    # IMPORTANTE: NO hacer click en Configuración si ya está abierto
    print("\n📂 PASO 4.1: Verificando si menú Configuración está expandido")
    try:
        # Intentar encontrar DIDs directamente (si el menú ya está abierto)
        dids_visible = driver.find_elements(By.XPATH, "//*[contains(text(), 'DIDs') or contains(text(), 'DID')]")
        dids_clickable = [d for d in dids_visible if d.is_displayed()]
        
        if dids_clickable:
            print("✅ Menú ya está expandido - DIDs visible")
        else:
            print("⚠️  Menú parece cerrado - expandiendo Configuración")
            click_menu_item("Configuración", wait_time=2)
    except:
        print("⚠️  No se pudo verificar - expandiendo Configuración por seguridad")
        click_menu_item("Configuración", wait_time=2)
    
    # Click en DIDs
    print("\n📂 PASO 4.2: Click en 'DIDs'")
    # Intentar varias variantes del texto
    dids_found = False
    for dids_text in ["DIDs", "DID", "dids"]:
        if click_menu_item(dids_text, wait_time=3):
            driver.save_screenshot(str(debug_dir / "04a_navegado_dids.png"))
            print(f"✅ Navegado a DIDs - URL: {driver.current_url}")
            dids_found = True
            break
    
    if not dids_found:
        print("❌ No se pudo navegar a DIDs - intentando URL directa")
        driver.get("https://pbx.neotel2000.com/pbx/client/ivr/did")
        time.sleep(3)
    
    # Esperar a que cargue
    print("\n⏳ PASO 4.3: Esperando a que cargue DIDs...")
    wait_for_content_load(15)
    driver.save_screenshot(str(debug_dir / "04b_dids_cargado.png"))
    
    # Buscar SELECTs visibles
    print("\n📋 PASO 4.4: Analizando SELECTs de DIDs...")
    all_selects = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects = [s for s in all_selects if s.is_displayed()]
    
    print(f"📋 SELECT visibles: {len(visible_selects)}")
    
    for i, select_elem in enumerate(visible_selects):
        try:
            select_id = select_elem.get_attribute('id')
            select_name = select_elem.get_attribute('name')
            select_class = select_elem.get_attribute('class')
            
            print(f"\n  SELECT {i+1}:")
            print(f"    ID: {select_id if select_id else '(sin id)'}")
            print(f"    Name: {select_name if select_name else '(sin name)'}")
            print(f"    Class: {select_class if select_class else '(sin class)'}")
            
            select = Select(select_elem)
            options = select.options
            print(f"    Opciones: {len(options)}")
            
            if len(options) > 0:
                print(f"    Primeras 10 opciones:")
                for j, option in enumerate(options[:10]):
                    print(f"      [{j}] {option.text}")
                
                # ¿Es el de DIDs?
                if len(options) > 50:
                    print(f"    ⭐ ¡Este probablemente es el SELECT de DIDs! (tiene {len(options)} opciones)")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    print("\n" + "="*80)
    print("📋 RESUMEN DIDs")
    print("="*80)
    if visible_selects:
        print(f"✅ Se encontraron {len(visible_selects)} SELECT(s) visible(s)")
        print("👉 Busca cuál tiene números de teléfono (muchas opciones)")
    else:
        print("❌ No se encontraron SELECTs visibles")
    print()
    
    # ========================================================================
    # PASO 5: NAVEGACIÓN A COLAS (CON CLICKS)
    # ========================================================================
    print("=" * 80)
    print("PASO 5: NAVEGANDO A COLAS (CON CLICKS EN MENÚ)")
    print("=" * 80)
    
    # IMPORTANTE: NO hacer click en Configuración si ya está abierto
    print("\n📂 PASO 5.1: Verificando si menú Configuración está expandido")
    try:
        colas_visible = driver.find_elements(By.XPATH, "//*[contains(text(), 'Colas') or contains(text(), 'Queues')]")
        colas_clickable = [c for c in colas_visible if c.is_displayed()]
        
        if colas_clickable:
            print("✅ Menú ya está expandido - Colas visible")
        else:
            print("⚠️  Menú parece cerrado - expandiendo Configuración")
            click_menu_item("Configuración", wait_time=2)
    except:
        print("⚠️  No se pudo verificar - expandiendo Configuración por seguridad")
        click_menu_item("Configuración", wait_time=2)
    
    # Click en Colas
    print("\n📂 PASO 5.2: Click en 'Colas'")
    if click_menu_item("Colas", wait_time=3):
        driver.save_screenshot(str(debug_dir / "05a_navegado_colas.png"))
        print(f"✅ Navegado a Colas - URL: {driver.current_url}")
    else:
        print("❌ No se pudo navegar a Colas")
    
    # Esperar a que cargue
    print("\n⏳ PASO 5.3: Esperando a que cargue Colas...")
    wait_for_content_load(15)
    driver.save_screenshot(str(debug_dir / "05b_colas_cargado.png"))
    
    # Esperar explícitamente a que aparezca el SELECT
    print("\n🔍 PASO 5.4: Esperando a que aparezca el SELECT de colas...")
    try:
        WebDriverWait(driver, 10).until(
            lambda d: len([s for s in d.find_elements(By.CSS_SELECTOR, 'select') if s.is_displayed()]) > 0
        )
        print("✅ SELECT detectado!")
    except:
        print("⚠️  SELECT no apareció automáticamente - esperando 5 segundos más")
        time.sleep(5)
    
    # Buscar SELECTs visibles
    print("\n📋 PASO 5.5: Analizando SELECTs de Colas...")
    all_selects_colas = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects_colas = [s for s in all_selects_colas if s.is_displayed()]
    
    print(f"📋 SELECT visibles: {len(visible_selects_colas)}")
    
    for i, select_elem in enumerate(visible_selects_colas):
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
                
                if len(options) > 20:
                    print(f"    ⭐ ¡Probablemente es el SELECT de COLAS! (tiene {len(options)} opciones)")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    # Buscar elementos de miembros
    print("\n📋 PASO 5.6: Buscando elementos de MIEMBROS...")
    try:
        ext_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Extensión:')]")
        print(f"  ✓ Encontrados {len(ext_elements)} elementos con 'Extensión:'")
        
        if ext_elements:
            print(f"\n  Muestra de los primeros 3:")
            for i, elem in enumerate(ext_elements[:3]):
                text = elem.text
                print(f"    {i+1}. {text[:120]}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
    
    print("\n" + "="*80)
    print("📋 RESUMEN COLAS")
    print("="*80)
    if visible_selects_colas:
        print(f"✅ Se encontraron {len(visible_selects_colas)} SELECT(s) visible(s)")
    else:
        print("❌ No se encontraron SELECTs visibles")
    print()
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("✅ DEBUGGING COMPLETADO")
    print("="*80)
    print()
    print("📁 Screenshots guardados en: debug_screenshots/")
    print()
    print("🔍 REVISA Y DIME:")
    print("  1. EXTENSIONES:")
    print("     - ¿Cuántas tablas visibles? ___")
    print("     - ¿Cuál tiene los datos correctos? TABLA #___")
    print("     - ¿Qué ID/Class tiene? ___")
    print()
    print("  2. DIDs:")
    print("     - ¿Cuántos SELECTs visibles? ___")
    print("     - ¿Cuál tiene los DIDs? SELECT #___")
    print("     - ¿Qué ID tiene? ___")
    print()
    print("  3. COLAS:")
    print("     - ¿Cuántos SELECTs visibles? ___")
    print("     - ¿Cuál tiene las colas? SELECT #___")
    print("     - ¿Qué ID tiene? ___")
    print("     - ¿Encontró elementos con 'Extensión:'? ___")
    print()
    
    input("\n👉 Presiona Enter para cerrar...")
    
except Exception as e:
    print(f"\n❌ ERROR CRÍTICO: {str(e)}")
    import traceback
    traceback.print_exc()
    driver.save_screenshot(str(debug_dir / "ERROR.png"))
    input("\n👉 Presiona Enter para cerrar...")

finally:
    driver.quit()
    print("\n✅ Navegador cerrado")