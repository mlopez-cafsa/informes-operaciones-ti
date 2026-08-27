"""
common.py
=========
Utilidades compartidas entre manage_informes.py, manage_pendientes.py y
reportes_lib.py — una sola fuente de verdad para evitar que la lógica de
slugs/enlaces de Jira se desincronice entre los dos módulos del sitio.
"""

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s_-]+", "-", texto)
    return texto.strip("-")


def parse_jira_url(url: str) -> dict:
    key_match = re.search(r"/browse/([A-Z][A-Z0-9]*-\d+)", url)
    key = key_match.group(1) if key_match else None
    label = f"Ver {key} en Jira" if key else "Ver tarea en Jira"
    return {"label": label, "url": url}
