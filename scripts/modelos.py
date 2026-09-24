"""
modelos.py
==========
Validación de forma para los registros de `data/informes.json` y
`data/pendientes.json`, usando únicamente `dataclasses` de la librería
estándar — sin JSON Schema ni ninguna dependencia externa (coherente con
el resto del proyecto, que es Python stdlib puro).

Patrón: cada `dataclass` valida su propia forma en `__post_init__()` —
tipos, campos obligatorios, valores permitidos (`prioridad`,
`criticidad`, etc.) y formato de fecha. `validar_informe()`/
`validar_pendiente()` reciben el `dict` tal como viene de JSON, intentan
construir la dataclass correspondiente, y si algo no calza levantan un
`ValueError` con un mensaje claro señalando el campo y el motivo.

Deliberadamente NO se usan estas dataclasses como el tipo de dato que
circula por el resto del sistema: `render_*()` en `manage_informes.py` y
`reportes_lib.py` siguen recibiendo `dict` como siempre. Este módulo se
usa solo en el borde de entrada/salida (`cargar_*()`/`guardar_*()`), para
detectar un dato mal formado en el momento de leer o escribir el JSON,
en vez de que el error aparezca más tarde como HTML roto o un
`KeyError` confuso a mitad de un render.
"""

from dataclasses import dataclass, field
from datetime import date

PRIORIDADES_VALIDAS = {"alta", "media", "baja"}
CUMPLIMIENTOS_VALIDOS = {"completado", "bloqueado", "vencido", "en_riesgo", "a_tiempo", "sin_fecha"}
ESTADOS_VALIDOS = {"verde", "amarillo", "rojo", "neutral"}
CRITICIDADES_VALIDAS = {"alta", "media", "baja"}
ESTADOS_ITEM_VALIDOS = {"pendiente", "en_atencion", "resuelto"}


def _requerido(nombre: str, valor) -> None:
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ValueError(f"'{nombre}' es obligatorio y no puede estar vacío")


def _fecha_iso(nombre: str, valor, opcional: bool = False) -> None:
    if valor is None:
        if opcional:
            return
        raise ValueError(f"'{nombre}' es obligatorio")
    if not isinstance(valor, str):
        raise ValueError(f"'{nombre}' debe ser texto en formato YYYY-MM-DD (recibido: {valor!r})")
    try:
        date.fromisoformat(valor)
    except ValueError:
        raise ValueError(f"'{nombre}' no es una fecha válida en formato YYYY-MM-DD (recibido: {valor!r})")


def _uno_de(nombre: str, valor, permitidos: set) -> None:
    if valor not in permitidos:
        raise ValueError(f"'{nombre}' inválido: {valor!r} — debe ser uno de {sorted(permitidos)}")


def _lista_de_dicts(nombre: str, valor, claves_requeridas: tuple = ()) -> None:
    if valor is None:
        return
    if not isinstance(valor, list):
        raise ValueError(f"'{nombre}' debe ser una lista (recibido: {type(valor).__name__})")
    for i, item in enumerate(valor):
        if not isinstance(item, dict):
            raise ValueError(f"'{nombre}[{i}]' debe ser un objeto (recibido: {type(item).__name__})")
        for clave in claves_requeridas:
            if clave not in item:
                raise ValueError(f"'{nombre}[{i}]' no tiene la clave obligatoria '{clave}'")


@dataclass
class Informe:
    """Espejo de la forma de un registro en `data/informes.json`. Ver
    `crear_informe()` en `manage_informes.py` para el flujo que produce
    estos campos por primera vez."""

    id: str
    titulo: str
    fecha: str
    categoria: str
    prioridad: str
    cumplimiento: str
    estado: str
    resumen: str
    ruta: str
    vencimiento: str = None
    avance: int = None
    subtareas_completadas: int = None
    subtareas_total: int = None
    fases: list = field(default_factory=list)
    jira_urls: list = field(default_factory=list)
    destacado: bool = False
    personalizado: bool = False
    orden_atencion: int = 999

    def __post_init__(self):
        for campo in ("id", "titulo", "categoria", "resumen", "ruta"):
            _requerido(campo, getattr(self, campo))
        _fecha_iso("fecha", self.fecha)
        _fecha_iso("vencimiento", self.vencimiento, opcional=True)
        _uno_de("prioridad", self.prioridad, PRIORIDADES_VALIDAS)
        _uno_de("cumplimiento", self.cumplimiento, CUMPLIMIENTOS_VALIDOS)
        _uno_de("estado", self.estado, ESTADOS_VALIDOS)
        if self.avance is not None and not (0 <= self.avance <= 100):
            raise ValueError(f"'avance' debe estar entre 0 y 100 (recibido: {self.avance})")
        _lista_de_dicts("fases", self.fases, claves_requeridas=("nombre", "avance"))
        for i, fase in enumerate(self.fases or []):
            if "subtareas" in fase and fase["subtareas"] is not None:
                _lista_de_dicts(f"fases[{i}].subtareas", fase["subtareas"], claves_requeridas=("jira_key", "resumen", "estado"))
        _lista_de_dicts("jira_urls", self.jira_urls, claves_requeridas=("label", "url"))


@dataclass
class Pendiente:
    """Espejo de la forma de un registro en `data/pendientes.json`. Ver
    `crear_pendiente()` en `manage_pendientes.py`."""

    id: str
    persona_slug: str
    persona_nombre: str
    persona_cargo: str
    fecha: str
    tema: str
    solicitud: str
    criticidad: str
    estado_item: str
    plazo: str = None
    recomendacion: str = None
    jira_urls: list = field(default_factory=list)

    def __post_init__(self):
        for campo in ("id", "persona_slug", "persona_nombre", "persona_cargo", "tema", "solicitud"):
            _requerido(campo, getattr(self, campo))
        _fecha_iso("fecha", self.fecha)
        _fecha_iso("plazo", self.plazo, opcional=True)
        _uno_de("criticidad", self.criticidad, CRITICIDADES_VALIDAS)
        _uno_de("estado_item", self.estado_item, ESTADOS_ITEM_VALIDOS)
        _lista_de_dicts("jira_urls", self.jira_urls, claves_requeridas=("label", "url"))


def _construir(cls, dato: dict, etiqueta: str):
    if not isinstance(dato, dict):
        raise ValueError(f"cada {etiqueta} debe ser un objeto JSON (recibido: {type(dato).__name__})")
    try:
        return cls(**dato)
    except TypeError as e:
        # dataclass levanta TypeError para claves inesperadas o
        # argumentos obligatorios faltantes — se traduce a un mensaje
        # consistente con los ValueError del resto de las validaciones.
        raise ValueError(f"{etiqueta} '{dato.get('id', '?')}' tiene campos inválidos o incompletos: {e}") from e


def validar_informe(dato: dict) -> None:
    """Levanta ValueError con un mensaje claro si `dato` no tiene la
    forma esperada de un informe. No modifica `dato` ni devuelve nada —
    se usa solo como chequeo antes de usar/guardar el registro."""
    _construir(Informe, dato, "informe")


def validar_pendiente(dato: dict) -> None:
    """Igual que `validar_informe()`, para un registro de pendiente."""
    _construir(Pendiente, dato, "pendiente")
