# Glosario de palabras clave — Informes Operaciones TI

> Utilidad descargable del portal Informes Operaciones TI (CAFSA).
> Documento vivo: cada vez que el proyecto crea un concepto/término
> nuevo, se agrega acá (ver `SOP.md`, SOP-13). Última actualización:
> **2026-09-07**.

## Estructura del sistema

- **Informe** — estado ejecutivo de un programa/proyecto, para Gerencia
  Operativa de TI. Vive en `informes/<categoria>/<slug>.html`, generado
  desde `data/informes.json`.
- **Pendiente** — solicitud/seguimiento puntual dirigido a una persona
  específica. Vive en `reportes/<persona-slug>/index.html`, generado
  desde `data/pendientes.json`.
- **Persona (página evergreen)** — cada persona con pendientes tiene una
  URL propia que acumula su historial en el tiempo, en vez de un
  documento que se reemplaza cada vez.
- **`personalizado: true`** — bandera en `data/informes.json` que protege
  una página hecha a mano de que el script la sobrescriba al regenerar.
- **Brief (diario)** — archivo HTML que Marco genera fuera del sistema
  (correo/Teams/Jira) y coloca en `briefs/` para verlo desde el índice.
  Estrictamente local — nunca se publica (ver plantilla dedicada).
- **Manifest (`manifest.json`)** — pequeño archivo JSON que le dice al
  JavaScript del sitio qué archivos existen y cuál es el más reciente,
  ya que un sitio estático no puede "listar una carpeta" por sí solo.
- **Degradación elegante** — patrón de diseño usado en `briefs/`: el
  mismo código se comporta distinto según el contexto (localmente
  funciona, en el sitio público la función se oculta sola porque el
  archivo que necesita nunca se sube) — sin duplicar código ni arriesgar
  una fuga de datos.
- **`.gitignore` / "gitignored"** — mecanismo de git para que ciertos
  archivos/carpetas nunca se suban al repositorio (código fuente
  incluido, pero nunca su contenido). Usado para `contexto-proyecto/` y
  `briefs/`.

## Fórmulas y métricas (con guiño matemático a propósito)

- **Gravitación / urgencia (`F = G·m/r²`)** — fórmula usada para calcular
  qué tan urgente es un pendiente según su criticidad y cercanía al
  plazo. Alimenta el "radar de urgencia" del panel "Mi seguimiento".
- **Magnitud de atención (Pitágoras, `√(a²+b²)`)** — combina cantidad y
  criticidad de los pendientes de una persona en un solo número, usado
  para ordenar dentro de cada nivel jerárquico.
- **Entropía (metáfora)** — porcentaje de pendientes todavía abiertos,
  mostrado en `reportes/index.html` como métrica general del sistema.
- **Semáforo continuo (π, `e(t) = (1 - cos(π·t)) / 2`)** — suavizado que
  define el color (rojo→ámbar→verde) de cualquier porcentaje de avance en
  el sitio, en vez de saltos bruscos entre colores.

## Jerarquía organizacional ("Reportes y seguimientos")

- **`nivel_jerarquico()`** — función que clasifica el cargo de una
  persona en Gerencia / Jefatura / PMO / Operativo, buscando palabras
  clave en el texto del cargo (ver `plantilla-actualizar-persona.md`).
- **`orden_persona()`** — criterio de orden de las tarjetas de persona:
  primero por nivel jerárquico, luego por magnitud de atención
  (descendente), luego por nombre.
- **`jerarquia-badge`** — la etiqueta de color (Gerencia/Jefatura/PMO/
  Operativo) que aparece en cada tarjeta de persona.
- **`redactarCorreo()`** — botón que abre un borrador de correo con el
  campo "Para" **vacío a propósito**: el sistema nunca guarda ni inventa
  direcciones de correo reales de terceros.
- **`texto_plano()`** — convierte el HTML de una solicitud/recomendación
  a texto plano legible para el cuerpo de un correo, sin decodificar
  entidades HTML (por seguridad del atributo donde se embebe).

## Seguridad y disciplina de contenido

- **Disciplina de contenido** — reglas explícitas (SOP-11) sobre qué
  nunca puede aparecer en el sitio público: contratos de proveedores,
  hallazgos de auditoría/SUGEF/CONASSIF, credenciales, IPs internas,
  vulnerabilidades, datos sensibles de personas, correos reales de
  terceros.
- **`index.lock` (git)** — archivo de bloqueo que git crea mientras
  trabaja; si un proceso se corta a la mitad, puede quedar huérfano y
  bloquear el siguiente `git add`/`commit` (ver SOP-07-a).

## Módulo de memoria de casos (diseño, todavía no implementado)

> Ver `contexto-proyecto/ARQUITECTURA-MEMORIA-CASOS.md` para el diseño
> completo — estos términos ya están acuñados aunque el módulo no exista
> todavía en código.

- **Caso** — registro de una situación/incidente/consulta que se abre y
  se resuelve, guardado en `casos.db.enc` (encriptado).
- **Recurrencia** — cuando un caso nuevo se parece (por similitud de
  texto, `difflib`) a uno ya resuelto; el sistema lo sugiere, nunca
  decide por Marco.
- **Cruce sutil** — mención detectada entre texto libre (un caso, un
  brief) y datos estructurados (una épica/proyecto de Jira), mostrada
  como una línea discreta, calculada al momento de consultar y nunca
  guardada — para no romper la separación entre datos estructurados y
  texto libre ni generar ciclos de sincronización.
- **Token de sesión** — código temporal que reemplaza tener que escribir
  la passphrase de `casos.db.enc` en cada ejecución, cacheado localmente
  por perfil con una expiración.
- **Perfil (de usuario)** — registro local (nombre, correo `@cafsa.fi.cr`,
  cargo) que identifica a quien usa el sistema — sin ser autenticación
  corporativa real.
- **Instancia independiente vs. datos compartidos** — la pregunta de
  fondo sobre si cada persona corre su propia copia del sistema (con sus
  propios datos) o si varias personas comparten la misma hoja de ruta;
  todavía sin resolver (ver arquitectura, sección 9.1).

## Utilidades del sistema

- **Utilidades únicas del sistema** — sección del portal con
  herramientas prácticas de uso diario: esta plantilla, el glosario, y a
  futuro la demo de cifrado/descifrado (ver arquitectura, Módulo E).
