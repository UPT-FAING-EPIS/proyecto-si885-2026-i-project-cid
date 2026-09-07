"""
transform.py — Limpieza, normalización y transformación al modelo dimensional (T2.2)
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple
from .categorizer import ContentCategorizer, VALID_CATEGORIES

SPANISH_MONTHS = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

CONTENT_TYPES = ["Foto", "Video", "Texto"]
SOCIAL_NETWORKS = ["Facebook"]

class DataTransformer:
    def __init__(self):
        self.categorizer = ContentCategorizer()

    def transform_pipeline(self, df_raw: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Ejecuta el pipeline completo de transformación y genera los dataframes dimensionales.
        Retorna diccionario con: dim_tiempo, dim_categoria, dim_tipo_contenido, dim_red_social, hecho_publicacion
        """
        df = df_raw.copy()
        
        # 1. Deduplicación por id_publicacion
        df = df.drop_duplicates(subset=["id_publicacion"]).reset_index(drop=True)
        
        # 2. Limpieza de texto y normalización de tipo de contenido
        df["texto"] = df["texto"].fillna("").astype(str).str.strip()
        df["tipo_contenido"] = df["tipo_contenido"].apply(
            lambda x: x if x in CONTENT_TYPES else "Foto"
        )
        df["red_social"] = df["red_social"].fillna("Facebook").astype(str)
        
        # 3. Métricas numéricas
        df["likes"] = pd.to_numeric(df["likes"], errors="coerce").fillna(0).astype(int)
        df["comentarios"] = pd.to_numeric(df["comentarios"], errors="coerce").fillna(0).astype(int)
        df["alcance"] = pd.to_numeric(df["alcance"], errors="coerce").fillna(0).astype(int)
        
        # 4. Fechas y componentes temporales
        df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
        df["id_tiempo"] = df["fecha_dt"].dt.strftime("%Y%m%d").astype(int)
        
        # 5. Aplicar categorización
        df["categoria_final"] = df.apply(
            lambda row: self.categorizer.categorize_text(row["texto"], row.get("categoria_sugerida")),
            axis=1
        )
        
        # --- Construcción de Tablas Dimensionales ---
        
        # Dimensión Categoría
        dim_categoria = pd.DataFrame({
            "id_categoria": range(1, len(VALID_CATEGORIES) + 1),
            "nombre_categoria": VALID_CATEGORIES
        })
        cat_to_id = dict(zip(dim_categoria["nombre_categoria"], dim_categoria["id_categoria"]))
        df["id_categoria"] = df["categoria_final"].map(cat_to_id)
        
        # Dimensión Tipo Contenido
        dim_tipo_contenido = pd.DataFrame({
            "id_tipo_contenido": range(1, len(CONTENT_TYPES) + 1),
            "nombre_tipo": CONTENT_TYPES
        })
        tipo_to_id = dict(zip(dim_tipo_contenido["nombre_tipo"], dim_tipo_contenido["id_tipo_contenido"]))
        df["id_tipo_contenido"] = df["tipo_contenido"].map(tipo_to_id)
        
        # Dimensión Red Social
        dim_red_social = pd.DataFrame({
            "id_red_social": range(1, len(SOCIAL_NETWORKS) + 1),
            "nombre_red": SOCIAL_NETWORKS
        })
        red_to_id = dict(zip(dim_red_social["nombre_red"], dim_red_social["id_red_social"]))
        df["id_red_social"] = df["red_social"].map(red_to_id).fillna(1).astype(int)
        
        # Dimensión Tiempo (únicos presentes)
        fechas_unicas = df["fecha_dt"].drop_duplicates().sort_values().reset_index(drop=True)
        dim_tiempo = pd.DataFrame({
            "id_tiempo": fechas_unicas.dt.strftime("%Y%m%d").astype(int),
            "fecha": fechas_unicas.dt.strftime("%Y-%m-%d"),
            "dia": fechas_unicas.dt.day,
            "mes": fechas_unicas.dt.month,
            "nombre_mes": fechas_unicas.dt.month.map(SPANISH_MONTHS),
            "semana": fechas_unicas.dt.isocalendar().week.astype(int),
            "año": fechas_unicas.dt.year,
            "trimestre": "T" + fechas_unicas.dt.quarter.astype(str)
        })
        
        # Tabla de Hechos: hecho_publicacion
        hecho_publicacion = pd.DataFrame({
            "id_publicacion": range(1, len(df) + 1),
            "codigo_publicacion": df["id_publicacion"],
            "id_tiempo": df["id_tiempo"],
            "id_categoria": df["id_categoria"],
            "id_tipo_contenido": df["id_tipo_contenido"],
            "id_red_social": df["id_red_social"],
            "likes": df["likes"],
            "comentarios": df["comentarios"],
            "alcance": df["alcance"],
            "engagement": df["likes"] + df["comentarios"],
            "texto_publicacion": df["texto"],
            "url_publicacion": df["url_publicacion"]
        })
        
        return {
            "dim_tiempo": dim_tiempo,
            "dim_categoria": dim_categoria,
            "dim_tipo_contenido": dim_tipo_contenido,
            "dim_red_social": dim_red_social,
            "hecho_publicacion": hecho_publicacion
        }
