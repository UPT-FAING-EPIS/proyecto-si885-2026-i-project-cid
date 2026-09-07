"""
test_etl.py — Pruebas unitarias completas para la Fase 2 (ETL y Modelo Dimensional)
"""
import unittest
import os
import sys
from pathlib import Path
import pandas as pd

src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from extraction.data_collector import DataCollector
from etl.categorizer import ContentCategorizer, VALID_CATEGORIES
from etl.transform import DataTransformer
from etl.load_sqlite import DatabaseLoader

class TestETLPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = str(Path(__file__).parent.parent)
        cls.collector = DataCollector(cls.base_dir)
        cls.raw_df = cls.collector.load_raw_dataset()
        cls.transformer = DataTransformer()
        cls.tables = cls.transformer.transform_pipeline(cls.raw_df)
        cls.loader = DatabaseLoader(cls.base_dir)
        cls.loader.load_dimensional_model(cls.tables)

    def test_t2_3_categorization(self):
        """Verifica T2.3: Categorización válida de contenidos"""
        categorizer = ContentCategorizer()
        cat1 = categorizer.categorize_text("Gran Ceremonia de Graduación y Colación de Grados")
        self.assertEqual(cat1, "Eventos")
        
        cat2 = categorizer.categorize_text("Estudiantes ganan Hackathon Regional de Innovación")
        self.assertEqual(cat2, "Logros/Becas")
        
        cat3 = categorizer.categorize_text("Convocatoria a prácticas pre profesionales")
        self.assertEqual(cat3, "Convocatorias")
        
        # Validar que todas las categorías del dataset estén en la lista oficial
        df_hechos = self.tables["hecho_publicacion"]
        dim_cat = self.tables["dim_categoria"]
        cats_usadas = df_hechos["id_categoria"].unique()
        self.assertTrue(set(cats_usadas).issubset(set(dim_cat["id_categoria"])))

    def test_t2_2_transformation_integrity(self):
        """Verifica T2.2: Limpieza, normalización de fechas y deduplicación"""
        df_hechos = self.tables["hecho_publicacion"]
        dim_tiempo = self.tables["dim_tiempo"]
        
        # Deduplicación: no códigos repetidos
        self.assertEqual(df_hechos["codigo_publicacion"].nunique(), len(df_hechos))
        
        # Llaves temporales existen en dim_tiempo
        self.assertTrue(set(df_hechos["id_tiempo"]).issubset(set(dim_tiempo["id_tiempo"])))
        
        # Validar consistencia de cálculo de engagement
        self.assertTrue((df_hechos["engagement"] == df_hechos["likes"] + df_hechos["comentarios"]).all())

    def test_t2_1_and_t2_4_schema_and_load(self):
        """Verifica T2.1 y T2.4: Esquema y carga en SQLite"""
        self.assertTrue(os.path.exists(self.loader.db_path))
        
        # Validar archivos CSV procesados exportados para Power BI
        for tbl in ["dim_tiempo", "dim_categoria", "dim_tipo_contenido", "dim_red_social", "hecho_publicacion"]:
            csv_f = os.path.join(self.loader.processed_dir, f"{tbl}.csv")
            self.assertTrue(os.path.exists(csv_f), f"Falta archivo procesado {tbl}.csv")

    def test_t2_5_database_integrity(self):
        """Verifica T2.5: Integridad referencial, llaves foráneas y ausencia de nulos"""
        report = self.loader.verify_database()
        self.assertTrue(report["is_valid"], f"Fallo de integridad: {report}")
        self.assertEqual(report["fk_violations"], 0, "No debe haber violaciones de FK")
        self.assertEqual(report["null_fact_fields"], 0, "No debe haber nulos en hechos")
        self.assertGreaterEqual(report["count_hecho_publicacion"], 20)
        self.assertGreater(report["total_likes"], 0)
        self.assertGreater(report["total_comentarios"], 0)

if __name__ == "__main__":
    unittest.main()
