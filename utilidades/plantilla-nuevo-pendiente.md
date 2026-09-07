# Plantilla — Registrar un pendiente nuevo (Reportes y seguimientos)

> Utilidad descargable del portal Informes Operaciones TI (CAFSA).
> Guía rápida para registrar una solicitud/pendiente dirigido a una
> persona específica. Detalle completo en `README.md`; paso a paso de
> publicación en `SOP.md` (SOP-04).

## ¿Dónde vive esto?

- **Fuente de verdad:** `data/pendientes.json` (no se edita a mano).
- **Página de la persona:** `reportes/<persona-slug>/index.html`
  (evergreen — acumula todos sus pendientes en el tiempo).
- **Directorio de personas:** `reportes/index.html`.
- **También aparece en:** `index.html` principal, sección "Reportes y
  seguimientos", ordenado por jerarquía organizacional (ver glosario).
- **Comando:** `python3 scripts/manage_pendientes.py nuevo [flags]`

## Datos que necesitás tener listos

```
Persona (nombre completo):     ________________________________________
Cargo de la persona:           ________________________________________
                                (usado para clasificar jerarquía — ver
                                glosario: Gerencia/Jefatura/PMO/Operativo)
Tema:                           ________________________________________
Solicitud (texto, puede llevar
  <ul>/<ol>/<li>/<br>/<p>):     ________________________________________
Criticidad:                    [ ] alta  [ ] media  [ ] baja
Plazo (opcional, YYYY-MM-DD):  ________________________________________
Recomendación (opcional):      ________________________________________
Link(s) de Jira (opcional,
  repetible):                  ________________________________________
Estado del ítem:               [ ] pendiente  [ ] en_atencion  [ ] resuelto
```

## Comando

```bash
python3 scripts/manage_pendientes.py nuevo \
  --persona-nombre "Nombre Apellido" \
  --persona-cargo "Cargo — Área" \
  --tema "Tema breve" \
  --solicitud "Descripción de la solicitud." \
  --criticidad media \
  --plazo 2026-12-31 \
  --jira-url "https://cafsa.atlassian.net/browse/XXX-000"
```

## Editar o cerrar un pendiente existente

```bash
# Editar (necesitás el --id exacto, visible en data/pendientes.json):
python3 scripts/manage_pendientes.py editar --id <id> --estado-item resuelto

# Actualizar nombre/cargo de una persona en todos sus pendientes:
python3 scripts/manage_pendientes.py actualizar-persona \
  --persona-slug <slug> --persona-cargo "Nuevo cargo"

# Eliminar (definitivo — no hay deshacer, ver SOP.md):
python3 scripts/manage_pendientes.py eliminar --id <id>
```

## Checklist de verificación rápida

- [ ] Corrí `python3 scripts/manage_pendientes.py build` (o el `nuevo`/
      `editar` ya lo hizo solo) y confirmé el mensaje `[OK]`.
- [ ] Revisé la página de la persona (`reportes/<slug>/index.html`) y el
      `index.html` principal — el pendiente aparece con la criticidad y
      el badge de jerarquía correctos.
- [ ] Si el cargo de la persona cambió, corrí `actualizar-persona` en vez
      de editar el JSON a mano.
- [ ] **No inventé ninguna dirección de correo real** — el botón
      "Redactar correo" siempre deja el campo "Para" vacío a propósito
      (ver glosario: `redactarCorreo`).
- [ ] `git add -A` / `commit` / `push` (SOP-01).

## Palabras clave relacionadas

`pendiente` · `criticidad` · `plazo` · `jerarquía organizacional` ·
`magnitud de atención` · `redactarCorreo` · `texto_plano` — ver
definiciones completas en `utilidades/glosario-palabras-clave.md`.
