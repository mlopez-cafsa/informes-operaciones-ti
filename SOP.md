# SOP — Procedimiento Estándar de Operación

## Portal "Informes de Operaciones de TI" (CAFSA)

| Campo | Valor |
|---|---|
| Código | SOP-IOTI-001 |
| Versión | 1.18 |
| Propietario / responsable | Marco Vinicio López Zamora — Ingeniero de Operaciones de TI |
| Fecha de emisión | 2026-08-29 |
| Última revisión | 2026-09-23 |
| Ciclo de revisión sugerido | Cada vez que cambie un procedimiento, o cada 6 meses |
| Documentos relacionados | `README.md` (referencia técnica de scripts y opciones), `contexto-proyecto/CONTEXTO.md` (historial de decisiones e interpretación de contexto, uso interno) |
| Repositorio | `https://github.com/mlopez-cafsa/informes-operaciones-ti` |

Este documento y `README.md` no se duplican a propósito: **README.md** explica *cómo* usar cada script y cada opción (referencia técnica). **Este SOP** define *cuándo*, *en qué orden* y *con qué verificación* se ejecuta cada procedimiento — el "manual de operación" propiamente dicho. `contexto-proyecto/CONTEXTO.md` es aparte: el porqué de cada decisión y el historial, para uso interno.

---

## 1. Propósito y alcance

Estandarizar la operación, el mantenimiento y la extensión del portal "Informes de Operaciones de TI": un sitio estático (sin backend) con dos módulos — **Informes** (estado ejecutivo por programa/proyecto) y **Reportes y seguimientos** (solicitudes puntuales dirigidas a una persona, ordenadas por jerarquía organizacional).

Aplica a cualquier persona que opere este sistema, hoy o en el futuro — el objetivo es que se pueda seguir paso a paso sin depender del historial de conversación de una sesión de Claude en particular.

## 2. Roles y responsabilidades

| Rol | Responsable | Alcance |
|---|---|---|
| Propietario del sistema | Marco Vinicio López Zamora | Única persona que opera el sistema hoy; dueño de toda decisión de contenido |
| Aprobador de contenido publicado | Marco Vinicio López Zamora | Aplica el checklist de sensibilidad (§7) antes de cada publicación |
| Fuente de datos Jira | Conector MCP de Atlassian, cuenta de Cowork de Marco | Snapshot manual (§6.7), sin automatización de refresco continuo |
| Fuente de datos SharePoint | Conector MCP de M365, cuenta de Cowork de Marco | Solo para el plan de pruebas de Migración 14C |

## 3. Glosario

- **Informe**: ficha ejecutiva de un proyecto/programa, dirigida a Gerencia Operativa de TI. Vive en `informes/` + `data/informes.json`.
- **Pendiente**: solicitud puntual dirigida a una persona específica. Vive en `reportes/` + `data/pendientes.json`.
- **`personalizado: true`**: marca en `data/informes.json` que protege una página HTML de ser sobrescrita por `regenerar-paginas` (contenido hecho a mano que no encaja en la plantilla genérica).
- **Jerarquía organizacional**: clasificación automática (Gerencia > Jefatura > PMO > Operativo) de cada persona del módulo Reportes, inferida de `persona_cargo` — no es una lista de nombres mantenida a mano.
- **Semáforo**: color (verde/amarillo/rojo) calculado por la matriz prioridad × cumplimiento — nunca se asigna a mano.
- **% Evaluado / % Aprobado**: en el informe de Migración 14C, cobertura de pruebas vs. aceptación real — ver nota de metodología en `contexto-proyecto/MIGRACION-14C-PLAN-PRUEBAS.md`.

## 4. Prerrequisitos técnicos

- Python 3 (librería estándar únicamente — ningún script requiere `pip install`).
- Git instalado y configurado (usuario/correo), idealmente con VS Code y su panel de Source Control.
- Acceso de escritura al repositorio remoto.
- Solo para los skills de sincronización (§6.7, §6.8): cuenta de Cowork con los conectores de Atlassian (Jira) y M365/SharePoint habilitados.

## 5. Estructura de archivos relevante para este SOP

```
data/informes.json        # Fuente de verdad de informes/
data/pendientes.json       # Fuente de verdad de reportes/
data/jira_snapshot.json    # Foto manual de pendientes de Jira (panel "Mi seguimiento")
scripts/manage_informes.py    # nuevo | build | regenerar-paginas
scripts/manage_pendientes.py  # nuevo | editar | eliminar | actualizar-persona | build
scripts/manage_briefs.py      # build (genera briefs/manifest.json — ver SOP correspondiente)
scripts/reportes_lib.py       # Lógica compartida (jerarquía, fórmulas, render de cards)
utilidades/                   # Plantillas descargables + glosario (ver SOP-13)
```

