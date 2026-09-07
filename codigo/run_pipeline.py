"""
run_pipeline.py — Script Maestro de Ejecución del Pipeline BI EPIS-UPT
Ejecuta secuencialmente extracción, ETL, carga dimensional, análisis exploratorio,
clustering y generación del dashboard interactivo.
"""
import os
import sys
import logging
import unittest
from datetime import datetime

# Configurar path a src
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from extraction.data_collector import DataCollector
from extraction.scraper import FacebookScraper
from etl.transform import DataTransformer
from etl.load_sqlite import DatabaseLoader
from analysis.eda import ExploratoryDataAnalysis
from analysis.clustering import PostClusteringAnalysis
from powerbi.dashboard_preview import DashboardGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("PipelineMaestro")

def main():
    print("=" * 70)
    print("   PIPELINE DE INTELIGENCIA DE NEGOCIOS — EPIS UPT (SI-885)")
    print("=" * 70)
    start_time = datetime.now()

    # 1. Fase 1 — Extracción
    logger.info(">>> FASE 1: Extracción y recolección de publicaciones")
    collector = DataCollector(BASE_DIR)
    collector.generate_template()
    raw_path = collector.consolidate_raw_dataset()
    raw_df = collector.load_raw_dataset()
    logger.info(f"Fase 1 completada. {len(raw_df)} publicaciones consolidadas en {raw_path}")

    # 2. Fase 2 — ETL y Carga Dimensional
    logger.info(">>> FASE 2: Transformación ETL y Almacén Dimensional SQLite")
    transformer = DataTransformer()
    tables = transformer.transform_pipeline(raw_df)
    loader = DatabaseLoader(BASE_DIR)
    loader.load_dimensional_model(tables)
    db_report = loader.verify_database()
    logger.info(f"Fase 2 completada. Base SQLite verificada: {db_report['count_hecho_publicacion']} hechos, 0 errores FK.")

    # 3. Fase 3 — Análisis Exploratorio y Minería
    logger.info(">>> FASE 3: Análisis Exploratorio (EDA) y Clustering K-Means")
    eda = ExploratoryDataAnalysis(BASE_DIR)
    eda.run_analysis()
    clustering = PostClusteringAnalysis(BASE_DIR)
    clustering.run_clustering()
    logger.info("Fase 3 completada. Gráficos, métricas y clusters exportados en data/processed.")

    # 4. Fase 4 — Dashboard y Artefactos Power BI
    logger.info(">>> FASE 4: Generación de Artefactos de Visualización y Dashboard")
    dash_gen = DashboardGenerator(BASE_DIR)
    html_path = dash_gen.generate_html()
    logger.info(f"Fase 4 completada. Dashboard interactivo generado en {html_path}")

    # 5. Ejecutar Test Suite Automatizado
    logger.info(">>> EJECUTANDO SUITE DE PRUEBAS AUTOMATIZADAS")
    loader_tests = unittest.TestLoader()
    suite = loader_tests.discover(os.path.join(BASE_DIR, "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    test_result = runner.run(suite)

    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 70)
    print("                  RESUMEN DE EJECUCIÓN")
    print("=" * 70)
    print(f" Tiempo total de ejecución: {elapsed:.2f} segundos")
    print(f" Estado de Pruebas Unitarias: {'EXITOSO (100% OK)' if test_result.wasSuccessful() else 'CON ERRORES'}")
    print(f" Publicaciones cargadas en SQLite: {db_report['count_hecho_publicacion']}")
    print(f" Total de Reacciones / Likes: {db_report['total_likes']}")
    print(f" Total de Comentarios: {db_report['total_comentarios']}")
    print(f" Total de Alcance Estimado: {db_report['total_alcance']}")
    print(f" Dashboard listo para abrir en: {html_path}")
    print("=" * 70)

    if not test_result.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    main()
