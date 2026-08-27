#!/usr/bin/env python3
"""
manage_informes.py
===================
Administra el sitio de informes de Operaciones de TI (CAFSA).

Subcomandos:
  nuevo   Crea un nuevo informe HTML a partir de la plantilla, lo registra
          en data/informes.json y regenera index.html de inmediato.
  build   Regenera index.html a partir de data/informes.json (sin crear
          informes nuevos). Útil si editaste el JSON a mano o cambiaste
          la prioridad/cumplimiento/fases de un informe existente.

IMPORTANTE: index.html se genera siempre a partir de este script.
No editar index.html directamente: los cambios se perderían en el
siguiente 'build'.

CRITERIO DE SEMÁFORO (definido)
--------------------------------
El color del semáforo (verde/amarillo/rojo) NO se asigna a mano: se calcula
a partir de dos datos que sí se declaran al crear el informe:

  --prioridad     alta | media | baja
  --cumplimiento  completado | bloqueado | vencido | en_riesgo |
                  a_tiempo | sin_fecha

Matriz de asignación (ver calcular_semaforo() y README.md para el detalle
y la justificación de cada celda):

  cumplimiento \\ prioridad     alta       media      baja
  completado                  verde      verde      verde
  bloqueado                   rojo       rojo       rojo
  vencido                     rojo       rojo       amarillo
  en_riesgo                   rojo       amarillo   amarillo
  a_tiempo                    amarillo   verde      verde
  sin_fecha                   amarillo   verde      verde

Reglas de fondo:
  - "completado" y "bloqueado" son absolutos: no dependen de la prioridad
    (un bloqueo activo siempre es crítico; un cierre siempre es positivo).
  - Un incumplimiento de plazo ("vencido") en algo de prioridad baja se
    suaviza a amarillo, pero nunca desaparece del radar.
  - Los temas de prioridad alta se mantienen en amarillo aun "a tiempo" o
    "sin_fecha", para conservar visibilidad ejecutiva sobre lo importante,
    no solo sobre lo que ya está mal.

`--estado` se mantiene como override manual opcional (por si un caso
puntual no encaja en la matriz), pero el uso recomendado es dejar que se
calcule solo a partir de prioridad + cumplimiento.

FASES (gráfico real de avance)
--------------------------------
Cada informe puede declarar sus fases con --fase "Nombre=NN" (repetible).
"NN" es 0-100. Convención de mapeo cuando la fase viene de un estado de
Jira (no de una medición real de esfuerzo): Done=100, En curso/indeterminado
=50, Por hacer=0. Es una aproximación declarada, no una medición exacta —
se documenta así para no presentar una estimación como si fuera un hecho.
El avance de la card (barra + KPI) es el promedio de las fases. Si un
informe no declara fases, se usa --avance o --subtareas-completadas/total
como antes.

Uso:
  python3 scripts/manage_informes.py nuevo \\
      --titulo "Avance proyecto X" \\
      --categoria "proyectos" \\
      --resumen "Resumen ejecutivo de una línea." \\
      --prioridad alta \\
      --cumplimiento en_riesgo \\
      --fase "Selección de proveedor=100" \\
      --fase "Migración de módulos=50" \\
      --fase "Pruebas=0" \\
      --jira-url "https://cafsagroup.atlassian.net/browse/DES-1741"

  python3 scripts/manage_informes.py build
"""

import argparse
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

from common import ROOT, slugify, parse_jira_url
from reportes_lib import agrupar_por_persona, cargar_pendientes, render_persona_card, texto_plazo

DATA_FILE = ROOT / "data" / "informes.json"
JIRA_SNAPSHOT_FILE = ROOT / "data" / "jira_snapshot.json"
TEMPLATES_DIR = ROOT / "templates"
INFORMES_DIR = ROOT / "informes"
INDEX_OUTPUT = ROOT / "index.html"

