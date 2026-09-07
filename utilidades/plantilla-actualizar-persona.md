# Plantilla — Actualizar el cargo/jerarquía de una persona

> Utilidad descargable del portal Informes Operaciones TI (CAFSA).
> Para cuando cambia el cargo de alguien, o para corregir cómo se
> clasifica su jerarquía en "Reportes y seguimientos" (Gerencia / Jefatura
> / PMO / Operativo). Detalle en `README.md`, sección "Jerarquía
> organizacional"; paso a paso en `SOP.md` (SOP-06).

## ¿Dónde vive esto?

- Se actualiza en `data/pendientes.json` (todos los pendientes de esa
  persona a la vez) — **nunca a mano**, siempre por el comando de abajo.
- El nivel jerárquico (badge de color) no se declara directo: se calcula
  solo, buscando palabras clave dentro del cargo (`nivel_jerarquico()` en
  `scripts/reportes_lib.py`). Ver la tabla de palabras clave más abajo.

## Comando

```bash
python3 scripts/manage_pendientes.py actualizar-persona \
  --persona-slug <slug-tal-como-aparece-en-reportes/> \
  --persona-cargo "Nuevo cargo — Área" \
  --persona-nombre "Nombre Apellido"   # opcional, solo si también cambió el nombre
```

El `--persona-slug` es el que aparece en la URL de su página, ej.
`reportes/maria-cristina-hernandez/index.html` → slug
`maria-cristina-hernandez`.

## Cómo se clasifica el cargo (para escribirlo bien a la primera)

| Si el cargo contiene...                          | Se clasifica como |
|---------------------------------------------------|--------------------|
| "gerente", "gerencia", "director", "dirección"     | **Gerencia**       |
| "jefe", "jefatura"                                 | **Jefatura**       |
| "pmo", "coordinaci..." (coordinación/coordinador)  | **PMO**            |
| cualquier otra cosa                                | **Operativo**      |

La búsqueda ignora tildes y mayúsculas/minúsculas. Si el cargo no debería
caer en "Operativo" por defecto, hay que incluir una de las palabras
clave de la tabla en el texto del cargo.

## Checklist de verificación rápida

- [ ] Corrí el comando y vi el mensaje `[OK] Página actualizada` +
      `[OK] index.html principal actualizado`.
- [ ] Revisé la card de esa persona en el `index.html` principal — el
      badge de jerarquía (Gerencia/Jefatura/PMO/Operativo) es el
      esperado.
- [ ] Si el badge quedó mal clasificado, ajusté el texto del cargo para
      incluir una palabra clave de la tabla (no hay forma de forzar el
      nivel manualmente — es intencional, para que sea consistente).
- [ ] `git add -A` / `commit` / `push` (SOP-01).

## Palabras clave relacionadas

`nivel_jerarquico` · `jerarquía organizacional` · `jerarquia-badge` ·
`orden_persona` · `magnitud de atención` — ver definiciones completas en
`utilidades/glosario-palabras-clave.md`.
