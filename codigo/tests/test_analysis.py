"""
test_analysis.py — Pruebas unitarias completas para la Fase 3 (EDA y Minería de Datos)
"""
import unittest
import os
import sys
from pathlib import Path
import pandas as pd

src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from analysis.eda import ExploratoryDataAnalysis
from analysis.clustering import PostClusteringAnalysis

class TestAnalysisPhase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = str(Path(__file__).parent.parent)
        cls.eda = ExploratoryDataAnalysis(cls.base_dir)
        cls.clustering = PostClusteringAnalysis(cls.base_dir)

    def test_t3_1_and_t3_2_eda_execution_and_findings(self):
        """Verifica T3.1 y T3.2: EDA, generación de gráficos y documento de hallazgos"""
        df = self.eda.run_analysis()
        self.assertGreater(len(df), 0)
        
        # Validar gráficos generados
        for img in ["distribucion_categorias.png", "evolucion_mensual.png", "engagement_por_tipo.png"]:
            img_path = os.path.join(self.eda.output_dir, img)
            self.assertTrue(os.path.exists(img_path), f"Falta imagen {img}")
            self.assertGreater(os.path.getsize(img_path), 1000, f"Imagen {img} está vacía")
            
        # Validar archivo de hallazgos para el informe
        self.assertTrue(os.path.exists(self.eda.findings_path))
        with open(self.eda.findings_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Hallazgo 1", content)
            self.assertIn("Hallazgo 2", content)
            self.assertIn("Hallazgo 3", content)

    def test_t3_3_clustering_execution(self):
        """Verifica T3.3: Clustering K-Means sobre engagement (Unidad III)"""
        df_clustered = self.clustering.run_clustering()
        self.assertIn("cluster_id", df_clustered.columns)
        self.assertIn("cluster_label", df_clustered.columns)
        self.assertEqual(df_clustered["cluster_id"].nunique(), 3)
        self.assertTrue(os.path.exists(self.clustering.output_csv))
        self.assertTrue(os.path.exists(self.clustering.chart_path))

if __name__ == "__main__":
    unittest.main()
