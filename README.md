# informes-operaciones-ti

Portal estático de Operaciones de TI (CAFSA), con dos módulos:

- **Informes** (`informes/`): estado ejecutivo por programa/proyecto, dirigido
  a Gerencia Operativa de TI. Un solo link (`index.html`) da acceso a todos.
- **Reportes y seguimientos** (`reportes/`): solicitudes/pendientes puntuales
  dirigidos a una persona específica (con enlace a Jira, botón de
  confirmación de seguimiento, y recomendación cuando aplica involucrar a
  otro equipo). Un link evergreen por persona (`reportes/<persona>/`).

Este README es la **referencia técnica** (cómo usar cada script y cada
opción). Para el **paso a paso operativo** — cuándo y en qué orden correr
cada procedimiento, con su verificación y su plan de rollback — ver
**`SOP.md`** en la raíz del repo.

## ⚠️ Repositorio público — disciplina de contenido

Este repositorio es **público** (requisito de GitHub Pages en su plan
estándar). Cualquier persona con el link tiene acceso al contenido, sin
autenticación de CAFSA, y **todo el historial de commits también es
público**, no solo la versión final publicada.

Reglas antes de subir cualquier informe:

- Nunca incluir detalles de contratos con proveedores, hallazgos de
  auditoría/SUGEF/CONASSIF, datos personales, credenciales, direcciones IP
  internas, ni información de vulnerabilidades o riesgos de seguridad.
- El contenido de cada informe debe ser la versión **resumida y ejecutiva**
  de tu brief interno — el brief completo se mantiene fuera de este repo.
- Los "enlaces a detalle ampliado" dentro de cada informe deben apuntar a
  sistemas internos con su propio control de acceso (Jira, SharePoint,
  intranet), nunca a documentos sensibles alojados en este repo.
- `robots.txt` está configurado para desalentar la indexación por buscadores
  (`Disallow: /`). Esto reduce el descubrimiento incidental, **no** es
  control de acceso: quien tenga el link igual puede entrar.

Ejemplo aplicado: los temas de renegociación o firma de contratos con
proveedores (expedientes, condiciones, plazos comerciales) **no se
publican aquí** — quedan solo en el seguimiento interno (Jira/hoja de
ruta). Lo que sí se publica es el estado ejecutivo del proyecto asociado
(ej. "migración de infraestructura en curso"), sin el detalle contractual
de fondo.

## Estado actual del sistema (al 30/09/2026)

Hecho verificable a partir de `data/*.json` al momento de escribir esto
— cambia con cada `build`/`regenerar-paginas`, no es un número fijo:

- **8 informes** publicados bajo `informes/`, en las categorías
  `datos-etl`, `gobierno-ti`, `core-financiero`, `riesgo-tecnologico`
  (×2 — PP-232 y PP-233, en cards separados), `infraestructura`,
  `finanzas-internas` y `operaciones`. De esos, **3 tienen
  `"personalizado": true`** (contenido hecho a mano, `regenerar-paginas`
  los salta): Migración de Core Financiero (Forms 14C), Quanto/Contabilidad
  (BMO-252) y Operaciones Diarias.
- **Módulo "Reportes y seguimientos"**: 3 personas registradas en
  `data/personas.json` (Luis Aguilar Morales — Gerente de TI, Cristopher
  Pérez Ugalde — Jefe de TI, María Cristina Hernández — PMO), con **7
  pendientes** abiertos/en seguimiento en `data/pendientes.json` y **1
  iniciativa** de análisis extendido (`data/iniciativas.json` — doble
  factor /df, de Cristopher).
- **Panel "Mi seguimiento (Jira)"**: snapshot de 33 pendientes propios
  abiertos en Jira, actualizado por última vez el 2026-09-23
  (`data/jira_snapshot.json.generado`) — correr la skill `-actualiza-jira`
  (o repetir la consulta JQL a mano) para refrescarlo.
- **Bitácora de Operaciones Diarias**: 311 registros estructurados
  (fecha/issue/proveedor/horas) en `data/bitacora_operaciones.json`,
  rango 2026-08-03 a 2026-09-28, 346.5 horas totales — actualizada al
  2026-09-30.
- **Página "Configuración y utilidades del sistema"**
  (`utilidades-sistema.html`, nueva desde 2026-09-30): reemplaza el
  acordeón que antes vivía dentro del `index.html` principal — ver
  sección dedicada más abajo.
- Repositorio en la rama `main`, publicado vía GitHub Pages, **sin
  dependencias externas de Python** — todo `scripts/*.py` corre con la
  librería estándar (probado con Python 3.10).

## Fases y enlaces a Jira

Un informe puede declarar `--fase "Nombre=NN"` (repetible) para mostrar un
gráfico real de avance por fase en vez de una sola barra genérica. El
avance de la card es el promedio de sus fases. Convención cuando la fase
viene de un estado de Jira: Done=100, En curso=50, Por hacer=0 (una
aproximación declarada, no una medición exacta — así se documenta en la
página del informe).

`--jira-url` (repetible) llena automáticamente la sección "Más detalle"
con enlaces reales al issue de Jira correspondiente (requiere login CAFSA,
así que es seguro enlazarlo aunque el repo sea público).

### Nombre de fase como hipervínculo

Si el `nombre` de una fase incluye la clave de Jira entre paréntesis (ej.
`"... (BMO-118)"`, `"... (GDT-120) - sin descripción..."`), el nombre
completo de la fase se convierte automáticamente en un link directo a ese
issue (`jira_key_de_fase()` / `fase_nombre_html()` en
`manage_informes.py`, vía una expresión regular sobre el paréntesis — no
hace falta declarar nada aparte). **Si TODAS las fases de un informe
resuelven así su propio enlace, la sección "Más detalle" se omite por
completo** — sería un duplicado exacto de los enlaces que ya están arriba.
Cuando alguna fase no trae clave en el nombre (por ejemplo "Modernización
de infraestructura /gx", donde las fases son etapas de trabajo genéricas y
no tickets individuales), "Más detalle" se sigue mostrando como respaldo
con lo que haya en `jira_urls`.

Si editás `fases` o `jira_urls` a mano en `data/informes.json`, corré
`python3 scripts/manage_informes.py regenerar-paginas` para que las
páginas individuales reflejen el cambio (a diferencia de `build`, que solo
regenera `index.html`).

### Desglose de subtareas por fase

Cuando una fase necesita seguimiento más fino que un solo %, se le puede
agregar `"subtareas": [{"jira_key": "ABC-1", "resumen": "...", "estado":
"Finalizada"}, ...]` directamente en `data/informes.json` (no hay flag de
CLI para esto — se edita el JSON a mano y se corre `regenerar-paginas`).
En cuanto una fase tiene `subtareas`, su `avance` se calcula solo: % de
subtareas con `estado` exactamente `"Finalizada"` sobre el total — un
hecho verificable recalculado en cada build, no una estimación editorial
(ver `avance_efectivo_fase()` en `manage_informes.py` y
`avance_de_subtareas()`/`render_desglose_subtareas()` en
`reportes_lib.py`). El HTML resultante muestra cada subtarea con link
directo a Jira y un badge de estado, debajo del nombre de su fase. Es
público (no oculto en modo local): es el mismo tipo de dato que ya se ve a
nivel de fase, solo que más detallado.

## Agrupación por programa, o card propio por ticket

