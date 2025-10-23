#!/usr/bin/env python3
"""
Script de prueba para validar el envío de emails del módulo EmailSender.

Modo por defecto: dry-run (construye el mensaje y muestra resumen, NO envía).
Flag --send : realiza el envío real (usa ConfigAudit.EMAIL_CONFIG o overrides por variables de entorno).

Uso:
    python3 tests/test_email_send.py         # dry-run
    python3 tests/test_email_send.py --send  # enviar realmente

Recomendación: antes de --send, ajusta CONFIG para usar un SMTP de pruebas (Mailtrap) o
modifica temporalmente ConfigAudit.EMAIL_CONFIG para no molestar producción.
También puedes exportar TEST_RECIPIENTS="you@yourdomain.com" para enviar a otra dirección.
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

# Importa las configuraciones y el EmailSender del proyecto
from config_audit import ConfigAudit
from email_sender import EmailSender

def build_sample_changes():
    # Cambios de ejemplo
    return {
        'dids_added': [{'numero': '1111', 'locucion': 'Prueba'}],
        'dids_removed': [],
        'dids_modified': [],
        'extensions_added': [],
        'extensions_removed': [],
        'extensions_modified': [{'extension': '2001', 'anterior': {'estado_colas': 'todas_activas'}, 'actual': {'estado_colas': 'mixto'}}],
        'colas_added': [],
        'colas_removed': [],
        'colas_modified': []
    }

def create_sample_report(path: Path):
    html = f"<html><body><h1>Reporte de prueba - {datetime.now().isoformat()}</h1><p>Contenido de prueba</p></body></html>"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true', help='Enviar realmente el email (por defecto solo dry-run)')
    args = parser.parse_args()

    # Preparar configuración (permite override por env vars)
    cfg = ConfigAudit.EMAIL_CONFIG.copy()
    # Si se define TEST_SMTP_SERVER en entorno, lo usamos
    cfg['smtp_server'] = os.environ.get('TEST_SMTP_SERVER', cfg.get('smtp_server'))
    cfg['smtp_port'] = int(os.environ.get('TEST_SMTP_PORT', cfg.get('smtp_port', 587)))
    cfg['username'] = os.environ.get('TEST_SMTP_USER', cfg.get('username'))
    cfg['password'] = os.environ.get('TEST_SMTP_PASS', cfg.get('password'))
    recipients_override = os.environ.get('TEST_RECIPIENTS')
    if recipients_override:
        cfg['recipients'] = [r.strip() for r in recipients_override.split(',') if r.strip()]

    sender = EmailSender(cfg)

    # Construir cambios y reporte de prueba
    changes = build_sample_changes()
    report_path = create_sample_report(ConfigAudit.REPORTS_DIR / "test_report_html_for_email.html")

    print("=== PRUEBA DE EMAIL (dry-run por defecto) ===")
    print(f"SMTP server: {cfg['smtp_server']}:{cfg['smtp_port']}")
    print(f"From: {cfg.get('from_name')} <{cfg.get('from_email')}>")
    print(f"To: {cfg.get('recipients')}")
    print(f"Report file: {report_path}")
    print()

    if not args.send:
        print("Dry-run: construyendo mensaje y adjunto (NO se enviará).")
        # Llamamos a send_change_report pero interceptamos para no enviar;
        # para seguridad, en dry-run solo construiremos el mensaje usando la función privada _create_text_summary
        summary = sender._create_text_summary(changes, datetime.now(), sum([
            len(changes.get('dids_added', [])),
            len(changes.get('dids_removed', [])),
            len(changes.get('dids_modified', [])),
            len(changes.get('extensions_added', [])),
            len(changes.get('extensions_removed', [])),
            len(changes.get('extensions_modified', [])),
            len(changes.get('colas_added', [])),
            len(changes.get('colas_removed', [])),
            len(changes.get('colas_modified', [])),
        ]))
        print("Resumen de correo (texto):")
        print("-------------------------------------------------")
        print(summary)
        print("-------------------------------------------------")
        print("Fichero HTML de reporte creado en:", report_path)
        print("Si quieres enviar realmente el correo, ejecuta con --send")
        return

    # Enviar realmente
    print("Enviando email REAL...")
    ok = sender.send_change_report(str(report_path), changes, datetime.now())
    if ok:
        print("OK: Email enviado (según respuesta del módulo).")
    else:
        print("ERROR: envío falló. Revisa logs y credenciales.")

if __name__ == '__main__':
    main()
