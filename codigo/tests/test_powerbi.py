"""
test_powerbi.py — Pruebas unitarias completas para la Fase 4 (Soporte y Dashboard Power BI)
"""
import unittest
import os
import sys
from pathlib import Path

src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from powerbi.dashboard_preview import DashboardGenerator

class TestPowerBIPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = str(Path(__file__).parent.parent)
        cls.generator = DashboardGenerator(cls.base_dir)

    def test_t4_1_artifacts_for_powerbi_exist(self):
        """Verifica T4.1: Existencia de base de datos SQLite y CSVs dimensionales procesados"""
        db_path = os.path.join(self.base_dir, "data", "database", "bi_epis_upt.db")
        self.assertTrue(os.path.exists(db_path))
        
        proc_dir = os.path.join(self.base_dir, "data", "processed")
        for f in ["dim_tiempo.csv", "dim_categoria.csv", "dim_tipo_contenido.csv", "dim_red_social.csv", "hecho_publicacion.csv"]:
            csv_path = os.path.join(proc_dir, f)
            self.assertTrue(os.path.exists(csv_path), f"Falta {f}")

    def test_t4_2_to_t4_5_dax_and_views(self):
        """Verifica T4.2 a T4.5: Archivos de medidas DAX, vistas SQL y guía de diseño"""
        dax_file = os.path.join(self.base_dir, "src", "powerbi", "dax_measures.dax")
        sql_file = os.path.join(self.base_dir, "src", "powerbi", "sql_views.sql")
        guide_file = os.path.join(self.base_dir, "src", "powerbi", "powerbi_guide.md")
        
        self.assertTrue(os.path.exists(dax_file))
        self.assertTrue(os.path.exists(sql_file))
        self.assertTrue(os.path.exists(guide_file))
        
        with open(dax_file, "r", encoding="utf-8") as f:
            dax = f.read()
            self.assertIn("Total Publicaciones", dax)
            self.assertIn("Total Likes", dax)
            self.assertIn("Total Comentarios", dax)
            self.assertIn("Total Alcance", dax)
            self.assertIn("Total Engagement", dax)

    def test_t4_6_interactive_html_dashboard(self):
        """Verifica generación de dashboard interactivo con 3 pestañas y exportación PDF"""
        html_path = self.generator.generate_html()
        self.assertTrue(os.path.exists(html_path))
        self.assertGreater(os.path.getsize(html_path), 5000)
        
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Resumen General", content)
            self.assertIn("Detalle por Publicación", content)
            self.assertIn("Tendencias en el Tiempo", content)
            self.assertIn("window.print()", content)
            self.assertIn("#003366", content)

if __name__ == "__main__":
    unittest.main()
