"""
scraper.py — Extractor de publicaciones públicas de Facebook para EPIS-UPT
Valida conectividad pública, extrae metadatos y publicaciones accesibles.
"""
import re
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FacebookScraper")

class FacebookScraper:
    """Extractor para la página pública de Facebook https://www.facebook.com/uptsistemas"""
    
    DEFAULT_URL = "https://www.facebook.com/uptsistemas"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, page_url: str = DEFAULT_URL, timeout: int = 15):
        self.page_url = page_url
        self.timeout = timeout
        self.session = requests.Session()


    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba el acceso público a la página de Facebook.
        Retorna un diccionario de diagnóstico con status, título y accesibilidad.
        """
        try:
            response = self.session.get(self.page_url, timeout=self.timeout)
            status_code = response.status_code
            html_text = response.text
            
            # Verificar título y elementos básicos
            soup = BeautifulSoup(html_text, "html.parser")
            title = soup.title.string.strip() if soup.title else "Sin título"
            
            # Verificar si existe bloqueo o pantalla de inicio de sesión obligatoria
            is_login_wall = "Iniciar sesión" in html_text and "Regístrate" in html_text and "uptsistemas" not in html_text.lower()
            is_accessible = status_code == 200 and not is_login_wall
            
            logger.info(f"Conexión exitosa a {self.page_url}. Código: {status_code}, Título: {title}")
            return {
                "success": is_accessible,
                "status_code": status_code,
                "page_title": title,
                "bytes_received": len(html_text),
                "is_login_wall": is_login_wall,
                "message": "Página pública accesible" if is_accessible else "Página restringida o requiere autenticación"
            }
        except Exception as e:
            logger.error(f"Error al conectar con {self.page_url}: {e}")
            return {
                "success": False,
                "status_code": 0,
                "page_title": "",
                "bytes_received": 0,
                "is_login_wall": False,
                "message": str(e)
            }

    def extract_recent_posts(self) -> List[Dict[str, Any]]:
        """
        Extrae publicaciones del payload HTML público disponible.
        Busca bloques JSON de Relay y meta tags.
        """
        posts = []
        try:
            response = self.session.get(self.page_url, timeout=self.timeout)
            if response.status_code != 200:
                return posts
            
            html = response.text
            
            # Buscar menciones de texto de publicaciones en el HTML estático
            # Facebook inserta fragmentos en bloques de script con textos de publicaciones
            matches = re.findall(r'"message":\{"text":"(.*?)"\}', html)
            for i, msg in enumerate(matches):
                clean_msg = msg.encode().decode('unicode_escape')
                if len(clean_msg) > 15:
                    posts.append({
                        "texto": clean_msg,
                        "tipo_contenido": "Foto",
                        "red_social": "Facebook",
                        "fuente": "scraping_html"
                    })
        except Exception as e:
            logger.warning(f"Extracción directa parcial: {e}")
            
        return posts

if __name__ == "__main__":
    scraper = FacebookScraper()
    diag = scraper.test_connection()
    print("Diagnóstico de conexión:")
    for k, v in diag.items():
        print(f"  {k}: {v}")
