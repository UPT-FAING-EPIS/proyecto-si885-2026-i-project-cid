"""
Módulo de extracción para datos de redes sociales EPIS-UPT
"""
from .scraper import FacebookScraper
from .data_collector import DataCollector

__all__ = ["FacebookScraper", "DataCollector"]
