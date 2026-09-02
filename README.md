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

Ejemplo aplicado: al alimentar este portal desde el seguimiento interno de
Jira/Hoja de Ruta, los temas de renegociación o firma de contratos con
proveedores (expedientes, condiciones, plazos comerciales) **no se
publican aquí** — quedan solo en el seguimiento interno. Lo que sí se
publica es el estado ejecutivo del proyecto asociado (ej. "migración de
infraestructura en curso"), sin el detalle contractual de fondo.

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

Si editás `fases` o `jira_urls` a mano en `data/informes.json`, corré
`python3 scripts/manage_informes.py regenerar-paginas` para que las
páginas individuales reflejen el cambio (a diferencia de `build`, que solo
regenera `index.html`).

## Agrupación por programa, no por issue individual

Cada card representa un **programa o iniciativa** (a veces varios issues
de Jira relacionados), no cada issue suelto — así se evita un índice con
decenas de cards diminutas. Ejemplo: "Gestión de riesgo tecnológico y
obsolescencia crítica" agrupa PP-232, PP-233 y PP-229 en una sola card con
tres fases.

La card **"Backlog y mejoras continuas"** agrupa 4 iniciativas de menor
tamaño individual que igual requieren seguimiento activo: BMO-118
(Implementación, Análisis y Estabilización del Framework ETL |
DataWareHouse — la de mayor peso real, headline del resumen), BMO-13
(Facturas y Transferencias), PP-264 (análisis crediticio) y ST-2773
(Acuerdo de Comité). Se corrigió en agosto/2026 porque el resumen anterior
no reflejaba que BMO-118 es la que de verdad necesita continuidad —
regla de fondo: **el resumen de una card agrupada siempre debe encabezar
con el issue de mayor peso real**, no con una descripción genérica del
grupo.

La card **"Gobierno de TI y Cumplimiento (COBIT / CONASSIF)"** agrupa el
clúster GDT-100/106/120/320/107 (gestión de expedientes de proveedores,
cumplimiento COBIT 2019 / CONASSIF 5-24) — separada de "Backlog" porque
tiene entidad propia y GDT-100 está vencido, lo que en la matriz de
semáforo la marca en rojo (ver criterio de semáforo abajo).

## Buscador y orden (index)

El índice tiene un buscador de texto libre (filtra por título, categoría y
resumen, sin distinguir acentos ni mayúsculas) y un selector de orden
(más recientes, prioridad, estado, título). Ambos combinan con los botones
de categoría — los tres filtros aplican a la vez. Todo corre en el
navegador (sin backend), así que no requiere tocar el script para usarse.

## Estructura

```
informes-operaciones-ti/
├── index.html                  # Generado por el script — NO editar a mano
├── README.md                    # Referencia técnica (cómo usar cada script)
├── SOP.md                       # Procedimiento estándar paso a paso (cuándo/en qué orden)
├── robots.txt
├── logos-cafsa/                # Logos originales (fuente, sin optimizar)
├── assets/
│   ├── css/style.css           # Paleta CAFSA (gris oscuro/negro/blanco) + semáforo
│   ├── js/mailto-consulta.js   # Botones de mailto (consulta / confirmar seguimiento / redactar correo)
│   ├── js/color-semaforo.js    # Semáforo de color para % de avance (ver sección de matemáticas)
│   └── img/logos/              # Logos optimizados para web + favicon
├── informes/
│   └── <categoria>/<slug>.html # Un archivo HTML por informe
├── reportes/
│   ├── index.html              # Generado — directorio de personas
│   ├── <persona-slug>/index.html   # Generado — página evergreen de esa persona
│   └── DD-MM-YYYY/             # Bandeja de memos fuente (.docx) — NUNCA se publica
├── data/
│   ├── informes.json           # Fuente de verdad de informes/
│   ├── pendientes.json         # Fuente de verdad de reportes/
│   ├── jira_snapshot.json      # Foto de mis pendientes en Jira (panel "Mi seguimiento")
│   └── bitacora_operaciones.json # Registros estructurados para el buscador de Operaciones Diarias
├── templates/
│   ├── index_template.html            # Plantilla del índice de informes
│   ├── informe_template.html          # Plantilla de un informe nuevo
│   ├── reportes_index_template.html   # Plantilla del directorio de personas
│   └── pendiente_persona_template.html # Plantilla de la página de una persona
└── scripts/
    ├── common.py            # slugify / parse_jira_url — compartido
    ├── reportes_lib.py      # Datos + tarjeta de persona — compartido
    ├── manage_informes.py   # Crea informes y regenera index.html
    └── manage_pendientes.py # Registra pendientes y regenera reportes/ + index.html
```

`index.html` ya no depende solo de `informes.json`: la sección "Reportes y
seguimientos" que se ve arriba del catálogo de informes se arma con los
mismos datos de `pendientes.json` y la misma tarjeta de persona que usa
`reportes/index.html` (ambas viven en `reportes_lib.py`, para que no haya
dos diseños de card divergiendo). Por eso **cualquiera de los dos scripts**
(`manage_informes.py build` o `manage_pendientes.py nuevo`/`build`) deja
`index.html` completo y al día — no hace falta correr ambos a mano.

Cada persona con pendientes aparece en el `index.html` principal con un
badge resumen calculado en cada build (no guardado a mano): "Al día" si no
tiene pendientes abiertos, "En seguimiento" si tiene pendientes abiertos sin criticidad alta, o
"Atención requerida" si tiene alguno de criticidad alta sin atender. Así,
cualquiera con acceso al link principal puede ubicar y abrir directamente
su propia página de seguimiento, con el detalle de cada solicitud y sus
enlaces a Jira.

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
  la card solo muestra la fecha de actualización, igual que antes.
- `--destacado`: si se agrega, el informe aparece primero en el índice.

Después de crear el archivo, edita manualmente el HTML generado en
`informes/<categoria>/<slug>.html` para ajustar el gráfico (Chart.js), los
enlaces de "más detalle" y cualquier contenido adicional.

Si editas `data/informes.json` a mano (por ejemplo, para cambiar el estado
de un informe existente), regenera el índice con:

```bash
python3 scripts/manage_informes.py build
```

## Criterio de semáforo (definido)

El color ya no se elige a mano: se calcula a partir de dos datos que se
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

## Botón "Enviar consulta sobre este informe"

Abre un borrador de correo (`mailto:`) dirigido siempre a
`mlopezz@cafsa.fi.cr`, con el título y resumen del informe como contexto.
No envía nada automáticamente: primero pide confirmación en el navegador, y
luego el usuario revisa y envía desde su propio cliente de correo.

## Jerarquía organizacional en "Reportes y seguimientos" (2026-08-29)

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

Sección al inicio del index principal, alimentada por `data/jira_snapshot.json`
— una foto de mis propios pendientes abiertos en Jira (`assignee =
currentUser() AND statusCategory != Done`), tomada en vivo vía el conector
MCP de Atlassian. Objetivo: que el index no solo muestre el estado
"bonito" de cada programa (`informes.json`), sino también, de un vistazo,
**qué tengo que atender yo** y con qué urgencia — sin depender de abrir
Jira o de revisar la hoja de ruta manual.

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
  snapshot), para ver el detalle completo de los 44 (o los que haya) sin
  reconstruir la consulta a mano.

