#!/usr/bin/env python3
"""
Script de debugging exhaustivo para identificar selectores correctos
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
from pathlib import Path

# Crear carpeta para screenshots
debug_dir = Path("debug_screenshots")
debug_dir.mkdir(exist_ok=True)

print("=" * 80)
print("🔍 DEBUGGING EXHAUSTIVO DE SELECTORES NEOTEL")
print("=" * 80)
print()

# Configurar Chrome
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

try:
    # ========================================================================
    # PASO 1: LOGIN
    # ========================================================================
    print("=" * 80)
    print("PASO 1: LOGIN")
    print("=" * 80)
    
    driver.get("https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server")
    
    wait = WebDriverWait(driver, 20)
    
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
    password = driver.find_element(By.CSS_SELECTOR, '#password')
    
    username.send_keys("movimerworld")
    password.send_keys("movimer_92")
    
    driver.find_element(By.CSS_SELECTOR, '#kc-login').click()
    
    print("⏳ Esperando login...")
    time.sleep(5)
    
    print(f"✅ Login OK - URL actual: {driver.current_url}")
    driver.save_screenshot(str(debug_dir / "01_login_ok.png"))
    print(f"📸 Screenshot guardado: 01_login_ok.png")
    print()
    
    # ========================================================================
    # PASO 2: IR A EXTENSIONES
    # ========================================================================
    print("=" * 80)
    print("PASO 2: NAVEGANDO A EXTENSIONES")
    print("=" * 80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/ivr/extension/search")
    print("⏳ Esperando carga de página...")
    time.sleep(5)
    
    print(f"✅ Página cargada - URL: {driver.current_url}")
    driver.save_screenshot(str(debug_dir / "02_extensiones_inicial.png"))
    print(f"📸 Screenshot guardado: 02_extensiones_inicial.png")
    print()
    
    # Esperar más tiempo para JavaScript
    print("⏳ Esperando 5 segundos adicionales para JavaScript...")
    time.sleep(5)
    driver.save_screenshot(str(debug_dir / "03_extensiones_con_datos.png"))
    print(f"📸 Screenshot guardado: 03_extensiones_con_datos.png")
    print()
    
    # ========================================================================
    # PASO 3: ANALIZAR TODAS LAS TABLAS
    # ========================================================================
    print("=" * 80)
    print("PASO 3: ANALIZANDO TODAS LAS TABLAS")
    print("=" * 80)
    
    tables = driver.find_elements(By.CSS_SELECTOR, 'table')
    print(f"📊 Total de tablas encontradas: {len(tables)}")
    print()
    
    for i, table in enumerate(tables):
        print(f"\n{'='*60}")
        print(f"TABLA {i+1} de {len(tables)}")
        print(f"{'='*60}")
        
        try:
            # Información de la tabla
            table_class = table.get_attribute('class')
            table_id = table.get_attribute('id')
            
            print(f"  ID: {table_id if table_id else '(sin id)'}")
            print(f"  Class: {table_class if table_class else '(sin class)'}")
            
            # ¿Es visible?
            is_visible = table.is_displayed()
            print(f"  ¿Visible?: {is_visible}")
            
            if not is_visible:
                print("  ⚠️  Tabla NO visible - saltando")
                continue
            
            # Buscar thead
            theads = table.find_elements(By.TAG_NAME, 'thead')
            print(f"  <thead>: {len(theads)} encontrados")
            
            if theads:
                headers = theads[0].find_elements(By.TAG_NAME, 'th')
                print(f"  Headers ({len(headers)}):")
                for j, header in enumerate(headers[:15]):  # Máximo 15
                    text = header.text.strip()
                    if text:
                        print(f"    [{j}] {text}")
            
            # Buscar tbody
            tbodies = table.find_elements(By.TAG_NAME, 'tbody')
            print(f"  <tbody>: {len(tbodies)} encontrados")
            
            if tbodies:
                rows = tbodies[0].find_elements(By.TAG_NAME, 'tr')
                print(f"  Filas de datos: {len(rows)}")
                
                if len(rows) > 0:
                    print(f"\n  📋 PRIMERA FILA (muestra):")
                    first_row = rows[0]
                    cells = first_row.find_elements(By.TAG_NAME, 'td')
                    print(f"    Celdas en la fila: {len(cells)}")
                    
                    for k, cell in enumerate(cells[:15]):  # Máximo 15
                        text = cell.text.strip()
                        if text:
                            print(f"      [{k}] {text[:60]}")  # Máximo 60 caracteres
                        else:
                            # Ver si tiene elementos hijos
                            children = cell.find_elements(By.XPATH, ".//*")
                            if children:
                                print(f"      [{k}] (vacío - tiene {len(children)} elementos hijo)")
                            else:
                                print(f"      [{k}] (vacío)")
                    
                    # Mostrar 3 filas más si hay
                    if len(rows) > 1:
                        print(f"\n  📋 SEGUNDA FILA (muestra):")
                        second_row = rows[1]
                        cells2 = second_row.find_elements(By.TAG_NAME, 'td')
                        for k, cell in enumerate(cells2[:10]):
                            text = cell.text.strip()
                            if text:
                                print(f"      [{k}] {text[:60]}")
                
        except Exception as e:
            print(f"  ❌ Error analizando tabla: {str(e)}")
    
    print("\n" + "="*80)
    print("RESUMEN TABLA EXTENSIONES")
    print("="*80)
    print("\n¿Cuál de las tablas anteriores contiene las extensiones?")
    print("(Busca la que tiene headers como: Extensión, Nombre, Grupo, etc.)")
    print()
    
    # ========================================================================
    # PASO 4: ANALIZAR DIDs
    # ========================================================================
    print("\n" + "="*80)
    print("PASO 4: NAVEGANDO A DIDs")
    print("="*80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/ivr/did")
    print("⏳ Esperando carga...")
    time.sleep(5)
    
    driver.save_screenshot(str(debug_dir / "04_dids_pagina.png"))
    print(f"📸 Screenshot guardado: 04_dids_pagina.png")
    
    # Buscar elementos SELECT
    selects = driver.find_elements(By.CSS_SELECTOR, 'select')
    print(f"\n📋 SELECT encontrados: {len(selects)}")
    
    for i, select_elem in enumerate(selects):
        try:
            select_id = select_elem.get_attribute('id')
            select_name = select_elem.get_attribute('name')
            select_class = select_elem.get_attribute('class')
            is_visible = select_elem.is_displayed()
            
            print(f"\n  SELECT {i+1}:")
            print(f"    ID: {select_id if select_id else '(sin id)'}")
            print(f"    Name: {select_name if select_name else '(sin name)'}")
            print(f"    Class: {select_class if select_class else '(sin class)'}")
            print(f"    ¿Visible?: {is_visible}")
            
            if is_visible:
                select = Select(select_elem)
                options = select.options
                print(f"    Opciones: {len(options)}")
                
                # Mostrar primeras 5 opciones
                print(f"    Primeras opciones:")
                for j, option in enumerate(options[:5]):
                    print(f"      [{j}] {option.text}")
                
                # ¿Es el select de DIDs?
                if len(options) > 50 and any(char.isdigit() for char in options[0].text):
                    print(f"    ⭐ ¡Este probablemente es el SELECT de DIDs!")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    print("\n" + "="*80)
    print("RESUMEN DIDs")
    print("="*80)
    print("¿Cuál SELECT tiene los números de teléfono (DIDs)?")
    print()
    
    # ========================================================================
    # PASO 5: ANALIZAR COLAS
    # ========================================================================
    print("\n" + "="*80)
    print("PASO 5: NAVEGANDO A COLAS")
    print("="*80)
    
    driver.get("https://pbx.neotel2000.com/pbx/client/queue")
    print("⏳ Esperando carga...")
    time.sleep(5)
    
    driver.save_screenshot(str(debug_dir / "05_colas_pagina.png"))
    print(f"📸 Screenshot guardado: 05_colas_pagina.png")
    
    # Buscar elementos SELECT
    selects_colas = driver.find_elements(By.CSS_SELECTOR, 'select')
    print(f"\n📋 SELECT encontrados: {len(selects_colas)}")
    
    for i, select_elem in enumerate(selects_colas):
        try:
            select_id = select_elem.get_attribute('id')
            is_visible = select_elem.is_displayed()
            
            print(f"\n  SELECT {i+1}:")
            print(f"    ID: {select_id if select_id else '(sin id)'}")
            print(f"    ¿Visible?: {is_visible}")
            
            if is_visible:
                select = Select(select_elem)
                options = select.options
                print(f"    Opciones: {len(options)}")
                
                # Mostrar primeras 5 opciones
                print(f"    Primeras opciones:")
                for j, option in enumerate(options[:5]):
                    print(f"      [{j}] {option.text}")
                
                # ¿Es el select de Colas?
                if len(options) > 20:
                    print(f"    ⭐ ¡Este probablemente es el SELECT de COLAS!")
        
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    # Buscar sección de miembros
    print("\n📋 Buscando sección de MIEMBROS...")
    
    # Intentar varios selectores posibles
    member_selectors = [
        '.miembros',
        '.members',
        '[class*="miembro"]',
        '[class*="member"]',
        'div:has(h3:contains("Miembros"))',
        'div:has(h4:contains("Miembros"))',
    ]
    
    for selector in member_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  ✓ Encontrado con selector: {selector}")
                print(f"    Elementos: {len(elements)}")
        except:
            pass
    
    # Buscar texto que contenga "Extensión:"
    print("\n📋 Buscando elementos con texto 'Extensión:'...")
    try:
        extension_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Extensión:')]")
        print(f"  Encontrados: {len(extension_elements)} elementos")
        
        if extension_elements:
            print(f"\n  Muestra de los primeros 3:")
            for i, elem in enumerate(extension_elements[:3]):
                text = elem.text
                parent_html = elem.get_attribute('outerHTML')[:200]
                print(f"\n    Elemento {i+1}:")
                print(f"      Texto: {text}")
                print(f"      HTML: {parent_html}...")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    print("\n" + "="*80)
    print("✅ DEBUGGING COMPLETADO")
    print("="*80)
    print()
    print("📁 Screenshots guardados en: debug_screenshots/")
    print()
    print("PRÓXIMO PASO:")
    print("1. Revisa la salida de arriba")
    print("2. Identifica qué tabla/select/selector usar")
    print("3. Pásame los números de las tablas/selects correctos")
    print()
    
    input("Presiona Enter para cerrar...")
    
finally:
    driver.quit()
    print("\n✅ Navegador cerrado")