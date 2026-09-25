"""
reportes_lib.py
================
Lógica de datos y renderizado del módulo "Reportes y seguimientos",
compartida entre:

  - manage_pendientes.py: dueño de los datos (registra pendientes, genera
    reportes/index.html y la página de cada persona).
  - manage_informes.py: consumidor de solo lectura (embebe la sección
    "Reportes y seguimientos" dentro del index.html principal, con la
    MISMA tarjeta de persona que se usa en reportes/index.html, para que
    no haya dos diseños de card divergiendo con el tiempo).

Mantener acá cualquier cambio de formato de tarjeta/badge para que ambos
lugares se actualicen juntos.

FÓRMULAS
--------
Por pedido explícito del usuario, este módulo usa un par de fórmulas
matemáticas conocidas como herramientas reales de cálculo (no solo
decoración) — cada una documentada en su función, con la fórmula visible
en pantalla (tooltip) para quien revise el sistema:

  - Ley de Gravitación Universal (F = G·m/r²) -> urgencia_gravitacional()
  - Teorema de Pitágoras (c = √(a²+b²))       -> magnitud_atencion()
  - Entropía (2ª ley de la termodinámica, como metáfora de desorden
    acumulado) -> entropia_sistema()

Ver también: PI y la Identidad de Euler aparecen como guiños decorativos
en assets/css/style.css y en los <head> de las plantillas HTML — esos no
alimentan ningún cálculo, son un saludo para quien lea el código fuente.
"""

import json
import math
import re
import sys
import unicodedata
from datetime import date

from common import (  # noqa: F401  (slugify re-exportado por conveniencia)
    ROOT,
    esc,
    guardar_json_atomico,
    slugify,
    icono,
    icono_flecha,
    ICONO_CORREO,
    ICONO_CHECK,
)
from modelos import validar_pendiente, validar_iniciativa

PENDIENTES_FILE = ROOT / "data" / "pendientes.json"
PERSONAS_FILE = ROOT / "data" / "personas.json"
INICIATIVAS_FILE = ROOT / "data" / "iniciativas.json"

# ---------- Jerarquía organizacional (petición explícita, 2026-08-29) ----------
# Se usa para ORDENAR y ETIQUETAR las tarjetas de persona (mayor jerarquía
# primero: Gerencia > Jefatura > PMO/Coordinación > Contacto operativo). NO
# cambia la criticidad de cada pendiente individual, que sigue siendo un dato
# declarado aparte por ítem — esto es una capa distinta, sobre la PERSONA.
#
# Se infiere del texto de `persona_cargo` por palabra clave, no de una lista
# aparte de nombres: en cuanto se registra un pendiente con un cargo que
# matchee, la persona queda clasificada automáticamente. Esto es deliberado:
# evita mantener un "directorio" separado de nombres+cargos, y evita crear
# tarjetas para personas que todavía no tienen ningún pendiente registrado
# (ver nota en CONTEXTO.md sobre Luis Aguilar / Geovanny).
NIVELES_JERARQUICOS = [
    # (orden, etiqueta, palabras clave sin tildes/minúsculas)
    # Etiquetas cortas y de largo parejo a propósito (2026-08-29): una
    # palabra cada una, para que el badge quepa en la card compacta junto
    # al estado sin desbordarse, sin importar cuál combinación salga.
    (1, "Gerencia", ("gerente", "gerencia", "director", "direccion")),
    (2, "Jefatura", ("jefe", "jefatura")),
    (3, "PMO", ("pmo", "coordinaci")),
]
NIVEL_DEFECTO = (4, "Operativo")


def _sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii").lower()


def nivel_jerarquico(persona_cargo: str):
    """(orden:int, etiqueta:str) según palabras clave del cargo declarado.
    Orden más bajo = más jerarquía (1=Gerencia). Se recalcula del texto de
    `persona_cargo` en cada build — no es un dato manual por persona."""
    cargo_normalizado = _sin_tildes(persona_cargo)
    for orden, etiqueta, claves in NIVELES_JERARQUICOS:
        if any(clave in cargo_normalizado for clave in claves):
            return orden, etiqueta
    return NIVEL_DEFECTO


