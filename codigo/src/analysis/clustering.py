"""
clustering.py — Minería de Datos: Clustering K-Means de Publicaciones (T3.3)
Segmentación no supervisada según engagement y características de publicación (Unidad III).
"""
import os
import sqlite3
import logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

logger = logging.getLogger("Clustering")

CLUSTER_LABELS_MAP = {
    0: "Alto Impacto y Tracción",
    1: "Interacción Formativa Moderada",
    2: "Avisos Operativos / Básicos"
}

class PostClusteringAnalysis:
    def __init__(self, base_dir: str, n_clusters: int = 3):
        self.base_dir = base_dir
        self.n_clusters = n_clusters
        self.db_path = os.path.join(base_dir, "data", "database", "bi_epis_upt.db")
        self.output_csv = os.path.join(base_dir, "data", "processed", "clustering_results.csv")
        self.chart_path = os.path.join(base_dir, "data", "processed", "eda_charts", "cluster_dispersion.png")

    def run_clustering(self) -> pd.DataFrame:
        query = """
        SELECT 
            h.id_publicacion,
            h.codigo_publicacion,
            c.nombre_categoria,
            tc.nombre_tipo AS tipo_contenido,
            h.likes,
            h.comentarios,
            h.alcance,
            h.engagement,
            LENGTH(h.texto_publicacion) AS longitud_texto,
            h.texto_publicacion
        FROM hecho_publicacion h
        JOIN dim_categoria c ON h.id_categoria = c.id_categoria
        JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido;
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)

        features = ["likes", "comentarios", "alcance", "longitud_texto"]
        X = df[features].copy()
        
        # Escalar variables
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Aplicar KMeans
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        df["cluster_id"] = kmeans.fit_predict(X_scaled)
        
        # Ordenar clusters de mayor a menor engagement medio para consistencia de etiquetas
        cluster_order = df.groupby("cluster_id")["engagement"].mean().sort_values(ascending=False).index
        remapping = {orig_id: new_id for new_id, orig_id in enumerate(cluster_order)}
        df["cluster_id"] = df["cluster_id"].map(remapping)
        df["cluster_label"] = df["cluster_id"].map(CLUSTER_LABELS_MAP)

        # Guardar CSV
        df.to_csv(self.output_csv, index=False, encoding="utf-8")
        logger.info(f"Clustering completado y guardado en {self.output_csv}")

        # Gráfico de dispersión
        plt.figure(figsize=(9, 6))
        colors = ["#27ae60", "#2980b9", "#7f8c8d"]
        for cid in sorted(df["cluster_id"].unique()):
            sub = df[df["cluster_id"] == cid]
            plt.scatter(
                sub["likes"], 
                sub["comentarios"], 
                s=sub["alcance"] / 15,
                color=colors[cid], 
                label=f"{CLUSTER_LABELS_MAP[cid]} (n={len(sub)})", 
                alpha=0.7, 
                edgecolors="black"
            )

        plt.title("Segmentación K-Means de Publicaciones EPIS-UPT (Unidad III)", fontsize=13, fontweight="bold", pad=15)
        plt.xlabel("Reacciones / Likes", fontsize=10)
        plt.ylabel("Comentarios", fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.savefig(self.chart_path, dpi=200)
        plt.close()
        logger.info(f"Gráfico de clusters guardado en {self.chart_path}")

        return df

if __name__ == "__main__":
    clustering = PostClusteringAnalysis(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    res = clustering.run_clustering()
    print("Resumen de clusters:")
    print(res.groupby(["cluster_id", "cluster_label"]).agg({"likes": "mean", "comentarios": "mean", "alcance": "mean", "id_publicacion": "count"}))
