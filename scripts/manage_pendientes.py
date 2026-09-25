#!/usr/bin/env python3
"""
manage_pendientes.py
=====================
Administra el módulo "Reportes y seguimientos": páginas evergreen por
persona, con pendientes/solicitudes puntuales dirigidas a esa persona
(enlace a Jira, botón de confirmación de seguimiento, y una recomendación
opcional cuando aplica involucrar a otro equipo/departamento).

Distinto de manage_informes.py (informes ejecutivos por programa/proyecto
para Gerencia): aquí cada ítem es una solicitud puntual dirigida a UNA
persona, y la URL que se comparte es por persona (no por fecha), para
poder reenviar siempre el mismo link a medida que se acumulan pendientes.

La lógica de datos/renderizado de tarjetas vive en reportes_lib.py,
compartida con manage_informes.py (que embebe la misma tarjeta de persona
dentro del index.html principal — ver ese script).

Subcomandos:
  nuevo   Registra un pendiente nuevo en data/pendientes.json, regenera la
          página de esa persona, el directorio reportes/index.html Y el
          index.html principal (para que la sección "Reportes y
          seguimientos" del index quede al día de inmediato).
  editar  Modifica un pendiente existente (por --id): reasignar estado,
          actualizar la solicitud/recomendación, agregar enlaces de Jira,
          etc. Regenera las mismas páginas que 'nuevo'.
  build   Igual regeneración completa, a partir de data/pendientes.json
          (útil tras editar el JSON a mano, p. ej. para marcar un
          pendiente como 'resuelto').

Los memos fuente (.docx) que originan estos pendientes viven en
reportes/DD-MM-YYYY/ como bandeja de entrada de trabajo — NUNCA se
publican ni se comitean (ver .gitignore); solo la versión destilada que
se registra acá.

Uso:
  python3 scripts/manage_pendientes.py nuevo \\
      --persona-nombre "Cristopher Pérez Ugalde" \\
      --persona-cargo "Jefe de TI" \\
      --tema "DES-1741 — Migración Core Financiero ABANKS (Forms 14c)" \\
      --solicitud "Indicar con quién coordinar instalación de servidores..." \\
      --criticidad alta \\
      --plazo 2026-09-30 \\
      --recomendacion "Se sugiere involucrar a Infraestructura." \\
      --jira-url "https://cafsagroup.atlassian.net/browse/DES-1741"

  python3 scripts/manage_pendientes.py build
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from common import ROOT, esc, icono_seccion, slugify, parse_jira_url, ICONO_GRAFICO, ICONO_OBJETIVO
from reportes_lib import (
    CRITICIDADES_VALIDAS,
    ESTADOS_ITEM_VALIDOS,
    ORDEN_ESTADO,
    cargar_iniciativas,
    cargar_pendientes,
    entropia_sistema,
    guardar_iniciativas,
    guardar_pendientes,
    informes_por_propietario,
    iniciativas_por_persona,
    orden_persona,
    personas_a_mostrar,
    render_iniciativa_card,
    render_pendiente_item,
    render_persona_card,
    render_proyecto_persona_card,
    urgencia_gravitacional,
)

TEMPLATES_DIR = ROOT / "templates"
REPORTES_DIR = ROOT / "reportes"
REPORTES_INDEX_OUTPUT = REPORTES_DIR / "index.html"


def render_proyectos_seccion(persona_slug: str, informes: list) -> str:
    """Sección 'Proyectos en seguimiento' de la página de una persona:
    informes cuyo propietario_slug coincide con ella (ver
    reportes_lib.informes_por_propietario/render_proyecto_persona_card).
    Distinto de los pendientes: no es una solicitud puntual, es el estado
    real y verificable de un proyecto completo del que es responsable, con
    % de avance, para que lo revise directo sin ir hasta 'Tus informes'.
    Devuelve "" (sección omitida del todo) si la persona no tiene ningún
    informe marcado con su propietario_slug."""
    propios = informes_por_propietario(informes, persona_slug)
    if not propios:
        return ""
    tarjetas = "\n".join(render_proyecto_persona_card(i) for i in propios)
    return f"""  <div class="titulo-seccion">
    {icono_seccion(ICONO_GRAFICO, 20)}
    <h2 class="page-title">Proyectos en seguimiento</h2>
  </div>
  <p class="page-meta">Estado real tomado de Jira · actualizado al {date.today().isoformat()} · {len(propios)} proyecto(s)</p>

  <div class="informes-grid">
{tarjetas}
  </div>