**Cómo regenerar el snapshot:** no hay script automatizado todavía (se
arma manualmente vía consulta JQL al conector MCP de Atlassian y se guarda
en `data/jira_snapshot.json` con los campos `key`, `proyecto`, `tipo`,
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

## Buscador de la bitácora (Operaciones Diarias)

`informes/operaciones/operaciones-diarias.html` tiene un buscador propio
(en el navegador, sin backend) sobre `data/bitacora_operaciones.json` —
una bitácora de 117 registros de agosto/2026 con **solo campos
estructurados**: `fecha`, `jira_key`, `proveedor`, `horas`. Deliberadamente
**no incluye la descripción de cada tarea**: ese texto libre trae nombres
de personas, detalle de negociación con proveedores y algún tema de
acceso/credenciales — contenido que ya la disciplina de este repo excluye
(ver arriba). Se evaluó explícitamente antes de construirlo y se decidió
reducir el alcance a los campos que sí son seguros de publicar, en vez de
sanitizar el texto libre a mano entrada por entrada.

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
`file://` o servido por GitHub Pages). Actualizar esta bitácora es manual
por ahora: no hay subcomando dedicado (a diferencia de `informes/` y
`reportes/`, que sí regeneran solo). Si se vuelve una tarea frecuente,
vale la pena un script que tome el snapshot de la bitácora interna, filtre
solo esos 4 campos, y reescriba tanto `data/bitacora_operaciones.json`
como el bloque embebido en la página.

