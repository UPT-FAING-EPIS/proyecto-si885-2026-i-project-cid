# Inteligencia de Negocios — Dashboard EPIS-UPT (SI-885)

Sistema analítico integral para la monitorización, extracción, modelamiento dimensional y visualización de contenidos en redes sociales de la **Escuela Profesional de Ingeniería de Sistemas (EPIS) - Universidad Privada de Tacna (UPT)**.

---

## 🏗️ Arquitectura de la Solución

```
[Facebook: facebook.com/uptsistemas]
            │
            ▼ (Extracción y Respaldo)
   [publicaciones_raw.csv]
            │
            ▼ (ETL Pandas: categorizer.py + transform.py)
 [Almacén Dimensional SQLite: bi_epis_upt.db]
   ├── dim_tiempo
   ├── dim_categoria
   ├── dim_tipo_contenido
   ├── dim_red_social
   └── hecho_publicacion (★)
            │
    ┌───────┴────────────────────────┐
    ▼                                ▼
[Minería: EDA & K-Means]   [Visualización Power BI & Web]
- Gráficos estadísticos     - Catálogo DAX (dax_measures.dax)
- Clustering K-Means         - Vistas SQL (sql_views.sql)
- Hallazgos para informe    - Visor interactivo (dashboard_epis_upt.html)
```

---

## 📁 Estructura del Código

```
codigo/
├── data/
│   ├── raw/                           # Datos crudos y plantilla de respaldo
│   │   ├── publicaciones_raw.csv
│   │   └── plantilla_registro_manual.csv
│   ├── processed/                     # Tablas procesadas y reportes analíticos
│   │   ├── dim_tiempo.csv
│   │   ├── dim_categoria.csv
│   │   ├── dim_tipo_contenido.csv
│   │   ├── dim_red_social.csv
│   │   ├── hecho_publicacion.csv
│   │   ├── clustering_results.csv
│   │   ├── hallazgos_eda.md
│   │   ├── dashboard_epis_upt.html    # Dashboard interactivo local
│   │   └── eda_charts/                # Gráficos estadísticos exportados en PNG
│   └── database/
│       └── bi_epis_upt.db             # Base de datos SQLite dimensional
├── src/
│   ├── extraction/                    # Fase 1: Extracción de datos
│   │   ├── scraper.py
│   │   └── data_collector.py
│   ├── etl/                           # Fase 2: ETL y Almacén Dimensional
│   │   ├── categorizer.py
│   │   ├── transform.py
│   │   └── load_sqlite.py
│   ├── analysis/                      # Fase 3: Minería y EDA
│   │   ├── eda.py
│   │   └── clustering.py
│   └── powerbi/                       # Fase 4: Soporte Power BI
│       ├── dax_measures.dax
│       ├── sql_views.sql
│       ├── powerbi_guide.md
│       ├── dashboard_preview.py
│       └── sustentacion_guide.md
├── tests/                             # Suite de pruebas unitarias automatizadas
│   ├── test_extraction.py
│   ├── test_etl.py
│   ├── test_analysis.py
│   └── test_powerbi.py
├── run_pipeline.py                    # Script maestro de ejecución y verificación
├── requirements.txt                   # Dependencias del proyecto
└── README.md
```

---

## 🚀 Guía de Ejecución Rápida

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el pipeline completo (un solo comando)
```bash
python run_pipeline.py
```
Este comando ejecuta automáticamente:
1. La recolección y validación de publicaciones de Facebook.
2. La limpieza ETL y carga al esquema estrella en `bi_epis_upt.db`.
3. La generación de gráficos EDA y clustering K-Means.
4. La generación del dashboard interactivo `data/processed/dashboard_epis_upt.html`.
5. La suite completa de 12 pruebas unitarias.

### 3. Abrir el Dashboard Interactivo
Doble clic en el archivo:
`codigo/data/processed/dashboard_epis_upt.html`  
(No requiere servidor ni conexión a internet, funciona en cualquier navegador).

### 4. Abrir en Power BI Desktop
Consultar [src/powerbi/powerbi_guide.md](src/powerbi/powerbi_guide.md) para importar los CSVs de `data/processed/` y vincular el esquema estrella en 2 minutos.

---

## 🧪 Ejecución Individual de Pruebas Unitarias

```bash
# Fase 1: Extracción
python -m unittest tests/test_extraction.py

# Fase 2: ETL y Modelo Dimensional
python -m unittest tests/test_etl.py

# Fase 3: Análisis Exploratorio y Clustering
python -m unittest tests/test_analysis.py

# Fase 4: Soporte y Dashboard Power BI
python -m unittest tests/test_powerbi.py
```
