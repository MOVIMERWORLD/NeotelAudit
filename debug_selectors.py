#!/usr/bin/env python3
"""Debug rápido de selectores"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Configurar Chrome
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

try:
    # Login
    driver.get("https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server")
    
    wait = WebDriverWait(driver, 20)
    
    username = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
    password = driver.find_element(By.CSS_SELECTOR, '#password')
    
    username.send_keys("movimerworld")
    password.send_keys("movimer_92")
    
    driver.find_element(By.CSS_SELECTOR, '#kc-login').click()
    
    time.sleep(5)
    
    # Ir a extensiones
    driver.get("https://pbx.neotel2000.com/pbx/client/ivr/extension/search")
    time.sleep(5)
    
    print("\n=== PÁGINA DE EXTENSIONES ===")
    print("URL:", driver.current_url)
    
    # Probar selectores
    print("\n¿Hay tabla?")
    tables = driver.find_elements(By.CSS_SELECTOR, '.table')
    print(f"  Encontradas {len(tables)} tablas")
    
    print("\n¿Hay filas?")
    rows = driver.find_elements(By.CSS_SELECTOR, '.table tbody tr')
    print(f"  Encontradas {len(rows)} filas")
    
    if rows:
        print("\nPrimera fila:")
        first_row = rows[0]
        cells = first_row.find_elements(By.TAG_NAME, 'td')
        print(f"  Celdas: {len(cells)}")
        for i, cell in enumerate(cells):
            print(f"  Celda {i}: {cell.text[:50]}")
    
    input("\nPresiona Enter para cerrar...")
    
finally:
    driver.quit()