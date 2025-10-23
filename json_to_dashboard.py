#!/usr/bin/env python3
"""
Generador de Dashboard HTML Interactivo
Crea un dashboard profesional y visual desde snapshots JSON
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Importar configuración
from config_audit import ConfigAudit

class DashboardGenerator:
    """Generador de dashboard HTML profesional"""
    
    def __init__(self):
        """Inicializar generador"""
        pass
    
    def generate_html_dashboard(self, json_file, output_file=None):
        """Generar dashboard HTML completo"""
        try:
            print(f"📖 Leyendo archivo JSON: {json_file}")
            
            # Leer JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer configuración
            if 'config' in data:
                config_data = data['config']
                timestamp = data.get('timestamp', datetime.now().isoformat())
            else:
                config_data = data
                timestamp = datetime.now().isoformat()
            
            print("🎨 Generando dashboard HTML...")
            
            # Generar HTML completo
            html = self._generate_complete_html(config_data, timestamp)
            
            # Generar nombre de archivo si no se proporciona
            if output_file is None:
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = ConfigAudit.REPORTS_DIR / f"dashboard_neotel_{timestamp_str}.html"
            
            # Guardar
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"✅ Dashboard generado exitosamente: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Error generando dashboard: {str(e)}")
            raise
    
    def _generate_complete_html(self, config_data, timestamp):
        """Generar HTML completo con estilos y JavaScript"""
        
        extensiones = config_data.get('extensiones', [])
        dids = config_data.get('dids', [])
        colas = config_data.get('colas', [])
        
        # Calcular estadísticas
        stats = self._calculate_stats(config_data)
        
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Configuración Neotel</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            /* Paleta corporativa minimalista */
            --primary: #2c3e50;
            --primary-light: #34495e;
            --accent: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --info: #3498db;
            
            /* Neutros */
            --background: #f8f9fa;
            --surface: #ffffff;
            --border: #dee2e6;
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --text-light: #95a5a6;
            
            /* Sombras sutiles */
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.12);
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--background);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-primary);
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: var(--surface);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }}
        
        /* Header - Minimalista */
        .header {{
            background: var(--primary);
            color: white;
            padding: 30px 40px;
            border-bottom: 3px solid var(--accent);
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .header .timestamp {{
            font-size: 13px;
            opacity: 0.85;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 400;
        }}
        
        /* Stats Cards - Limpias y profesionales */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            padding: 30px 40px;
            background: var(--background);
        }}
        
        .stat-card {{
            background: var(--surface);
            padding: 24px;
            border-radius: 6px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
            border-left: 3px solid var(--primary);
        }}
        
        .stat-card:hover {{
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }}
        
        .stat-card.success {{
            border-left-color: var(--success);
        }}
        
        .stat-card.warning {{
            border-left-color: var(--warning);
        }}
        
        .stat-card.info {{
            border-left-color: var(--info);
        }}
        
        .stat-card .icon {{
            font-size: 32px;
            margin-bottom: 12px;
            opacity: 0.9;
        }}
        
        .stat-card .label {{
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .stat-card .value {{
            font-size: 32px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}
        
        .stat-card .breakdown {{
            font-size: 13px;
            color: var(--text-light);
            line-height: 1.4;
        }}
        
        /* Navigation Tabs - Minimalista */
        .tabs {{
            display: flex;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 0 40px;
            gap: 8px;
            overflow-x: auto;
        }}
        
        .tab {{
            padding: 14px 20px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            border-bottom: 2px solid transparent;
            white-space: nowrap;
        }}
        
        .tab:hover {{
            color: var(--primary);
            background: rgba(52, 73, 94, 0.04);
        }}
        
        .tab.active {{
            color: var(--primary);
            border-bottom-color: var(--accent);
        }}
        
        /* Content */
        .content {{
            padding: 40px;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.2s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Search Bar - Limpia */
        .search-bar {{
            margin-bottom: 24px;
            position: relative;
        }}
        
        .search-bar input {{
            width: 100%;
            padding: 12px 40px 12px 16px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s ease;
            background: var(--surface);
            color: var(--text-primary);
        }}
        
        .search-bar input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }}
        
        .search-bar input::placeholder {{
            color: var(--text-light);
        }}
        
        .search-bar::after {{
            content: "🔍";
            position: absolute;
            right: 14px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
            opacity: 0.5;
        }}
        
        /* Tables - Minimalistas */
        .table-container {{
            overflow-x: auto;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
        }}
        
        thead {{
            background: var(--primary);
            color: white;
        }}
        
        th {{
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }}
        
        tbody tr {{
            border-bottom: 1px solid var(--border);
            transition: background 0.15s ease;
        }}
        
        tbody tr:last-child {{
            border-bottom: none;
        }}
        
        tbody tr:hover {{
            background: rgba(52, 73, 94, 0.02);
        }}
        
        td {{
            padding: 14px 16px;
            font-size: 14px;
            color: var(--text-primary);
        }}
        
        td strong {{
            font-weight: 600;
            color: var(--primary);
        }}
        
        /* Badges - Minimalistas */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .badge.success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .badge.warning {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .badge.info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        /* Accordion (Colas) - Minimalista */
        .accordion {{
            margin-bottom: 12px;
        }}
        
        .accordion-header {{
            background: var(--surface);
            padding: 18px 20px;
            cursor: pointer;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
            border: 1px solid var(--border);
        }}
        
        .accordion-header:hover {{
            background: rgba(52, 73, 94, 0.02);
            border-color: var(--primary);
        }}
        
        .accordion-header.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            border-radius: 6px 6px 0 0;
        }}
        
        .accordion-title {{
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .accordion-stats {{
            display: flex;
            gap: 12px;
            font-size: 13px;
        }}
        
        .accordion-icon {{
            transition: transform 0.2s ease;
            font-size: 20px;
            opacity: 0.7;
        }}
        
        .accordion-header.active .accordion-icon {{
            transform: rotate(180deg);
        }}
        
        .accordion-content {{
            display: none;
            padding: 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-top: none;
            border-radius: 0 0 6px 6px;
        }}
        
        .accordion-content.active {{
            display: block;
            animation: slideDown 0.2s ease;
        }}
        
        @keyframes slideDown {{
            from {{ opacity: 0; max-height: 0; }}
            to {{ opacity: 1; max-height: 1000px; }}
        }}
        
        .members-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        
        .member-card {{
            background: var(--background);
            padding: 14px 16px;
            border-radius: 6px;
            border-left: 3px solid var(--success);
            transition: all 0.15s ease;
        }}
        
        .member-card:hover {{
            box-shadow: var(--shadow-sm);
            transform: translateX(3px);
        }}
        
        .member-card.paused {{
            border-left-color: var(--danger);
        }}
        
        .member-name {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .member-details {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.4;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-light);
        }}
        
        .empty-state .icon {{
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.2;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 22px;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
                padding: 20px;
                gap: 16px;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .tabs {{
                padding: 0 20px;
            }}
            
            table {{
                font-size: 13px;
            }}
            
            th, td {{
                padding: 10px 12px;
            }}
            
            .members-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>
                <span>📊</span>
                Dashboard Configuración Neotel
            </h1>
            <div class="timestamp">
                <span>🕐</span>
                Snapshot: {datetime.fromisoformat(timestamp).strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📞</div>
                <div class="label">Extensiones</div>
                <div class="value">{len(extensiones)}</div>
                <div class="breakdown">
                    Extensiones de cada agente
                </div>
            </div>
            
            <div class="stat-card success">
                <div class="icon">📱</div>
                <div class="label">DIDs</div>
                <div class="value">{len(dids)}</div>
                <div class="breakdown">
                    Números de teléfono configurados
                </div>
            </div>
            
            <div class="stat-card warning">
                <div class="icon">📋</div>
                <div class="label">Colas</div>
                <div class="value">{len(colas)}</div>
                <div class="breakdown">
                    Colas de gestión configuradas
                </div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('extensiones')">
                📞 Extensiones
            </button>
            <button class="tab" onclick="showTab('dids')">
                📱 DIDs
            </button>
            <button class="tab" onclick="showTab('colas')">
                📋 Colas
            </button>
        </div>
        
        <!-- Content -->
        <div class="content">
            <!-- Extensiones Tab -->
            <div id="extensiones" class="tab-content active">
                <div class="search-bar">
                    <input type="text" id="searchExtensiones" placeholder="Buscar extensiones..." onkeyup="filterTable('extensionesTable', 'searchExtensiones')">
                </div>
                
                <div class="table-container">
                    <table id="extensionesTable">
                        <thead>
                            <tr>
                                <th>Extensión</th>
                                <th>Nombre</th>
                                <th>Grupo</th>
                                <th>Agente Asignado</th>
                                <th>Número Saliente</th>
                                <th>Estado Colas</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_extensiones_rows(extensiones)}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- DIDs Tab -->
            <div id="dids" class="tab-content">
                <div class="search-bar">
                    <input type="text" id="searchDids" placeholder="Buscar DIDs..." onkeyup="filterTable('didsTable', 'searchDids')">
                </div>
                
                <div class="table-container">
                    <table id="didsTable">
                        <thead>
                            <tr>
                                <th>Número</th>
                                <th>Locución</th>
                                <th>Acción 1</th>
                                <th>Acción 2</th>
                                <th>Acción 3</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_dids_rows(dids)}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Colas Tab -->
            <div id="colas" class="tab-content">
                <div class="search-bar">
                    <input type="text" id="searchColas" placeholder="Buscar colas..." onkeyup="filterColas('searchColas')">
                </div>
                
                <div id="colasAccordion">
                    {self._generate_colas_accordion(colas, extensiones)}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab Navigation
        function showTab(tabName) {{
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Remove active from buttons
            const buttons = document.querySelectorAll('.tab');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Activate button
            event.target.classList.add('active');
        }}
        
        // Table Filter
        function filterTable(tableId, searchId) {{
            const input = document.getElementById(searchId);
            const filter = input.value.toUpperCase();
            const table = document.getElementById(tableId);
            const tr = table.getElementsByTagName('tr');
            
            for (let i = 1; i < tr.length; i++) {{
                let visible = false;
                const td = tr[i].getElementsByTagName('td');
                
                for (let j = 0; j < td.length; j++) {{
                    if (td[j]) {{
                        const txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                            visible = true;
                            break;
                        }}
                    }}
                }}
                
                tr[i].style.display = visible ? '' : 'none';
            }}
        }}
        
        // Accordion Toggle
        function toggleAccordion(id) {{
            const header = document.querySelector(`[data-accordion="${{id}}"]`);
            const content = document.getElementById(id);
            
            header.classList.toggle('active');
            content.classList.toggle('active');
        }}
        
        // Filter Colas
        function filterColas(searchId) {{
            const input = document.getElementById(searchId);
            const filter = input.value.toUpperCase();
            const accordions = document.querySelectorAll('.accordion');
            
            accordions.forEach(accordion => {{
                const header = accordion.querySelector('.accordion-header');
                const title = header.querySelector('.accordion-title').textContent;
                
                if (title.toUpperCase().indexOf(filter) > -1) {{
                    accordion.style.display = '';
                }} else {{
                    accordion.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""
        
        return html
    
    def _calculate_stats(self, config_data):
        """Calcular estadísticas"""
        extensiones = config_data.get('extensiones', [])
        
        ext_activas = sum(1 for e in extensiones if e.get('estado_colas') == 'todas_activas')
        ext_pausadas = sum(1 for e in extensiones if e.get('estado_colas') == 'todas_pausadas')
        ext_mixto = sum(1 for e in extensiones if e.get('estado_colas') == 'mixto')
        
        return {
            'ext_activas': ext_activas,
            'ext_pausadas': ext_pausadas,
            'ext_mixto': ext_mixto
        }
    
    def _get_extension_name(self, extension_code, extensiones):
        """Obtener nombre de usuario desde código de extensión"""
        for ext in extensiones:
            if ext.get('extension', '') == extension_code:
                nombre = ext.get('nombre', '').strip()
                return nombre if nombre else extension_code
        return extension_code
    
    def _generate_extensiones_rows(self, extensiones):
        """Generar filas de tabla de extensiones"""
        rows = []
        for ext in extensiones:
            estado = ext.get('estado_colas', '')
            
            # Badge según estado
            if estado == 'todas_activas':
                badge = '<span class="badge success">✓ Activas</span>'
            elif estado == 'todas_pausadas':
                badge = '<span class="badge danger">⏸ Pausadas</span>'
            elif estado == 'mixto':
                badge = '<span class="badge warning">⚡ Mixto</span>'
            else:
                badge = '<span class="badge info">○ Sin Colas</span>'
            
            rows.append(f"""
                <tr>
                    <td><strong>{ext.get('extension', '')}</strong></td>
                    <td>{ext.get('nombre', '')}</td>
                    <td>{ext.get('grupo', '-')}</td>
                    <td>{ext.get('agente_asignado', '-')}</td>
                    <td>{ext.get('numero_saliente', '-')}</td>
                    <td>{badge}</td>
                </tr>
            """)
        
        return '\n'.join(rows) if rows else '<tr><td colspan="6" class="empty-state"><div class="icon">📭</div><div>No hay extensiones</div></td></tr>'

    def _generate_dids_rows(self, dids):
        """Generar filas de tabla de DIDs"""
        rows = []
        for did in dids:
            rows.append(f"""
                <tr>
                    <td><strong>{did.get('numero', '')}</strong></td>
                    <td>{did.get('locucion', '')}</td>
                    <td>{did.get('accion1', '')}</td>
                    <td>{did.get('accion2', '')}</td>
                    <td>{did.get('accion3', '')}</td>
                </tr>
            """)
        
        return '\n'.join(rows) if rows else '<tr><td colspan="5" class="empty-state"><div class="icon">📭</div><div>No hay DIDs</div></td></tr>'
    
    def _generate_colas_accordion(self, colas, extensiones):
        """Generar acordeones para colas"""
        if not colas:
            return '<div class="empty-state"><div class="icon">📭</div><div>No hay colas configuradas</div></div>'
        
        accordions = []
        for idx, cola in enumerate(colas):
            miembros = cola.get('miembros', [])
            activos = sum(1 for m in miembros if m.get('estado') == 'activo')
            pausados = sum(1 for m in miembros if m.get('estado') == 'pausado')
            
            # Generar cards de miembros con nombres
            member_cards = []
            for miembro in miembros:
                extension_code = miembro.get('extension', '')
                estado = miembro.get('estado', '')
                texto_completo = miembro.get('texto', '')
                
                # Obtener nombre del usuario
                nombre_usuario = self._get_extension_name(extension_code, extensiones)
                
                # Determinar clase y icono según estado
                estado_class = 'paused' if estado == 'pausado' else ''
                estado_icon = '⏸' if estado == 'pausado' else '▶'
                
                # Extraer información del texto (Est, Pen, Pri)
                info_parts = []
                if 'Est:' in texto_completo:
                    info_parts.append(f"Ext: {extension_code}")
                if texto_completo:
                    # Mantener solo Est, Pen, Pri del texto original
                    parts = texto_completo.split('Extensión:')[0].strip()
                    if parts:
                        info_parts.append(parts)
                
                info_line = ' | '.join(info_parts) if info_parts else f"Ext: {extension_code}"
                
                member_cards.append(f"""
                    <div class="member-card {estado_class}">
                        <div class="member-name">
                            <span>{estado_icon}</span>
                            <span>{nombre_usuario}</span>
                        </div>
                        <div class="member-details">{info_line}</div>
                    </div>
                """)
            
            members_html = '\n'.join(member_cards) if member_cards else '<div class="empty-state">Sin miembros</div>'
            
            accordions.append(f"""
                <div class="accordion">
                    <div class="accordion-header" data-accordion="cola{idx}" onclick="toggleAccordion('cola{idx}')">
                        <div class="accordion-title">
                            <span>📋</span>
                            <span>{cola.get('nombre', '')}</span>
                        </div>
                        <div class="accordion-stats">
                            <span class="badge success">▶ {activos}</span>
                            <span class="badge danger">⏸ {pausados}</span>
                            <span class="badge info">👥 {len(miembros)}</span>
                        </div>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <div class="accordion-content" id="cola{idx}">
                        <div class="members-grid">
                            {members_html}
                        </div>
                    </div>
                </div>
            """)
        
        return '\n'.join(accordions)

def generate_latest_dashboard():
    """Generar dashboard del snapshot más reciente"""
    try:
        # Buscar el snapshot más reciente
        snapshots = sorted(ConfigAudit.SNAPSHOTS_DIR.glob("*.json"), reverse=True)
        
        if not snapshots:
            print("❌ No se encontraron snapshots")
            return
        
        latest_snapshot = snapshots[0]
        print(f"📁 Snapshot más reciente: {latest_snapshot.name}")
        
        # Generar dashboard
        generator = DashboardGenerator()
        dashboard_file = generator.generate_html_dashboard(latest_snapshot)
        
        print()
        print("=" * 80)
        print("✅ DASHBOARD GENERADO")
        print("=" * 80)
        print(f"\nArchivo HTML: {dashboard_file}")
        print(f"\n💡 Abre el archivo en tu navegador para visualizarlo")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

def generate_specific_dashboard(date_str):
    """Generar dashboard de un snapshot específico"""
    try:
        snapshot_file = ConfigAudit.SNAPSHOTS_DIR / f"{date_str}_snapshot.json"
        
        if not snapshot_file.exists():
            print(f"❌ No se encontró snapshot para la fecha {date_str}")
            return
        
        print(f"📁 Snapshot encontrado: {snapshot_file.name}")
        
        # Generar dashboard
        generator = DashboardGenerator()
        dashboard_file = generator.generate_html_dashboard(snapshot_file)
        
        print()
        print("=" * 80)
        print("✅ DASHBOARD GENERADO")
        print("=" * 80)
        print(f"\nArchivo HTML: {dashboard_file}")
        print(f"\n💡 Abre el archivo en tu navegador para visualizarlo")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

def main():
    """Función principal"""
    print("=" * 80)
    print("🎨 GENERADOR DE DASHBOARD HTML - NEOTEL")
    print("=" * 80)
    print()
    
    if len(sys.argv) > 1:
        # Generar dashboard específico
        date_str = sys.argv[1]
        print(f"Generando dashboard de fecha: {date_str}")
        generate_specific_dashboard(date_str)
    else:
        # Generar dashboard del más reciente
        print("Generando dashboard del snapshot más reciente...")
        generate_latest_dashboard()


if __name__ == "__main__":
    main()