## Páginas con contenido hecho a mano (`"personalizado": true`)

Algunos informes tienen contenido que la plantilla genérica
(`informe_template.html`) no reproduce: KPIs propios, más de un gráfico,
texto narrativo adicional. Ejemplos:

- `informes/operaciones/operaciones-diarias.html` — bitácora de horas, dos
  gráficos (horas por mes y distribución interno/externo) y el buscador
  de la bitácora.
- `informes/core-financiero/migracion-de-core-financiero-forms-14c.html`
  — además del gráfico de fases estándar, agrega un segundo gráfico y
  tabla con el estado del plan de pruebas por módulo (503 objetos,
  cruzado desde el Excel en SharePoint) y bloques de recomendación por
  segmento. Detalle completo y desglose por sub-área (sin publicar) en
  `contexto-proyecto/MIGRACION-14C-PLAN-PRUEBAS.md`.

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
termina desproporcionadamente grande (fue el caso original de
"Distribución de la carga interno/externo" en Operaciones Diarias).

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
  Cuando la persona ya resolvió algo, se cambia a mano en
  `data/pendientes.json` y se corre `manage_pendientes.py build`.
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

## Matemáticas usadas en el sistema

A pedido explícito del usuario, el sistema usa un par de fórmulas conocidas
como herramientas reales de cálculo (no solo decoración), más un par de
guiños puramente decorativos. Todas están documentadas en el código y
visibles en pantalla, para que sea fácil ubicarlas:

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
  criterio de urgencia para todo el sistema, no dos fórmulas distintas
  conviviendo.
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
  cerca de los extremos y más marcado a la mitad, en vez de un degradado
  parejo de punta a punta. Para valores donde "más alto" es peor (ej.
  entropía), se invierte con `data-invertido="true"`. Aplicar el
  semáforo a un número nuevo es tan simple como
  `<span class="pct-semaforo" data-pct="72">72%</span>` — el script se
  encarga solo, no hay que calcular el color a mano.

**Decorativas (no alimentan ningún cálculo, son un guiño):**

- **PI**: la transición `hover` de las tarjetas de persona dura `0.314s`
  (≈ π/10) en vez del `0.15s` genérico de las demás tarjetas — ver
  `.persona-card` en `assets/css/style.css`. (π también tiene ahora un
  uso funcional real, ver arriba — este detalle sigue siendo puramente
  decorativo.)
- **Identidad de Euler** (`e^(iπ) + 1 = 0`): aparece como comentario HTML
  en el `<head>` de las 4 plantillas (`templates/*.html`) — visible solo
  al ver el código fuente de la página.

No se forzó una fórmula para cada tema que se mencionó (relatividad,
Maxwell, Schrödinger) — no tenían una relación honesta con lo que hace
este sistema, y forzarlas habría sido decoración vacía en vez de algo
realmente curioso.

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