---

## 6. Procedimientos estándar

Cada procedimiento sigue el mismo formato: **Objetivo**, **Cuándo aplica**, **Pasos**, **Verificación**, **Qué hacer si falla**.

### SOP-01 — Publicar cambios al repositorio remoto

**Objetivo:** reflejar los cambios locales en GitHub.
**Cuándo aplica:** al cierre de cualquier sesión de trabajo sobre el proyecto.

**Pasos:**
1. Abrir una terminal en la carpeta del proyecto (VS Code → Terminal → New Terminal).
2. `git status` — revisar qué cambió antes de mandarlo todo.
3. `git add -A`
4. `git commit -m "<mensaje descriptivo del cambio>"`
5. `git push`

**Verificación:** `git status` debe reportar "nothing to commit, working tree clean" y "up to date with 'origin/main'".

**Qué hacer si falla:**
- `fatal: Unable to create '.../.git/index.lock'` → ver SOP-07-a.
- `! [rejected] ... non-fast-forward` → ver SOP-07-d.

### SOP-02 — Crear un informe nuevo

**Objetivo:** dar de alta un programa/proyecto en el catálogo de Informes.
**Cuándo aplica:** arranca un proyecto nuevo que Gerencia debe poder ver en el index.
**Prerrequisitos:** título, categoría, resumen de una línea, prioridad (`alta`/`media`/`baja`), cumplimiento (`completado`/`bloqueado`/`vencido`/`en_riesgo`/`a_tiempo`/`sin_fecha`).

**Pasos:**
1. `python3 scripts/manage_informes.py nuevo --titulo "..." --categoria "..." --resumen "..." --prioridad alta --cumplimiento en_riesgo --fase "Nombre=NN" --jira-url "https://..."` (ver `--help` para el resto de opciones: `--vencimiento`, `--avance`, `--destacado`).
2. Abrir el HTML generado en `informes/<categoria>/<slug>.html` y completar el detalle (gráfico, enlaces de "más detalle") si aplica.
3. Confirmar visualmente la card nueva en `index.html`.

**Verificación:** el color de semáforo de la card coincide con la matriz prioridad × cumplimiento documentada en `README.md`.

**Rollback:** no existe subcomando "eliminar" para informes — quitar la entrada de `data/informes.json` a mano, borrar el HTML asociado, correr `build`.

### SOP-03 — Editar un informe existente

**Pasos:**
1. Editar los campos que correspondan directamente en `data/informes.json` (`fases`, `resumen`, `vencimiento`, `cumplimiento`, `prioridad`, etc.).
2. Correr `python3 scripts/manage_informes.py build` (regenera solo `index.html`) o `regenerar-paginas` (regenera además cada página individual — respeta `personalizado: true`).

**Advertencia:** nunca editar `index.html` a mano — se pierde en el siguiente `build`. Las páginas con `personalizado: true` sí se editan a mano directamente (no tienen otra vía).

### SOP-04 — Registrar un pendiente nuevo (Reportes y seguimientos)

**Objetivo:** dar de alta una solicitud puntual dirigida a una persona.

**Pasos:**
1. `python3 scripts/manage_pendientes.py nuevo --persona-nombre "..." --persona-cargo "..." --tema "..." --solicitud "..." --criticidad alta [--plazo YYYY-MM-DD] [--recomendacion "..."] [--jira-url "https://..."]`
2. No hace falta ningún paso adicional para la jerarquía: se infiere sola de `--persona-cargo` (ver §3). Usar una palabra clave reconocida ("gerente"/"director", "jefe", "pmo"/"coordinaci") o la persona queda clasificada como "Operativo" por defecto.

**Verificación:** la card de la persona aparece en el orden correcto (por jerarquía, luego por magnitud de atención) tanto en `reportes/index.html` como en la sección "Reportes y seguimientos" del index principal.

### SOP-05 — Editar / resolver / eliminar un pendiente

- Editar: `manage_pendientes.py editar --id <id> [--estado-item ...] [--criticidad ...] [--solicitud ...] [--recomendacion ...] [--plazo ...] [--agregar-jira-url ...]`
- Marcar como resuelto: `--id <id> --estado-item resuelto`.
- Eliminar (irreversible salvo por git): `manage_pendientes.py eliminar --id <id>`.