"""


def render_iniciativas_seccion(persona_slug: str, iniciativas: list) -> str:
    """Sección 'Iniciativas' de la página de una persona: documentos de
    análisis/propuesta puntuales que se le han enviado para revisión (ver
    reportes_lib.iniciativas_por_persona/render_iniciativa_card). Distinto
    de un pendiente (solicitud con seguimiento/estado) y de un proyecto
    (avance %) — acá cada card es simplemente un documento para que la
    persona lo abra y lo revise. Devuelve "" (sección omitida del todo) si
    la persona no tiene ninguna iniciativa registrada."""
    propias = iniciativas_por_persona(iniciativas, persona_slug)
    if not propias:
        return ""
    tarjetas = "\n".join(render_iniciativa_card(i, base_path="../../") for i in propias)
    return f"""  <div class="titulo-seccion">
    {icono_seccion(ICONO_OBJETIVO, 20)}
    <h2 class="page-title">Iniciativas</h2>
  </div>
  <p class="page-meta">Documentos de análisis para tu revisión · actualizado al {date.today().isoformat()} · {len(propias)} iniciativa(s)</p>

  <div class="informes-grid">
{tarjetas}
  </div>
"""


def render_persona_page(persona_slug: str, persona: dict, informes: list, iniciativas: list) -> str:
    """persona: dict {'nombre','cargo','items'} armado por
    reportes_lib.personas_a_mostrar() — 'items' puede ser [] cuando la
    persona no tiene ningún pendiente puntual pero sí proyectos en
    seguimiento (petición explícita, 2026-09-24)."""
    plantilla = (TEMPLATES_DIR / "pendiente_persona_template.html").read_text(encoding="utf-8")
    items = persona["items"]
    # Orden: primero por estado de flujo (pendiente > en_atención > resuelto),
    # y dentro de cada estado, por urgencia gravitacional descendente
    # (F=G·m/r² — ver reportes_lib.urgencia_gravitacional). Los ítems sin
    # plazo (F=None) se tratan como urgencia 0 y quedan al final de su grupo.
    items_ordenados = sorted(
        items,
        key=lambda x: (
            ORDEN_ESTADO.get(x["estado_item"], 9),
            -(urgencia_gravitacional(x) or 0),
            x["fecha"],
        ),
    )
    items_html = (
        "\n".join(render_pendiente_item(i) for i in items_ordenados)
        if items_ordenados else
        '    <p class="page-meta">Sin pendientes puntuales registrados actualmente.</p>'
    )
    proyectos_html = render_proyectos_seccion(persona_slug, informes)
    iniciativas_html = render_iniciativas_seccion(persona_slug, iniciativas)

    salida = plantilla
    salida = salida.replace("{{PERSONA_NOMBRE}}", esc(persona["nombre"]))
    salida = salida.replace("{{PERSONA_CARGO}}", esc(persona["cargo"]))
    salida = salida.replace("{{FECHA_GENERACION}}", date.today().isoformat())
    salida = salida.replace("{{TOTAL_PENDIENTES}}", str(len(items)))
    salida = salida.replace("<!--__PENDIENTES_LISTA__-->", items_html)
    salida = salida.replace("<!--__INICIATIVAS_SECCION__-->", iniciativas_html)
    salida = salida.replace("<!--__PROYECTOS_SECCION__-->", proyectos_html)
    return salida


def build_reportes_index(personas: dict, pendientes: list) -> None:
    plantilla_index = (TEMPLATES_DIR / "reportes_index_template.html").read_text(encoding="utf-8")
    # Orden por jerarquía organizacional (Gerencia > Jefatura > PMO/
    # Coordinación > Contacto operativo), no alfabético — ver orden_persona().
    orden = sorted(personas.items(), key=lambda kv: orden_persona(kv[1]))
    tarjetas = "\n".join(
        render_persona_card(slug, persona) for slug, persona in orden
    ) if personas else '    <p class="page-meta">Todavía no hay pendientes registrados.</p>'

    entropia = entropia_sistema(pendientes)
    entropia_html = (
        f'<span class="formula-nota" title="Metáfora de la 2ª ley de la termodinámica: '
        f'porcentaje de pendientes que siguen abiertos sobre el total histórico. '
        f'No es una entropía física real — es una lectura libre de la idea, para tener '
        f'una sola cifra de salud general del sistema. Color invertido: más alto es peor '
        f'(más pendientes sin cerrar), así que se acerca al rojo en vez de al verde.'
        f'">Entropía del sistema: '
        f'<span class="pct-semaforo" data-pct="{entropia}" data-invertido="true">{entropia}%</span></span>'
        if entropia is not None else ""
    )

    salida = plantilla_index
    salida = salida.replace("<!--__PERSONAS_GRID__-->", tarjetas)
    salida = salida.replace("{{FECHA_GENERACION}}", date.today().isoformat())
    salida = salida.replace("{{TOTAL_PERSONAS}}", str(len(personas)))
    salida = salida.replace("<!--__ENTROPIA__-->", entropia_html)
    REPORTES_INDEX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORTES_INDEX_OUTPUT.write_text(salida, encoding="utf-8")
    print(f"[OK] reportes/index.html regenerado con {len(personas)} persona(s).")


def build() -> None:
    pendientes = cargar_pendientes()
    iniciativas = cargar_iniciativas()
    # Import diferido (no a nivel de módulo): evita un import circular, ya
    # que manage_informes.py importa de reportes_lib.py.
    import manage_informes
    informes = manage_informes.cargar_informes()
    # Unión de "tiene al menos un pendiente" con "es propietaria de al
    # menos un proyecto" (informes.json/propietario_slug) — petición
    # explícita 2026-09-24: una persona no debe perder su página de
    # seguimiento solo porque ya no le queda ningún pendiente puntual, si
    # todavía tiene proyectos reales que revisar. Ver personas_a_mostrar().
    personas = personas_a_mostrar(pendientes, informes)

    for persona_slug, persona in personas.items():
        destino = REPORTES_DIR / persona_slug / "index.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(render_persona_page(persona_slug, persona, informes, iniciativas), encoding="utf-8")
        print(f"[OK] Regenerado: {destino.relative_to(ROOT)}")

    build_reportes_index(personas, pendientes)

    # Mantiene sincronizada la sección "Reportes y seguimientos" del index
    # principal, que vive en manage_informes.py (mismo directorio scripts/).
    manage_informes.build_index()


def eliminar_pendiente(args) -> None:
    pendientes = cargar_pendientes()
    idx = next((i for i, p in enumerate(pendientes) if p["id"] == args.id), None)
    if idx is None:
        sys.exit(f"[ERROR] No existe ningún pendiente con id '{args.id}'.")

    eliminado = pendientes.pop(idx)
    guardar_pendientes(pendientes)

    persona_slug = eliminado["persona_slug"]
    restantes = [p for p in pendientes if p["persona_slug"] == persona_slug]

    build()

    print(f"[OK] Pendiente '{args.id}' eliminado (tema: {eliminado['tema']}).")
    print("[OK] index.html principal y reportes/index.html actualizados.")

    if not restantes:
        import manage_informes
        tiene_proyectos = any(
            i.get("propietario_slug") == persona_slug for i in manage_informes.cargar_informes()
        )
        pagina = REPORTES_DIR / persona_slug / "index.html"
        if tiene_proyectos:
            print(f"[OK] '{eliminado['persona_nombre']}' ya no tiene pendientes puntuales, pero su página")
            print(f"     sigue enlazada por sus proyectos en seguimiento: {pagina.relative_to(ROOT)}")
        else:
            print(f"[AVISO] '{eliminado['persona_nombre']}' ya no tiene pendientes registrados.")
            print(f"        {pagina.relative_to(ROOT)} ya no está enlazada desde ningún índice,")
            print("        pero el archivo sigue existiendo en disco (no se borra solo). Bórralo a mano si ya no aplica.")


def crear_iniciativa(args) -> None:
    persona_slug = args.persona_slug
    ruta_archivo = Path(args.archivo)
    if not ruta_archivo.is_absolute():
        ruta_archivo = ROOT / ruta_archivo
    if not ruta_archivo.exists():
        sys.exit(f"[ERROR] No existe el archivo '{ruta_archivo}'. Colócalo primero en "
                  f"reportes/{persona_slug}/iniciativas/ y vuelve a correr este comando.")

    fecha = args.fecha or date.today().isoformat()
    tema_slug = slugify(args.titulo)[:50]
    iniciativa_id = f"{persona_slug}-{fecha}-{tema_slug}"

    iniciativas = cargar_iniciativas()
    if any(i["id"] == iniciativa_id for i in iniciativas):
        sys.exit(f"[ERROR] Ya existe una iniciativa con id '{iniciativa_id}'. Usa otro título o fecha.")

    iniciativa = {
        "id": iniciativa_id,
        "persona_slug": persona_slug,
        "titulo": args.titulo,
        "fecha": fecha,
        "categoria": args.categoria,
        "resumen": args.resumen,
        "ruta": str(ruta_archivo.relative_to(ROOT)).replace("\\", "/"),
    }

    iniciativas.append(iniciativa)
    guardar_iniciativas(iniciativas)
    build()

    print(f"[OK] Iniciativa registrada con id '{iniciativa_id}'.")
    print(f"[OK] Página actualizada: reportes/{persona_slug}/index.html")
    print("[OK] index.html principal actualizado (sección Reportes y seguimientos).")


def actualizar_persona(args) -> None:
    """Actualiza persona_nombre/persona_cargo en TODOS los pendientes de esa
    persona a la vez (por persona_slug) — evita que un dato quede
    desalineado entre ítems si la persona tiene más de un pendiente."""
    pendientes = cargar_pendientes()
    afectados = [p for p in pendientes if p["persona_slug"] == args.persona_slug]
    if not afectados:
        sys.exit(f"[ERROR] No hay ningún pendiente con persona-slug '{args.persona_slug}'.")

    cambios = []
    if args.persona_cargo is not None:
        for p in afectados:
            p["persona_cargo"] = args.persona_cargo
        cambios.append(f"persona_cargo -> '{args.persona_cargo}'")
    if args.persona_nombre is not None:
        for p in afectados:
            p["persona_nombre"] = args.persona_nombre
        cambios.append(f"persona_nombre -> '{args.persona_nombre}'")

    if not cambios:
        sys.exit("[ERROR] Indica --persona-cargo y/o --persona-nombre.")

    guardar_pendientes(pendientes)
    build()

    print(f"[OK] {len(afectados)} pendiente(s) de '{args.persona_slug}' actualizados: {', '.join(cambios)}.")
    print(f"[OK] Página regenerada: reportes/{args.persona_slug}/index.html")
    print("[OK] index.html principal actualizado (sección Reportes y seguimientos).")


def crear_pendiente(args) -> None:
    if args.criticidad not in CRITICIDADES_VALIDAS:
        sys.exit(f"[ERROR] criticidad inválida '{args.criticidad}'. Usa uno de: {list(CRITICIDADES_VALIDAS)}")
    if args.estado_item not in ESTADOS_ITEM_VALIDOS:
        sys.exit(f"[ERROR] estado-item inválido '{args.estado_item}'. Usa uno de: {list(ESTADOS_ITEM_VALIDOS)}")
    if args.plazo:
        try:
            date.fromisoformat(args.plazo)
        except ValueError:
            sys.exit(f"[ERROR] --plazo debe tener formato YYYY-MM-DD (recibido: '{args.plazo}').")

    fecha = args.fecha or date.today().isoformat()
    persona_slug = slugify(args.persona_nombre)
    tema_slug = slugify(args.tema)[:50]
    pendiente_id = f"{persona_slug}-{fecha}-{tema_slug}"

    pendientes = cargar_pendientes()
    if any(p["id"] == pendiente_id for p in pendientes):
        sys.exit(f"[ERROR] Ya existe un pendiente con id '{pendiente_id}'. Usa otro tema o fecha.")

    jira_urls = [parse_jira_url(u) for u in (args.jira_url or [])]

    pendiente = {
        "id": pendiente_id,
        "persona_slug": persona_slug,
        "persona_nombre": args.persona_nombre,
        "persona_cargo": args.persona_cargo,
        "fecha": fecha,
        "tema": args.tema,
        "solicitud": args.solicitud,
        "plazo": args.plazo,
        "criticidad": args.criticidad,
        "recomendacion": args.recomendacion,
        "jira_urls": jira_urls,
        "estado_item": args.estado_item,
    }

    pendientes.append(pendiente)
    guardar_pendientes(pendientes)
    build()

    print(f"[OK] Pendiente registrado con id '{pendiente_id}'.")
    print(f"[OK] Página actualizada: reportes/{persona_slug}/index.html")
    print("[OK] index.html principal actualizado (sección Reportes y seguimientos).")


def editar_pendiente(args) -> None:
    pendientes = cargar_pendientes()
    idx = next((i for i, p in enumerate(pendientes) if p["id"] == args.id), None)
    if idx is None:
        sys.exit(f"[ERROR] No existe ningún pendiente con id '{args.id}'.")

    pendiente = pendientes[idx]
    cambios = []

    if args.estado_item is not None:
        if args.estado_item not in ESTADOS_ITEM_VALIDOS:
            sys.exit(f"[ERROR] estado-item inválido '{args.estado_item}'. Usa uno de: {list(ESTADOS_ITEM_VALIDOS)}")
        pendiente["estado_item"] = args.estado_item
        cambios.append(f"estado_item -> {args.estado_item}")

    if args.criticidad is not None:
        if args.criticidad not in CRITICIDADES_VALIDAS:
            sys.exit(f"[ERROR] criticidad inválida '{args.criticidad}'. Usa uno de: {list(CRITICIDADES_VALIDAS)}")
        pendiente["criticidad"] = args.criticidad
        cambios.append(f"criticidad -> {args.criticidad}")

    if args.solicitud is not None:
        pendiente["solicitud"] = args.solicitud
        cambios.append("solicitud actualizada")

    if args.recomendacion is not None:
        pendiente["recomendacion"] = args.recomendacion
        cambios.append("recomendacion actualizada")

    if args.plazo is not None:
        try:
            date.fromisoformat(args.plazo)
        except ValueError:
            sys.exit(f"[ERROR] --plazo debe tener formato YYYY-MM-DD (recibido: '{args.plazo}').")
        pendiente["plazo"] = args.plazo
        cambios.append(f"plazo -> {args.plazo}")

    if args.agregar_jira_url:
        existentes = pendiente.get("jira_urls", [])
        nuevas = [parse_jira_url(u) for u in args.agregar_jira_url]
        urls_existentes = {j["url"] for j in existentes}
        agregadas = [j for j in nuevas if j["url"] not in urls_existentes]
        pendiente["jira_urls"] = existentes + agregadas
        if agregadas:
            cambios.append(f"+{len(agregadas)} enlace(s) de Jira")

    if not cambios:
        sys.exit("[ERROR] No se indicó ningún cambio. Usa al menos una de las opciones de edición (ver --help).")

    pendientes[idx] = pendiente
    guardar_pendientes(pendientes)
    build()

    print(f"[OK] Pendiente '{args.id}' actualizado: {', '.join(cambios)}.")
    print(f"[OK] Página regenerada: reportes/{pendiente['persona_slug']}/index.html")
    print("[OK] index.html principal actualizado (sección Reportes y seguimientos).")


def main():
    parser = argparse.ArgumentParser(description="Administrador de reportes/pendientes CAFSA")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_nuevo = sub.add_parser("nuevo", help="Registrar un pendiente y regenerar las páginas afectadas")
    p_nuevo.add_argument("--persona-nombre", required=True, dest="persona_nombre")
    p_nuevo.add_argument("--persona-cargo", required=True, dest="persona_cargo")
    p_nuevo.add_argument("--tema", required=True)
    p_nuevo.add_argument("--solicitud", required=True)
    p_nuevo.add_argument("--criticidad", required=True, choices=list(CRITICIDADES_VALIDAS))
    p_nuevo.add_argument("--plazo", default=None, help="YYYY-MM-DD (opcional)")
    p_nuevo.add_argument("--recomendacion", default=None, help="Texto libre (opcional)")
    p_nuevo.add_argument("--jira-url", action="append", dest="jira_url", help="URL de Jira, repetible")
    p_nuevo.add_argument("--estado-item", default="pendiente", dest="estado_item", choices=list(ESTADOS_ITEM_VALIDOS))
    p_nuevo.add_argument("--fecha", default=None, help="YYYY-MM-DD (default: hoy)")
    p_nuevo.set_defaults(func=crear_pendiente)

    p_editar = sub.add_parser("editar", help="Modificar un pendiente existente por --id")
    p_editar.add_argument("--id", required=True, help="id exacto del pendiente (ver data/pendientes.json)")
    p_editar.add_argument("--estado-item", default=None, dest="estado_item", choices=list(ESTADOS_ITEM_VALIDOS))
    p_editar.add_argument("--criticidad", default=None, choices=list(CRITICIDADES_VALIDAS))
    p_editar.add_argument("--solicitud", default=None)
    p_editar.add_argument("--recomendacion", default=None)
    p_editar.add_argument("--plazo", default=None, help="YYYY-MM-DD")
    p_editar.add_argument("--agregar-jira-url", action="append", dest="agregar_jira_url", help="URL de Jira a agregar, repetible")
    p_editar.set_defaults(func=editar_pendiente)

    p_eliminar = sub.add_parser("eliminar", help="Eliminar un pendiente por --id")
    p_eliminar.add_argument("--id", required=True, help="id exacto del pendiente (ver data/pendientes.json)")
    p_eliminar.set_defaults(func=eliminar_pendiente)

    p_persona = sub.add_parser("actualizar-persona", help="Actualizar nombre/cargo en todos los pendientes de una persona")
    p_persona.add_argument("--persona-slug", required=True, dest="persona_slug", help="Slug tal como aparece en reportes/<slug>/")
    p_persona.add_argument("--persona-cargo", default=None, dest="persona_cargo")
    p_persona.add_argument("--persona-nombre", default=None, dest="persona_nombre")
    p_persona.set_defaults(func=actualizar_persona)

    p_iniciativa = sub.add_parser("nueva-iniciativa", help="Registrar una iniciativa (documento HTML ya creado) y regenerar las páginas afectadas")
    p_iniciativa.add_argument("--persona-slug", required=True, dest="persona_slug", help="Slug tal como aparece en reportes/<slug>/ (ver data/personas.json)")
    p_iniciativa.add_argument("--titulo", required=True)
    p_iniciativa.add_argument("--categoria", required=True, help="Etiqueta corta, ej. 'Análisis de proveedor'")
    p_iniciativa.add_argument("--resumen", required=True, help="1-2 líneas para la card, no el documento completo")
    p_iniciativa.add_argument("--archivo", required=True, help="Ruta al .html ya colocado en reportes/<slug>/iniciativas/")
    p_iniciativa.add_argument("--fecha", default=None, help="YYYY-MM-DD (default: hoy)")
    p_iniciativa.set_defaults(func=crear_iniciativa)

    p_build = sub.add_parser("build", help="Regenerar todas las páginas desde data/pendientes.json")
    p_build.set_defaults(func=lambda args: build())

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