Un card puede representar un **programa** (varios issues de Jira
relacionados bajo un mismo objetivo — ej. "Gobierno de TI y Cumplimiento"
agrupa el clúster GDT-100/106/120/320/107) o un **ticket individual** que
necesita seguimiento especializado (ej. "Integración GAUDI en CAFSA en
Línea — FASE 1 (PP-233)", con su propio desglose de subtareas). La regla
para decidir cuál usar: si hace falta ver el % y las subtareas de un
ticket específico sin que quede diluido entre otros, ese ticket sale a su
propio card, aunque comparta epopeya/eje con otro (ej. PP-232 y PP-233:
ambos son parte del mismo eje XL-TEC-01, pero viven en cards separados
porque cada uno se sigue por su propio ritmo).

Cuando un card sí agrupa varios issues menores sin necesidad de
seguimiento fino por separado (ej. issues de backlog de bajo impacto
individual), la regla de fondo se mantiene: **el resumen de una card
agrupada siempre debe encabezar con el issue de mayor peso real**, no con
una descripción genérica del grupo.

## Buscador y orden (index)

El índice tiene un buscador de texto libre y aproximado (tolera errores de
tipeo y no requiere que las palabras aparezcan en el orden exacto) sobre
tres capas de datos: lo visible en la card (título, resumen, categoría,
estado, prioridad), los nombres de fase (aunque no se impriman en la
card), y cada referencia de Jira del informe (ticket principal y
subtareas — key, resumen y URL). Cuando una coincidencia viene de una
referencia que no se ve en la card, se muestra una pista debajo del
resumen ("Coincide con: BMO-155 — ...") con link directo a Jira. Un
selector de orden (prioridad de atención, más recientes, prioridad,
estado, título) y los botones de categoría se combinan con la búsqueda —
los tres filtros aplican a la vez. Todo corre en el navegador (sin
backend).

## Estructura

```
informes-operaciones-ti/
├── index.html                  # Generado por el script — NO editar a mano
├── utilidades-sistema.html     # Configuración y utilidades del sistema — hecha a mano, NO se regenera sola
├── README.md                    # Referencia técnica (cómo usar cada script)
├── SOP.md                       # Procedimiento estándar paso a paso (cuándo/en qué orden)
├── robots.txt
├── .gitignore
├── logos-cafsa/                 # Logos originales (fuente, sin optimizar)
├── assets/
│   ├── css/style.css           # Paleta CAFSA + semáforo + sistema visual (acento, sombras, iconografía)
│   ├── js/mailto-consulta.js   # Botones de mailto (consulta / confirmar seguimiento / redactar correo)
│   ├── js/color-semaforo.js    # Semáforo de color para % de avance (ver sección de matemáticas)
│   ├── js/modo-vista.js        # Vista local (Marco) vs. pública (Jefatura/PMO/Gerencia) — ver sección dedicada
│   ├── js/brief-viewer.js      # Botón + <dialog> del brief diario (solo aparece si briefs/manifest.json existe)
│   └── img/logos/              # Logos optimizados para web + favicon
├── informes/
│   └── <categoria>/<slug>.html # Un archivo HTML por informe (8 al día de hoy — ver "Estado actual del sistema")
├── reportes/
│   ├── index.html              # Generado — directorio de personas
│   ├── <persona-slug>/         # Generado — página evergreen de esa persona (incluye iniciativas/ si aplica)
│   │   ├── index.html
│   │   └── iniciativas/*.html  # Análisis extendido de una iniciativa puntual (ej. doble factor /df)
│   └── DD-MM-YYYY/             # Bandeja de memos fuente (.docx) — NUNCA se publica (ver .gitignore)
├── briefs/                     # Briefs diarios en HTML — excluido de git (.gitignore)
│   ├── manifest.json           # Generado por manage_briefs.py build — NUNCA se comitea
│   └── DD-##-MM-YYYY-brief.html
├── data/
│   ├── informes.json           # Fuente de verdad de informes/
│   ├── pendientes.json         # Fuente de verdad de reportes/
│   ├── iniciativas.json        # Iniciativas de análisis extendido por persona (reportes/<persona>/iniciativas/)
│   ├── personas.json           # Registro slug → nombre/cargo (una sola fuente para ambos scripts)
│   ├── jira_snapshot.json      # Foto de mis pendientes en Jira (panel "Mi seguimiento")
│   └── bitacora_operaciones.json # Registros estructurados para el buscador de Operaciones Diarias
├── utilidades/                 # Plantillas descargables + glosario — formato de referencia/respaldo
│   ├── plantilla-nuevo-informe.md
│   ├── plantilla-nuevo-pendiente.md
│   ├── plantilla-actualizar-persona.md
│   ├── plantilla-brief-diario.md
│   └── glosario-palabras-clave.md
├── templates/
│   ├── index_template.html            # Plantilla del índice de informes
│   ├── informe_template.html          # Plantilla de un informe nuevo
│   ├── reportes_index_template.html   # Plantilla del directorio de personas
│   └── pendiente_persona_template.html # Plantilla de la página de una persona
├── scripts/
│   ├── common.py            # slugify / parse_jira_url / esc() / guardar_json_atomico() / iconografía — compartido
│   ├── modelos.py           # Dataclasses Informe/Pendiente/Iniciativa — validan la forma de data/*.json
│   ├── reportes_lib.py      # Datos + tarjeta de persona — compartido
│   ├── manage_informes.py   # Crea informes, regenera index.html, detecta páginas huérfanas
│   ├── manage_pendientes.py # Registra/edita/elimina pendientes y regenera reportes/ + index.html
│   └── manage_briefs.py     # Regenera briefs/manifest.json a partir de los .html en briefs/
└── contexto-proyecto/           # Memoria/contexto interno — excluido de git (.gitignore), NO viaja con el repo
    ├── CONTEXTO.md              # Historial de decisiones, detalle sin curar — no tiene versión pública
    ├── HOJA-RUTA.xlsx           # Hoja de ruta personal de seguimiento (referencia complementaria a Jira)
    ├── ARQUITECTURA-MEMORIA-CASOS.md
    └── *.xlsx / *.md            # Insumos puntuales (ej. plan de pruebas Forms 14C) — ver sección dedicada
```

**`contexto-proyecto/` no está en git** (ver `.gitignore`): si clonás este repo en una computadora nueva, esta carpeta **no llega** — hay que copiarla manualmente desde donde se respalde, o recrearla. Ver "Implementar este sistema en otra computadora" más abajo.

`index.html` no depende solo de `informes.json`: la sección "Reportes y
seguimientos" que se ve arriba del catálogo de informes se arma con los
mismos datos de `pendientes.json` y la misma tarjeta de persona que usa
`reportes/index.html` (ambas viven en `reportes_lib.py`, para que no haya
dos diseños de card divergiendo). Por eso **cualquiera de los dos scripts**
(`manage_informes.py build` o `manage_pendientes.py nuevo`/`build`) deja
`index.html` completo y al día — no hace falta correr ambos a mano.

Cada persona con pendientes aparece en el `index.html` principal con un
badge resumen calculado en cada build (no guardado a mano): "Al día" si no
tiene pendientes abiertos, "En seguimiento" si tiene pendientes abiertos
sin criticidad alta, o "Atención requerida" si tiene alguno de criticidad
alta sin atender. Así, cualquiera con acceso al link principal puede
ubicar y abrir directamente su propia página de seguimiento, con el
detalle de cada solicitud y sus enlaces a Jira.

## Cómo crear un informe nuevo

No se edita `index.html` a mano. Se usa el script, que crea el HTML, lo
registra en `data/informes.json` y regenera el índice automáticamente:

```bash
python3 scripts/manage_informes.py nuevo \
  --titulo "Avance proyecto X" \
  --categoria "proyectos" \
  --resumen "Resumen ejecutivo de una línea, claro y directo." \
  --prioridad alta \
  --cumplimiento en_riesgo \
  --avance 40 \
  --fecha 2026-08-21
```

Parámetros:

- `--titulo`, `--categoria`, `--resumen`: obligatorios.
- `--prioridad`: `alta` | `media` | `baja` — obligatorio. Ver criterio del semáforo abajo.
- `--cumplimiento`: `completado` | `bloqueado` | `vencido` | `en_riesgo` | `a_tiempo` | `sin_fecha` — obligatorio.
- `--avance`: porcentaje 0-100 (opcional). Se muestra como barra de progreso en la card.
- `--subtareas-completadas` / `--subtareas-total`: alternativa a `--avance` cuando el progreso viene de un conteo real de etapas (ej. `1` de `3`); el porcentaje se calcula solo y se prioriza sobre `--avance` si ambos vienen.
- `--estado`: override manual del semáforo (`verde`/`amarillo`/`rojo`/`neutral`). No recomendado — se calcula automáticamente a partir de prioridad + cumplimiento.
- `--fecha`: `YYYY-MM-DD` (default: hoy).
- `--vencimiento`: `YYYY-MM-DD` (opcional). Solo si el informe tiene una
  fecha límite realmente declarada (ej. una meta de proyecto). Si se
  indica, se muestra en el pie de la card junto a `--fecha`, calculado en
  vivo con el mismo texto de "faltan N días" / "vencido hace N días" que
  usa el módulo de reportes (`reportes_lib.texto_plazo()`), para no tener
  dos fórmulas de plazo distintas en el sitio. Si no se indica, el pie de
  la card solo muestra la fecha de actualización.
- `--destacado`: si se agrega, el informe aparece primero en el índice.

Después de crear el archivo, edita manualmente el HTML generado en
`informes/<categoria>/<slug>.html` para ajustar el gráfico (Chart.js), los
enlaces de "más detalle" y cualquier contenido adicional.

### Subcomandos de `manage_informes.py`

- `nuevo`: crea un informe, lo registra en `data/informes.json` y regenera `index.html` (ver arriba).
- `build`: regenera solo `index.html` a partir de `data/informes.json` (no toca las páginas individuales). Útil tras editar el JSON a mano (por ejemplo, para cambiar el estado de un informe existente).
- `regenerar-paginas`: re-renderiza **todas** las páginas individuales desde `data/informes.json` (útil tras editar `fases`/`jira_urls`/`subtareas` a mano en el JSON) y luego el índice. Salta los informes con `"personalizado": true` (ver sección dedicada más abajo). Al terminar, compara las rutas registradas en `data/informes.json` contra los `.html` que realmente existen bajo `informes/` y **avisa** (sin borrar) si encuentra alguno sin registro — `[AVISO] N página(s) .html en informes/ sin registro en data/informes.json`.

## Criterio de semáforo

El color no se elige a mano: se calcula a partir de dos datos que se
declaran al crear el informe — **prioridad** (alta/media/baja) y
**cumplimiento** (completado, bloqueado, vencido, en riesgo, a tiempo, sin
fecha). Es un criterio combinado, la opción recomendada frente a usar solo
plazo o solo riesgo por separado.

| Cumplimiento \ Prioridad | Alta | Media | Baja |
|---|---|---|---|
| Completado | Verde | Verde | Verde |
| Bloqueado | Rojo | Rojo | Rojo |
| Vencido | Rojo | Rojo | Amarillo |
| En riesgo | Rojo | Amarillo | Amarillo |
| A tiempo | Amarillo | Verde | Verde |
| Sin fecha definida | Amarillo | Verde | Verde |

Lógica detrás de la matriz:

- **Completado** y **bloqueado** son absolutos: no dependen de la prioridad.
  Un bloqueo activo siempre es crítico; un cierre siempre es positivo.
- Un **vencido** de prioridad baja se suaviza a amarillo, pero nunca
  desaparece del radar (nunca llega a verde).
- Los temas de **prioridad alta** se mantienen en amarillo aunque estén "a
  tiempo" o "sin fecha", para conservar visibilidad ejecutiva sobre lo
  importante, no solo sobre lo que ya está mal.

El cálculo vive en `calcular_semaforo()` dentro de `scripts/manage_informes.py`.
Si en el futuro Gerencia pide ajustar algún cruce de la matriz, se cambia
ahí (una sola fuente de verdad) y se corre `build` para que todos los
informes existentes se actualicen.

## Sistema visual

`assets/css/style.css` define el sistema visual de todo el sitio a partir
de variables en `:root`:

- **Color de acento** (`--accent`, verde musgo oscuro) para links, foco,
  hover de "ver más" y la barra de avance — reservado a interacción
  genérica, nunca se mezcla con el semáforo de estado (verde/amarillo/rojo
  sigue siendo el único código de color con significado de riesgo). Los
  títulos que además son link (`.informe-card h3 a`, `.persona-card h3
  a`) usan `--cafsa-black` en vez de heredar el acento del selector `a`
  global — un título no debe leerse como un link de color.
- **Radio de borde e sombras en capas** (dos sombras superpuestas, tinte
  neutro) en todas las cards — ambos se controlan desde `:root`.
- **Iconografía SVG inline** (sin CDN ni fuentes de íconos externas): set
  compartido en `scripts/common.py` (`icono()`, `icono_seccion()`,
  `icono_flecha()`, constantes `ICONO_*`), usado en encabezados de sección
  y en los botones principales (correo, confirmar, Jira, ver más). Aplica
  a las 4 plantillas generadas y a las páginas `"personalizado": true`
  (si se agrega un encabezado de sección nuevo a esas 2 páginas, usar el
  mismo set de íconos para mantener consistencia visual).
- Microinteracciones sutiles (flecha que se desliza al hover, botones con
  leve elevación al pasar el mouse).

## Botón "Enviar consulta sobre este informe"

Abre un borrador de correo (`mailto:`) dirigido siempre a
`mlopezz@cafsa.fi.cr`, con el título y resumen del informe como contexto.
No envía nada automáticamente: primero pide confirmación en el navegador, y
luego el usuario revisa y envía desde su propio cliente de correo.

## Configuración y utilidades del sistema

Página propia — `utilidades-sistema.html`, en la raíz del repo, **hecha a
mano** (no se regenera con `regenerar-paginas`) — enlazada desde el
segmento "Configuración" al final del panel "Mi seguimiento (Jira)" (ver
esa sección más abajo). Hasta el 2026-09-30 este contenido vivía como un
acordeón chico dentro del `index.html` principal; se movió a una página
dedicada para aprovechar el ancho completo en vez de tarjetas colapsadas.

Layout de 2 columnas: un TOC fijo a la izquierda con anclas a cada tema, y
el contenido siempre desplegado a la derecha (sin clics para expandir) —
una sección por cada operación de mantenimiento del sistema (registrar
informe, registrar pendiente, actualizar persona, registrar brief), con
una explicación en lenguaje simple de qué es y cuándo usarlo, y el
comando técnico exacto al final para quien lo necesite copiar. El
glosario (`<dl class="glosario-lista">`, agrupado por categoría) documenta
todos los términos acuñados en el proyecto — se agrega un término cada
vez que el proyecto crea uno nuevo (ver SOP-13 en `SOP.md`).

Toda la página está gateada `data-modo-local="bloque"` (solo visible en
modo local — ver "Vista local vs. vista pública" abajo); en vista pública
muestra un aviso breve en vez del contenido completo. Contenido no
sensible en sí mismo — vive en el repo público, igual que
`README.md`/`SOP.md` — pero es de uso exclusivo de Marco, sin interés
para Jefatura/PMO/Gerencia.

Los archivos `.md` en `utilidades/` son la misma información en formato
descargable, de referencia/respaldo — el contenido vivo y completo está en
`utilidades-sistema.html`.

## Vista local vs. vista pública

El mismo `index.html`/`reportes/` se comporta distinto según **dónde se
abre**, sin generar dos sitios ni mantener dos versiones:

- **Local** (`python -m http.server`, `hostname` = `localhost`/
  `127.0.0.1`): vista completa — recuadros de "Recomendación" (notas
  internas de Marco), botones de acción ("Confirmar seguimiento",
  "Redactar correo"), la sección "Utilidades únicas del sistema", y
  algunos encabezados dirigidos a Marco en segunda persona ("Tu
  seguimiento de...", "Tus informes").
- **Pública** (GitHub Pages, cualquier otro dominio): vista resumida —
  solo lo que le sirve a Jefatura/PMO/Gerencia revisando desde afuera:
  estado (semáforo), % de avance, prioridad/criticidad, links de Jira.
  Sin notas internas, sin botones de acción que son tareas de Marco, sin
  la sección de utilidades de mantenimiento.

**Cómo funciona:** `assets/js/modo-vista.js` detecta `location.hostname`
y agrega la clase `modo-local` o `modo-publico` a `<html>` — se carga
**sin `defer`**, lo más arriba posible en `<head>`, para que la clase
exista antes de que el navegador pinte el `<body>` (sin parpadeo). El
CSS (`[data-modo-local]` en `style.css`) oculta por defecto cualquier
elemento marcado y solo lo revela en el modo que corresponde — si el JS
no llega a correr por algún motivo, **gana la vista pública/resumida**
(falla hacia el lado seguro). Los textos personalizados usan el atributo
`data-texto-local="..."`, reemplazados por JS después de que el DOM
carga.

**Para marcar contenido como "solo local":** agregar
`data-modo-local="bloque"` (elementos tipo `<div>`/`<section>`) o
`data-modo-local="boton"` (elementos tipo `<button>`/`<a>` con
`display: inline-flex`) al HTML generado por los scripts (ver
`scripts/reportes_lib.py`, `render_pendiente_item()`, como ejemplo ya
implementado).

## Jerarquía organizacional en "Reportes y seguimientos"

Las tarjetas de persona (`reportes/index.html` y la sección del index
principal) se ordenan por **jerarquía organizacional**, no alfabéticamente:
Gerencia > Jefatura > PMO > Operativo (etiquetas cortas a propósito, para
que el badge no se desborde de la card compacta). Se infiere
automáticamente de palabras clave en `persona_cargo` (`nivel_jerarquico()`
en `scripts/reportes_lib.py`) — no hay que mantener una lista aparte de
nombres. Dentro de un mismo nivel, se ordena por magnitud de atención
descendente (`orden_persona()`).

Una card solo aparece si esa persona tiene al menos un pendiente
registrado en `data/pendientes.json` — el sistema no genera cards para
un "directorio" de contactos sin pendientes reales.

Botón **"Redactar correo a &lt;Persona&gt;"** (junto a "Confirmar
seguimiento" en cada pendiente): a diferencia de ese otro botón — que
siempre le escribe a Marco mismo, como registro — este arma un borrador
dirigido a la persona del pendiente, con la solicitud/recomendación como
cuerpo. El campo "Para" queda **vacío a propósito**: el sistema no
almacena direcciones de correo reales de terceros, así que hay que
completarlo a mano antes de enviar (`redactarCorreo()` en
`assets/js/mailto-consulta.js`).

## Panel consolidado "Mi seguimiento" (index principal)

Barra lateral izquierda colapsable (`<aside class="sidebar-jira">`),
alimentada por `data/jira_snapshot.json` — una foto de mis propios
pendientes abiertos en Jira (`assignee = currentUser() AND statusCategory
!= Done`), tomada vía el conector MCP de Atlassian. Objetivo: que el index
no solo muestre el estado "bonito" de cada programa (`informes.json`),
sino también, de un vistazo, **qué tengo que atender yo** y con qué
urgencia — sin depender de abrir Jira o de revisar la hoja de ruta manual.

Muestra:

- Desglose por prioridad de Jira (Highest/High/Medium/Low/Lowest) y total
  de pendientes abiertos.
- **Radar de urgencia**: los 5 issues con mayor urgencia calculada, usando
  la misma fórmula gravitacional que el módulo de Reportes
  (`F = G·peso/dias²`, ver sección de matemáticas), aplicada aquí al campo
  `vencimiento` de Jira en vez de al `plazo` de un pendiente. Solo entran
  al radar los issues que sí tienen fecha de vencimiento declarada en
  Jira — los que no la tienen quedan fuera del cálculo, no se les asigna
  una urgencia inventada.
- Enlace directo al filtro real de Jira (`filtro_jira_url` en el
  snapshot), para ver el detalle completo sin reconstruir la consulta a
  mano.

**Cómo regenerar el snapshot:** no hay script automatizado (se arma
manualmente vía consulta JQL al conector MCP de Atlassian y se guarda en
`data/jira_snapshot.json` con los campos `key`, `proyecto`, `tipo`,
`resumen`, `estado`, `prioridad`, `vencimiento`, `url` por issue — sin
descripción completa ni comentarios, para no arrastrar contenido sensible
al repo público). Tras actualizar el archivo, correr
`python3 scripts/manage_informes.py build` para que el panel refleje los
datos nuevos. Si el archivo no existe, la sección simplemente no aparece
en el index (no rompe el build).

**Jira vs. `contexto-proyecto/HOJA-RUTA.xlsx`:** la hoja de ruta en Excel
es un documento de trabajo personal, más lento de mantener al día. Jira es
la fuente vigente y se prioriza sobre el Excel cuando hay diferencia entre
ambos — el Excel sirve como referencia complementaria (contexto histórico,
notas por issue), no como fuente de verdad para el panel.

### Comportamiento del sidebar

- El `<aside>` es `position: fixed` — su posición es siempre relativa al
  viewport, nunca se mueve ni se "asienta" al scrollear.
- Vive dentro de un **carril reservado de ancho constante** (variable
  `--sidebar-w: 340px` en `:root`, aplicada como `padding-left` de
  `.main-index`) que no cambia nunca, esté el panel abierto o cerrado. Al
  cerrarlo, el panel solo se desliza fuera de vista dentro de su propio
  carril (`transform: translateX(-100%)`) — `.contenido-central` no tiene
  ninguna regla que dependa del estado del sidebar, así que su ancho es
  siempre el mismo.
- El botón de mostrar/ocultar (`#btn-toggle-sidebar-jira`,
  `.btn-toggle-sidebar-flotante`) vive **fuera** del `<aside>` a
  propósito, para no deslizarse junto con el panel y quedar inalcanzable
  una vez colapsado.
- El estado (mostrado/oculto) se guarda en `localStorage`
  (`sidebarJiraColapsado`) y se aplica con un `<script>` inline que corre
  apenas se genera el `<aside>` (antes de que cargue el resto de la
  página), para evitar el parpadeo de "se ve abierto y se cierra". Sin JS,
  el panel simplemente queda visible siempre (degradación segura).
- Si `data/jira_snapshot.json` todavía no existe, `render_panel_consolidado()`
  devuelve `""` — ni el `<aside>` ni el botón se generan, y el carril
  reservado queda en blanco.
- En pantallas angostas (`max-width: 900px`), `.main-index` deja de
  reservar el carril y el panel pasa a modo overlay puro (se superpone al
  contenido, como un drawer de navegación móvil).
- Esto aplica solo al `index.html` principal (clase `.main-index`); las
  páginas de informe individual y de reportes por persona no cambian.
  `.contenido-central` usa hasta 1520px (descontado el carril del
  sidebar).

## Buscador de la bitácora (Operaciones Diarias)

`informes/operaciones/operaciones-diarias.html` tiene un buscador propio
(en el navegador, sin backend) sobre `data/bitacora_operaciones.json` —
una bitácora con **solo campos estructurados**: `fecha`, `jira_key`,
`proveedor`, `horas`. Deliberadamente **no incluye la descripción de cada
tarea**: ese texto libre trae nombres de personas, detalle de negociación
con proveedores y algún tema de acceso/credenciales — contenido que ya la
disciplina de este repo excluye (ver arriba). Se optó por reducir el
alcance a los campos que sí son seguros de publicar, en vez de sanitizar
el texto libre a mano entrada por entrada.

Dos formas de filtrar, combinables:

- **Calendario** (`<input type="date">`): salta directo a una fecha
  puntual y muestra solo esa fecha.
- **Texto libre**: busca por proveedor o issue de Jira (ej. "Quanto",
  "BMO-333").

El resultado se **agrupa por fecha y, dentro de cada fecha, por
proveedor** (cada fecha corresponde a un único issue de bitácora en
Jira) — no una tabla plana fila por fila. No se muestran horas por
proveedor, solo un contador `×N` cuando el proveedor aparece más de una
vez ese día; el detalle de horas ya vive en los KPIs/gráficos de arriba
de la misma página.

Los datos están embebidos en un `<script type="application/json">` dentro
del HTML (no vía `fetch`, para que funcione igual abierto con
`file://` o servido por GitHub Pages). Actualizar esta bitácora es manual:
no hay subcomando dedicado (a diferencia de `informes/` y `reportes/`, que
sí regeneran solo).

## Páginas con contenido hecho a mano (`"personalizado": true`)

Algunos informes tienen contenido que la plantilla genérica
(`informe_template.html`) no reproduce: KPIs propios, más de un gráfico,
texto narrativo adicional. Ejemplos:

- `informes/operaciones/operaciones-diarias.html` — bitácora de horas, dos
  gráficos (horas por mes y distribución interno/externo) y el buscador
  de la bitácora.
- `informes/core-financiero/migracion-de-core-financiero-forms-14c.html`
  — además del gráfico de fases estándar, agrega un segundo gráfico y
  tabla con el estado del plan de pruebas por módulo (cruzado desde el
  Excel en SharePoint) y bloques de recomendación por segmento. Detalle
  completo y desglose por sub-área (sin publicar) en
  `contexto-proyecto/MIGRACION-14C-PLAN-PRUEBAS.md`.
- `informes/finanzas-internas/correccion-de-discrepancias-en-estimaciones-contables.html`
  — barra de avance en vez de gráfico Chart.js, sección "Frentes de
  trabajo" con una card compacta por tarea, y un diagrama SVG inline de
  los objetos de base de datos involucrados.

Para que `regenerar-paginas` no destruya ese contenido a mano, el informe
correspondiente en `data/informes.json` se marca `"personalizado": true`.
`regenerar_paginas()` en `scripts/manage_informes.py` salta cualquier
informe con esa marca (imprime `[SKIP] <ruta> (personalizado=true, no se
toca)`) y solo regenera el resto. **Editar esos archivos HTML directamente
a mano** — no correr `nuevo` ni depender de `regenerar-paginas` para
actualizarlos.

## Gráficos: tamaño y etiquetas (patrón `chart-box`)

Los gráficos de Chart.js usan `responsive:true` + `maintainAspectRatio:false`
dentro de un contenedor `<div class="chart-box">` de alto fijo (o, en
`informe_template.html`, un alto calculado según la cantidad de fases —
ver `render_informe_html()`). Sin esto, Chart.js calcula un alto
proporcional al ancho del contenedor y en pantallas anchas el gráfico
termina desproporcionadamente grande.

Variantes de `.chart-box` (`assets/css/style.css`):

- `.chart-box` — 220px de alto, hasta 480px de ancho (gráfico "normal").
- `.chart-box.chart-box-ancho` — 200px de alto, ancho completo (para un
  gráfico de barras con varias categorías en el eje X).

Todos los gráficos usan además `chartjs-plugin-datalabels` (CDN) para
mostrar el valor directamente sobre cada barra/sector, sin depender del
hover — más legible en una vista ejecutiva rápida.

## Módulo "Reportes y seguimientos"

Flujo de trabajo:

1. Cuando surge algo que hay que comunicarle a una persona puntual (pedirle
   una gestión, informarle un estado, o solicitar algo sobre un tema
   específico), el memo/documento fuente se guarda en
   `reportes/DD-MM-YYYY/` como bandeja de entrada de trabajo. Esa carpeta
   **no se publica** (ver `.gitignore`: los `.docx`/`.doc` bajo `reportes/`
   quedan excluidos del repo).
2. De ese memo se extrae cada punto como un pendiente y se registra con el
   script — esto crea/actualiza la página de esa persona y el directorio:

```bash
python3 scripts/manage_pendientes.py nuevo \
  --persona-nombre "Cristopher Pérez Ugalde" \
  --persona-cargo "Jefe de TI" \
  --tema "DES-1741 — Migración Core Financiero ABANKS (Forms 14c)" \
  --solicitud "Indicar con quién coordinar la instalación de servidores/componentes de producción y del ambiente Virtualizador de Oracle." \
  --criticidad alta \
  --plazo 2026-09-30 \
  --recomendacion "Se sugiere involucrar al equipo de Infraestructura." \
  --jira-url "https://cafsagroup.atlassian.net/browse/DES-1741" \
  --fecha 2026-08-27
```

Parámetros:

- `--persona-nombre`, `--persona-cargo`, `--tema`, `--solicitud`,
  `--criticidad`: obligatorios. `--criticidad`: `alta` | `media` | `baja`.
- `--plazo`: `YYYY-MM-DD` (opcional). Si se declara, la página calcula en
  cada `build` cuántos días faltan (o pasaron) — es un cálculo hecho al
  momento de generar la página, no un texto fijo que se desactualiza.
- `--recomendacion`: texto libre (opcional) — para sugerir involucrar a
  otro equipo/departamento cuando aplique.
- `--jira-url`: repetible, enlaza directo al issue (requiere login CAFSA).
- `--estado-item`: `pendiente` (default) | `en_atencion` | `resuelto`.
- `--fecha`: `YYYY-MM-DD` (default: hoy).

3. La URL que se comparte con la persona es **evergreen**:
   `reportes/<persona-slug>/index.html`. No cambia entre envíos — todos
   los pendientes que se le registren a futuro se acumulan en esa misma
   página, por eso el link se manda una sola vez y sirve siempre.

Cada pendiente en la página muestra: el tema, la solicitud puntual, el
plazo (si aplica, con el cálculo de días descrito arriba), la recomendación
(si aplica, resaltada), el enlace directo a Jira, y un botón "Confirmar
seguimiento" que abre un correo prellenado hacia `mlopezz@cafsa.fi.cr`
confirmando que la persona está atendiendo ese punto — mismo mecanismo de
confirmación previa que el botón de consulta de `informes/` (nunca se
envía nada sin que la persona lo revise y lo mande ella misma).

### Subcomandos de `manage_pendientes.py`

- `nuevo`: registra un pendiente nuevo (ver arriba).
- `editar --id <id>`: modifica un pendiente existente — `--estado-item`, `--criticidad`, `--solicitud`, `--recomendacion`, `--plazo`, y `--agregar-jira-url` (repetible, solo agrega enlaces nuevos sin duplicar los existentes). Regenera las mismas páginas que `nuevo`. El `id` exacto se busca en `data/pendientes.json`.
- `eliminar --id <id>`: elimina un pendiente por su `id`. Si era el último pendiente de esa persona, avisa que la página `reportes/<persona-slug>/index.html` queda sin enlazar desde ningún índice, pero **no la borra** — queda en disco hasta que se decida a mano si aplica eliminarla.
- `actualizar-persona --persona-slug <slug>`: corrige `persona_nombre`/`persona_cargo` en **todos** los pendientes de esa persona a la vez (evita que el dato quede desalineado entre ítems si tiene más de uno).
- `build`: regenera todas las páginas de `reportes/` + `index.html` principal desde `data/pendientes.json` (útil tras editar el JSON a mano).

## Módulo "Briefs diarios"

`briefs/` es la bandeja de briefs diarios en HTML que Marco genera fuera de
este sistema (correo/Teams/Jira) y deja caer ahí para poder verlos desde un
botón en el `index.html` principal (`assets/js/brief-viewer.js`, un
`<dialog>` con el brief embebido en `<iframe>`). **La carpeta está excluida
de git a propósito** (ver `.gitignore`): los briefs traen correos reales de
colegas y proveedores, detalle de negociación de contratos, montos/facturas
y casos de clientes — contenido que la disciplina de este repo público
excluye (ver arriba). El script y el manifiesto que genera viven
físicamente en el repo, pero nunca se comitean.

Convención de nombre de archivo: `DD-##-MM-YYYY-brief.html` (día,
secuencia del brief dentro de ese día — permite más de uno, p. ej. mañana y
tarde —, mes, año). Ejemplo: `23-01-09-2026-brief.html` = 23 de septiembre
de 2026, brief #1.

```bash
python3 scripts/manage_briefs.py build
```

Escanea `briefs/*.html`, valida cada nombre contra el patrón (los que no
matchean se ignoran con un aviso, no rompen el build), y escribe
`briefs/manifest.json` con la lista completa y cuál es "el más reciente"
(por fecha desc, luego secuencia desc) — el `index.html` público lee este
manifiesto por `fetch()`; si la carpeta no existe (p. ej. en el sitio
publicado en GitHub Pages, donde `briefs/` nunca llega porque está en
`.gitignore`), el `fetch` falla en silencio y el botón del brief
simplemente no aparece.

## Matemáticas usadas en el sistema

El sistema usa un par de fórmulas conocidas como herramientas reales de
cálculo (no solo decoración), más un par de guiños puramente decorativos.
Todas están documentadas en el código y visibles en pantalla:

**Funcionales (alimentan un cálculo real, visible con tooltip en la UI):**

- **Ley de Gravitación Universal** (`F = G·m/r²`) → `urgencia_gravitacional()`
  en `scripts/reportes_lib.py`. Por cada pendiente con plazo: `m` es el peso
  de la criticidad (alta=3, media=2, baja=1), `r` son los días que faltan
  (piso en 1), `G=50` es una constante estilizada elegida por legibilidad
  (no la física real, que daría números ilegibles acá). Se ve en cada
  pendiente ("Urgencia (F=G·m/r²): ...") y define el orden dentro de la
  página de cada persona: a mayor F, más arriba. Misma fórmula reutilizada
  en `urgencia_jira()` (`scripts/manage_informes.py`) para el radar de
  urgencia del panel "Mi seguimiento", con `m` = peso de prioridad de Jira
  (Highest=5 … Lowest=1) y `r` = días hasta `vencimiento` — un solo
  criterio de urgencia para todo el sistema.
- **Teorema de Pitágoras** (`c = √(a²+b²)`) → `magnitud_atencion()` en
  `scripts/reportes_lib.py`. Por persona: `a` = pendientes abiertos, `b` =
  de esos, cuántos son de criticidad alta. Se ve en cada tarjeta de persona
  ("Magnitud de atención (√(a²+b²)): ...") — el efecto de la raíz es que
  la criticidad alta pesa más que lineal en el número final.
- **Entropía** (2ª ley de la termodinámica, usada como metáfora, no como
  cálculo físico real) → `entropia_sistema()` en `scripts/reportes_lib.py`.
  Es el % de pendientes que siguen abiertos sobre el total histórico —
  se ve arriba del directorio en `reportes/index.html`.
- **π, vía suavizado coseno** → `assets/js/color-semaforo.js`. Todo
  porcentaje de avance del sitio (fases de un informe, barra de progreso
  de una card, entropía, y el detalle del plan de pruebas de Forms 14C)
  se muestra con el color del texto en un semáforo continuo: rojo en 0%,
  ámbar en 50%, verde en 100%. La transición no es lineal — usa
  `e(t) = (1 - cos(π·t)) / 2` para que el cambio de color sea más suave
  cerca de los extremos y más marcado a la mitad. Para valores donde "más
  alto" es peor (ej. entropía), se invierte con `data-invertido="true"`.
  Aplicar el semáforo a un número nuevo es tan simple como
  `<span class="pct-semaforo" data-pct="72">72%</span>` — el script se
  encarga solo, no hay que calcular el color a mano.

**Decorativas (no alimentan ningún cálculo, son un guiño):**

- **PI**: la transición `hover` de las tarjetas de persona dura `0.314s`
  (≈ π/10) en vez del `0.15s` genérico de las demás tarjetas — ver
  `.persona-card` en `assets/css/style.css`.
- **Identidad de Euler** (`e^(iπ) + 1 = 0`): aparece como comentario HTML
  en el `<head>` de las 4 plantillas (`templates/*.html`) — visible solo
  al ver el código fuente de la página.

No se forzó una fórmula para cada tema posible (relatividad, Maxwell,
Schrödinger) — solo se usan las que tienen una relación honesta con lo que
hace este sistema.

## Estándares internos de desarrollo

`scripts/common.py` centraliza dos garantías que cualquier script/función
nueva de este proyecto debe seguir usando (no reinventar `open(..., "w")`
ni interpolación cruda de texto en HTML):

- **`guardar_json_atomico(ruta, datos)`**: toda escritura de un archivo de
  datos (`data/informes.json`, `data/pendientes.json`,
  `briefs/manifest.json`) pasa por acá. Escribe primero a un archivo
  temporal en el mismo directorio y solo al final hace `os.replace()`
  (atómico en el mismo filesystem) sobre el destino, para que una
  interrupción a mitad de camino (Ctrl+C, corte de luz, error de disco)
  nunca deje el archivo original truncado o inválido. Usada por
  `guardar_informes()` (`manage_informes.py`), `guardar_pendientes()`
  (`reportes_lib.py`) y `build()` (`manage_briefs.py`).
- **`esc(texto)`**: envoltorio de `html.escape(str(texto), quote=True)`
  (tolera `None`/no-strings). Se usa en **todo** campo de texto plano que
  se interpola en un `render_*()` — título, resumen, categoría, nombre,
  cargo, tema, keys/labels/resúmenes de Jira, nombres de fase — para que
  un `&`/`<`/`>` en el dato de origen (copiado de Jira, de un correo,
  etc.) no genere HTML mal formado. **Excepción deliberada:** `solicitud`
  y `recomendacion` de `data/pendientes.json` llevan HTML enriquecido a
  propósito (`<strong>`, `<ol>`, `<li>` — ver `render_pendiente_item()` en
  `reportes_lib.py`) y **nunca** deben pasar por `esc()`, porque
  destruiría ese formato convirtiendo las etiquetas en texto literal. Si
  se agrega un campo de texto plano nuevo a cualquier `render_*()`, debe
  envolverse en `esc()` salvo que, como esos dos, sea explícitamente un
  campo de HTML enriquecido documentado como tal.
- **Detección de huérfanos**: `manage_informes.py regenerar-paginas`
  compara automáticamente las rutas de `data/informes.json` contra los
  `.html` reales bajo `informes/` y avisa (sin borrar) si encuentra
  alguno sin registro — ver detalle en la sección de `manage_informes.py`
  más arriba.

**Validación de forma (`scripts/modelos.py`):** `data/informes.json` y
`data/pendientes.json` se validan contra dos `dataclasses` (`Informe`,
`Pendiente`), sin dependencias externas — la validación vive en
`__post_init__()` de cada una (campos obligatorios, valores permitidos
de `prioridad`/`cumplimiento`/`estado`/`criticidad`/`estado_item`,
formato de fecha `YYYY-MM-DD`, y que `fases`/`jira_urls`/`subtareas`
sean listas de objetos con las claves esperadas). `cargar_informes()`,
`guardar_informes()`, `cargar_pendientes()` y `guardar_pendientes()`
corren esta validación y, si un registro no calza, detienen la
ejecución con `[ERROR]` señalando el campo y el motivo exacto — en vez
de que el problema aparezca después como HTML mal formado o un
`KeyError` a mitad de un render. El resto del código (`render_*()`,
etc.) sigue trabajando con `dict` normales; las dataclasses se usan
solo como validador en el borde de entrada/salida.

Recomendaciones identificadas pero no implementadas (a evaluar si el
proyecto lo justifica): pruebas automatizadas, estructura de paquete
Python (`src/` + `pyproject.toml`), y linting/type-checking en CI.

## Implementar este sistema en otra computadora

Guía paso a paso para seguir trabajando con este mismo sistema desde una
computadora distinta a la actual (reemplazo de equipo, segunda estación de
trabajo, etc.). Se divide en lo que **sí viaja con git** (el repo público)
y lo que **no viaja** (contenido privado y permisos de cuenta).

### 1. Requisitos previos

- **Git** instalado.
- **Python 3.10 o superior**. No hace falta `pip install` nada ni crear un
  entorno virtual: los 6 scripts bajo `scripts/` solo usan librería
  estándar (`json`, `os`, `re`, `sys`, `html`, `math`, `argparse`,
  `dataclasses`, `datetime`, `pathlib`, `tempfile`, `unicodedata`).
- Un navegador, para revisar el sitio localmente y en producción.
- Cuenta de GitHub con acceso de escritura al repositorio
  `mlopez-cafsa/informes-operaciones-ti`, si desde la computadora nueva se
  va a comitear/publicar (no solo a consultar).
- Si además vas a usar un asistente de Claude (Cowork/Claude Code) para
  operar el sistema (crear informes, refrescar Jira, cerrar el día): las
  skills de este proyecto disponibles en esa sesión —
  `anthropic-skills:actualiza-jira`, `anthropic-skills:actualiza-plan-14c`,
  `anthropic-skills:cierre-dia-mlopezz` — y los conectores descritos en el
  paso 4.

### 2. Clonar el repositorio

```bash
git clone https://github.com/mlopez-cafsa/informes-operaciones-ti.git
cd informes-operaciones-ti
```

Esto trae **todo el contenido público** del sistema: `index.html`,
`utilidades-sistema.html`, `informes/`, `reportes/` (solo lo publicado,
nunca los `.docx` fuente), `data/*.json`, `scripts/`, `templates/`,
`assets/`, `README.md`, `SOP.md`. Por diseño (ver `.gitignore`), **dos
carpetas no viajan con git** y hay que decidir qué hacer con cada una:

- **`contexto-proyecto/`** — memoria/contexto interno del proyecto
  (decisiones, detalle sin curar) y la **hoja de ruta personal**,
  `contexto-proyecto/HOJA-RUTA.xlsx`. No existe ningún mecanismo
  automático para traerla: hay que **copiarla a mano** desde la
  computadora anterior (USB, OneDrive personal, el medio que uses para
  respaldos) a la misma ruta `contexto-proyecto/` en la computadora nueva.
  Sin ella, el sistema funciona igual (nada de `informes/` ni `reportes/`
  depende de esta carpeta en tiempo de build), pero se pierde el
  historial de decisiones y la hoja de ruta deja de reflejar tu estado
  real. **Antes de retomar el trabajo en la computadora nueva, completá
  `contexto-proyecto/HOJA-RUTA.xlsx`** con lo que haya quedado pendiente
  de actualizar — recordá que Jira es la fuente que se prioriza sobre
  este Excel cuando hay diferencia entre ambos (ver "Panel consolidado
  'Mi seguimiento'" más arriba), pero el Excel sigue siendo tu referencia
  de contexto que Jira no guarda.
- **`briefs/`** — briefs diarios en HTML con correos y datos reales de
  proveedores/clientes. Tampoco viaja con git. Si querés seguir usando el
  botón "Brief del día" en la computadora nueva, recreá la carpeta ahí y
  corré `python3 scripts/manage_briefs.py build` para generar su
  manifiesto la primera vez.

### 3. Probar el sitio localmente

```bash
python3 -m http.server 8000
```

Abrí `http://localhost:8000/index.html`. Al estar en `localhost`, el
sitio carga en **vista local** (ver "Vista local vs. vista pública" más
arriba): se ven la sección "Configuración", los botones de acción y el
panel "Mi seguimiento (Jira)".

### 4. Otorgar permisos a Jira y Microsoft 365 (si vas a usar el asistente)

Esto es lo que casi siempre falta al migrar de computadora, porque **no
es un archivo que se copie**: son permisos de tu propia cuenta,
autorizados por separado en cada sesión/dispositivo donde uses el
asistente. Sin ellos, el sitio y los scripts siguen funcionando
igual — lo que deja de funcionar es el *mantenimiento asistido* (refrescar
Jira, cruzar el plan de pruebas, cerrar el día):

- **Jira/Confluence (Atlassian)** — necesario para refrescar
  `data/jira_snapshot.json` (skill `-actualiza-jira`), consultar el estado
  de cualquier issue citado en `informes.json`/`pendientes.json`, y cruzar
  la Epic DES-1741 con el plan de pruebas (skill `-actualiza-plan-14c`).
  La primera vez que el asistente intente una consulta de Jira en la
  computadora nueva, vas a tener que autorizar el conector de Atlassian
  con tu cuenta de `cafsagroup.atlassian.net` (login CAFSA) — acceso de
  lectura como mínimo, y de escritura si además vas a crear/editar issues
  desde ahí.
- **Microsoft 365 (correo, calendario, Teams, SharePoint)** — necesario
  para leer el plan de pruebas Excel en SharePoint, buscar contexto en
  correo/Teams antes de redactar un informe o pendiente, y (si usás
  `-cierre`) armar el cierre de día desde tu calendario y correo reales.
  Hay que autorizar el conector de Microsoft 365 con tu cuenta corporativa
  (`@cafsa.fi.cr`) — permisos típicos: lectura de correo, calendario,
  Teams (chats/canales) y archivos de SharePoint/OneDrive.
- **Read AI** (opcional — solo si usás `-cierre` con resúmenes de
  reuniones grabadas) — conector aparte, autorizalo únicamente si vas a
  seguir usando esa integración desde la computadora nueva.

Ninguno de estos permisos se guarda en este repositorio ni en ningún
archivo del proyecto: viven asociados a tu cuenta en la plataforma de
Claude y se piden la primera vez que una skill o una consulta los
necesita. Si al correr `-actualiza-jira`, `-actualiza-plan-14c` o
`-cierre` el asistente reporta que no tiene acceso a Jira o a M365, es
este paso el que falta completar.

### 5. Publicar y flujo de trabajo posterior

Con el sitio probado localmente y, si aplica, los permisos del paso 4
otorgados, seguí las dos secciones de abajo: "Publicar con GitHub Pages"
(paso único, solo si este repo en particular todavía no está publicado —
si ya lo está, no hay que repetirlo) y "Flujo de trabajo en Visual Studio
Code" (para cada cambio posterior: editar, `git add`/`commit`/`push`).

## Publicar con GitHub Pages (paso manual, una sola vez)

1. En GitHub, entra al repo → **Settings** → **Pages**.
2. En "Build and deployment" → **Source**, selecciona **Deploy from a
   branch**.
3. Selecciona la rama `main` y la carpeta `/ (root)`.
4. Guarda. GitHub publicará el sitio en una URL tipo
   `https://mlopez-cafsa.github.io/informes-operaciones-ti/`.
5. Ese es el link único que se comparte con Gerencia.

## Flujo de trabajo en Visual Studio Code

1. Editar/crear informes localmente (con el script o a mano).
2. Revisar cambios: `git status`.
3. `git add -A`
4. `git commit -m "Agrega informe: <titulo>"`
5. `git push`

> Nota: si `git` reporta un error de `index.lock` ("Unable to create
> .../.git/index.lock: File exists"), significa que quedó un bloqueo de un
> proceso anterior (por ejemplo, el panel de Source Control de VS Code
> ejecutando una operación al mismo tiempo). Cierra cualquier operación de
> git en curso y, si el error persiste sin que haya ningún proceso de git
> activo, borra manualmente el archivo `.git/index.lock`.

## Prompt para retomar el sistema con una IA nueva (otra computadora/cuenta)

Escenario: descargaste/clonaste este repositorio en una computadora nueva
(ver "Implementar este sistema en otra computadora" arriba) y le vas a dar
la ruta a un asistente de IA con acceso a archivos y terminal (Claude,
Cowork, Claude Code, u otro con capacidades equivalentes) para que
**retome el desarrollo y mantenimiento del sistema** — no para que lo
analice desde cero como si fuera código ajeno.

Copiá y pegá el siguiente prompt tal cual, reemplazando únicamente la
ruta entre `< >`:

```
Vas a administrar y dar seguimiento a un sistema ya existente, no a
analizarlo como código nuevo ni a proponer una reestructuración. El
sistema completo está en esta ruta: <RUTA_COMPLETA_AL_REPO>.

Antes de hacer o proponer cualquier cosa, en este orden:

1. Leé completo README.md en la raíz del repo — es la referencia técnica
   de cada script, cada convención y el estado actual del sistema.
2. Leé completo SOP.md — es el procedimiento paso a paso (cuándo y en qué
   orden correr cada operación, con su verificación y su rollback).
3. Si existe la carpeta contexto-proyecto/ (no siempre está — no viaja
   con git, ver README), leé contexto-proyecto/CONTEXTO.md completo: es
   el historial real de decisiones, nombres, hallazgos y contexto sin
   curar de este proyecto. Si no existe, decímelo y seguí sin ella — no
   es un bloqueante, pero no inventes ese contexto si falta.
4. Revisá el estado real del repo antes de asumir nada: `git status`,
   `git log -10 --oneline`, y el contenido actual de cada archivo bajo
   data/*.json (informes.json, pendientes.json, iniciativas.json,
   personas.json, jira_snapshot.json, bitacora_operaciones.json).

Mientras trabajás en este sistema, respetá estrictamente lo ya
documentado en README.md/SOP.md — en particular:

- Nunca edites a mano index.html, reportes/index.html, ni ninguna página
  bajo reportes/<persona>/ — son generados por los scripts. Los cambios
  van en data/*.json, en templates/*.html o en los propios scripts, y
  después corrés el subcomando de regeneración correspondiente.
- Las páginas marcadas "personalizado": true en data/informes.json (hoy:
  Migración Core Financiero Forms 14C, Quanto/Contabilidad BMO-252,
  Operaciones Diarias) se editan directamente a mano — regenerar-paginas
  las salta a propósito, no se tocan con el generador genérico.
- Toda escritura de un data/*.json pasa por guardar_json_atomico()
  (scripts/common.py) y todo campo de texto plano interpolado en HTML
  pasa por esc() — no reinventar ninguna de las dos cosas.
- Este repositorio es público (GitHub Pages) — nunca subas detalle de
  contratos con proveedores, hallazgos de auditoría/SUGEF/CONASSIF,
  credenciales, IPs internas, ni datos personales sensibles. Ver
  "Repositorio público — disciplina de contenido" en README.md antes de
  publicar cualquier contenido nuevo.
- Respetá la separación vista local (Marco) vs. vista pública
  (Jefatura/PMO/Gerencia) documentada en README.md — cualquier contenido
  nuevo de uso interno se marca data-modo-local, no se asume visible para
  todos por default.
- Nunca ejecutes git add/commit/push sin que yo lo pida explícitamente en
  ese momento, aunque el cambio parezca trivial.
- Si te falta información para hacer algo con precisión (un dato, una
  decisión de alcance, un valor de un campo), preguntame de forma puntual
  antes de asumirlo — no lo completes con un supuesto razonable y lo
  aclarés después.
- Distinguí siempre, en lo que me digas, qué es un hecho verificable en
  el sistema/Jira/los datos, y qué es una recomendación u opinión técnica
  tuya.

Mi perfil: soy Ingeniero de Operaciones de TI en CAFSA, con formación en
ingeniería de software; en proceso de formación activa en temas legales y
regulatorios (contratos con proveedores, SUGEF, CONASSIF). Comunicación
directa y sin rodeos, formal pero sencilla, priorizando siempre precisión
sobre velocidad. No me expliques conceptos básicos de programación,
arquitectura o seguridad — sí dame contexto normativo cuando aplique, sin
sobreexplicar lo evidente. Al revisar cualquier contrato con proveedores,
identificá primero cláusulas de riesgo (SLA, penalidades, propiedad de
datos, continuidad del servicio, salida/reversibilidad) antes de comentar
aspectos menores.

Cuando termines de leer lo anterior, decime en pocas líneas en qué estado
encontraste el sistema (última fecha de actualización de cada data/*.json,
qué hay en git status, si contexto-proyecto/ está presente o no) y
preguntame qué querés hacer a continuación — no empieces ningún cambio
todavía.
```

Notas sobre este prompt:

- Es **agnóstico de a qué operación vas a pedirle después** (crear un
  informe, refrescar Jira, revisar un contrato, lo que sea) — su único
  objetivo es que la IA llegue al primer pedido real ya con el contexto
  completo del sistema, en vez de improvisando sobre supuestos.
- Si vas a usar Claude en Cowork/Claude Code y ya tenés las skills de
  este proyecto instaladas ahí (`anthropic-skills:actualiza-jira`,
  `anthropic-skills:actualiza-plan-14c`, `anthropic-skills:cierre-dia-mlopezz`),
  no hace falta mencionarlas en este prompt — se activan solas por
  nombre/frase disparadora cuando las invocás directamente.
- Los permisos de Jira/Microsoft 365 (ver "Implementar este sistema en
  otra computadora" arriba) son independientes de este prompt: ni este
  texto ni ningún archivo del repo los otorga — se autorizan aparte,
  la primera vez que una consulta a esas herramientas los necesite.
