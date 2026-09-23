"""
common.py
=========
Utilidades compartidas entre manage_informes.py, manage_pendientes.py y
reportes_lib.py — una sola fuente de verdad para evitar que la lógica de
slugs/enlaces de Jira se desincronice entre los dos módulos del sitio.
"""

import html
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def esc(texto) -> str:
    """Escapa HTML (&, <, >, comillas) para texto que debe insertarse tal
    cual en una página — título, categoría, nombre, cargo, etc.

    2026-09-23 (auditoría): antes, estos campos se interpolaban crudos en
    los f-strings de render_*() de manage_informes.py/reportes_lib.py. En
    la práctica nunca rompió nada porque nadie ha puesto un "&"/"<" suelto
    en un título todavía, pero era una dependencia silenciosa de la buena
    suerte, no del código — cualquier título o nombre futuro con esos
    caracteres (copiado de Jira, de un correo, etc.) generaría HTML mal
    formado. `esc()` es la barrera explícita para esos campos de texto
    plano.

    OJO — no usar en TODOS los campos de texto: `solicitud` y
    `recomendacion` en data/pendientes.json llevan HTML enriquecido a
    propósito (`<strong>`, `<ol>`, `<li>`) — ver render_pendiente_item()
    en reportes_lib.py. Aplicar esc() ahí destruiría ese formato
    (convertiría las etiquetas en texto literal). Este helper es para los
    campos que deben ser SIEMPRE texto plano.

    Acepta no-strings (números, None) sin reventar, igual que hacían los
    f-strings originales."""
    if texto is None:
        return ""
    return html.escape(str(texto), quote=True)


def guardar_json_atomico(ruta: Path, datos) -> None:
    """Escribe `datos` como JSON en `ruta` de forma atómica: primero a un
    archivo temporal en el mismo directorio, y solo al final lo renombra
    sobre el destino (`os.replace`, atómico en el mismo filesystem).

    2026-09-23 (auditoría): antes, guardar_informes()/guardar_pendientes()
    escribían directo sobre data/informes.json y data/pendientes.json con
    `open(..., "w")`. Si el proceso se interrumpe a mitad de esa escritura
    (Ctrl+C, corte de luz, error de disco), el archivo queda truncado —
    JSON inválido — y el sitio completo deja de poder regenerarse hasta
    reparar el archivo a mano. Escribir a un temporal y renombrar al final
    evita ese escenario: o el reemplazo ocurre completo, o el archivo
    original queda intacto."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=ruta.parent, prefix=f".{ruta.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, ruta)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


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


# ---------- Iconografía SVG compartida (2026-09-18) ----------
# Set pequeño de íconos de línea (stroke, viewBox 24x24, currentColor) —
# una sola fuente de verdad para que manage_informes.py, reportes_lib.py
# y manage_pendientes.py usen siempre el mismo lenguaje visual, en vez de
# repetir <svg> a mano en cada función de render. Sin dependencias
# externas (nada de fuentes de íconos ni CDN): son strings planos,
# coherente con el resto del proyecto (Python stdlib únicamente).
def _icono(paths: str, tamano: int = 16, clase: str = "") -> str:
    clase_attr = f' class="{clase}"' if clase else ""
    return (
        f'<svg{clase_attr} width="{tamano}" height="{tamano}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{paths}</svg>'
    )


def icono_flecha(tamano: int = 14) -> str:
    """Flecha "→" en SVG (reemplaza el entity &rarr; en los links de
    "ver más"). Lleva la clase .icono-flecha para el desplazamiento sutil
    al pasar el mouse (ver .icono-flecha en style.css)."""
    return _icono(
        '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
        tamano, "icono-flecha",
    )


def icono_seccion(paths: str, tamano: int = 20) -> str:
    """Ícono de encabezado de sección — usar junto con la clase
    .titulo-seccion envolviendo el <h2>. Ver ICONO_* más abajo para las
    figuras disponibles."""
    return _icono(paths, tamano, "icono-seccion")


def icono(paths: str, tamano: int = 16) -> str:
    """Ícono genérico sin clase especial (botones, estados vacíos)."""
    return _icono(paths, tamano)


# Figuras (paths internos, sin el <svg> envolvente) — pasar a icono()/icono_seccion().
ICONO_PERSONAS = ('<circle cx="9" cy="7" r="4"/><path d="M2 21v-2a4 4 0 0 1 4-4h6a4 4 0 0 1 4 4v2"/>'
                   '<circle cx="17" cy="7" r="3"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/>')
ICONO_GRAFICO = '<line x1="6" y1="20" x2="6" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="18" y1="20" x2="18" y2="14"/>'
ICONO_LLAVE = ('<path d="M14.7 6.3a4 4 0 1 0-5.66 5.66L3 18v3h3l6.04-6.04a4 4 0 0 0 5.66-5.66'
               'l-2.83 2.83-2-2 2.83-2.83z"/>')
ICONO_TICKET = ('<rect x="4" y="3" width="16" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/>'
                '<line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/>')
ICONO_CORREO = '<rect x="3" y="5" width="18" height="14" rx="2"/><polyline points="3 7 12 13 21 7"/>'
ICONO_CHECK = '<circle cx="12" cy="12" r="9"/><polyline points="8 12 11 15 16 9"/>'
ICONO_EXTERNO = ('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
                  '<polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>')
ICONO_BUZON_VACIO = ('<path d="M22 12h-6l-2 3h-4l-2-3H2"/>'
                      '<path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89'
                      'A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>')
ICONO_OBJETIVO = '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>'
