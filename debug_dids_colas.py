#!/usr/bin/env python3
"""
Script RÁPIDO solo para DIDs y Colas
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

print("🚀 DEBUG RÁPIDO: SOLO DIDs Y COLAS")
print("=" * 80)

options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

def click_menu_item(text, wait_time=3):
    try:
        print(f"🔍 Buscando: '{text}'")
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
        
        print(f"✅ Click en '{text}'")
        time.sleep(wait_time)
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

try:
    # LOGIN
    print("\n1️⃣  LOGIN...")
    driver.get("https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server")
    
    wait = WebDriverWait(driver, 30)
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
    password = driver.find_element(By.CSS_SELECTOR, '#password')
    
    username.send_keys("movimerworld")
    password.send_keys("movimer_92")
    driver.find_element(By.CSS_SELECTOR, '#kc-login').click()
    
    time.sleep(8)
    print(f"✅ Login OK")
    
    # ========================================================================
    # DIDs
    # ========================================================================
    print("\n" + "=" * 80)
    print("2️⃣  PROBANDO DIDs")
    print("=" * 80)
    
    # Expandir Configuración (solo una vez)
    print("\n📂 Expandiendo menú Configuración...")
    click_menu_item("Configuración", wait_time=2)
    
    # Click en DIDs (con variantes)
    print("\n📂 Navegando a DIDs...")
    dids_found = False
    for dids_text in ["DIDs", "DID", "dids", "Did"]:
        if click_menu_item(dids_text, wait_time=3):
            dids_found = True
            break
    
    if not dids_found:
        print("⚠️  No se encontró por menú - probando URL directa")
        driver.get("https://pbx.neotel2000.com/pbx/client/ivr/did")
        time.sleep(5)
    
    driver.save_screenshot(str(debug_dir / "dids_test.png"))
    print(f"📸 Screenshot: dids_test.png")
    
    # Esperar y buscar SELECTs
    print("\n⏳ Esperando 15 segundos...")
    time.sleep(15)
    
    print("\n🔍 Buscando SELECTs...")
    all_selects = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects = [s for s in all_selects if s.is_displayed()]
    
    print(f"📋 SELECTs visibles: {len(visible_selects)}")
    
    for i, select_elem in enumerate(visible_selects):
        select_id = select_elem.get_attribute('id')
        select_name = select_elem.get_attribute('name')
        
        print(f"\n  SELECT {i+1}:")
        print(f"    ID: {select_id}")
        print(f"    Name: {select_name}")
        
        select = Select(select_elem)
        options = select.options
        print(f"    Total opciones: {len(options)}")
        
        if len(options) > 0:
            print(f"    Primeras 5:")
            for j, opt in enumerate(options[:5]):
                print(f"      [{j}] {opt.text}")
    
    # ========================================================================
    # COLAS
    # ========================================================================
    print("\n" + "=" * 80)
    print("3️⃣  PROBANDO COLAS")
    print("=" * 80)
    
    # El menú YA ESTÁ ABIERTO - no hacer click en Configuración de nuevo
    print("\n📂 Navegando a Colas (menú ya abierto)...")
    
    # Click en Colas
    if click_menu_item("Colas", wait_time=3):
        print("✅ Navegado a Colas")
    else:
        print("⚠️  No se encontró - probando URL directa")
        driver.get("https://pbx.neotel2000.com/pbx/client/ivr/queues")
        time.sleep(5)
    
    driver.save_screenshot(str(debug_dir / "colas_test.png"))
    print(f"📸 Screenshot: colas_test.png")
    
    # Esperar y buscar SELECTs
    print("\n⏳ Esperando 15 segundos...")
    time.sleep(15)
    
    print("\n🔍 Buscando SELECTs...")
    all_selects_colas = driver.find_elements(By.CSS_SELECTOR, 'select')
    visible_selects_colas = [s for s in all_selects_colas if s.is_displayed()]
    
    print(f"📋 SELECTs visibles: {len(visible_selects_colas)}")
    
    for i, select_elem in enumerate(visible_selects_colas):
        select_id = select_elem.get_attribute('id')
        select_name = select_elem.get_attribute('name')
        
        print(f"\n  SELECT {i+1}:")
        print(f"    ID: {select_id}")
        print(f"    Name: {select_name}")
        
        select = Select(select_elem)
        options = select.options
        print(f"    Total opciones: {len(options)}")
        
        if len(options) > 0:
            print(f"    Primeras 5:")
            for j, opt in enumerate(options[:5]):
                print(f"      [{j}] {opt.text}")
    
    # Buscar miembros
    print("\n🔍 Buscando elementos 'Extensión:'...")
    ext_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Extensión:')]")
    print(f"📋 Encontrados: {len(ext_elements)}")
    
    if ext_elements:
        for i, elem in enumerate(ext_elements[:3]):
            print(f"  {i+1}. {elem.text[:120]}")
    
    print("\n" + "=" * 80)
    print("✅ DEBUG COMPLETADO")
    print("=" * 80)
    print("\n📁 Screenshots en: debug_screenshots/")
    print("  - dids_test.png")
    print("  - colas_test.png")
    
    input("\nPresiona Enter para cerrar...")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    input("\nPresiona Enter para cerrar...")

finally:
    driver.quit()