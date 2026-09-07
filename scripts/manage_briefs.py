#!/usr/bin/env python3
"""
manage_briefs.py
=================
Administra el manifiesto de `briefs/` — briefs diarios en HTML que Marco
genera fuera de este sistema (correo/Teams/Jira) y deja caer en esa
carpeta para poder verlos desde el index del portal.

IMPORTANTE — contenido sensible, carpeta NUNCA pública:
`briefs/` está excluida en `.gitignore` a propósito (2026-09-07): los
briefs traen correos reales de colegas y proveedores, detalle de
negociación de contratos, montos/facturas y casos de clientes con datos
operativos. Este script y el manifiesto que genera viven físicamente
dentro del repo, pero nunca deben comitearse. Ver la nota completa en
`contexto-proyecto/CONTEXTO.md` (sección de 2026-09-07).

Convención de nombre de archivo: `DD-##-MM-YYYY-brief.html`
  DD    = día del mes (2 dígitos)
  ##    = número de secuencia del brief dentro de ese mismo día (2 dígitos,
          empieza en 01; permite más de un brief por día, ej. uno matutino
          y una actualización de tarde)
  MM    = mes (2 dígitos)
  YYYY  = año (4 dígitos)

Ejemplo: `07-01-09-2026-brief.html` = 7 de septiembre de 2026, brief #1.

Subcomandos:
  build   Escanea briefs/*.html, valida el nombre de cada archivo, y
          escribe briefs/manifest.json con la lista completa y cuál es
          "el más reciente" (por fecha desc, luego secuencia desc),
          además de qué tan reciente es respecto a hoy. El index.html
          público lee este manifiesto por JavaScript (`fetch`) — si la
          carpeta no existe (ej. en el sitio publicado en GitHub Pages),
          el fetch falla en silencio y el botón del brief simplemente no
          aparece. Ver `assets/js/brief-viewer.js`.

Uso:
  python3 scripts/manage_briefs.py build
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

from common import ROOT

BRIEFS_DIR = ROOT / "briefs"
MANIFEST_FILE = BRIEFS_DIR / "manifest.json"

NOMBRE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{2})-(\d{4})-brief\.html$")

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def parse_nombre_brief(nombre: str):
    """Valida y descompone 'DD-##-MM-YYYY-brief.html'. Devuelve
    (fecha: date, secuencia: int) o None si el nombre no matchea el
    patrón o la fecha no es válida (no se asume nada — se descarta con
    aviso en vez de adivinar)."""
    m = NOMBRE_RE.match(nombre)
    if not m:
        return None
    dd, secuencia, mm, yyyy = m.groups()
    try:
        fecha = date(int(yyyy), int(mm), int(dd))
    except ValueError:
        return None
    return fecha, int(secuencia)


def etiqueta_fecha(fecha: date, secuencia: int) -> str:
    return f"{fecha.day} de {MESES[fecha.month - 1]} {fecha.year} — brief #{secuencia}"


def build() -> None:
    if not BRIEFS_DIR.exists():
        sys.exit(f"[ERROR] No existe la carpeta {BRIEFS_DIR}.")

    encontrados = []
    descartados = []
    for archivo in sorted(BRIEFS_DIR.glob("*.html")):
        parsed = parse_nombre_brief(archivo.name)
        if parsed is None:
            descartados.append(archivo.name)
            continue
        fecha, secuencia = parsed
        encontrados.append(
            {
                "archivo": archivo.name,
                "fecha": fecha.isoformat(),
                "secuencia": secuencia,
                "etiqueta": etiqueta_fecha(fecha, secuencia),
            }
        )

    # Más reciente = fecha más alta y, dentro de la misma fecha, la
    # secuencia más alta (el último brief generado ese día).
    encontrados.sort(key=lambda b: (b["fecha"], b["secuencia"]), reverse=True)

    hoy = date.today()
    mas_reciente = None
    if encontrados:
        primero = encontrados[0]
        fecha_brief = date.fromisoformat(primero["fecha"])
        dias_diferencia = (hoy - fecha_brief).days
        mas_reciente = {
            **primero,
            "es_de_hoy": fecha_brief == hoy,
            "dias_de_diferencia": dias_diferencia,
        }

    manifiesto = {
        "generado": hoy.isoformat(),
        "total": len(encontrados),
        "briefs": encontrados,
        "mas_reciente": mas_reciente,
    }

    MANIFEST_FILE.write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[OK] briefs/manifest.json regenerado con {len(encontrados)} brief(s).")
    if mas_reciente:
        frescura = "de hoy" if mas_reciente["es_de_hoy"] else f"hace {mas_reciente['dias_de_diferencia']} día(s)"
        print(f"[OK] Más reciente: {mas_reciente['archivo']} ({frescura}).")
    if descartados:
        print(f"[AVISO] {len(descartados)} archivo(s) en briefs/ no siguen el patrón 'DD-##-MM-YYYY-brief.html' y se ignoraron: {', '.join(descartados)}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "build":
        sys.exit("Uso: python3 scripts/manage_briefs.py build")
    build()


if __name__ == "__main__":
    main()