def orden_persona(persona: dict):
    """Clave de orden para las tarjetas de persona: primero por jerarquía
    organizacional (menor número = más jerarquía), y dentro del mismo
    nivel, por magnitud de atención descendente (quien más necesita
    atención primero dentro de su propio nivel). 'persona' es el dict
    {'nombre','cargo','items'} que arma personas_a_mostrar() — 'items'
    puede ser [] (persona sin pendientes, solo con proyectos)."""
    orden, _ = nivel_jerarquico(persona["cargo"])
    return (orden, -magnitud_atencion(persona["items"]), persona["nombre"])


def texto_plano(html: str) -> str:
    """Convierte a texto plano el HTML simple que usan solicitud/
    recomendacion (listas <ul>/<ol>/<li>, <strong>, <br>) para poder
    meterlo en el cuerpo de un correo (mailto: no interpreta HTML). No es
    un parser HTML completo — alcanza para el subconjunto de etiquetas que
    este sistema genera.

    IMPORTANTE: el resultado se embebe en un atributo HTML (`data-cuerpo`),
    así que las entidades (`&quot;`, `&amp;`, etc.) se dejan tal cual —
    NO se decodifican acá. El navegador ya las decodifica solo al leer el
    atributo (`element.dataset.cuerpo`), que es donde deben volverse texto
    real. Decodificarlas en Python metería comillas/ampersands crudos
    dentro del atributo y rompería el HTML generado."""
    if not html:
        return ""
    texto = html
    texto = re.sub(r"<(ul|ol)>", "\n", texto)
    texto = re.sub(r"</(ul|ol)>", "\n", texto)
    texto = re.sub(r"<li>", "- ", texto)
    texto = re.sub(r"</li>", "\n", texto)
    texto = re.sub(r"<br\s*/?>", "\n", texto)
    texto = re.sub(r"</p>", "\n\n", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

CRITICIDADES_VALIDAS = {
    "alta": "Criticidad alta",
    "media": "Criticidad media",
    "baja": "Criticidad baja",
}

ESTADOS_ITEM_VALIDOS = {
    "pendiente": ("estado-rojo", "Pendiente"),
    "en_atencion": ("estado-amarillo", "En atención"),
    "resuelto": ("estado-verde", "Resuelto"),
}

ORDEN_ESTADO = {"pendiente": 0, "en_atencion": 1, "resuelto": 2}
ORDEN_CRITICIDAD = {"alta": 0, "media": 1, "baja": 2}

# "Masa" de cada criticidad para la fórmula de gravitación de abajo.
# Escala arbitraria (1-3), no una unidad física real.
PESO_CRITICIDAD = {"alta": 3, "media": 2, "baja": 1}

# Constante gravitacional "G" estilizada: NO es la constante física real
# (6.674e-11), que produciría números ilegibles en este contexto. Se eligió
# 50 solo para que F caiga en un rango de una o dos cifras la mayoría de
# las veces — es una elección de legibilidad, no un hecho físico.
G_ESTILIZADA = 50


def cargar_pendientes() -> list:
    if not PENDIENTES_FILE.exists():
        return []
    with open(PENDIENTES_FILE, "r", encoding="utf-8") as f:
        pendientes = json.load(f)
    for pendiente in pendientes:
        try:
            validar_pendiente(pendiente)
        except ValueError as e:
            sys.exit(f"[ERROR] data/pendientes.json tiene un registro inválido: {e}")
    return pendientes


def guardar_pendientes(pendientes: list) -> None:
    for pendiente in pendientes:
        try:
            validar_pendiente(pendiente)
        except ValueError as e:
            sys.exit(f"[ERROR] No se guardó data/pendientes.json — registro inválido: {e}")
    ordenados = sorted(pendientes, key=lambda x: x["fecha"], reverse=True)
    guardar_json_atomico(PENDIENTES_FILE, ordenados)


def agrupar_por_persona(pendientes: list) -> dict:
    por_persona: dict = {}
    for item in pendientes:
        por_persona.setdefault(item["persona_slug"], []).append(item)
    return por_persona


def cargar_personas() -> dict:
    """Registro de personas (slug -> {'nombre','cargo'}) en
    data/personas.json. Existe SOLO como respaldo de nombre/cargo para una
    persona que puede tener página de seguimiento sin tener ningún
    pendiente activo — por ejemplo, alguien que es propietario de
    proyectos (informes.json/propietario_slug) pero ya no tiene ninguna
    solicitud puntual registrada (petición explícita, 2026-09-24: no
    perder de vista sus proyectos solo porque su último pendiente se
    eliminó). Para cualquier persona que SÍ tiene al menos un pendiente,
    su nombre/cargo se sigue tomando de ahí — ver personas_a_mostrar()."""
    if not PERSONAS_FILE.exists():
        return {}
    with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
        registro = json.load(f)
    return {p["slug"]: p for p in registro}


def personas_a_mostrar(pendientes: list, informes: list) -> dict:
    """Slug -> {'nombre', 'cargo', 'items'} para TODA persona que debe
    tener tarjeta/página en el módulo Reportes y seguimientos: quien
    tenga al menos un pendiente (activo o resuelto), UNIDO con quien sea
    propietaria de al menos un proyecto (informes.json/propietario_slug),
    UNIDO con cualquier persona registrada en data/personas.json (el
    directorio de personas que Marco sigue puntualmente, aunque hoy no
    tenga ningún pendiente ni proyecto — corregido 2026-09-25: antes una
    persona sin nada activo desaparecía del todo y su página quedaba
    huérfana en disco con contenido desactualizado; ahora su página se
    regenera igual, mostrando 'Sin pendientes puntuales registrados
    actualmente', para que nunca muestre información vieja). 'items' es
    su lista de pendientes (puede ser []). Una persona sin ningún
    pendiente/proyecto y SIN registro en personas.json se omite del
    todo — no hay de dónde sacar su nombre/cargo, y no vale la pena
    inventarlos."""
    resultado: dict = {}
    for slug, items in agrupar_por_persona(pendientes).items():
        resultado[slug] = {
            "nombre": items[0]["persona_nombre"],
            "cargo": items[0]["persona_cargo"],
            "items": items,
        }

    registro = cargar_personas()
    propietarios = {i["propietario_slug"] for i in informes if i.get("propietario_slug")}
    for slug in propietarios | set(registro):
        if slug in resultado:
            continue
        persona = registro.get(slug)
        if not persona:
            continue
        resultado[slug] = {"nombre": persona["nombre"], "cargo": persona["cargo"], "items": []}

    return resultado


def dias_restantes(plazo: str):
    """Días entre hoy y el plazo declarado (negativo si ya venció).
    None si el string no es una fecha ISO válida."""
    try:
        fecha_plazo = date.fromisoformat(plazo)
    except (ValueError, TypeError):
        return None
    return (fecha_plazo - date.today()).days


def texto_plazo(plazo: str) -> str:
    """Calcula, a la fecha de build, cuántos días faltan (o pasaron) del
    plazo declarado. Es un cálculo real hecho en el momento de generar la
    página, no un texto fijo que se desactualiza."""
    dias = dias_restantes(plazo)
    if dias is None:
        return f"Plazo: {plazo}"
    try:
        fecha_fmt = date.fromisoformat(plazo).strftime("%d/%m/%Y")
    except ValueError:
        fecha_fmt = plazo
    if dias > 0:
        return f"Vence: {fecha_fmt} (faltan {dias} día{'s' if dias != 1 else ''})"
    if dias == 0:
        return f"Vence: {fecha_fmt} (hoy)"
    return f"Vence: {fecha_fmt} (vencido hace {abs(dias)} día{'s' if abs(dias) != 1 else ''})"


def urgencia_gravitacional(item: dict):
    """Ley de Gravitación Universal, estilizada: F = G·m/r²

    m ("masa") = peso de la criticidad declarada (alta=3, media=2, baja=1).
    r ("distancia") = días que faltan para el plazo, con piso en 1 — un
      pendiente vencido o que vence hoy se trata como 'a distancia mínima'
      (máxima fuerza), en vez de dividir entre cero o un número negativo.
    G = 50 (constante ilustrativa, ver G_ESTILIZADA arriba).

    Devuelve None si el ítem no tiene plazo declarado (la fórmula no
    aplica: sin r, no hay distancia que medir). El resultado sube muy
    rápido a medida que el plazo se acerca — exactamente el comportamiento
    de la ley real, y es por eso que se eligió: la urgencia real de un
    pendiente también se dispara cerca de la fecha límite, no crece
    lineal."""
    plazo = item.get("plazo")
    if not plazo:
        return None
    dias = dias_restantes(plazo)
    if dias is None:
        return None
    r = max(dias, 1)
    m = PESO_CRITICIDAD.get(item.get("criticidad"), 1)
    F = (G_ESTILIZADA * m) / (r ** 2)
    return round(F, 2)


def magnitud_atencion(items: list):
    """Teorema de Pitágoras, c = √(a²+b²), combinando dos conteos
    independientes de una persona en una sola magnitud:

    a = cantidad de pendientes abiertos (no resueltos).
    b = cantidad de esos abiertos que además son de criticidad alta.

    b siempre es un subconjunto de a, así que esto no es una medición
    geométrica real — es una forma deliberada de que la criticidad alta
    'pese más que lineal' en la magnitud final, igual que la hipotenusa de
    un triángulo crece más que la simple suma de sus catetos cuando ambos
    son grandes."""
    abiertos = [i for i in items if i["estado_item"] != "resuelto"]
    a = len(abiertos)
    b = len([i for i in abiertos if i.get("criticidad") == "alta"])
    return round(math.sqrt(a ** 2 + b ** 2), 2)


def entropia_sistema(pendientes: list):
    """Metáfora de la 2ª ley de la termodinámica: un sistema tiende al
    desorden si nadie interviene. Acá 'desorden' = proporción de
    pendientes que siguen abiertos sobre el total histórico registrado.
    No es una entropía termodinámica real (no hay estados microscópicos
    que contar) — es una lectura deliberadamente libre de la idea, para
    tener una sola cifra de 'salud general' del sistema. None si no hay
    ningún pendiente registrado todavía."""
    if not pendientes:
        return None
    abiertos = len([p for p in pendientes if p["estado_item"] != "resuelto"])
    return round(100 * abiertos / len(pendientes), 1)


# ---------- Desglose de subtareas de Jira (fase -> subtareas) ----------
# Objetivo (petición explícita, 2026-09-18): cuando una fase de un informe
# SÍ tiene desglose real de subtareas de Jira, su avance deja de ser una
# estimación editorial (Done=100/En curso=50/Por hacer=0, convención
# documentada en manage_informes.py) y se vuelve un HECHO VERIFICABLE: %
# de subtareas en estado "Finalizada" sobre el total, recalculado en cada
# build directamente desde data/informes.json. Distinguir "esto es un
# hecho verificable" de "esto es una estimación" es un principio explícito
# de este proyecto (ver CONTEXTO.md) — este es el primer lugar del sistema
# donde una fase puede tener las dos cosas a la vez y hay que dejar claro
# cuál aplica.
ESTADO_SUBTAREA_CLASE = {
    "Finalizada": "estado-verde",
    "Abierta": "estado-amarillo",
    "Tareas por hacer": "estado-amarillo",
    "En curso": "estado-amarillo",
    "Evaluación de Viabilidad": "estado-amarillo",
    "Bloqueada": "estado-rojo",
}


def clase_estado_subtarea(estado: str) -> str:
    return ESTADO_SUBTAREA_CLASE.get(estado, "estado-neutral")


def avance_de_subtareas(subtareas: list) -> int:
    """% de subtareas con estado 'Finalizada' sobre el total. Hecho
    verificable (se recalcula siempre desde el detalle real de Jira
    guardado en el JSON), no una estimación a mano — ver nota arriba."""
    if not subtareas:
        return 0
    finalizadas = sum(1 for s in subtareas if s.get("estado") == "Finalizada")
    return round(100 * finalizadas / len(subtareas))


def avance_efectivo_fase(fase: dict) -> int:
    """Avance real de una fase de informe. Si la fase declara "subtareas"
    (desglose real de Jira), el avance ES el % de subtareas 'Finalizada'
    — un hecho verificable que se recalcula siempre desde ese detalle, y
    por lo tanto IGNORA cualquier número que haya quedado guardado en
    "avance" para esa fase (para no arriesgar que ambos se
    desincronicen). Si la fase no tiene desglose, se usa el número
    declarado a mano (estimación editorial, ver convención
    Done=100/En curso=50/Por hacer=0 documentada en manage_informes.py).

    Vive acá (no en manage_informes.py) para que manage_pendientes.py
    también pueda calcular el % real de un informe (sección 'Proyectos en
    seguimiento' de la página de persona) sin crear un import circular
    entre los dos scripts — manage_informes.py importa esta misma función
    en vez de duplicarla."""
    subtareas = fase.get("subtareas")
    if subtareas:
        return avance_de_subtareas(subtareas)
    return fase["avance"]


def avance_de(informe: dict):
    """Devuelve (pct, detalle) o (None, None) si un informe no tiene dato
    de avance. Prioridad: fases > subtareas_completadas/total > avance
    explícito. Ver nota de avance_efectivo_fase() sobre por qué vive acá."""
    fases = informe.get("fases") or []
    if fases:
        pct = round(sum(avance_efectivo_fase(f) for f in fases) / len(fases))
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


def render_desglose_subtareas(subtareas: list) -> str:
    """Lista de subtareas de Jira bajo una fase, con enlace directo a cada
    una y badge de estado — reusa las mismas clases estado-verde/amarillo/
    rojo del resto del sitio en vez de inventar una paleta nueva solo para
    este nivel de detalle. Misma filosofía que render_persona_card()/
    render_pendiente_item(): una sola función de renderizado, para que
    cualquier vista futura que necesite el mismo desglose (hoy solo el
    informe individual) lo pinte siempre igual."""
    if not subtareas:
        return ""
    filas = "\n".join(
        f'        <li class="subtarea-item">'
        f'<a href="https://cafsagroup.atlassian.net/browse/{esc(s["jira_key"])}" target="_blank" rel="noopener">{esc(s["jira_key"])}</a>'
        f' — {esc(s["resumen"])} '
        f'<span class="estado-badge estado-badge-mini {clase_estado_subtarea(s.get("estado", ""))}">{esc(s.get("estado", ""))}</span>'
        f'</li>'
        for s in subtareas
    )
    finalizadas = sum(1 for s in subtareas if s.get("estado") == "Finalizada")
    return f"""      <ul class="subtareas-lista">
{filas}
      </ul>
      <p class="subtareas-nota">{finalizadas}/{len(subtareas)} subtarea(s) finalizada(s) en Jira — dato verificable, recalculado en cada build.</p>"""


def _con_saltos(texto: str) -> str:
    """Convierte '\\n' literales del texto (JSON no guarda saltos de línea
    reales de forma legible) en <br> — permite escribir solicitudes/
    recomendaciones de varios puntos cortos en vez de un párrafo corrido."""
    return texto.replace("\n", "<br>")


def render_pendiente_item(item: dict) -> str:
    estado_clase, estado_label = ESTADOS_ITEM_VALIDOS[item["estado_item"]]
    criticidad = item.get("criticidad", "media")
    criticidad_label = CRITICIDADES_VALIDAS.get(criticidad, "")

    plazo_html = ""
    urgencia_html = ""
    if item.get("plazo"):
        plazo_html = f'      <p class="plazo-badge">{texto_plazo(item["plazo"])}</p>'
        F = urgencia_gravitacional(item)
        if F is not None:
            urgencia_html = (
                '      <p class="formula-nota" '
                'title="Ley de Gravitación Universal (estilizada): F = G·m/r² — '
                'm = peso de la criticidad, r = días que faltan (mínimo 1), '
                'G=50 (constante ilustrativa elegida por legibilidad, no la física real). '
                'Sube muy rápido cuando el plazo se acerca.">'
                f'Urgencia (F=G·m/r²): {F}</p>'
            )

    # data-modo-local="bloque": nota interna de Marco para su propio
    # seguimiento — se oculta en la vista pública (GitHub Pages) y solo se
    # ve corriendo el sistema en localhost. Ver assets/js/modo-vista.js.
    recomendacion_html = ""
    if item.get("recomendacion"):
        recomendacion_html = (
            f'      <div class="recomendacion-box" data-modo-local="bloque"><strong>Recomendación:</strong> '
            f'{_con_saltos(item["recomendacion"])}</div>'
        )

    jira_botones = "\n".join(
        f'        <a class="btn-secundario" href="{esc(j["url"])}" target="_blank" rel="noopener">{esc(j["label"])} {icono_flecha()}</a>'
        for j in item.get("jira_urls", [])
    )

    # Cuerpo en texto plano para el botón "Redactar correo" — sin destinatario
    # fijo (no tenemos la dirección real de correo de cada persona en el
    # sistema; el usuario la completa él mismo al abrir el borrador). Ver
    # redactarCorreo() en mailto-consulta.js.
    partes_cuerpo = [f"Tema: {item['tema']}", "", texto_plano(item["solicitud"])]
    if item.get("recomendacion"):
        partes_cuerpo += ["", f"Recomendación: {texto_plano(item['recomendacion'])}"]
    cuerpo_correo = "\n".join(partes_cuerpo)

    return f"""    <article class="pendiente-item">
      <div class="card-top">
        <span class="estado-badge {estado_clase}">{estado_label}</span>
        <span class="prioridad-badge prioridad-{criticidad}">{criticidad_label}</span>
      </div>
      <h3>{esc(item['tema'])}</h3>
      <p class="page-meta" style="margin-bottom:4px">{item['fecha']}</p>
      <p class="solicitud">{_con_saltos(item['solicitud'])}</p>
{plazo_html}
{urgencia_html}
{recomendacion_html}
      <div class="acciones">
{jira_botones}
        <button class="btn-consulta" data-modo-local="boton" data-tema="{esc(item['tema'])}" onclick="confirmarSeguimiento(this)">
          {icono(ICONO_CHECK)} Confirmar seguimiento
        </button>
        <button class="btn-secundario btn-redactar" data-modo-local="boton" data-persona="{esc(item['persona_nombre'])}" data-tema="{esc(item['tema'])}" data-cuerpo="{cuerpo_correo}" onclick="redactarCorreo(this)">
          {icono(ICONO_CORREO)} Redactar correo a {esc(item['persona_nombre'].split()[0])}
        </button>
      </div>
    </article>"""


def resumen_persona(items: list):
    """Badge-resumen de una persona a partir de sus pendientes abiertos:
    rojo = algo de criticidad alta sin atender, amarillo = hay abiertos
    pero controlados, verde = todo resuelto. Es una lectura agregada, no
    un dato declarado a mano — se recalcula en cada build."""
    abiertos = [i for i in items if i["estado_item"] != "resuelto"]
    if not abiertos:
        return "estado-verde", "Al día"
    if any(i["estado_item"] == "pendiente" and i.get("criticidad") == "alta" for i in abiertos):
        return "estado-rojo", "Atención requerida"
    return "estado-amarillo", "En seguimiento"


def render_persona_card(persona_slug: str, persona: dict, base_path: str = "") -> str:
    """base_path: prefijo relativo hasta la carpeta reportes/. Vacío cuando
    se renderiza dentro de reportes/index.html (los links son 'slug/...'),
    'reportes/' cuando se renderiza en el index.html principal (los links
    deben ser 'reportes/slug/...'). 'persona' es el dict
    {'nombre','cargo','items'} que arma personas_a_mostrar() — 'items'
    puede ser [] (persona sin ningún pendiente, solo con proyectos en
    seguimiento).

    Estructura fija de 'carriles' (jerarquía / estado / título / cargo /
    conteo / magnitud / link) para que todas las cards midan igual sin
    importar el largo del nombre o el cargo — ver .persona-card en
    style.css. Orden de las cards en el grid: ver orden_persona()."""
    items = persona["items"]
    abiertos = [i for i in items if i["estado_item"] != "resuelto"]
    nombre = persona["nombre"]
    cargo = persona["cargo"]
    clase_badge, label_badge = resumen_persona(items)
    nivel_orden, nivel_etiqueta = nivel_jerarquico(cargo)
    if not items:
        conteo = "Sin pendientes puntuales registrados actualmente"
    elif abiertos:
        conteo = f"{len(abiertos)} pendiente(s) abierto(s) de {len(items)} total"
    else:
        conteo = f"Sin pendientes abiertos ({len(items)} en historial)"
    magnitud = magnitud_atencion(items)
    href = f"{base_path}{persona_slug}/index.html"
    return f"""    <div class="persona-card">
      <div class="card-top">
        <span class="jerarquia-badge jerarquia-{nivel_orden}" title="Jerarquía organizacional: se infiere del cargo declarado (Gerencia &gt; Jefatura &gt; PMO/Coordinación &gt; Contacto operativo). Define el orden de las tarjetas, no la criticidad de cada pendiente.">{nivel_etiqueta}</span>
        <span class="estado-badge {clase_badge}">{label_badge}</span>
      </div>
      <h3><a href="{href}">{esc(nombre)}</a></h3>
      <p class="cargo" title="{esc(cargo)}">{esc(cargo)}</p>
      <p class="conteo">{esc(conteo)}</p>
      <p class="formula-nota" title="Teorema de Pitágoras: magnitud = √(a²+b²) — a = pendientes abiertos, b = de esos, cuántos son de criticidad alta. Así lo de criticidad alta 'pesa' más que lineal en el total.">Magnitud de atención (√(a²+b²)): {magnitud}</p>
      <a href="{href}">Ver pendientes y solicitudes {icono_flecha()}</a>
    </div>"""


ESTADOS_INFORME_LABEL = {
    "verde": "A tiempo",
    "amarillo": "En riesgo",
    "rojo": "Atrasado",
    "neutral": "Sin definir",
}

PRIORIDADES_INFORME_LABEL = {
    "alta": "Prioridad alta",
    "media": "Prioridad media",
    "baja": "Prioridad baja",
}


def cargar_iniciativas() -> list:
    """Registro de iniciativas (data/iniciativas.json): documentos de
    análisis/propuesta puntuales, escritos a mano como HTML autocontenido
    (no generados por plantilla), que se registran acá SOLO para que
    aparezcan listados y enlazados desde la página de la persona
    correspondiente — el contenido del documento en sí vive en su propio
    archivo bajo reportes/<persona-slug>/iniciativas/."""
    if not INICIATIVAS_FILE.exists():
        return []
    with open(INICIATIVAS_FILE, "r", encoding="utf-8") as f:
        iniciativas = json.load(f)
    for iniciativa in iniciativas:
        try:
            validar_iniciativa(iniciativa)
        except ValueError as e:
            sys.exit(f"[ERROR] data/iniciativas.json tiene un registro inválido: {e}")
    return iniciativas


def guardar_iniciativas(iniciativas: list) -> None:
    for iniciativa in iniciativas:
        try:
            validar_iniciativa(iniciativa)
        except ValueError as e:
            sys.exit(f"[ERROR] No se guardó data/iniciativas.json — registro inválido: {e}")
    ordenadas = sorted(iniciativas, key=lambda x: x["fecha"], reverse=True)
    guardar_json_atomico(INICIATIVAS_FILE, ordenadas)


def iniciativas_por_persona(iniciativas: list, persona_slug: str) -> list:
    """Iniciativas de una persona, más recientes primero (mismo orden que
    guardar_iniciativas())."""
    propias = [i for i in iniciativas if i["persona_slug"] == persona_slug]
    return sorted(propias, key=lambda i: i["fecha"], reverse=True)


def render_iniciativa_card(iniciativa: dict, base_path: str = "") -> str:
    """Card de una iniciativa dentro de la página de una persona — reusa
    las mismas clases .informe-card/.categoria/.card-footer que ya pinta
    el resto del sitio (mismo lenguaje visual, sin inventar una card
    nueva). A diferencia de un pendiente (solicitud con seguimiento/
    estado) o un proyecto (avance %), una iniciativa es un documento de
    análisis puntual — la card solo necesita título, categoría, resumen y
    el link al documento completo.

    base_path: prefijo relativo hasta la raíz del sitio (por defecto
    '../../', la profundidad real de reportes/<slug>/index.html) — la
    'ruta' del registro ya incluye 'reportes/<slug>/iniciativas/...'."""
    href = f"{base_path}{iniciativa['ruta']}"
    return f"""    <div class="informe-card">
      <div class="card-top">
        <span class="categoria">{esc(iniciativa['categoria'])}</span>
      </div>
      <h3><a href="{href}">{esc(iniciativa['titulo'])}</a></h3>
      <p class="resumen">{esc(iniciativa['resumen'])}</p>
      <div class="card-footer">
        <span>{iniciativa['fecha']}</span>
        <a href="{href}">Ver análisis completo {icono_flecha()}</a>
      </div>
    </div>"""


def informes_por_propietario(informes: list, persona_slug: str) -> list:
    """Informes cuyo campo 'propietario_slug' coincide con la persona —
    ver render_proyecto_persona_card(). Orden: mismo criterio ejecutivo
    que el index principal (orden_atencion, menor primero, sin declarar
    va al final)."""
    propios = [i for i in informes if i.get("propietario_slug") == persona_slug]
    return sorted(propios, key=lambda i: i.get("orden_atencion", 999))


def render_proyecto_persona_card(informe: dict, base_path: str = "../../") -> str:
    """Card compacta de proyecto dentro de la página de una persona —
    'Proyectos en seguimiento' (petición explícita, 2026-09-24): a
    diferencia de un pendiente (una solicitud puntual dirigida a esa
    persona), esto es el estado real y verificable de un proyecto del que
    esa persona es responsable, para que lo pueda revisar directo sin
    tener que ir hasta 'Tus informes'. Reutiliza las mismas clases
    .informe-card/.progreso/.pct-semaforo que ya pinta el index principal
    — mismo diseño, sin inventar una card nueva — y enlaza al informe
    completo para el detalle fase por fase.

    base_path: prefijo relativo hasta la raíz del sitio (por defecto
    '../../', que es la profundidad real de reportes/<slug>/index.html)."""
    estado = informe.get("estado", "neutral")
    estado_label = ESTADOS_INFORME_LABEL.get(estado, "Sin definir")
    prioridad = informe.get("prioridad")
    prioridad_label = PRIORIDADES_INFORME_LABEL.get(prioridad, "")
    prioridad_html = (
        f'<span class="prioridad-badge prioridad-{prioridad}">{prioridad_label}</span>'
        if prioridad else ""
    )

    pct, detalle = avance_de(informe)
    progreso_html = ""
    if pct is not None:
        pct = max(0, min(100, pct))
        progreso_html = f"""      <div class="progreso" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" aria-label="Avance: {detalle}">
        <div class="progreso-barra"><div class="progreso-relleno" data-pct="{pct}" style="width:{pct}%"></div></div>
        <span class="progreso-label">{detalle} (<span class="pct-semaforo" data-pct="{pct}">{pct}%</span>)</span>
      </div>"""

    vencimiento = informe.get("vencimiento")
    vencimiento_html = f" &middot; {texto_plazo(vencimiento)}" if vencimiento else ""

    href = f"{base_path}{informe['ruta']}"
    return f"""    <div class="informe-card">
      <div class="card-top">
        <span class="categoria">{esc(informe['categoria'])}</span>
        <div class="badges-wrap">
          {prioridad_html}
          <span class="estado-badge estado-{estado}">{estado_label}</span>
        </div>
      </div>
      <h3><a href="{href}">{esc(informe['titulo'])}</a></h3>
      <p class="resumen">{esc(informe['resumen'])}</p>
{progreso_html}
      <div class="card-footer">
        <span>{informe['fecha']}{vencimiento_html}</span>
        <a href="{href}">Ver informe completo {icono_flecha()}</a>
      </div>
    </div>"""
