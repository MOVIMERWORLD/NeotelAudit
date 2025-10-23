#!/usr/bin/env python3
"""
Script para detectar y trabajar con SELECTs que usan Chosen.js
Los SELECTs reales están ocultos con display:none
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
from pathlib import Path

debug_dir = Path("debug_screenshots")
debug_dir.mkdir(exist_ok=True)

print("🔍 DETECTOR DE CHOSEN.JS SELECTs")
print("=" * 80)

options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

def click_menu_item(text, wait_time=3):
    try:
        selectors = [
            f"//a[contains(text(), '{text}')]",
            f"//div[contains(text(), '{text}')]",
            f"//span[contains(text(), '{text}')]",
            f"//*[contains(text(), '{text}')]"
        ]
        
        element = None
        for selector in selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                try:
                    if elem.is_displayed() and elem.is_enabled():
                        element = elem
                        break
                except:
                    continue
            if element:
                break
        
        if not element:
            return False
        
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        
        try:
            element.click()
        except:
            driver.execute_script("arguments[0].click();", element)
        
        time.sleep(wait_time)
        return True
        
    except:
        return False

def find_hidden_selects(page_name):
    """Buscar SELECTs ocultos (incluyendo los de Chosen.js)"""
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALIZANDO: {page_name}")
    print(f"{'='*80}")
    
    # 1. Buscar TODOS los <select> (sin filtrar por visibilidad)
    print("\n1️⃣  Buscando TODOS los <select> (incluso ocultos)...")
    all_selects = driver.find_elements(By.CSS_SELECTOR, 'select')
    print(f"   Total encontrados: {len(all_selects)}")
    
    hidden_selects = []
    
    for i, sel in enumerate(all_selects):
        try:
            sel_id = sel.get_attribute('id')
            sel_name = sel.get_attribute('name')
            sel_class = sel.get_attribute('class')
            
            # Verificar si está oculto
            is_displayed = sel.is_displayed()
            display_css = driver.execute_script("return window.getComputedStyle(arguments[0]).display;", sel)
            
            print(f"\n   SELECT {i+1}:")
            print(f"     ID: {sel_id if sel_id else '(sin id)'}")
            print(f"     Name: {sel_name if sel_name else '(sin name)'}")
            print(f"     Class: {sel_class if sel_class else '(sin class)'}")
            print(f"     is_displayed(): {is_displayed}")
            print(f"     CSS display: {display_css}")
            
            # Aunque esté oculto, intentar leer opciones
            try:
                options = sel.find_elements(By.TAG_NAME, 'option')
                print(f"     Total opciones: {len(options)}")
                
                if len(options) > 0:
                    print(f"     Primeras 10 opciones:")
                    for j, option in enumerate(options[:10]):
                        opt_text = option.text
                        opt_value = option.get_attribute('value')
                        if opt_text or opt_value:
                            print(f"       [{j}] {opt_text if opt_text else opt_value}")
                    
                    if len(options) > 50:
                        print(f"     ⭐ ¡Este SELECT tiene {len(options)} opciones!")
                    
                    # Guardar info del select oculto
                    hidden_selects.append({
                        'element': sel,
                        'id': sel_id,
                        'name': sel_name,
                        'class': sel_class,
                        'options_count': len(options),
                        'options': [(o.text, o.get_attribute('value')) for o in options[:10]]
                    })
                
            except Exception as e:
                print(f"     Error leyendo opciones: {str(e)}")
        
        except Exception as e:
            print(f"   Error analizando SELECT {i+1}: {str(e)}")
    
    # 2. Buscar contenedores Chosen
    print(f"\n2️⃣  Buscando contenedores Chosen.js...")
    chosen_containers = driver.find_elements(By.CSS_SELECTOR, '.chosen-container')
    print(f"   Contenedores Chosen encontrados: {len(chosen_containers)}")
    
    for i, container in enumerate(chosen_containers):
        try:
            container_id = container.get_attribute('id')
            print(f"\n   Chosen Container {i+1}:")
            print(f"     ID: {container_id}")
            
            # El ID del container suele ser: chosen_[id_del_select]
            if container_id and 'chosen' in container_id.lower():
                original_select_id = container_id.replace('_chosen', '').replace('-chosen', '')
                print(f"     Posible SELECT original: #{original_select_id}")
        except:
            pass
    
    # 3. Buscar inputs de búsqueda Chosen
    print(f"\n3️⃣  Buscando inputs de búsqueda Chosen...")
    chosen_inputs = driver.find_elements(By.CSS_SELECTOR, 'input.chosen-search-input')
    print(f"   Inputs de búsqueda encontrados: {len(chosen_inputs)}")
    
    # 4. Tomar screenshot
    screenshot_name = f"{page_name.lower()}_chosen.png"
    driver.save_screenshot(str(debug_dir / screenshot_name))
    print(f"\n📸 Screenshot: {screenshot_name}")
    
    return hidden_selects

try:
    # LOGIN
    print("\n🔐 LOGIN...")
    driver.get("https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server")
    
    wait = WebDriverWait(driver, 30)
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
    password = driver.find_element(By.CSS_SELECTOR, '#password')
    
    username.send_keys("movimerworld")
    password.send_keys("movimer_92")
    driver.find_element(By.CSS_SELECTOR, '#kc-login').click()
    
    time.sleep(8)
    print("✅ Login OK\n")
    
    # ========================================================================
    # ANALIZAR DIDs
    # ========================================================================
    print("=" * 80)
    print("📍 ANALIZANDO DIDs")
    print("=" * 80)
    
    click_menu_item("Configuración", wait_time=2)
    
    for did_variant in ["DIDs", "DID", "dids"]:
        if click_menu_item(did_variant, wait_time=3):
            print(f"✅ Navegado a DIDs con '{did_variant}'")
            break
    
    print(f"📍 URL: {driver.current_url}")
    print("⏳ Esperando 20 segundos...")
    time.sleep(20)
    
    dids_selects = find_hidden_selects("DIDs")
    
    # ========================================================================
    # ANALIZAR COLAS
    # ========================================================================
    print("\n" + "=" * 80)
    print("📍 ANALIZANDO COLAS")
    print("=" * 80)
    
    click_menu_item("Colas", wait_time=3)
    print(f"📍 URL: {driver.current_url}")
    print("⏳ Esperando 20 segundos...")
    time.sleep(20)
    
    colas_selects = find_hidden_selects("Colas")
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*80)
    
    print(f"\n📊 RESUMEN:")
    print(f"   DIDs: {len(dids_selects)} SELECT(s) oculto(s) encontrado(s)")
    print(f"   Colas: {len(colas_selects)} SELECT(s) oculto(s) encontrado(s)")
    
    if dids_selects:
        print(f"\n📋 DIDS - Detalles del primer SELECT:")
        sel = dids_selects[0]
        print(f"   ID: {sel['id']}")
        print(f"   Name: {sel['name']}")
        print(f"   Class: {sel['class']}")
        print(f"   Opciones: {sel['options_count']}")
    
    if colas_selects:
        print(f"\n📋 COLAS - Detalles del primer SELECT:")
        sel = colas_selects[0]
        print(f"   ID: {sel['id']}")
        print(f"   Name: {sel['name']}")
        print(f"   Class: {sel['class']}")
        print(f"   Opciones: {sel['options_count']}")
    
    print(f"\n📁 Screenshots en: debug_screenshots/")
    print(f"   - dids_chosen.png")
    print(f"   - colas_chosen.png")
    
    print(f"\n💡 SIGUIENTE PASO:")
    print(f"   Ahora que sabemos los IDs de los SELECTs ocultos,")
    print(f"   podemos extraer su configuración fácilmente!")
    
    input("\nPresiona Enter para cerrar...")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    driver.save_screenshot(str(debug_dir / "error_chosen.png"))
    input("Presiona Enter para cerrar...")

finally:
    driver.quit()