# ---------- Panel consolidado "Mi seguimiento" (data/jira_snapshot.json) ----------
# Mismo criterio de urgencia gravitacional que reportes_lib.urgencia_gravitacional
# (F = G * peso / dias_restantes^2), aplicado aquí a los issues de Jira que sí
# declaran fecha de vencimiento, para no tener dos fórmulas de urgencia distintas
# conviviendo en el mismo sistema.
G_ESTILIZADA_JIRA = 50
PESO_PRIORIDAD_JIRA = {"Highest": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
ETIQUETA_PRIORIDAD_JIRA = {
    "Highest": "Highest",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
    "Lowest": "Lowest",
}
# Reutiliza las clases de semáforo ya existentes (estado-rojo/amarillo/verde)
# en vez de inventar una paleta nueva de badges para Jira.
PRIORIDAD_JIRA_ESTILO = {
    "Highest": "rojo",
    "High": "rojo",
    "Medium": "amarillo",
    "Low": "verde",
    "Lowest": "verde",
}
ORDEN_PRIORIDAD_JIRA = ["Highest", "High", "Medium", "Low", "Lowest"]

ESTADOS_VALIDOS = {
    "verde": "A tiempo",
    "amarillo": "En riesgo",
    "rojo": "Atrasado",
    "neutral": "Sin definir",
}

PRIORIDADES_VALIDAS = {
    "alta": "Prioridad alta",
    "media": "Prioridad media",
    "baja": "Prioridad baja",
}

CUMPLIMIENTOS_VALIDOS = {
    "completado": "Completado",
    "bloqueado": "Bloqueado",
    "vencido": "Vencido",
    "en_riesgo": "En riesgo",
    "a_tiempo": "A tiempo",
    "sin_fecha": "Sin fecha definida",
}

# Matriz cumplimiento -> {prioridad: color}. Ver docstring del módulo.
MATRIZ_SEMAFORO = {
    "completado": {"alta": "verde", "media": "verde", "baja": "verde"},
    "bloqueado": {"alta": "rojo", "media": "rojo", "baja": "rojo"},
    "vencido": {"alta": "rojo", "media": "rojo", "baja": "amarillo"},
    "en_riesgo": {"alta": "rojo", "media": "amarillo", "baja": "amarillo"},
    "a_tiempo": {"alta": "amarillo", "media": "verde", "baja": "verde"},
    "sin_fecha": {"alta": "amarillo", "media": "verde", "baja": "verde"},
}


def calcular_semaforo(prioridad: str, cumplimiento: str) -> str:
    """Calcula el color del semáforo a partir de prioridad y cumplimiento.
    Ver la matriz documentada en el docstring del módulo y en README.md."""
    fila = MATRIZ_SEMAFORO.get(cumplimiento)
    if not fila:
        return "neutral"
    return fila.get(prioridad, "neutral")


def parse_fase(valor: str) -> dict:
    if "=" not in valor:
        sys.exit(f"[ERROR] --fase debe tener el formato 'Nombre=NN' (recibido: '{valor}')")
    nombre, pct = valor.rsplit("=", 1)
    nombre = nombre.strip()
    try:
        pct = int(pct.strip())
    except ValueError:
        sys.exit(f"[ERROR] el porcentaje de la fase '{nombre}' no es un entero válido.")
    if not (0 <= pct <= 100):
        sys.exit(f"[ERROR] el porcentaje de la fase '{nombre}' debe estar entre 0 y 100.")
    return {"nombre": nombre, "avance": pct}


def cargar_informes() -> list:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_informes(informes: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    informes_ordenados = sorted(
        informes, key=lambda x: (x.get("destacado", False), x["fecha"]), reverse=True
    )
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(informes_ordenados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def avance_de(informe: dict):
    """Devuelve (pct, detalle) o (None, None) si no hay dato de avance.
    Prioridad: fases > subtareas_completadas/total > avance explícito."""
    fases = informe.get("fases") or []
    if fases:
        pct = round(sum(f["avance"] for f in fases) / len(fases))
        return pct, f"{len(fases)} fase(s) · promedio"

    completadas = informe.get("subtareas_completadas")
    total = informe.get("subtareas_total")
    if completadas is not None and total:
        pct = round(100 * completadas / total)
        return pct, f"{completadas}/{total} etapas"

    avance = informe.get("avance")
    if avance is not None:
        return avance, f"{avance}% de avance"

    return None, None


def render_progreso(informe: dict) -> str:
    """Barra de avance de la card. Ver avance_de() para la prioridad de
    fuentes. Si no hay ningún dato de avance declarado, no se muestra barra
    (evita inventar un porcentaje que no es un hecho verificable ni una
    estimación declarada)."""
    pct, detalle = avance_de(informe)
    if pct is None:
        return ""
    pct = max(0, min(100, pct))
    return f"""      <div class="progreso" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" aria-label="Avance: {detalle}">
        <div class="progreso-barra"><div class="progreso-relleno" style="width:{pct}%"></div></div>
        <span class="progreso-label">{detalle} (<span class="pct-semaforo" data-pct="{pct}">{pct}%</span>)</span>
      </div>"""


def render_card(informe: dict) -> str:
    estado = informe.get("estado", "neutral")
    estado_label = ESTADOS_VALIDOS.get(estado, "Sin definir")
    prioridad = informe.get("prioridad")
    prioridad_label = PRIORIDADES_VALIDAS.get(prioridad, "")
    prioridad_html = (
        f'<span class="prioridad-badge prioridad-{prioridad}">{prioridad_label}</span>'
        if prioridad else ""
    )
    progreso_html = render_progreso(informe)

    # Texto normalizado (sin acentos, minúsculas) para el buscador en vivo.
    texto_busqueda = f"{informe['titulo']} {informe['resumen']} {informe['categoria']}"
    texto_busqueda = unicodedata.normalize("NFKD", texto_busqueda).encode("ascii", "ignore").decode("ascii").lower()

    # Fecha de vencimiento: solo si el informe la tiene declarada (no todos la
    # tienen). Reutiliza texto_plazo() de reportes_lib para no tener dos
    # fórmulas de "días restantes / vencido" distintas en el mismo sistema.
    vencimiento = informe.get("vencimiento")
    vencimiento_html = f" &middot; {texto_plazo(vencimiento)}" if vencimiento else ""

    return f"""    <div class="informe-card" data-categoria="{informe['categoria']}" data-busqueda="{texto_busqueda}" data-prioridad="{prioridad or ''}" data-fecha="{informe['fecha']}" data-estado="{estado}">
      <div class="card-top">
        <span class="categoria">{informe['categoria']}</span>
        <div class="badges-wrap">
          {prioridad_html}
          <span class="estado-badge estado-{estado}">{estado_label}</span>
        </div>
      </div>
      <h3><a href="{informe['ruta']}">{informe['titulo']}</a></h3>
      <p class="resumen">{informe['resumen']}</p>
{progreso_html}
      <div class="card-footer">
        <span>{informe['fecha']}{vencimiento_html}</span>
        <a href="{informe['ruta']}">Ver informe &rarr;</a>
      </div>
    </div>"""


def render_filtro(categoria: str) -> str:
    return f'      <button type="button" data-filtro="{categoria}" role="tab" aria-selected="false">{categoria}</button>'


def render_seccion_reportes() -> str:
    """Sección 'Reportes y seguimientos' embebida en el index principal —
    misma tarjeta de persona que reportes/index.html (ver reportes_lib.py),
    con base_path='reportes/' porque los links parten desde la raíz."""
    pendientes = cargar_pendientes()
    por_persona = agrupar_por_persona(pendientes)
    if not por_persona:
        return '    <p class="page-meta">Todavía no hay reportes/pendientes registrados.</p>'
    return "\n".join(
        render_persona_card(slug, items, base_path="reportes/")
        for slug, items in sorted(por_persona.items())
    )


def cargar_jira_snapshot():
    """Carga data/jira_snapshot.json (foto de mis pendientes reales en Jira,
    tomada vía MCP). Devuelve None si el archivo no existe todavía — el panel
    consolidado simplemente no se muestra en ese caso (no se inventa data)."""
    if not JIRA_SNAPSHOT_FILE.exists():
        return None
    with open(JIRA_SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def urgencia_jira(issue: dict, hoy: date):
    """F = (G * peso_prioridad) / dias_restantes^2. Devuelve (F, dias) o None
    si el issue no tiene fecha de vencimiento declarada en Jira."""
    venc = issue.get("vencimiento")
    if not venc:
        return None
    anio, mes, dia = (int(x) for x in venc.split("-"))
    dias = (date(anio, mes, dia) - hoy).days
    r = max(dias, 1)
    peso = PESO_PRIORIDAD_JIRA.get(issue.get("prioridad"), 2)
    F = round((G_ESTILIZADA_JIRA * peso) / (r ** 2), 2)
    return F, dias


def texto_plazo_jira(dias: int) -> str:
    if dias < 0:
        return f"Vencido hace {abs(dias)} día(s)"
    if dias == 0:
        return "Vence hoy"
    return f"Vence en {dias} día(s)"


def render_radar_item(F: float, dias: int, issue: dict) -> str:
    clase = PRIORIDAD_JIRA_ESTILO.get(issue.get("prioridad"), "neutral")
    return f"""      <a class="radar-item" href="{issue['url']}" target="_blank" rel="noopener">
        <span class="estado-badge estado-{clase}">{issue['prioridad']}</span>
        <span class="radar-texto">
          <strong>{issue['key']}</strong> — {issue['resumen']}
          <span class="formula-nota" title="Urgencia gravitacional: F = (50 × peso de prioridad) / días_restantes². A mayor prioridad y menor plazo, mayor F. Mismo criterio que en Reportes y seguimientos.">{texto_plazo_jira(dias)} · F={F}</span>
        </span>
      </a>"""


def render_panel_consolidado() -> str:
    """Panel 'Mi seguimiento' — consolidado de mis pendientes reales en Jira
    (data/jira_snapshot.json), con radar de urgencia (top 5 por fórmula
    gravitacional) y enlace directo al filtro en vivo de Jira. Si todavía no
    se ha generado el snapshot, la sección se omite del index."""
    snapshot = cargar_jira_snapshot()
    if not snapshot:
        return ""

    issues = snapshot.get("issues", [])
    total = len(issues)

    desglose = {}
    for issue in issues:
        p = issue.get("prioridad", "")
        desglose[p] = desglose.get(p, 0) + 1
    desglose_html = "\n".join(
        f'      <div class="kpi-box kpi-box-mini"><span class="kpi-valor">{desglose.get(p, 0)}</span>'
        f'<span class="kpi-label">{ETIQUETA_PRIORIDAD_JIRA[p]}</span></div>'
        for p in ORDEN_PRIORIDAD_JIRA if desglose.get(p)
    )

    hoy = date.today()
    urgentes = []
    for issue in issues:
        resultado = urgencia_jira(issue, hoy)
        if resultado is None:
            continue
        F, dias = resultado
        urgentes.append((F, dias, issue))
    urgentes.sort(key=lambda x: -x[0])
    top = urgentes[:5]

    radar_html = "\n".join(render_radar_item(F, dias, issue) for F, dias, issue in top) if top else \
        '      <p class="page-meta">Ninguno de los pendientes abiertos tiene fecha de vencimiento declarada en Jira.</p>'

    filtro_url = snapshot.get("filtro_jira_url", "#")
    generado = snapshot.get("generado", "")

    return f"""  <section class="panel-consolidado" aria-labelledby="titulo-consolidado">
    <div class="seccion-reportes-header">
      <h2 id="titulo-consolidado" class="page-title" style="margin-bottom:2px">Mi seguimiento (Jira)</h2>
      <a href="{filtro_url}" class="ver-todos" target="_blank" rel="noopener">Ver los {total} pendientes en Jira &rarr;</a>
    </div>
    <p class="page-meta">
      Consolidado de mis tareas abiertas asignadas en Jira, actualizado al {generado}
      · {total} pendiente(s) abierto(s)
    </p>
    <div class="kpi-grid kpi-grid-mini">
{desglose_html}
    </div>
    <h3 class="radar-titulo">Radar de urgencia <span class="formula-nota" title="Los 5 pendientes con mayor F = (50 × peso de prioridad) / días_restantes², solo entre los que tienen fecha de vencimiento en Jira.">top 5 por urgencia calculada</span></h3>
    <div class="radar-urgencia">
{radar_html}
    </div>
  </section>

  <hr class="separador-seccion">
"""


def build_index() -> None:
    informes = cargar_informes()
    template = (TEMPLATES_DIR / "index_template.html").read_text(encoding="utf-8")

    categorias = sorted({i["categoria"] for i in informes})
    filtros_html = "\n".join(render_filtro(c) for c in categorias)
    grid_html = "\n".join(render_card(i) for i in informes) if informes else \
        '    <p class="page-meta">Todavía no hay informes publicados.</p>'

    pendientes = cargar_pendientes()
    total_personas = len(agrupar_por_persona(pendientes))
    reportes_html = render_seccion_reportes()
    panel_consolidado_html = render_panel_consolidado()

    salida = template
    salida = salida.replace("<!--__FILTROS_CATEGORIA__-->", filtros_html)
    salida = salida.replace("<!--__INFORMES_GRID__-->", grid_html)
    salida = salida.replace("<!--__REPORTES_PERSONAS_GRID__-->", reportes_html)
    salida = salida.replace("<!--__PANEL_CONSOLIDADO__-->", panel_consolidado_html)
    salida = salida.replace("{{TOTAL_PERSONAS_REPORTES}}", str(total_personas))
    salida = salida.replace("{{FECHA_GENERACION}}", date.today().isoformat())
    salida = salida.replace("{{TOTAL_INFORMES}}", str(len(informes)))

    INDEX_OUTPUT.write_text(salida, encoding="utf-8")
    print(f"[OK] index.html regenerado con {len(informes)} informe(s) y {total_personas} persona(s) en seguimiento.")


def color_de_fase(pct: int) -> str:
    if pct >= 100:
        return "#2e7d32"
    if pct > 0:
        return "#b8860b"
    return "#9a9a9a"


def render_informe_html(informe: dict) -> str:
    """Renderiza (o re-renderiza) el HTML individual de un informe a partir
    de sus datos en informes.json — usado tanto por crear_informe() como por
    una futura regeneración masiva."""
    plantilla = (TEMPLATES_DIR / "informe_template.html").read_text(encoding="utf-8")
    contenido = plantilla

    fases = informe.get("fases") or []
    if fases:
        labels = [f["nombre"] for f in fases]
        valores = [f["avance"] for f in fases]
        colores = [color_de_fase(v) for v in valores]
    else:
        pct, _ = avance_de(informe)
        labels = ["Avance general"]
        valores = [pct if pct is not None else 0]
        colores = [color_de_fase(valores[0])]

    # Alto del gráfico proporcional a la cantidad de fases (no un tamaño fijo
    # para todos): pocas fases, gráfico chico; muchas fases, más espacio.
    altura_chart = max(140, min(560, 46 * len(labels) + 60))

    fases_lista_html = "\n".join(
        f'      <li><span class="fase-nombre">{f["nombre"]}</span>'
        f'<span class="fase-pct pct-semaforo" data-pct="{f["avance"]}">{f["avance"]}%</span></li>'
        for f in fases
    ) if fases else ""

    detalle_urls = informe.get("jira_urls") or []
    if detalle_urls:
        detalle_html = "\n".join(
            f'      <li><a href="{d["url"]}" target="_blank" rel="noopener">{d["label"]}</a></li>'
            for d in detalle_urls
        )
    else:
        detalle_html = (
            '      <li><a href="#" target="_blank" rel="noopener">Enlace a detalle ampliado (editar)</a></li>'
        )

    contenido = contenido.replace("{{TITULO}}", informe["titulo"])
    contenido = contenido.replace("{{FECHA}}", informe["fecha"])
    contenido = contenido.replace("{{CATEGORIA}}", informe["categoria"])
    contenido = contenido.replace("{{RESUMEN}}", informe["resumen"])
    contenido = contenido.replace("{{ESTADO_CLASE}}", f"estado-{informe['estado']}")
    contenido = contenido.replace("{{ESTADO_LABEL}}", ESTADOS_VALIDOS[informe["estado"]])
    contenido = contenido.replace("{{PRIORIDAD_LABEL}}", PRIORIDADES_VALIDAS[informe["prioridad"]])
    contenido = contenido.replace("{{PRIORIDAD_CLASE}}", f"prioridad-{informe['prioridad']}")
    contenido = contenido.replace("{{CUMPLIMIENTO_LABEL}}", CUMPLIMIENTOS_VALIDOS[informe["cumplimiento"]])
    contenido = contenido.replace("{{FASES_ALTURA}}", str(altura_chart))
    contenido = contenido.replace("{{FASES_LISTA_HTML}}", fases_lista_html)
    contenido = contenido.replace("{{FASES_LABELS_JSON}}", json.dumps(labels, ensure_ascii=False))
    contenido = contenido.replace("{{FASES_DATA_JSON}}", json.dumps(valores))
    contenido = contenido.replace("{{FASES_COLORS_JSON}}", json.dumps(colores))
    contenido = contenido.replace("{{DETALLE_LINKS_HTML}}", detalle_html)
    return contenido


def crear_informe(args) -> None:
    if args.prioridad not in PRIORIDADES_VALIDAS:
        sys.exit(f"[ERROR] prioridad inválida '{args.prioridad}'. Usa uno de: {list(PRIORIDADES_VALIDAS)}")
    if args.cumplimiento not in CUMPLIMIENTOS_VALIDOS:
        sys.exit(f"[ERROR] cumplimiento inválido '{args.cumplimiento}'. Usa uno de: {list(CUMPLIMIENTOS_VALIDOS)}")

    estado = args.estado or calcular_semaforo(args.prioridad, args.cumplimiento)
    if estado not in ESTADOS_VALIDOS:
        sys.exit(f"[ERROR] estado inválido '{estado}'. Usa uno de: {list(ESTADOS_VALIDOS)}")

    if args.subtareas_total is not None and args.subtareas_completadas is None:
        sys.exit("[ERROR] si usas --subtareas-total también debes indicar --subtareas-completadas.")
    if args.avance is not None and not (0 <= args.avance <= 100):
        sys.exit("[ERROR] --avance debe estar entre 0 y 100.")
    if args.vencimiento:
        try:
            date.fromisoformat(args.vencimiento)
        except ValueError:
            sys.exit(f"[ERROR] --vencimiento debe tener formato YYYY-MM-DD (recibido: '{args.vencimiento}').")

    fases = [parse_fase(f) for f in (args.fase or [])]
    jira_urls = [parse_jira_url(u) for u in (args.jira_url or [])]

    fecha = args.fecha or date.today().isoformat()
    categoria_slug = slugify(args.categoria)
    titulo_slug = slugify(args.titulo)
    informe_id = f"{fecha}-{titulo_slug}"

    informes = cargar_informes()
    if any(i["id"] == informe_id for i in informes):
        sys.exit(f"[ERROR] Ya existe un informe con id '{informe_id}'. Usa otro título o fecha.")

    ruta_relativa = f"informes/{categoria_slug}/{titulo_slug}.html"
    destino = ROOT / ruta_relativa
    destino.parent.mkdir(parents=True, exist_ok=True)

    informe = {
        "id": informe_id,
        "titulo": args.titulo,
        "fecha": fecha,
        "vencimiento": args.vencimiento,
        "categoria": categoria_slug,
        "prioridad": args.prioridad,
        "cumplimiento": args.cumplimiento,
        "estado": estado,
        "avance": args.avance,
        "subtareas_completadas": args.subtareas_completadas,
        "subtareas_total": args.subtareas_total,
        "fases": fases,
        "jira_urls": jira_urls,
        "resumen": args.resumen,
        "ruta": ruta_relativa,
        "destacado": args.destacado,
    }

    destino.write_text(render_informe_html(informe), encoding="utf-8")

    informes.append(informe)
    guardar_informes(informes)
    build_index()

    print(f"[OK] Informe creado en: {destino.relative_to(ROOT)}")
    print(f"[OK] Registrado en data/informes.json con id '{informe_id}' — semáforo calculado: {estado}.")
    print("[OK] index.html actualizado automáticamente.")


def regenerar_paginas(args) -> None:
    """Re-renderiza las páginas individuales desde informes.json (útil tras
    editar fases/jira_urls a mano en el JSON) y luego el índice.

    Salta los informes marcados "personalizado": true — su HTML tiene
    contenido a mano (KPIs, gráficos extra, texto) que la plantilla
    genérica no reproduce; regenerarlos los destruiría. Para esos, edita
    el archivo HTML directamente."""
    informes = cargar_informes()
    saltados = []
    for informe in informes:
        if informe.get("personalizado"):
            saltados.append(informe["ruta"])
            continue
        destino = ROOT / informe["ruta"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(render_informe_html(informe), encoding="utf-8")
        print(f"[OK] Regenerado: {informe['ruta']}")
    for ruta in saltados:
        print(f"[SKIP] {ruta} (personalizado=true, no se toca)")
    build_index()


def main():
    parser = argparse.ArgumentParser(description="Administrador de informes CAFSA")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_nuevo = sub.add_parser("nuevo", help="Crear un nuevo informe y registrarlo en el índice")
    p_nuevo.add_argument("--titulo", required=True)
    p_nuevo.add_argument("--categoria", required=True)
    p_nuevo.add_argument("--resumen", required=True)
    p_nuevo.add_argument("--prioridad", required=True, choices=list(PRIORIDADES_VALIDAS))
    p_nuevo.add_argument("--cumplimiento", required=True, choices=list(CUMPLIMIENTOS_VALIDOS))
    p_nuevo.add_argument("--avance", type=int, default=None, help="Porcentaje 0-100 (opcional)")
    p_nuevo.add_argument("--subtareas-completadas", type=int, default=None, dest="subtareas_completadas")
    p_nuevo.add_argument("--subtareas-total", type=int, default=None, dest="subtareas_total")
    p_nuevo.add_argument("--fase", action="append", help="'Nombre=NN', repetible")
    p_nuevo.add_argument("--jira-url", action="append", dest="jira_url", help="URL de Jira, repetible")
    p_nuevo.add_argument("--estado", default=None, choices=list(ESTADOS_VALIDOS),
                          help="Override manual del semáforo (no recomendado; se calcula solo).")
    p_nuevo.add_argument("--fecha", default=None, help="YYYY-MM-DD (default: hoy)")
    p_nuevo.add_argument("--vencimiento", default=None, help="YYYY-MM-DD (opcional, solo si hay una fecha límite declarada)")
    p_nuevo.add_argument("--destacado", action="store_true")
    p_nuevo.set_defaults(func=crear_informe)

    p_build = sub.add_parser("build", help="Regenerar index.html desde data/informes.json")
    p_build.set_defaults(func=lambda args: build_index())

    p_regen = sub.add_parser("regenerar-paginas", help="Re-renderizar todas las páginas individuales + índice")
    p_regen.set_defaults(func=regenerar_paginas)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
