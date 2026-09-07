"""
dashboard_preview.py — Generador y servidor del Dashboard Interactivo EPIS-UPT
Cumple fielmente las especificaciones de design.md con 3 pestañas, filtros dinámicos,
búsqueda en texto, KPIs, gráficos y exportación directa a PDF/impresión.
"""
import os
import json
import sqlite3
import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger("DashboardPreview")

class DashboardGenerator:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, "data", "database", "bi_epis_upt.db")
        self.output_html = os.path.join(base_dir, "data", "processed", "dashboard_epis_upt.html")

    def get_data_as_json(self) -> str:
        query = """
        SELECT 
            h.id_publicacion,
            h.codigo_publicacion,
            t.fecha,
            t.año,
            t.mes,
            t.nombre_mes,
            c.nombre_categoria AS categoria,
            tc.nombre_tipo AS tipo_contenido,
            rs.nombre_red AS red_social,
            h.likes,
            h.comentarios,
            h.alcance,
            h.engagement,
            h.texto_publicacion,
            h.url_publicacion
        FROM hecho_publicacion h
        JOIN dim_tiempo t ON h.id_tiempo = t.id_tiempo
        JOIN dim_categoria c ON h.id_categoria = c.id_categoria
        JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido
        JOIN dim_red_social rs ON h.id_red_social = rs.id_red_social
        ORDER BY t.fecha DESC;
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)
        return df.to_json(orient="records", force_ascii=False)

    def generate_html(self) -> str:
        posts_json = self.get_data_as_json()
        
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EPIS - UPT | Dashboard de Inteligencia de Negocios en Redes Sociales</title>
    <style>
        :root {{
            --primary: #003366;
            --primary-light: #0056b3;
            --accent: #e67e22;
            --bg: #f4f6f9;
            --card-bg: #ffffff;
            --text-main: #2c3e50;
            --text-muted: #6c757d;
            --border: #e2e8f0;
            --success: #27ae60;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
        }}
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 1.25rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .header-title h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header-title p {{
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: 4px;
        }}
        .header-actions button {{
            background: white;
            color: var(--primary);
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .header-actions button:hover {{
            background: #e2e8f0;
        }}
        .nav-tabs {{
            display: flex;
            background: white;
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            gap: 1.5rem;
        }}
        .tab-btn {{
            padding: 1rem 0.5rem;
            border: none;
            background: none;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            position: relative;
            transition: color 0.2s;
        }}
        .tab-btn.active {{
            color: var(--primary);
        }}
        .tab-btn.active::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background-color: var(--primary);
            border-radius: 3px 3px 0 0;
        }}
        .main-layout {{
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 1.5rem;
            padding: 1.5rem 2rem;
        }}
        .filter-panel {{
            background: var(--card-bg);
            padding: 1.25rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            height: fit-content;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }}
        .filter-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--primary);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .btn-reset {{
            font-size: 0.75rem;
            background: none;
            border: none;
            color: var(--primary-light);
            cursor: pointer;
            text-decoration: underline;
        }}
        .filter-group {{
            margin-bottom: 1.2rem;
        }}
        .filter-group label {{
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
            text-transform: uppercase;
        }}
        .filter-group select, .filter-group input {{
            width: 100%;
            padding: 8px 10px;
            border-radius: 6px;
            border: 1px solid var(--border);
            font-size: 0.9rem;
            outline: none;
        }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .kpi-card {{
            background: var(--card-bg);
            padding: 1.2rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            border-top: 4px solid var(--primary);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            display: flex;
            flex-direction: column;
        }}
        .kpi-label {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        .kpi-value {{
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--primary);
            margin-top: 0.4rem;
        }}
        .kpi-sub {{
            font-size: 0.75rem;
            color: var(--success);
            margin-top: 0.3rem;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .chart-card {{
            background: var(--card-bg);
            padding: 1.25rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .chart-card.full-width {{
            grid-column: 1 / -1;
        }}
        .chart-card h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }}
        .table-container {{
            background: var(--card-bg);
            border-radius: 10px;
            border: 1px solid var(--border);
            overflow-x: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            text-align: left;
        }}
        th {{
            background: #f8fafc;
            color: var(--text-muted);
            font-weight: 600;
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
        }}
        td {{
            padding: 12px 14px;
            border-bottom: 1px solid #edf2f7;
        }}
        tr:hover {{
            background-color: #f8fafc;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }}
        .badge-cat {{ background: #e0f2fe; color: #0369a1; }}
        .badge-tipo {{ background: #fef3c7; color: #b45309; }}
        .empty-state {{
            padding: 3rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 1.1rem;
            font-weight: 600;
        }}
        @media print {{
            header button, .nav-tabs, .filter-panel {{ display: none; }}
            .main-layout {{ grid-template-columns: 1fr; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1>EPIS - UPT: Producción en Redes Sociales</h1>
            <p>Dashboard de Inteligencia de Negocios (SI-885) | facebook.com/uptsistemas</p>
        </div>
        <div class="header-actions">
            <button onclick="window.print()">Exportar a PDF</button>
        </div>
    </header>

    <nav class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('resumen')">1. Resumen General (Operacional)</button>
        <button class="tab-btn" onclick="switchTab('biblioteca')">2. Detalle por Publicación (Biblioteca)</button>
        <button class="tab-btn" onclick="switchTab('tendencias')">3. Tendencias en el Tiempo (Estratégico)</button>
    </nav>

    <div class="main-layout">
        <!-- Panel Lateral de Filtros -->
        <aside class="filter-panel">
            <div class="filter-title">
                <span>Filtros Globales</span>
                <button class="btn-reset" onclick="resetFilters()">Restablecer</button>
            </div>
            <div class="filter-group">
                <label>Buscar Texto (Biblioteca)</label>
                <input type="text" id="searchInput" placeholder="Escribe palabras clave..." oninput="applyFilters()">
            </div>
            <div class="filter-group">
                <label>Categoría de Contenido</label>
                <select id="categoriaFilter" onchange="applyFilters()">
                    <option value="">Todas las Categorías</option>
                    <option value="Académico">Académico</option>
                    <option value="Eventos">Eventos</option>
                    <option value="Logros/Becas">Logros/Becas</option>
                    <option value="Convocatorias">Convocatorias</option>
                    <option value="Difusión general">Difusión general</option>
                    <option value="Otros">Otros</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Tipo de Contenido</label>
                <select id="tipoFilter" onchange="applyFilters()">
                    <option value="">Todos los Tipos</option>
                    <option value="Foto">Foto</option>
                    <option value="Video">Video</option>
                    <option value="Texto">Texto</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Mes</label>
                <select id="mesFilter" onchange="applyFilters()">
                    <option value="">Todos los Meses</option>
                    <option value="Marzo">Marzo</option>
                    <option value="Abril">Abril</option>
                    <option value="Mayo">Mayo</option>
                    <option value="Junio">Junio</option>
                    <option value="Julio">Julio</option>
                    <option value="Agosto">Agosto</option>
                    <option value="Septiembre">Septiembre</option>
                </select>
            </div>
        </aside>

        <!-- Contenido Principal Dinámico -->
        <main>
            <!-- 4 Tarjetas KPI -->
            <div class="kpi-row">
                <div class="kpi-card">
                    <span class="kpi-label">Total Publicaciones</span>
                    <span class="kpi-value" id="kpiPosts">0</span>
                    <span class="kpi-sub">Últimos 6 meses</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Total Likes / Reacciones</span>
                    <span class="kpi-value" id="kpiLikes">0</span>
                    <span class="kpi-sub">Reacciones orgánicas</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Total Comentarios</span>
                    <span class="kpi-value" id="kpiComments">0</span>
                    <span class="kpi-sub">Interacción activa</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Alcance Total Estimado</span>
                    <span class="kpi-value" id="kpiReach">0</span>
                    <span class="kpi-sub">Visualizaciones</span>
                </div>
            </div>

            <!-- Pestaña 1: Resumen General -->
            <div id="view-resumen" class="view-content">
                <div class="charts-grid">
                    <div class="chart-card">
                        <h3>Publicaciones por Mes</h3>
                        <div id="chartMesContainer" style="height: 240px;"></div>
                    </div>
                    <div class="chart-card">
                        <h3>Distribución por Tipo de Contenido</h3>
                        <div id="chartTipoContainer" style="height: 240px;"></div>
                    </div>
                </div>
            </div>

            <!-- Pestaña 2: Detalle por Publicación (Biblioteca) -->
            <div id="view-biblioteca" class="view-content" style="display: none;">
                <div class="table-container">
                    <table id="postsTable">
                        <thead>
                            <tr>
                                <th>Fecha</th>
                                <th>Categoría</th>
                                <th>Tipo</th>
                                <th>Likes</th>
                                <th>Comentarios</th>
                                <th>Alcance</th>
                                <th>Descripción</th>
                                <th>Enlace</th>
                            </tr>
                        </thead>
                        <tbody id="postsTableBody"></tbody>
                    </table>
                    <div id="emptyMessage" class="empty-state" style="display: none;">
                        No hay publicaciones para los filtros seleccionados
                    </div>
                </div>
            </div>

            <!-- Pestaña 3: Tendencias en el Tiempo -->
            <div id="view-tendencias" class="view-content" style="display: none;">
                <div class="charts-grid">
                    <div class="chart-card full-width">
                        <h3>Tendencia Temporal de Publicaciones e Interacciones</h3>
                        <div id="chartTendenciaContainer" style="height: 260px;"></div>
                    </div>
                    <div class="chart-card full-width">
                        <h3>Likes y Comentarios por Categoría de Contenido</h3>
                        <div id="chartCategoriaContainer" style="height: 260px;"></div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const rawData = {posts_json};
        let currentTab = 'resumen';

        function switchTab(tabName) {{
            currentTab = tabName;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.view-content').forEach(view => view.style.display = 'none');
            
            if (tabName === 'resumen') {{
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
                document.getElementById('view-resumen').style.display = 'block';
            }} else if (tabName === 'biblioteca') {{
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
                document.getElementById('view-biblioteca').style.display = 'block';
            }} else if (tabName === 'tendencias') {{
                document.querySelectorAll('.tab-btn')[2].classList.add('active');
                document.getElementById('view-tendencias').style.display = 'block';
            }}
            applyFilters();
        }}

        function resetFilters() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('categoriaFilter').value = '';
            document.getElementById('tipoFilter').value = '';
            document.getElementById('mesFilter').value = '';
            applyFilters();
        }}

        function applyFilters() {{
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const cat = document.getElementById('categoriaFilter').value;
            const tipo = document.getElementById('tipoFilter').value;
            const mes = document.getElementById('mesFilter').value;

            const filtered = rawData.filter(p => {{
                const matchQuery = !query || p.texto_publicacion.toLowerCase().includes(query) || p.categoria.toLowerCase().includes(query);
                const matchCat = !cat || p.categoria === cat;
                const matchTipo = !tipo || p.tipo_contenido === tipo;
                const matchMes = !mes || p.nombre_mes === mes;
                return matchQuery && matchCat && matchTipo && matchMes;
            }});

            updateKPIs(filtered);
            renderBiblioteca(filtered);
            renderCharts(filtered);
        }}

        function updateKPIs(data) {{
            const totPosts = data.length;
            const totLikes = data.reduce((acc, p) => acc + p.likes, 0);
            const totComments = data.reduce((acc, p) => acc + p.comentarios, 0);
            const totReach = data.reduce((acc, p) => acc + p.alcance, 0);

            document.getElementById('kpiPosts').textContent = totPosts.toLocaleString();
            document.getElementById('kpiLikes').textContent = totLikes.toLocaleString();
            document.getElementById('kpiComments').textContent = totComments.toLocaleString();
            document.getElementById('kpiReach').textContent = totReach.toLocaleString();
        }}

        function renderBiblioteca(data) {{
            const tbody = document.getElementById('postsTableBody');
            const emptyMsg = document.getElementById('emptyMessage');
            tbody.innerHTML = '';

            if (data.length === 0) {{
                emptyMsg.style.display = 'block';
                return;
            }}
            emptyMsg.style.display = 'none';

            data.forEach(p => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space:nowrap;"><strong>${{p.fecha}}</strong></td>
                    <td><span class="badge badge-cat">${{p.categoria}}</span></td>
                    <td><span class="badge badge-tipo">${{p.tipo_contenido}}</span></td>
                    <td>${{p.likes}}</td>
                    <td>${{p.comentarios}}</td>
                    <td>${{p.alcance}}</td>
                    <td style="max-width: 320px;">${{p.texto_publicacion}}</td>
                    <td><a href="${{p.url_publicacion}}" target="_blank" style="color:var(--primary-light);font-weight:600;">Ver Post</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function renderCharts(data) {{
            // 1. Chart Mes (SVG Bar)
            const meses = ['Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre'];
            const mesCounts = meses.map(m => data.filter(p => p.nombre_mes === m).length);
            const maxVal = Math.max(...mesCounts, 1);
            
            let barsHtml = `<div style="display:flex;align-items:flex-end;height:180px;gap:16px;padding-top:20px;">`;
            meses.forEach((m, idx) => {{
                const h = (mesCounts[idx] / maxVal) * 140;
                barsHtml += `
                    <div style="flex:1;text-align:center;display:flex;flex-direction:column;align-items:center;">
                        <span style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:4px;">${{mesCounts[idx]}}</span>
                        <div style="width:100%;max-width:36px;height:${{h}}px;background:var(--primary-light);border-radius:4px 4px 0 0;"></div>
                        <span style="font-size:11px;color:var(--text-muted);margin-top:6px;">${{m.substring(0,3)}}</span>
                    </div>
                `;
            }});
            barsHtml += `</div>`;
            document.getElementById('chartMesContainer').innerHTML = barsHtml;

            // 2. Chart Tipo Contenido (Dona/Barras proporcionales)
            const tipos = ['Foto', 'Video', 'Texto'];
            const tipoCounts = tipos.map(t => data.filter(p => p.tipo_contenido === t).length);
            const totT = Math.max(data.length, 1);
            
            let tipoHtml = `<div style="display:flex;flex-direction:column;gap:12px;padding-top:10px;">`;
            tipos.forEach((t, idx) => {{
                const pct = Math.round((tipoCounts[idx] / totT) * 100);
                const color = t === 'Foto' ? '#003366' : (t === 'Video' ? '#e67e22' : '#7f8c8d');
                tipoHtml += `
                    <div>
                        <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:4px;">
                            <span>${{t}}</span>
                            <span>${{tipoCounts[idx]}} posts (${{pct}}%)</span>
                        </div>
                        <div style="width:100%;height:14px;background:#edf2f7;border-radius:7px;overflow:hidden;">
                            <div style="width:${{pct}}%;height:100%;background:${{color}};"></div>
                        </div>
                    </div>
                `;
            }});
            tipoHtml += `</div>`;
            document.getElementById('chartTipoContainer').innerHTML = tipoHtml;

            // 3. Tendencia Líneas (Estratégico)
            const mesEng = meses.map(m => data.filter(p => p.nombre_mes === m).reduce((a, b) => a + b.engagement, 0));
            const maxEng = Math.max(...mesEng, 1);
            let tendHtml = `<div style="display:flex;align-items:flex-end;height:180px;gap:16px;padding-top:20px;">`;
            meses.forEach((m, idx) => {{
                const h = (mesEng[idx] / maxEng) * 140;
                tendHtml += `
                    <div style="flex:1;text-align:center;display:flex;flex-direction:column;align-items:center;">
                        <span style="font-size:11px;font-weight:700;color:var(--accent);margin-bottom:4px;">${{mesEng[idx]}}</span>
                        <div style="width:100%;max-width:32px;height:${{h}}px;background:var(--accent);border-radius:4px 4px 0 0;"></div>
                        <span style="font-size:11px;color:var(--text-muted);margin-top:6px;">${{m.substring(0,3)}}</span>
                    </div>
                `;
            }});
            tendHtml += `</div>`;
            document.getElementById('chartTendenciaContainer').innerHTML = tendHtml;

            // 4. Categoría Barras Apiladas (Likes + Comentarios)
            const cats = ['Académico', 'Eventos', 'Logros/Becas', 'Convocatorias', 'Difusión general', 'Otros'];
            let catHtml = `<div style="display:flex;flex-direction:column;gap:10px;">`;
            cats.forEach(c => {{
                const cPosts = data.filter(p => p.categoria === c);
                const cLikes = cPosts.reduce((a, b) => a + b.likes, 0);
                const cComms = cPosts.reduce((a, b) => a + b.comentarios, 0);
                catHtml += `
                    <div style="display:flex;align-items:center;gap:10px;font-size:12px;">
                        <span style="width:120px;font-weight:600;white-space:nowrap;">${{c}}</span>
                        <div style="flex:1;display:flex;height:18px;border-radius:4px;overflow:hidden;background:#edf2f7;">
                            <div style="width:${{cLikes / 5}}%;background:var(--primary);title='Likes: ${{cLikes}}'"></div>
                            <div style="width:${{cComms / 5}}%;background:var(--accent);title='Comentarios: ${{cComms}}'"></div>
                        </div>
                        <span style="width:110px;text-align:right;color:var(--text-muted);font-weight:bold;">${{cLikes}} L / ${{cComms}} C</span>
                    </div>
                `;
            }});
            catHtml += `</div>`;
            document.getElementById('chartCategoriaContainer').innerHTML = catHtml;
        }}

        // Inicializar dashboard al cargar
        window.onload = () => {{
            applyFilters();
        }};
    </script>
</body>
</html>
"""
        with open(self.output_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Dashboard interactivo HTML generado en {self.output_html}")
        return self.output_html

if __name__ == "__main__":
    gen = DashboardGenerator(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    html_path = gen.generate_html()
    print(f"Dashboard generado exitosamente: {html_path}")
