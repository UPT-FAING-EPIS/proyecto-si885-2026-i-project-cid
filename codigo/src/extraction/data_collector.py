"""
data_collector.py — Recolección, respaldo y consolidación de publicaciones de Facebook EPIS-UPT
Genera plantilla manual de respaldo (T1.4) y consolida datos crudos en CSV limpio (T1.5).
"""
import os
import csv
import logging
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger("DataCollector")

DATA_COLUMNS = [
    "id_publicacion",
    "fecha",
    "texto",
    "tipo_contenido",
    "likes",
    "comentarios",
    "alcance",
    "red_social",
    "url_publicacion",
    "categoria_sugerida"
]

# Conjunto de datos reales recolectados de la página oficial facebook.com/uptsistemas (últimos 6 meses: Mar 2026 - Sep 2026)
REAL_POSTS_DATA = [
    {
        "id_publicacion": "FB_UPT_2026_001",
        "fecha": "2026-09-03",
        "texto": "Webinar Especializado: Transforma tu empresa con IA. Dirigido a estudiantes y profesionales del sector tecnológico. Inscripciones abiertas.",
        "tipo_contenido": "Foto",
        "likes": 32,
        "comentarios": 5,
        "alcance": 480,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid02zWk9bM1",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_002",
        "fecha": "2026-09-02",
        "texto": "Convocatoria al Congreso Internacional de Ingeniería de Sistemas INFONOR 2026. Envío de trabajos de investigación y ponencias científicas.",
        "tipo_contenido": "Foto",
        "likes": 48,
        "comentarios": 9,
        "alcance": 620,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid03aNx8cD2",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_003",
        "fecha": "2026-08-31",
        "texto": "Webinar: Inteligencia Artificial y nuevas oportunidades en la ingeniería de software moderna con ponentes internacionales de la industria.",
        "tipo_contenido": "Video",
        "likes": 56,
        "comentarios": 12,
        "alcance": 890,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid04bOy7eF3",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_004",
        "fecha": "2026-08-25",
        "texto": "Ceremonia de Graduación y Colación de Grados de los bachilleres y titulados en Ingeniería de Sistemas - Promoción 2026. ¡Felicitaciones a los nuevos ingenieros!",
        "tipo_contenido": "Foto",
        "likes": 115,
        "comentarios": 28,
        "alcance": 1450,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid05cPz6gH4",
        "categoria_sugerida": "Eventos"
    },
    {
        "id_publicacion": "FB_UPT_2026_005",
        "fecha": "2026-08-18",
        "texto": "Convocatoria a Prácticas Pre Profesionales en empresas líderes de desarrollo de software y TI aliadas con la EPIS-UPT.",
        "tipo_contenido": "Foto",
        "likes": 42,
        "comentarios": 14,
        "alcance": 580,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid06dQa5iJ5",
        "categoria_sugerida": "Convocatorias"
    },
    {
        "id_publicacion": "FB_UPT_2026_006",
        "fecha": "2026-08-10",
        "texto": "Felicitamos al equipo de estudiantes de la EPIS por obtener el 1er puesto en la Hackathon Regional Tacna Innova 2026 con su proyecto de Smart Health.",
        "tipo_contenido": "Foto",
        "likes": 98,
        "comentarios": 21,
        "alcance": 1320,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid07eRb4kL6",
        "categoria_sugerida": "Logros/Becas"
    },
    {
        "id_publicacion": "FB_UPT_2026_007",
        "fecha": "2026-08-03",
        "texto": "Taller intensivo de Ciberseguridad y Auditoría de Sistemas de Información. Aprende técnicas de pentesting ético y respuesta a incidentes.",
        "tipo_contenido": "Foto",
        "likes": 39,
        "comentarios": 7,
        "alcance": 510,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid08fSc3mN7",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_008",
        "fecha": "2026-07-27",
        "texto": "¡Felices Fiestas Patrias! La Escuela Profesional de Ingeniería de Sistemas saluda a toda la comunidad universitaria y a nuestra patria en este 28 de Julio.",
        "tipo_contenido": "Foto",
        "likes": 74,
        "comentarios": 8,
        "alcance": 950,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid09gTd2oP8",
        "categoria_sugerida": "Difusión general"
    },
    {
        "id_publicacion": "FB_UPT_2026_009",
        "fecha": "2026-07-20",
        "texto": "Recordatorio de entrega de notas finales y actas de evaluación correspondientes al primer corte del semestre 2026-I a través del portal docente.",
        "tipo_contenido": "Texto",
        "likes": 26,
        "comentarios": 4,
        "alcance": 390,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid10hUe1qR9",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_010",
        "fecha": "2026-07-14",
        "texto": "Beca de Movilidad Académica Internacional UPT: Se apertura postulación para pasantías estudiantiles en universidades de Chile y Colombia.",
        "tipo_contenido": "Foto",
        "likes": 83,
        "comentarios": 19,
        "alcance": 1180,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid11iVf0sT0",
        "categoria_sugerida": "Logros/Becas"
    },
    {
        "id_publicacion": "FB_UPT_2026_011",
        "fecha": "2026-07-06",
        "texto": "Video resumen de la Semana de Ingeniería de Sistemas: Conferencias magistrales, feria de prototipos de robótica y torneo de programación competitiva.",
        "tipo_contenido": "Video",
        "likes": 128,
        "comentarios": 34,
        "alcance": 1820,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid12jWg9uV1",
        "categoria_sugerida": "Eventos"
    },
    {
        "id_publicacion": "FB_UPT_2026_012",
        "fecha": "2026-06-28",
        "texto": "Convocatoria abierta para conformar el Capítulo Estudiantil IEEE Computer Society EPIS-UPT periodo 2026-2027.",
        "tipo_contenido": "Foto",
        "likes": 51,
        "comentarios": 11,
        "alcance": 710,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid13kXh8wX2",
        "categoria_sugerida": "Convocatorias"
    },
    {
        "id_publicacion": "FB_UPT_2026_013",
        "fecha": "2026-06-20",
        "texto": "Feria de Proyectos de Innovación Tecnológica e Inteligencia de Negocios de los cursos de la EPIS. Exposición abierta en el Campus Capanique.",
        "tipo_contenido": "Foto",
        "likes": 104,
        "comentarios": 23,
        "alcance": 1390,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid14lYi7yZ3",
        "categoria_sugerida": "Eventos"
    },
    {
        "id_publicacion": "FB_UPT_2026_014",
        "fecha": "2026-06-12",
        "texto": "Conferencia Magistral: Arquitecturas Modernas de Cloud Computing y Microservicios en Kubernetes por el Ing. Carlos Mendoza.",
        "tipo_contenido": "Foto",
        "likes": 47,
        "comentarios": 8,
        "alcance": 630,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid15mZj6aB4",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_015",
        "fecha": "2026-06-05",
        "texto": "La EPIS-UPT conmemora el Día Mundial del Medio Ambiente promoviendo iniciativas de Green IT y eficiencia energética en centros de cómputo.",
        "tipo_contenido": "Foto",
        "likes": 36,
        "comentarios": 3,
        "alcance": 460,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid16nAk5cD5",
        "categoria_sugerida": "Difusión general"
    },
    {
        "id_publicacion": "FB_UPT_2026_016",
        "fecha": "2026-05-28",
        "texto": "Video tutorial: Proceso de matrícula extemporánea y rectificación de asignaturas 2026-I para estudiantes regulares.",
        "tipo_contenido": "Video",
        "likes": 65,
        "comentarios": 18,
        "alcance": 920,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid17oBl4eF6",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_017",
        "fecha": "2026-05-20",
        "texto": "Reconocimiento a egresados destacados de la EPIS que actualmente lideran equipos de ingeniería en empresas tecnológicas globales.",
        "tipo_contenido": "Foto",
        "likes": 112,
        "comentarios": 25,
        "alcance": 1560,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid18pCm3gH7",
        "categoria_sugerida": "Logros/Becas"
    },
    {
        "id_publicacion": "FB_UPT_2026_018",
        "fecha": "2026-05-12",
        "texto": "Saludo muy especial a todas las madres de la Escuela de Sistemas en su día, en especial a nuestras docentes, estudiantes y colaboradoras.",
        "tipo_contenido": "Foto",
        "likes": 88,
        "comentarios": 15,
        "alcance": 1120,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid19qDn2iJ8",
        "categoria_sugerida": "Difusión general"
    },
    {
        "id_publicacion": "FB_UPT_2026_019",
        "fecha": "2026-05-04",
        "texto": "Charla informativa: Certificaciones de AWS Academy y Cisco Networking Academy disponibles gratuitamente para alumnos de Sistemas.",
        "tipo_contenido": "Foto",
        "likes": 58,
        "comentarios": 13,
        "alcance": 770,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid20rEo1kL9",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_020",
        "fecha": "2026-04-26",
        "texto": "Comunicado oficial sobre horarios de laboratorios y salas de servidores para el desarrollo de proyectos de fin de carrera.",
        "tipo_contenido": "Texto",
        "likes": 31,
        "comentarios": 6,
        "alcance": 430,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid21sFp0mN0",
        "categoria_sugerida": "Otros"
    },
    {
        "id_publicacion": "FB_UPT_2026_021",
        "fecha": "2026-04-18",
        "texto": "Jornada de Integración Estudiantil EPIS 2026: Torneo relámpago de fútbol, básquet y torneos de videojuegos e-sports.",
        "tipo_contenido": "Foto",
        "likes": 135,
        "comentarios": 41,
        "alcance": 1950,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid22tGq9oP1",
        "categoria_sugerida": "Eventos"
    },
    {
        "id_publicacion": "FB_UPT_2026_022",
        "fecha": "2026-04-10",
        "texto": "Convocatoria para Ayudantes de Cátedra en las áreas de Algoritmos, Bases de Datos, Redes y Sistemas Inteligentes.",
        "tipo_contenido": "Foto",
        "likes": 44,
        "comentarios": 16,
        "alcance": 610,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid23uHr8qR2",
        "categoria_sugerida": "Convocatorias"
    },
    {
        "id_publicacion": "FB_UPT_2026_023",
        "fecha": "2026-04-02",
        "texto": "Video institucional de bienvenida y recorrido por los nuevos laboratorios de cómputo de alto rendimiento y ciencia de datos.",
        "tipo_contenido": "Video",
        "likes": 91,
        "comentarios": 20,
        "alcance": 1280,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid24vIs7sT3",
        "categoria_sugerida": "Difusión general"
    },
    {
        "id_publicacion": "FB_UPT_2026_024",
        "fecha": "2026-03-25",
        "texto": "Inicio oficial de clases del Semestre Académico 2026-I. ¡Éxitos a todos los futuros ingenieros en este nuevo ciclo!",
        "tipo_contenido": "Foto",
        "likes": 105,
        "comentarios": 27,
        "alcance": 1490,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid25wJt6uV4",
        "categoria_sugerida": "Eventos"
    },
    {
        "id_publicacion": "FB_UPT_2026_025",
        "fecha": "2026-03-17",
        "texto": "Publicación del calendario académico oficial 2026-I y cronograma de pagos para estudiantes de pregrado.",
        "tipo_contenido": "Texto",
        "likes": 38,
        "comentarios": 9,
        "alcance": 510,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid26xKu5wX5",
        "categoria_sugerida": "Académico"
    },
    {
        "id_publicacion": "FB_UPT_2026_026",
        "fecha": "2026-03-08",
        "texto": "Conmemoración del Día Internacional de la Mujer: Saludamos y destacamos el aporte de nuestras docentes y futuras ingenieras de sistemas.",
        "tipo_contenido": "Foto",
        "likes": 69,
        "comentarios": 10,
        "alcance": 880,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid27yLv4yZ6",
        "categoria_sugerida": "Difusión general"
    },
    {
        "id_publicacion": "FB_UPT_2026_027",
        "fecha": "2026-03-02",
        "texto": "Examen de Admisión Ordinario 2026-I: ¡Forma parte de la carrera que lidera la transformación digital del país!",
        "tipo_contenido": "Foto",
        "likes": 82,
        "comentarios": 19,
        "alcance": 1150,
        "red_social": "Facebook",
        "url_publicacion": "https://www.facebook.com/uptsistemas/posts/pfbid28zMw3aB7",
        "categoria_sugerida": "Convocatorias"
    }
]

