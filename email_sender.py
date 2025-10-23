#!/usr/bin/env python3
"""
Módulo de envío de emails para reportes de auditoría
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path

class EmailSender:
    """Gestor de envío de emails"""
    
    def __init__(self, config):
        """
        Inicializar gestor de emails
        
        Args:
            config: Diccionario con configuración email
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_change_report(self, report_file, changes, report_date):
        """Enviar email con reporte de cambios (versión mejorada)"""
        try:
            # Calcular totales
            total_ext = (len(changes.get('extensions_added', [])) + 
                        len(changes.get('extensions_removed', [])) + 
                        len(changes.get('extensions_modified', [])))
            
            total_dids = (len(changes.get('dids_added', [])) + 
                        len(changes.get('dids_removed', [])) + 
                        len(changes.get('dids_modified', [])))
            
            total_colas = (len(changes.get('colas_added', [])) + 
                        len(changes.get('colas_removed', [])) + 
                        len(changes.get('colas_modified', [])))
            
            total_changes = total_ext + total_dids + total_colas
            
            # Asunto
            subject = f"🔍 Cambios en Neotel - {report_date.strftime('%d/%m/%Y')} ({total_changes} cambios)"
            
            # Cuerpo del email en texto plano
            body = f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║          REPORTE DE CAMBIOS - CONFIGURACIÓN NEOTEL            ║
    ╚════════════════════════════════════════════════════════════════╝

    📅 Fecha: {report_date.strftime('%d/%m/%Y')}
    🕐 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

    ════════════════════════════════════════════════════════════════

    📊 RESUMEN EJECUTIVO
    ════════════════════════════════════════════════════════════════

    🔢 TOTAL DE CAMBIOS: {total_changes}

    📞 Extensiones: {total_ext} cambios
        ✅ Añadidas:    {len(changes.get('extensions_added', []))}
        ❌ Eliminadas:  {len(changes.get('extensions_removed', []))}
        🔄 Modificadas: {len(changes.get('extensions_modified', []))}

    📱 DIDs: {total_dids} cambios
        ✅ Añadidos:    {len(changes.get('dids_added', []))}
        ❌ Eliminados:  {len(changes.get('dids_removed', []))}
        🔄 Modificados: {len(changes.get('dids_modified', []))}

    📋 Colas: {total_colas} cambios
        ✅ Añadidas:    {len(changes.get('colas_added', []))}
        ❌ Eliminadas:  {len(changes.get('colas_removed', []))}
        🔄 Modificadas: {len(changes.get('colas_modified', []))}

    ════════════════════════════════════════════════════════════════

    🔗 REPORTE COMPLETO
    ════════════════════════════════════════════════════════════════

    Para ver el detalle completo de todos los cambios, abre el archivo
    adjunto en tu navegador web.

    ════════════════════════════════════════════════════════════════

    Este es un reporte automático del Sistema de Auditoría Neotel.
    Para consultas, contacta al equipo de IT.

    ════════════════════════════════════════════════════════════════
    """
            
            # Enviar email
            if self._send_email(subject, body, [report_file]):
                print(f"✅ Email de cambios enviado con {total_changes} cambios detectados")
                return True
            else:
                print(f"❌ Error enviando email de cambios")
                return False
                
        except Exception as e:
            print(f"❌ Error preparando email de cambios: {str(e)}")
            return False
    
    def send_no_changes_notification(self, report_date):
        """
        Enviar notificación de que no hubo cambios
        
        Args:
            report_date: Fecha del reporte
        """
        try:
            subject = f"✅ Sin cambios en Neotel - {report_date.strftime('%d/%m/%Y')}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2e7d32;">✅ Sin cambios detectados</h2>
                </div>
                
                <p>La auditoría de configuración de Neotel se ha completado exitosamente.</p>
                
                <p><strong>Fecha de auditoría:</strong> {report_date.strftime('%d/%m/%Y')}</p>
                <p><strong>Hora de ejecución:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
                
                <div style="background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 5px;">
                    <p style="margin: 0;"><strong>Resultado:</strong> No se detectaron cambios en:</p>
                    <ul>
                        <li>DIDs (numeraciones)</li>
                        <li>Extensiones (agentes)</li>
                        <li>Colas de llamadas</li>
                    </ul>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="color: #666; font-size: 12px;">
                    Este es un mensaje automático del Auditor de Configuración Neotel.<br>
                    Si tiene alguna pregunta, contacte con el departamento de IT.
                </p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            msg['To'] = ', '.join(self.config['recipients'])
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            self._send_email(msg)
            
            self.logger.info("✅ Notificación de 'sin cambios' enviada")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error enviando notificación: {str(e)}")
            return False
    
    def send_error_notification(self, error_message, error_details=None):
        """
        Enviar notificación de error a equipo técnico
        
        Args:
            error_message: Mensaje de error principal
            error_details: Detalles adicionales del error
        """
        try:
            subject = f"🔴 ERROR - Auditor Neotel - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #c62828;">🔴 Error en Auditoría Neotel</h2>
                </div>
                
                <p><strong>Fecha y hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                
                <div style="background: #fff3e0; padding: 15px; margin: 20px 0; border-left: 3px solid #ff9800;">
                    <h3 style="margin-top: 0;">Error:</h3>
                    <pre style="background: white; padding: 10px; overflow-x: auto;">{error_message}</pre>
                </div>
                
                {f'<div style="background: #f5f5f5; padding: 15px; margin: 20px 0;"><h3 style="margin-top: 0;">Detalles:</h3><pre style="background: white; padding: 10px; overflow-x: auto;">{error_details}</pre></div>' if error_details else ''}
                
                <p><strong>Acción requerida:</strong> Revisar logs y verificar configuración del auditor.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="color: #666; font-size: 12px;">
                    Notificación automática del Auditor de Configuración Neotel.
                </p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            msg['To'] = ', '.join(self.config['recipients_errors'])
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            self._send_email(msg)
            
            self.logger.info("✅ Notificación de error enviada a equipo técnico")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error enviando notificación de error: {str(e)}")
            return False
    
    def _create_text_summary(self, changes_summary, report_date, total_changes):
        """Crear resumen en texto plano"""
        lines = []
        lines.append(f"REPORTE DE CAMBIOS - NEOTEL")
        lines.append(f"Fecha: {report_date.strftime('%d/%m/%Y')}")
        lines.append(f"Total de cambios: {total_changes}")
        lines.append("=" * 60)
        lines.append("")
        
        # DIDs
        if any(k in changes_summary for k in ['dids_added', 'dids_removed', 'dids_modified']):
            lines.append("📞 CAMBIOS EN DIDs:")
            if changes_summary.get('dids_added'):
                lines.append(f"  + Añadidos: {len(changes_summary['dids_added'])}")
            if changes_summary.get('dids_removed'):
                lines.append(f"  - Eliminados: {len(changes_summary['dids_removed'])}")
            if changes_summary.get('dids_modified'):
                lines.append(f"  ≠ Modificados: {len(changes_summary['dids_modified'])}")
            lines.append("")
        
        # Extensiones
        if any(k in changes_summary for k in ['extensions_added', 'extensions_removed', 'extensions_modified']):
            lines.append("👤 CAMBIOS EN EXTENSIONES:")
            if changes_summary.get('extensions_added'):
                lines.append(f"  + Añadidas: {len(changes_summary['extensions_added'])}")
            if changes_summary.get('extensions_removed'):
                lines.append(f"  - Eliminadas: {len(changes_summary['extensions_removed'])}")
            if changes_summary.get('extensions_modified'):
                lines.append(f"  ≠ Modificadas: {len(changes_summary['extensions_modified'])}")
            lines.append("")
        
        # Colas
        if any(k in changes_summary for k in ['colas_added', 'colas_removed', 'colas_modified']):
            lines.append("📋 CAMBIOS EN COLAS:")
            if changes_summary.get('colas_added'):
                lines.append(f"  + Añadidas: {len(changes_summary['colas_added'])}")
            if changes_summary.get('colas_removed'):
                lines.append(f"  - Eliminadas: {len(changes_summary['colas_removed'])}")
            if changes_summary.get('colas_modified'):
                lines.append(f"  ≠ Modificadas: {len(changes_summary['colas_modified'])}")
            lines.append("")
        
        lines.append("Para ver el detalle completo, consulte el reporte HTML adjunto.")
        
        return "\n".join(lines)
    
    def _send_email(self, msg):
        """
        Enviar email usando SMTP
        
        Args:
            msg: Mensaje MIMEMultipart configurado
        """
        try:
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['username'], self.config['password'])
                server.send_message(msg)
                
            self.logger.info(f"📧 Email enviado exitosamente")
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("❌ Error de autenticación SMTP - Verifica usuario y contraseña")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"❌ Error SMTP: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error inesperado enviando email: {str(e)}")
            raise