### SOP-06 — Actualizar nombre/cargo de una persona

`manage_pendientes.py actualizar-persona --persona-slug <slug> --persona-cargo "..." [--persona-nombre "..."]` — propaga el cambio a todos los pendientes de esa persona y **recalcula su jerarquía automáticamente** a partir del nuevo cargo, sin ningún paso manual adicional.

### SOP-07 — Runbook de incidentes de git

**a) `index.lock` huérfano** ("Unable to create .../.git/index.lock: File exists"):
1. Cerrar cualquier operación de git en curso (spinner del panel de Source Control de VS Code, otras terminales, otros clientes de git abiertos sobre esta carpeta).
2. Borrar `.git/index.lock` a mano (Explorador de Windows con "Mostrar elementos ocultos" activado, o `Remove-Item .git\index.lock` en PowerShell).
3. Reintentar la operación de git.

**b) Rama que ya existe localmente** ("fatal: a branch named 'X' already exists"): usar `git checkout X` (sin `-b`) en vez de crearla de nuevo.

**c) "You have divergent branches"** al hacer `pull`: elegir estrategia explícita en vez de dejar que git adivine — `git pull --no-rebase` (fusiona con un commit de merge, más seguro) o, si se puede, evitar el problema desde el inicio creando una rama local dedicada (`git checkout -b <rama>` + `git pull origin <rama>`) en vez de mezclar directo sobre la rama en la que se estaba parado.

**d) Push rechazado por historial divergente** (`! [rejected] ... non-fast-forward`), típicamente al vincular por primera vez un repo local con uno ya creado en GitHub:
1. Confirmar que el remoto no tiene nada que no se pueda perder (ej. solo el README placeholder de creación).
2. `git remote add origin <url>` (si todavía no está vinculado).
3. `git push -u origin main --force` — **solo** tras confirmar el punto 1. Si el remoto sí tiene commits que importan, usar en cambio `git pull origin main --allow-unrelated-histories`, resolver el conflicto (normalmente en `README.md`) y luego `git push` normal.

**Verificación general de cualquier incidente de git:** `git remote -v`, `git log --oneline -5`, `git status`.

### SOP-08 — Ejecutar el skill "-actualiza-jira"

**Cuándo aplica:** hay cambios recientes en Jira (estados, prioridades, fechas de vencimiento, descripciones) que deben reflejarse en el sistema.
**Cómo:** escribir "-actualiza-jira" (o una variante como "actualiza jira", "sincroniza con jira") en el chat con Claude. El runbook completo vive en el skill guardado en la cuenta de Cowork de Marco; resumen de qué toca en `contexto-proyecto/CONTEXTO.md`.
**Nota:** no reescribe el detalle del plan de pruebas de Migración 14C (eso es SOP-09) — coordina con ese skill si detecta cambios en la familia DES-1741.

### SOP-09 — Ejecutar el skill "-actualiza-plan-14c"

**Cuándo aplica:** hay una actualización del plan de pruebas ABANKS 14C en SharePoint que debe reflejarse en el informe público de Migración 14C.
**Cómo:** escribir "-actualiza-plan-14c" (o "actualiza el plan de pruebas") en el chat con Claude.

### SOP-10 — Checklist de verificación previa a publicar

Antes de cerrar cualquier sesión de trabajo sobre este proyecto:

- [ ] `git status` revisado — solo aparecen los archivos que realmente se tocaron.
- [ ] Balance de etiquetas HTML en cualquier archivo editado a mano (ver Anexo A).
- [ ] Las páginas `personalizado: true` siguen intactas — buscar `[SKIP]` en la salida de `regenerar-paginas`, nunca `[OK] Regenerado` para esas rutas.
- [ ] Ningún dato nuevo viola el checklist de sensibilidad (SOP-11).
- [ ] El color de semáforo de cualquier card nueva/editada se calculó solo (prioridad × cumplimiento), no se asignó a mano.
- [ ] Si el cambio agrega contenido que solo le sirve a Marco (una nota interna, un botón de acción), ¿lleva `data-modo-local="bloque"` o `="boton"`? (ver README, "Vista local vs. vista pública"). Si no lleva nada, se muestra en ambos modos por defecto — confirmar que eso es lo que corresponde.

### SOP-11 — Checklist de disciplina de contenido y sensibilidad

Antes de publicar cualquier contenido nuevo en este repositorio (público):

