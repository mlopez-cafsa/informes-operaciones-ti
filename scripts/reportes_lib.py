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
import unicodedata
from datetime import date

from common import ROOT, slugify  # noqa: F401  (slugify re-exportado por conveniencia)

PENDIENTES_FILE = ROOT / "data" / "pendientes.json"

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


def orden_persona(items: list):
    """Clave de orden para las tarjetas de persona: primero por jerarquía
    organizacional (menor número = más jerarquía), y dentro del mismo
    nivel, por magnitud de atención descendente (quien más necesita
    atención primero dentro de su propio nivel)."""
    orden, _ = nivel_jerarquico(items[0]["persona_cargo"])
    return (orden, -magnitud_atencion(items), items[0]["persona_nombre"])


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
        return json.load(f)


def guardar_pendientes(pendientes: list) -> None:
    PENDIENTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    ordenados = sorted(pendientes, key=lambda x: x["fecha"], reverse=True)
    with open(PENDIENTES_FILE, "w", encoding="utf-8") as f:
        json.dump(ordenados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def agrupar_por_persona(pendientes: list) -> dict:
    por_persona: dict = {}
    for item in pendientes:
        por_persona.setdefault(item["persona_slug"], []).append(item)
    return por_persona


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

    recomendacion_html = ""
    if item.get("recomendacion"):
        recomendacion_html = (
            f'      <div class="recomendacion-box"><strong>Recomendación:</strong> '
            f'{_con_saltos(item["recomendacion"])}</div>'
        )

    jira_botones = "\n".join(
        f'        <a class="btn-secundario" href="{j["url"]}" target="_blank" rel="noopener">{j["label"]} &rarr;</a>'
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
      <h3>{item['tema']}</h3>
      <p class="page-meta" style="margin-bottom:4px">{item['fecha']}</p>
      <p class="solicitud">{_con_saltos(item['solicitud'])}</p>
{plazo_html}
{urgencia_html}
{recomendacion_html}
      <div class="acciones">
{jira_botones}
        <button class="btn-consulta" data-tema="{item['tema']}" onclick="confirmarSeguimiento(this)">
          Confirmar seguimiento
        </button>
        <button class="btn-secundario btn-redactar" data-persona="{item['persona_nombre']}" data-tema="{item['tema']}" data-cuerpo="{cuerpo_correo}" onclick="redactarCorreo(this)">
          Redactar correo a {item['persona_nombre'].split()[0]}
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


def render_persona_card(persona_slug: str, items: list, base_path: str = "") -> str:
    """base_path: prefijo relativo hasta la carpeta reportes/. Vacío cuando
    se renderiza dentro de reportes/index.html (los links son 'slug/...'),
    'reportes/' cuando se renderiza en el index.html principal (los links
    deben ser 'reportes/slug/...').

    Estructura fija de 'carriles' (jerarquía / estado / título / cargo /
    conteo / magnitud / link) para que todas las cards midan igual sin
    importar el largo del nombre o el cargo — ver .persona-card en
    style.css. Orden de las cards en el grid: ver orden_persona()."""
    abiertos = [i for i in items if i["estado_item"] != "resuelto"]
    nombre = items[0]["persona_nombre"]
    cargo = items[0]["persona_cargo"]
    clase_badge, label_badge = resumen_persona(items)
    nivel_orden, nivel_etiqueta = nivel_jerarquico(cargo)
    conteo = (
        f"{len(abiertos)} pendiente(s) abierto(s) de {len(items)} total"
        if abiertos else f"Sin pendientes abiertos ({len(items)} en historial)"
    )
    magnitud = magnitud_atencion(items)
    href = f"{base_path}{persona_slug}/index.html"
    return f"""    <div class="persona-card">
      <div class="card-top">
        <span class="jerarquia-badge jerarquia-{nivel_orden}" title="Jerarquía organizacional: se infiere del cargo declarado (Gerencia &gt; Jefatura &gt; PMO/Coordinación &gt; Contacto operativo). Define el orden de las tarjetas, no la criticidad de cada pendiente.">{nivel_etiqueta}</span>
        <span class="estado-badge {clase_badge}">{label_badge}</span>
      </div>
      <h3><a href="{href}">{nombre}</a></h3>
      <p class="cargo" title="{cargo}">{cargo}</p>
      <p class="conteo">{conteo}</p>
      <p class="formula-nota" title="Teorema de Pitágoras: magnitud = √(a²+b²) — a = pendientes abiertos, b = de esos, cuántos son de criticidad alta. Así lo de criticidad alta 'pesa' más que lineal en el total.">Magnitud de atención (√(a²+b²)): {magnitud}</p>
      <a href="{href}">Ver pendientes y solicitudes &rarr;</a>
    </div>"""
