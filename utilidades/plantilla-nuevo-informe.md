# Plantilla — Registrar un informe nuevo

> Utilidad descargable del portal Informes Operaciones TI (CAFSA).
> Guía rápida de "qué necesito a mano y qué comando corro" antes de crear
> un informe nuevo en `informes/`. Detalle completo de cada flag en
> `README.md`; el paso a paso de publicación (git add/commit/push) está
> en `SOP.md` (SOP-02).

## ¿Dónde vive esto?

- **Fuente de verdad:** `data/informes.json` (no se edita a mano — lo
  escribe el script).
- **Página generada:** `informes/<categoria>/<slug>.html`.
- **Índice generado:** `index.html` (se actualiza solo al correr el
  comando de abajo).
- **Comando:** `python3 scripts/manage_informes.py nuevo [flags]`

## Datos que necesitás tener listos antes de correr el comando

Completá este bloque con tus propios datos (podés copiarlo a un borrador
de texto/correo y llenarlo antes de abrir la terminal):

```
Título:                ____________________________________________
Categoría:              ____________________________________________
Resumen (1-2 líneas):   ____________________________________________
Prioridad:              [ ] alta   [ ] media   [ ] baja
Cumplimiento:           [ ] completado  [ ] bloqueado  [ ] vencido
                        [ ] en_riesgo   [ ] a_tiempo    [ ] sin_fecha
Estado (semáforo):      [ ] verde (a tiempo)  [ ] amarillo (en riesgo)
                        [ ] rojo (atrasado)   [ ] neutral (sin definir)
% de avance (opcional): _______
Subtareas completadas/total (opcional): _____ / _____
Fase(s) (opcional, formato 'Nombre=NN', repetible): ________________
Link(s) de Jira (opcional, repetible):  ___________________________
Fecha de vencimiento (opcional, YYYY-MM-DD): _______________________
¿Destacado en el índice?  [ ] Sí  [ ] No
```

## Comando (ejemplo con los flags más comunes)

```bash
python3 scripts/manage_informes.py nuevo \
  --titulo "Título del informe" \
  --categoria "Categoría" \
  --resumen "Resumen ejecutivo en 1-2 líneas." \
  --prioridad alta \
  --cumplimiento en_riesgo \
  --estado amarillo \
  --avance 40 \
  --jira-url "https://cafsa.atlassian.net/browse/XXX-000" \
  --vencimiento 2026-12-31
```

`--jira-url` y `--fase` se pueden repetir varias veces si hay más de un
link o fase. Si no se pasa `--fecha`, se usa la fecha de hoy.

## Checklist de verificación rápida (después de correr el comando)

- [ ] El mensaje de la terminal dice `[OK] Informe creado` (o similar) sin
      errores.
- [ ] Abrí `index.html` localmente y el informe nuevo aparece en el
      catálogo, con el semáforo/prioridad correctos.
- [ ] Si el informe necesita contenido adicional (tabla, gráfico), lo
      agregué directo en `informes/<categoria>/<slug>.html` — pero ojo:
      si ese archivo se vuelve a regenerar (`regenerar-paginas`), un
      contenido a mano se pierde salvo que el informe tenga
      `"personalizado": true` en `data/informes.json` (ver README).
- [ ] Antes de publicar: repasar SOP-11 (disciplina de contenido) — nada
      de contratos, hallazgos de auditoría, credenciales, IPs internas.
- [ ] `git add -A` / `commit` / `push` (SOP-01).

## Palabras clave relacionadas

`informe` · `semáforo` · `prioridad` · `cumplimiento` · `personalizado` ·
`vencimiento` · `destacado` — ver definiciones completas en
`utilidades/glosario-palabras-clave.md`.