- [ ] ¿Contratos con proveedores, hallazgos de auditoría/SUGEF/CONASSIF, credenciales, IPs internas, o detalle de vulnerabilidades? → **no publicar**.
- [ ] ¿Datos personales sensibles de algún colaborador (salud, orientación, religión, afiliación sindical, datos biométricos o financieros)? → **no publicar**. Un cargo/título profesional y su nivel jerárquico **sí** están permitidos (ver nota sobre la Ley 8968 en `contexto-proyecto/CONTEXTO.md`) — es información profesional, no un dato sensible en el sentido de esa ley.
- [ ] ¿Direcciones de correo reales de terceros? El sistema **deliberadamente no las guarda** (ver botón "Redactar correo" en README) — no agregarlas sin confirmación explícita de la persona dueña del correo.
- [ ] Los enlaces de "más detalle" apuntan siempre a sistemas con su propio control de acceso (Jira, que requiere login CAFSA) — nunca a documentos sensibles alojados directamente en este repo.

### SOP-12 — Activar GitHub Pages (procedimiento único, pendiente al 2026-08-29)

1. En GitHub, ir a **Settings → Pages** del repositorio.
2. **Source**: "Deploy from a branch".
3. **Branch**: `main`, carpeta `/root`.
4. Guardar y esperar el primer deploy (unos minutos).

**Verificación:** la URL pública (`https://mlopez-cafsa.github.io/informes-operaciones-ti/`) carga correctamente el `index.html`.

### SOP-13 — Actualizar el glosario de palabras clave (2026-09-07, ajustado 2026-09-18)

**Objetivo:** que el glosario refleje siempre todos los términos/conceptos
que el proyecto ha ido creando, para que cualquiera (incluido Marco,
semanas después) pueda entender el sistema sin tener que releer el
historial completo de `CONTEXTO.md`.

**Cuándo aplica:** cada vez que se introduce un concepto nuevo en el
sistema — un campo nuevo, una función con nombre propio
(`nivel_jerarquico`, `orden_persona`, etc.), un patrón de diseño nuevo
("degradación elegante"), o una convención nueva (ej. el formato de
nombre de los briefs).

> **Nota (2026-09-18):** desde el rediseño de "Utilidades únicas del
> sistema", el glosario que ve cualquier usuario del sitio es el
> acordeón `.utilidad-glosario` dentro de
> `templates/index_template.html` (agrupado por categoría, `<dl
> class="glosario-lista">`) — ya no se descarga como `.md`.
> `utilidades/glosario-palabras-clave.md` se mantiene como referencia de
> texto plano, pero **hay que actualizar ambos** cuando se agrega un
> término, o van a quedar desincronizados.

**Pasos:**
1. Agregar el término en `templates/index_template.html`, dentro del
   `<div class="glosario-grupo">` que corresponda (crear uno nuevo con su
   propio `<h4>` si ninguno encaja), como un par `<dt>`/`<dd>` con una
   definición corta y en lenguaje simple.
2. Reflejar el mismo término en `utilidades/glosario-palabras-clave.md`
   (referencia de texto plano), en la sección equivalente.
3. Si el término es parte de un módulo todavía en diseño (ej. memoria de
   casos), agregarlo igual, pero dejar explícito que el módulo no está
   implementado — no hay que esperar a construirlo para documentarlo.
4. Correr `python3 scripts/manage_informes.py build` para que
   `index.html` refleje el cambio del template.

**Verificación:** el término aparece en el acordeón del glosario en
`index.html` (abrirlo y confirmar visualmente) y en
`utilidades/glosario-palabras-clave.md`.

**Qué hacer si falla:** si no es obvio en qué categoría va, agregarlo de
todos modos en la más cercana — es preferible un glosario
"un poco desordenado pero completo" a uno prolijo pero incompleto.

### SOP-14 — Dar de alta el desglose de subtareas de una fase (2026-09-18)

**Objetivo:** cuando Marco pide seguimiento "especializado" de una tarea
(que se vea el % real por subtarea, no solo un número agregado), o cuando
una tarea necesita salir de un card genérico a uno propio.

**Pasos:**
1. Verificar en Jira la estructura real con `parent = <CLAVE>` — **nunca**
   asumir relación padre-hijo por cercanía en un snapshot o listado previo
   (ver CONTEXTO.md, sección de errores, el caso BMO-175/BMO-252).
2. Si la tarea va a tener card propio: crear la entrada nueva en
   `data/informes.json` (o mover la fase existente) y quitarla del card de
   origen (fase + `jira_urls` correspondiente), dejando una nota en el
   `resumen` del card de origen sobre dónde quedó.
