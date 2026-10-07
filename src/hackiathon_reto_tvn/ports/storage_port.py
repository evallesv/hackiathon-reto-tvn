"""Storage Port specification for dataset ingestion, manifest hashing, and case persistence."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from hackiathon_reto_tvn.domain.models import EventoGeoJSON, FichaCaso, Indicador, Manifest, Noticia


class BaseStorageRepository(ABC):
    """Abstract interface for datasets and outputs storage."""

    @abstractmethod
    def load_noticias(self, path: Path) -> List[Noticia]:
        """Loads and validates noticias.csv."""
        pass

    @abstractmethod
    def load_indicadores(self, path: Path) -> List[Indicador]:
        """Loads and validates indicadores.csv."""
        pass

    @abstractmethod
    def load_eventos(self, path: Path) -> List[EventoGeoJSON]:
        """Loads and validates eventos.geojson."""
        pass

    @abstractmethod
    def save_fichas(self, fichas: List[FichaCaso], output_path: Path) -> None:
        """Persists fichas to jsonl."""
        pass

    @abstractmethod
    def generate_manifest(self, data_dir: Path) -> Manifest:
        """Generates manifest.json with SHA-256 hashes and metadata."""
        pass
