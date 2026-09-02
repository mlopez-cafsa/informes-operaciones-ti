# SOP — Procedimiento Estándar de Operación

## Portal "Informes de Operaciones de TI" (CAFSA)

| Campo | Valor |
|---|---|
| Código | SOP-IOTI-001 |
| Versión | 1.0 |
| Propietario / responsable | Marco Vinicio López Zamora — Ingeniero de Operaciones de TI |
| Fecha de emisión | 2026-08-29 |
| Última revisión | 2026-08-29 |
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
scripts/reportes_lib.py       # Lógica compartida (jerarquía, fórmulas, render de cards)
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