3. En la fase, agregar `"subtareas": [{"jira_key", "resumen", "estado"}]`
   con el estado **textual exacto** que tiene en Jira (`"Finalizada"`,
   `"Abierta"`, `"Tareas por hacer"`, etc. — el cálculo de avance busca la
   palabra exacta `"Finalizada"`, ver README).
4. Correr `python3 scripts/manage_informes.py regenerar-paginas`.
5. Verificar balance de HTML (Anexo A) y que el % mostrado en la fase
   coincida con el conteo manual de subtareas Finalizadas/total.

**Verificación:** el nuevo `%` de la fase es el resultado de
`avance_de_subtareas()`, no un número puesto a mano — si se edita
`avance` de una fase que ya tiene `subtareas`, ese valor se ignora en el
render (es intencional, ver README).

**Nota (2026-09-18):** si el `nombre` de la fase trae la clave de Jira
entre paréntesis, ese nombre se vuelve automáticamente el hipervínculo al
issue (no hace falta hacer nada extra) y, si TODAS las fases del informe
tienen esa clave, la sección "Más detalle" desaparece sola del HTML
generado — ver README, "Nombre de fase como hipervínculo".

---

## Anexo A — Verificación de balance de etiquetas HTML

Para cualquier archivo HTML editado a mano (páginas `personalizado: true`), correr esto antes de publicar:

```bash
python3 - << 'EOF'
import re
archivo = "informes/core-financiero/migracion-de-core-financiero-forms-14c.html"  # ajustar
html = open(archivo, encoding="utf-8").read()
for tag in ["div", "span", "p", "a", "button", "article", "ul", "ol", "li"]:
    abiertas = len(re.findall(rf"<{tag}[ >]", html))
    cerradas = len(re.findall(rf"</{tag}>", html))
    estado = "OK" if abiertas == cerradas else "MISMATCH"
    print(tag, abiertas, cerradas, estado)
EOF
```

