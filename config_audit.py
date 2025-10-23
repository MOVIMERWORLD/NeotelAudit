#!/usr/bin/env python3
"""
Configuración para el Auditor de Configuración Neotel
"""

import os
from datetime import datetime
from pathlib import Path

class ConfigAudit:
    """Configuración centralizada para el auditor"""
    
    # === CREDENCIALES NEOTEL ===
    NEOTEL_USERNAME = "movimerworld"
    NEOTEL_PASSWORD = "movimer_92"
    
    # === URLs NEOTEL ===
    LOGIN_URL = "https://pbx.neotel2000.com/auth/realms/Neotel/protocol/openid-connect/auth?redirect_uri=https%3A%2F%2Fpbx.neotel2000.com%2Flogin%2Fcallback&response_type=code&client_id=pbx-resource-server"
    BASE_URL = "https://pbx.neotel2000.com"
    EXTENSIONS_URL = f"{BASE_URL}/pbx/client/ivr/extension/search"
    DIDS_URL = f"{BASE_URL}/pbx/client/ivr/did"
    COLAS_URL = f"{BASE_URL}/pbx/client/queue"
    
    # === CONFIGURACIÓN EMAIL ===
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'notificacionesmovimer@gmail.com',
        'password': 'uimo vgyg ssif odam',
        'recipients': ['it@movimer.com'],  # Destinatario principal
        'recipients_errors': ['igalinov@movimer.com'],  # Solo errores técnicos
        'from_name': 'Auditor Neotel',
        'from_email': 'notificacionesmovimer@gmail.com'
    }
    
    # === DIRECTORIOS ===
    BASE_DIR = Path(__file__).parent
    SNAPSHOTS_DIR = BASE_DIR / "config_snapshots"
    REPORTS_DIR = BASE_DIR / "change_reports"
    LOG_DIR = BASE_DIR / "logs"
    DOWNLOAD_DIR = BASE_DIR / "temp_downloads"
    
    # === CONFIGURACIÓN GENERAL ===
    RETENTION_DAYS = 30  # Días de retención de snapshots
    HEADLESS_BROWSER = True  # Chrome sin interfaz gráfica
    
    # === LOGGING ===
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # === TIMEOUTS ===
    PAGE_LOAD_TIMEOUT = 30
    ELEMENT_WAIT_TIMEOUT = 20
    DOWNLOAD_TIMEOUT = 60
    
    # === SELECTORES CSS (basados en análisis de Chosen.js) ===
    SELECTORES = {
        # Login
        'username_field': '#username',
        'password_field': '#password',
        'login_button': '#kc-login',
    
        # Extensiones
        'extensions_table': 'table.table-responsive-lg.table-sm.table-hover tbody tr',
    
        # DIDs - CORREGIDOS CON IDs EXACTOS
        'dids_select': '#configuration_dids_view_did_list_dids',
        'did_detail_panel': '#configuration_dids_view_did_detail',
        
        # DIDs - Campos de detalle (IDs confirmados)
        'did_locucion': '#configuration_dids_view_did_details_loc',
        'did_accion1': '#configuration_dids_view_did_details_action1',
        'did_accion2': '#configuration_dids_view_did_details_action2',
        'did_accion3': '#configuration_dids_view_did_details_action3',
        'did_accion4': '#configuration_dids_view_did_details_action4',
        'did_accion5': '#configuration_dids_view_did_details_action5',  # Por patrón, confirmar si existe
    
        # Colas
        'colas_select': '#configuration_queues_view_queue_list_queues',
        'colas_detalle': '#configuration_queues_view_queue_detail',
        'colas_miembros': '#configuration_queues_view_queue_details_agents'
    }
    
    @classmethod
    def create_directories(cls):
        """Crear todos los directorios necesarios"""
        for directory in [cls.SNAPSHOTS_DIR, cls.REPORTS_DIR, 
                         cls.LOG_DIR, cls.DOWNLOAD_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_snapshot_filename(cls, date=None):
        """Obtener nombre de archivo snapshot para una fecha"""
        if date is None:
            date = datetime.now().date()
        return cls.SNAPSHOTS_DIR / f"{date.strftime('%Y-%m-%d')}_config.json"
    
    @classmethod
    def get_report_filename(cls, date=None):
        """Obtener nombre de archivo reporte para una fecha"""
        if date is None:
            date = datetime.now().date()
        return cls.REPORTS_DIR / f"{date.strftime('%Y-%m-%d')}_changes.html"
    
    @classmethod
    def validate_config(cls):
        """Validar que la configuración es correcta"""
        errors = []
        
        if not cls.NEOTEL_USERNAME or not cls.NEOTEL_PASSWORD:
            errors.append("Credenciales Neotel no configuradas")
        
        if not cls.EMAIL_CONFIG['username'] or not cls.EMAIL_CONFIG['password']:
            errors.append("Credenciales email no configuradas")
        
        if not cls.EMAIL_CONFIG['recipients']:
            errors.append("No hay destinatarios configurados para reportes")
        
        if errors:
            print("❌ ERRORES DE CONFIGURACIÓN:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def get_log_filename(cls):
        """Obtener nombre del archivo de log del día"""
        return cls.LOG_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.log"