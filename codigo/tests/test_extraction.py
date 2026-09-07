"""
test_extraction.py — Pruebas unitarias completas para la Fase 1 de extracción y recolección
"""
import unittest
import os
import sys
from pathlib import Path
import pandas as pd

src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from extraction.scraper import FacebookScraper
from extraction.data_collector import DataCollector, DATA_COLUMNS

class TestExtractionPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = str(Path(__file__).parent.parent)
        cls.collector = DataCollector(cls.base_dir)
        cls.scraper = FacebookScraper()

    def test_t1_2_scraper_connection(self):
        """Verifica T1.2: Probar scraping y conectividad a facebook.com/uptsistemas"""
        diag = self.scraper.test_connection()
        self.assertTrue(diag["success"])
        self.assertEqual(diag["status_code"], 200)
        self.assertIn("Sistemas", diag["page_title"])

    def test_t1_4_template_generation(self):
        """Verifica T1.4: Plantilla CSV para registro manual de respaldo"""
        path = self.collector.generate_template()
        self.assertTrue(os.path.exists(path))
        df_tmpl = pd.read_csv(path, encoding="utf-8")
        for col in DATA_COLUMNS:
            self.assertIn(col, df_tmpl.columns)

    def test_t1_3_and_t1_5_consolidated_dataset(self):
        """Verifica T1.3 y T1.5: Extracción de 6 meses y consolidación en CSV limpio"""
        path = self.collector.consolidate_raw_dataset()
        self.assertTrue(os.path.exists(path))
        df = self.collector.load_raw_dataset()
        
        # Validar cantidad de registros y columnas requeridas
        self.assertGreaterEqual(len(df), 20, "Debe contener al menos 20 publicaciones representativas de los 6 meses")
        for col in DATA_COLUMNS:
            self.assertIn(col, df.columns)
            
        # Validar ventana de tiempo (últimos 6 meses: 2026-03 a 2026-09)
        fechas = pd.to_datetime(df["fecha"])
        self.assertEqual(fechas.dt.year.unique().tolist(), [2026])
        meses_presentes = set(fechas.dt.month.unique())
        esperados = {3, 4, 5, 6, 7, 8, 9}
        self.assertTrue(esperados.issubset(meses_presentes), f"Faltan meses en la serie temporal: {esperados - meses_presentes}")
        
        # Validar no nulos en campos esenciales
        self.assertEqual(df["id_publicacion"].isnull().sum(), 0)
        self.assertEqual(df["texto"].isnull().sum(), 0)
        self.assertEqual(df["likes"].isnull().sum(), 0)
        self.assertEqual(df["comentarios"].isnull().sum(), 0)
        self.assertEqual(df["url_publicacion"].isnull().sum(), 0)

if __name__ == "__main__":
    unittest.main()
