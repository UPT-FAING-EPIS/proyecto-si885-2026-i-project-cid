"""
load_sqlite.py — Carga del modelo dimensional en SQLite y exportación para Power BI (T2.1, T2.4)
Crea esquema estrella con llaves foráneas, índices, vistas analíticas y exporta CSVs procesados.
"""
import os
import sqlite3
import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger("DatabaseLoader")

DDL_STATEMENTS = """
-- Habilitar llaves foráneas
PRAGMA foreign_keys = ON;

-- Dimensión Tiempo
CREATE TABLE IF NOT EXISTS dim_tiempo (
    id_tiempo INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL,
    dia INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    nombre_mes TEXT NOT NULL,
    semana INTEGER NOT NULL,
    año INTEGER NOT NULL,
    trimestre TEXT NOT NULL
);

-- Dimensión Categoría
CREATE TABLE IF NOT EXISTS dim_categoria (
    id_categoria INTEGER PRIMARY KEY,
    nombre_categoria TEXT NOT NULL UNIQUE
);

-- Dimensión Tipo de Contenido
CREATE TABLE IF NOT EXISTS dim_tipo_contenido (
    id_tipo_contenido INTEGER PRIMARY KEY,
    nombre_tipo TEXT NOT NULL UNIQUE
);

-- Dimensión Red Social
CREATE TABLE IF NOT EXISTS dim_red_social (
    id_red_social INTEGER PRIMARY KEY,
    nombre_red TEXT NOT NULL UNIQUE
);

-- Tabla de Hechos: hecho_publicacion
CREATE TABLE IF NOT EXISTS hecho_publicacion (
    id_publicacion INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_publicacion TEXT NOT NULL UNIQUE,
    id_tiempo INTEGER NOT NULL,
    id_categoria INTEGER NOT NULL,
    id_tipo_contenido INTEGER NOT NULL,
    id_red_social INTEGER NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    comentarios INTEGER NOT NULL DEFAULT 0,
    alcance INTEGER NOT NULL DEFAULT 0,
    engagement INTEGER NOT NULL DEFAULT 0,
    texto_publicacion TEXT NOT NULL,
    url_publicacion TEXT NOT NULL,
    FOREIGN KEY (id_tiempo) REFERENCES dim_tiempo(id_tiempo),
    FOREIGN KEY (id_categoria) REFERENCES dim_categoria(id_categoria),
    FOREIGN KEY (id_tipo_contenido) REFERENCES dim_tipo_contenido(id_tipo_contenido),
    FOREIGN KEY (id_red_social) REFERENCES dim_red_social(id_red_social)
);

-- Índices para optimización de consultas del dashboard
CREATE INDEX IF NOT EXISTS idx_hecho_tiempo ON hecho_publicacion(id_tiempo);
CREATE INDEX IF NOT EXISTS idx_hecho_categoria ON hecho_publicacion(id_categoria);
CREATE INDEX IF NOT EXISTS idx_hecho_tipo ON hecho_publicacion(id_tipo_contenido);

-- Vistas analíticas de soporte
DROP VIEW IF EXISTS vw_resumen_general;
CREATE VIEW vw_resumen_general AS
SELECT 
    t.año,
    t.mes,
    t.nombre_mes,
    c.nombre_categoria,
    tc.nombre_tipo AS tipo_contenido,
    COUNT(h.id_publicacion) AS total_publicaciones,
    SUM(h.likes) AS total_likes,
    SUM(h.comentarios) AS total_comentarios,
    SUM(h.alcance) AS total_alcance,
    SUM(h.engagement) AS total_engagement,
    ROUND(AVG(h.engagement), 2) AS engagement_promedio
FROM hecho_publicacion h
JOIN dim_tiempo t ON h.id_tiempo = t.id_tiempo
JOIN dim_categoria c ON h.id_categoria = c.id_categoria
JOIN dim_tipo_contenido tc ON h.id_tipo_contenido = tc.id_tipo_contenido
GROUP BY t.año, t.mes, t.nombre_mes, c.nombre_categoria, tc.nombre_tipo;

DROP VIEW IF EXISTS vw_detalle_biblioteca;
CREATE VIEW vw_detalle_biblioteca AS
SELECT 
    h.id_publicacion,
    h.codigo_publicacion,
    t.fecha,
    t.nombre_mes,
    c.nombre_categoria,
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
JOIN dim_red_social rs ON h.id_red_social = rs.id_red_social;
"""

class DatabaseLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.db_dir = os.path.join(base_dir, "data", "database")
        self.processed_dir = os.path.join(base_dir, "data", "processed")
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "bi_epis_upt.db")

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_schema(self):
        """Crea el esquema dimensional en SQLite (T2.1)"""
        with self.get_connection() as conn:
            conn.executescript(DDL_STATEMENTS)
        logger.info(f"Esquema dimensional creado exitosamente en {self.db_path}")

    def load_dimensional_model(self, tables_dict: Dict[str, pd.DataFrame]):
        """Carga las dimensiones y la tabla de hechos en SQLite y exporta a CSV (T2.4)"""
        self.create_schema()
        with self.get_connection() as conn:
            # Limpiar tablas existentes en orden inverso de dependencias
            conn.execute("DELETE FROM hecho_publicacion;")
            conn.execute("DELETE FROM dim_tiempo;")
            conn.execute("DELETE FROM dim_categoria;")
            conn.execute("DELETE FROM dim_tipo_contenido;")
            conn.execute("DELETE FROM dim_red_social;")
            
            # Cargar dimensiones
            tables_dict["dim_tiempo"].to_sql("dim_tiempo", conn, if_exists="append", index=False)
            tables_dict["dim_categoria"].to_sql("dim_categoria", conn, if_exists="append", index=False)
            tables_dict["dim_tipo_contenido"].to_sql("dim_tipo_contenido", conn, if_exists="append", index=False)
            tables_dict["dim_red_social"].to_sql("dim_red_social", conn, if_exists="append", index=False)
            
            # Cargar hechos
            tables_dict["hecho_publicacion"].to_sql("hecho_publicacion", conn, if_exists="append", index=False)
            conn.commit()

        logger.info(f"Datos cargados exitosamente en SQLite: {len(tables_dict['hecho_publicacion'])} hechos registrados.")

        # Exportar CSVs limpios para consumo directo en Power BI
        for table_name, df in tables_dict.items():
            csv_path = os.path.join(self.processed_dir, f"{table_name}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Archivos CSV procesados exportados en {self.processed_dir}")

    def verify_database(self) -> Dict[str, Any]:
        """Valida la integridad del modelo dimensional (T2.5)"""
        report = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Conteos
            for tbl in ["dim_tiempo", "dim_categoria", "dim_tipo_contenido", "dim_red_social", "hecho_publicacion"]:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                report[f"count_{tbl}"] = cursor.fetchone()[0]
                
            # Validar integridad referencial (Foreign Keys)
            cursor.execute("PRAGMA foreign_key_check;")
            fk_violations = cursor.fetchall()
            report["fk_violations"] = len(fk_violations)
            
            # Validar que no haya nulos en campos obligatorios de hechos
            cursor.execute("""
                SELECT COUNT(*) FROM hecho_publicacion 
                WHERE id_tiempo IS NULL OR id_categoria IS NULL OR id_tipo_contenido IS NULL 
                   OR likes IS NULL OR comentarios IS NULL OR texto_publicacion IS NULL;
            """)
            report["null_fact_fields"] = cursor.fetchone()[0]
            
            # Validar totales
            cursor.execute("SELECT SUM(likes), SUM(comentarios), SUM(alcance) FROM hecho_publicacion;")
            tot_likes, tot_comms, tot_reach = cursor.fetchone()
            report["total_likes"] = tot_likes
            report["total_comentarios"] = tot_comms
            report["total_alcance"] = tot_reach
            
        report["is_valid"] = (
            report["count_hecho_publicacion"] > 0 and 
            report["fk_violations"] == 0 and 
            report["null_fact_fields"] == 0
        )
        return report

if __name__ == "__main__":
    loader = DatabaseLoader(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    report = loader.verify_database()
    print("Reporte de verificación:")
    for k, v in report.items():
        print(f"  {k}: {v}")
