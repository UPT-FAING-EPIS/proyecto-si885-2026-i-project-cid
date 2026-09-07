"""
categorizer.py — Clasificador de publicaciones por categoría de contenido (T2.3)
Categorías oficiales según spec.md:
- Académico
- Eventos
- Logros/Becas
- Convocatorias
- Difusión general
- Otros
"""
import re
from typing import List

VALID_CATEGORIES = [
    "Académico",
    "Eventos",
    "Logros/Becas",
    "Convocatorias",
    "Difusión general",
    "Otros"
]

CATEGORY_RULES = {
    "Académico": [
        r"\bwebinar\b", r"\bconferencia\b", r"\bcongreso\b", r"\binfonor\b",
        r"\bponencia\b", r"\bcurso\b", r"\btaller\b", r"\bciberseguridad\b",
        r"\bclases?\b", r"\bnotas?\b", r"\bactas?\b", r"\bevaluaci[oó]n\b",
        r"\bc[aá]tedra\b", r"\baws academy\b", r"\bcisco\b", r"\bcloud\b",
        r"\bmatr[ií]cula\b", r"\bacad[eé]mic[oa]\b"
    ],
    "Eventos": [
        r"\bgraduaci[oó]n\b", r"\bcolaci[oó]n\b", r"\bgrados\b", r"\bsemana de ingenier[ií]a\b",
        r"\bferia\b", r"\bintegraci[oó]n\b", r"\btorneo\b", r"\baniversario\b",
        r"\bceremonia\b", r"\be-?sports\b", r"\bjornada\b", r"\binicio oficial\b"
    ],
    "Logros/Becas": [
        r"\bhackathon\b", r"\bpuesto\b", r"\bpremio\b", r"\bganador\b",
        r"\bbeca\b", r"\bmovilidad acad[eé]mica\b", r"\bpasant[ií]a\b",
        r"\begresados destacados\b", r"\breconocimiento\b", r"\blideran\b"
    ],
    "Convocatorias": [
        r"\bconvocatoria\b", r"\bpr[aá]cticas\b", r"\bpre profesionales\b",
        r"\bbolsa de trabajo\b", r"\bieee\b", r"\badmisi[oó]n\b", r"\bpostulaci[oó]n\b",
        r"\bayudantes\b", r"\binscripci[oó]n\b"
    ],
    "Difusión general": [
        r"\bfiestas patrias\b", r"\bmedio ambiente\b", r"\bd[ií]a de la madre\b",
        r"\bd[ií]a internacional de la mujer\b", r"\bsaludamos\b", r"\bsaludo\b",
        r"\befem[eé]rides\b", r"\blaboratorios de c[oó]mputo\b", r"\brecorrido\b"
    ]
}

class ContentCategorizer:
    @staticmethod
    def categorize_text(text: str, suggested_cat: str = None) -> str:
        """
        Clasifica el texto en una de las 6 categorías oficiales.
        Usa suggested_cat como referencia si es válida, o aplica reglas léxicas.
        """
        if suggested_cat and suggested_cat in VALID_CATEGORIES and suggested_cat != "Otros":
            return suggested_cat
            
        clean_text = text.lower()
        
        # Evaluar reglas con patrones regex
        for cat, patterns in CATEGORY_RULES.items():
            for pat in patterns:
                if re.search(pat, clean_text):
                    return cat
                    
        return "Otros"

    @staticmethod
    def get_valid_categories() -> List[str]:
        return list(VALID_CATEGORIES)