## Registro de cambios de este SOP

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 2026-08-29 | Versión inicial — cubre publicación en git, alta/edición de informes y pendientes, jerarquía organizacional, runbook de incidentes de git, checklists de verificación y sensibilidad, y activación de GitHub Pages. |
| 1.1 | 2026-09-07 | Agregado SOP-13 (mantener el glosario de palabras clave en `utilidades/`, sección de "Utilidades únicas del sistema"). |
| 1.2 | 2026-09-07 | Agregado ítem en SOP-10 sobre marcar contenido "solo local" con `data-modo-local` (ver README, "Vista local vs. vista pública"). |
| 1.3 | 2026-09-18 | Agregado SOP-14 (desglose de subtareas por fase y separación de cards para seguimiento especializado). |
| 1.4 | 2026-09-18 | Se quitaron los cards "Backlog y mejoras continuas", "Modernización comercial - Cotizador y Vista 360 de Cliente" y "Gestión de riesgo tecnológico y obsolescencia crítica" (a pedido). Nombre de fase como hipervínculo directo a Jira + remoción automática de "Más detalle" cuando aplica (SOP-14). PP-232 y PP-233 pasaron de un card combinado a dos cards independientes. |
| 1.5 | 2026-09-18 | Layout de dos columnas en el index principal: "Mi seguimiento (Jira)" pasó a sidebar izquierdo colapsable (`.sidebar-jira`, botón + `localStorage`); "Tu seguimiento de personas, Marco" y "Tus informes" quedaron en la columna central (`.contenido-central`). "Utilidades únicas del sistema" dejó de descargar `.md` crudo: ahora es un acordeón (`<details>`) legible directo en la página, en lenguaje simple, con el comando técnico al final de cada uno. SOP-13 ajustado para reflejar las dos copias del glosario (template + `.md` de referencia). |
| 1.6 | 2026-09-18 | Rediseño del sidebar "Mi seguimiento (Jira)" (feedback de Marco sobre la v1.5): pasó de `position: sticky` + flexbox a `position: fixed` dentro de un carril reservado de ancho constante (`--sidebar-w`), para que el contenido central nunca cambie de ancho al mostrar/ocultar el panel y para que no "baje" al hacer scroll. Botón de mostrar/ocultar movido fuera del `<aside>` (no se desliza con el panel). Contenido central ampliado a hasta 1520px (antes 1320px). |
| 1.7 | 2026-09-18 | Rediseño visual de todo el sitio (a pedido de Marco): color de acento (`--accent`, azul) agregado para links/hover/foco/barra de avance, sin tocar el semáforo de estado; radio de borde ampliado (6px→10px) y sombras "en capas" más suaves en todas las cards; iconografía SVG inline (sin dependencias externas) en encabezados de sección, botones principales (correo, confirmar, Jira, ver más) y estado vacío — set compartido en `scripts/common.py` (`icono()`/`icono_seccion()`/`icono_flecha()`/`ICONO_*`); más aire entre secciones (`separador-seccion` 32px→44px); microinteracciones sutiles (flecha que se desliza al hover, botones con leve elevación). Aplicado a las 4 plantillas generadas y replicado a mano en las 2 páginas `personalizado:true` (Forms 14C, Operaciones Diarias). |
| 1.8 | 2026-09-18 | Color de acento cambiado de azul a verde musgo oscuro (`--accent: #556b2f`, a pedido de Marco — "un color neutral, verde musgo oscuro"). Cambio aislado a las 4 variables `--accent*` y `--focus-ring` en `:root`; ningún otro archivo tocado, porque todo el uso del acento pasa por esas variables. Deliberadamente más oscuro/apagado (oliva) que `--status-green` (#2e7d32) para no confundirse con el semáforo "aprobado/a tiempo" al verse uno junto al otro. |
| 1.9 | 2026-09-23 | A pedido de Marco ("no me agrada del verde" en títulos/íconos): los íconos de encabezado de sección y todo `.icono-flecha` pasaron de color acento a `--cafsa-gray` (neutro, estandarizado — mismo gris ya usado en el resto del sitio). Los títulos que además son link (`.informe-card h3 a`, `.persona-card h3 a`) se fuerzan a `--cafsa-black` en vez de heredar el acento del selector `a` global — un título no debe leerse como un link de color. El acento (`--accent`) sigue vivo en botones/hover/barra de avance/borde del header, que no fueron parte del pedido. |
| 1.10 | 2026-09-23 | Buscador de "Tus informes" rehecho para ser flexible/aproximado (a pedido de Marco). `render_card()` en `manage_informes.py` ahora genera 3 capas de índice por card: `data-busqueda` (lo visible: título, resumen, categoría, estado y prioridad en palabras), `data-extra` (nombres de fase — texto real pero no impreso en la card) y `data-referencias` (JSON con cada ticket Jira del informe y cada subtarea: key + resumen + URL). En el front-end (`index_template.html`), la búsqueda se parte en tokens (AND entre palabras, sin importar el orden) y cada token se acepta por substring exacto o por distancia de edición ≤1/≤2 (typos). Si una card coincide solo por una referencia Jira no visible, se muestra una pista bajo el resumen ("Coincide con: BMO-155 — ...") con link directo a Jira (`.coincidencia-busqueda` en `style.css`). Con búsqueda activa, los resultados se reordenan por relevancia (más peso si el match está en el título/resumen que si viene de una referencia); sin búsqueda, manda el selector "Ordenar por" de siempre. |
| 1.11 | 2026-09-23 | Barra de avance de "Tus informes" (`.progreso-relleno`) pasó de un color fijo (acento) a un semáforo por porcentaje, en tono claro (a pedido de Marco: "tonalidad más clara y sensible"). `assets/js/color-semaforo.js` ganó `colorSemaforoRGB()` (refactor: extrae la interpolación rojo→ámbar→verde que ya usaba `colorSemaforoPct()`), `colorSemaforoPctSuave(pct, invertido, mezclaBlanco)` (mezcla ese RGB con blanco — 0.55 por defecto) e `initProgresoSemaforo()`, que colorea cada `.progreso-relleno[data-pct]` con un degradado de dos tonos claros (mezclaBlanco 0.72 → 0.4) del color correspondiente al %. `render_progreso()` en `manage_informes.py` agrega `data-pct` al div de relleno (antes solo tenía el `width` inline). El degradado fijo anterior en CSS queda como respaldo si el JS no carga (el `style` inline que pone la función tiene más especificidad). Deliberadamente más pálido que los badges de estado (`--status-rojo/ambar/verde`) para no competir visualmente con el semáforo "oficial" del estado del informe — mismo criterio que ya se aplicó al elegir el acento verde musgo (v1.8). |
| 1.12 | 2026-09-23 | Nuevo campo `orden_atencion` (entero 1..8) en cada informe de `data/informes.json`, declarado a mano por Marco como el orden de prioridad de atención real (distinto de `prioridad` alta/media/baja, que alimenta el semáforo, y explícitamente distinto del Radar de urgencia del sidebar — ese sigue siendo automático por fecha de vencimiento en Jira, sin cambios). Orden pedido: Forms 14C (1), Quanto BMO-252 (2), GAUDI PP-233 (3), Gobierno de TI (4), Infraestructura /gx (5), PEL Admin PHP PP-232 (6), Framework ETL (7), Operaciones Diarias (8). `render_card()` agrega `data-orden-atencion`; `build_index()` ahora genera el HTML del grid ordenado por ese campo (antes seguía el orden de guardado del JSON, ordenado por fecha/destacado). En el front-end, nueva opción "Prioridad de atención" en el selector "Ordenar por" (`index_template.html`), puesta como **valor por defecto** (antes el default era "Más recientes"); la opción vieja se renombró a "Prioridad (alta/media/baja)" para no confundirla. `aplicarOrden()` suma el criterio `atencion`, ordenando por `data-orden-atencion` ascendente (informes sin el campo se van al final, peso 999). |
| 1.14 | 2026-09-23 | Informe BMO-252 (Quanto - Contabilidad) actualizado con datos reales de Jira (Marco actualizó estado de épica/tareas/subtareas antes de pedir el refresh) y rediseñado para "visualización de contexto" en vez de texto corrido. `data/informes.json`: subtareas BMO-254/255/256/257/258 pasaron de "Abierta" a "Finalizada" (solo BMO-253 sigue abierta, bloqueada por BMO-260 y BMO-361) → avance real 83% (5/6); `personalizado: true` agregado; `resumen` y `fecha` actualizados. `informes/finanzas-internas/correccion-de-discrepancias-en-estimaciones-contables.html` reescrito a mano: reemplaza Chart.js por la barra `.progreso-barra`/`.progreso-relleno` ya existente (data-pct="83"), agrega sección "Frentes de trabajo" con una card compacta por tarea (`.frentes-grid`/`.frente-card`, nuevas en `style.css`) en vez de párrafos largos, y agrega un diagrama SVG inline de los 5 objetos de base de datos documentados en BMO-258 (2 vistas, 1 función, 1 paquete de caché, 1 catálogo) con sus relaciones (`.diagrama-bd-wrap`/`.diagrama-leyenda`, nuevas en `style.css`) — construido a partir de los comentarios técnicos reales de ese ticket, no inventado. |
| 1.15 | 2026-09-23 | Informe Forms 14C actualizado al corte del nuevo Excel de plan de pruebas (`contexto-proyecto/23092026-2026 - PLAN DE PRUEBAS MIGRACIÓN 14C - CAFSA - BESTR.xlsx`, 5 días después del corte anterior): migración del proveedor 90%→95%, aprobación real 51.4%→67.3% (+15.9 puntos, el ritmo más rápido del proyecto). `data/informes.json`: fase "Migración y pruebas de módulos/objetos Abanks" 51→67 (medición real, no estimación); `resumen`/`fecha` actualizados. `migracion-de-core-financiero-forms-14c.html`: KPIs, gráficos y tabla por módulo recalculados desde cero con los números nuevos (Total/Pendiente/En proceso/Aprobado/Rechazado por módulo); "Recomendaciones por segmento" reescritas — GENERALES se destrabó (3.7%→53.2%) pero ahora concentra 22 de los 41 rechazos del proyecto, BRANCH pasó a ser el módulo sin ningún movimiento (nuevo riesgo #1), y se señalan rechazos nuevos en BANCOS y COLOCACIÓN pese al buen avance. Se consultó también DES-1743 en Jira (a pedido de Marco, para documentar la migración por módulo desde ahí): el ticket no tiene subtareas, descripción ni adjuntos con detalle por objeto — solo un checklist genérico y fecha límite — así que el desglose sigue viniendo únicamente del Excel; se dejó nota explícita de este hallazgo en "Recomendaciones transversales" en vez de omitirlo. |
| 1.16 | 2026-09-23 | Quitado el bloque "No hay informes que coincidan con la búsqueda o el filtro seleccionado." de "Tus informes" (a pedido de Marco). Eliminados de `index_template.html`: el `<p class="sin-resultados" id="sin-resultados">` (con su ícono SVG), la constante JS `sinResultados` y las 2 líneas que la usaban en `aplicarFiltros()`. Eliminadas de `style.css` las reglas `.sin-resultados`/`.sin-resultados .icono-vacio`, que quedaban huérfanas. El contador "N de M informes" (`#contador-visibles`) sigue funcionando igual; ahora, si un filtro/búsqueda no encuentra nada, el grid simplemente queda vacío sin mensaje. |
| 1.18 | 2026-09-23 | Puesta al día de la documentación (a pedido de Marco, tras la auditoría v1.17): `README.md` ganó las secciones que faltaban desde hacía varias versiones — subcomandos de `manage_informes.py` (`build`/`regenerar-paginas`, con la nueva detección de huérfanos), subcomandos de `manage_pendientes.py` (`editar`/`eliminar`/`actualizar-persona`, no documentados antes), un módulo nuevo "Briefs diarios" describiendo `manage_briefs.py build` y la carpeta `briefs/`, y "Estándares internos de desarrollo" explicando `esc()`/`guardar_json_atomico()`/detección de huérfanos como convención a seguir en cualquier código nuevo. El árbol de `Estructura` se actualizó para incluir `briefs/` y `manage_briefs.py`. `contexto-proyecto/CONTEXTO.md` ganó una sección nueva **§1.1 "Estado actual del sistema"** con el snapshot vigente de los 8 informes y 2 pendientes activos, marcando explícitamente que §4 (fechada 2026-08-27) quedó como registro histórico y ya no representa el catálogo actual — evita que alguien retomando el proyecto confunda una foto vieja con el estado real. |
| 1.17 | 2026-09-23 | Auditoría integral del sistema (a pedido de Marco: "recorre todo el sistema, audita y aplica mejoras arquitectónicas y estándares generales"). Cuatro mejoras concretas, sin tocar diseño ni contenido: **(1) Limpieza de huérfanos** — eliminadas 4 páginas `.html` en `informes/` sin registro en `data/informes.json` (proyectos ya retirados de las cards en versiones anteriores, cuyo archivo nunca se borró), y las 2 carpetas que quedaron vacías. `logos-cafsa/` se tocó por error durante esta limpieza (parecía un duplicado de `assets/img/logos/`) y se restauró de inmediato vía `git checkout` al confirmar en `README.md`/`CONTEXTO.md` que es la carpeta de logos fuente sin optimizar, deliberada — no hubo pérdida de datos. **(2) Escritura atómica de JSON** — nueva función `guardar_json_atomico()` en `scripts/common.py` (escribe a un temporal en el mismo directorio y solo al final hace `os.replace()`); adoptada por `guardar_informes()`, `guardar_pendientes()` y el manifiesto de `manage_briefs.py`. Antes, una interrupción a mitad de escritura (Ctrl+C, corte de luz) podía dejar `data/informes.json` o `data/pendientes.json` truncado e inválido; ahora el archivo original queda intacto si algo falla a mitad de camino. **(3) Escapado HTML centralizado** — nueva función `esc()` en `common.py` (envoltorio de `html.escape`), aplicada a todos los campos de texto plano interpolados en HTML (título, resumen, categoría, nombre, cargo, tema, labels/keys de Jira, nombres de fase, filtros, radar de urgencia) en `manage_informes.py`, `reportes_lib.py` y `manage_pendientes.py`. Deliberadamente NO aplicada a `solicitud`/`recomendacion` de `data/pendientes.json`, que llevan HTML enriquecido a propósito (`<strong>`, `<ol>`, `<li>` — ver `render_pendiente_item()`); escaparlos destruiría ese formato. Sin este cambio, un título o nombre futuro con `&`/`<`/`>` (copiado de Jira o de un correo) habría generado HTML mal formado — nunca pasó porque nadie lo puso todavía, no porque el código lo impidiera. **(4) Detección de páginas huérfanas** — `regenerar-paginas` ahora compara, al final de cada corrida, las rutas de `data/informes.json` contra los `.html` reales bajo `informes/` y avisa (no borra) si aparece un huérfano nuevo, para que el hallazgo del punto (1) no se repita en silencio. Verificación tras los 4 cambios: balance de etiquetas HTML (12 páginas, 0 errores), balance de llaves en `style.css` (0 errores), `node --check` en todos los `<script>` inline (0 errores; un falso positivo inicial en el bloque `<script type="application/json">` de Operaciones Diarias, descartado por no ser JS ejecutable) y regeneración completa del sitio sin fallos. Fuera de alcance, quedan como recomendación para decisión futura de Marco: pruebas automatizadas, estructura de paquete Python (`src/` + `pyproject.toml`), linting/type-checking en CI, y validación de esquema para los JSON de datos. |