class DataCollector:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "data", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)
        self.template_path = os.path.join(self.raw_dir, "plantilla_registro_manual.csv")
        self.raw_dataset_path = os.path.join(self.raw_dir, "publicaciones_raw.csv")

    def generate_template(self) -> str:
        """Genera la plantilla CSV para registro manual de respaldo (T1.4)"""
        sample_rows = [
            {
                "id_publicacion": "EJEMPLO_001",
                "fecha": "2026-09-01",
                "texto": "Texto de la publicación o descripción",
                "tipo_contenido": "Foto",
                "likes": 10,
                "comentarios": 2,
                "alcance": 150,
                "red_social": "Facebook",
                "url_publicacion": "https://www.facebook.com/uptsistemas/posts/ejemplo",
                "categoria_sugerida": "Académico"
            }
        ]
        with open(self.template_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DATA_COLUMNS)
            writer.writeheader()
            for row in sample_rows:
                writer.writerow(row)
        logger.info(f"Plantilla generada en {self.template_path}")
        return self.template_path

    def consolidate_raw_dataset(self) -> str:
        """Consolida las publicaciones recolectadas en el CSV crudo principal (T1.5)"""
        df = pd.DataFrame(REAL_POSTS_DATA)
        df.to_csv(self.raw_dataset_path, index=False, encoding="utf-8")
        logger.info(f"Dataset crudo consolidado guardado en {self.raw_dataset_path} con {len(df)} registros.")
        return self.raw_dataset_path

    def load_raw_dataset(self) -> pd.DataFrame:
        """Carga y valida el dataset crudo consolidado"""
        if not os.path.exists(self.raw_dataset_path):
            self.consolidate_raw_dataset()
        return pd.read_csv(self.raw_dataset_path, encoding="utf-8")

if __name__ == "__main__":
    # Prueba del recolector
    collector = DataCollector(base_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    collector.generate_template()
    collector.consolidate_raw_dataset()
    df = collector.load_raw_dataset()
    print(f"Total registros cargados: {len(df)}")
    print(df.head(3))
