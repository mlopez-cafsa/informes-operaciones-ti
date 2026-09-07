# Plantilla — Registrar un brief diario

> Utilidad descargable del portal Informes Operaciones TI (CAFSA).
> **Importante:** esta plantilla describe un flujo **estrictamente
> local** — nunca se publica en el sitio público. Ver la nota de
> seguridad completa en `CONTEXTO.md` (entrada del 2026-09-07).

## ¿Dónde vive esto?

- **Carpeta:** `briefs/` en la raíz del proyecto — **gitignored siempre**,
  nunca se comitea, sin excepción, mientras traiga correos reales,
  detalle de contratos o datos de casos de cliente.
- **Manifiesto:** `briefs/manifest.json`, generado por
  `python3 scripts/manage_briefs.py build` (también gitignored).
- **Visor:** botón "Brief de hoy" en el header del `index.html` local —
  no aparece en el sitio publicado en GitHub Pages (el manifiesto nunca
  se sube, así que el botón se queda oculto ahí).

## Convención de nombre de archivo (obligatoria)

```
DD-##-MM-YYYY-brief.html
```

- `DD` — día del mes (2 dígitos)
- `##` — secuencia del brief dentro del mismo día (2 dígitos, empieza en
  `01`; permite más de uno por día)
- `MM` — mes (2 dígitos)
- `YYYY` — año (4 dígitos)

Ejemplo: `07-01-09-2026-brief.html` = 7 de septiembre de 2026, brief #1.

Un archivo que no siga este patrón exacto se ignora al generar el
manifiesto (con aviso en la terminal) — no se "adivina" la fecha.

## Pasos

1. Colocar el archivo `.html` del brief dentro de `briefs/`, con el
   nombre en el formato de arriba.
2. Correr:
   ```bash
   python3 scripts/manage_briefs.py build
   ```
3. Abrir (o refrescar) `index.html` localmente — el botón "Brief de hoy"
   debería aparecer/actualizarse solo.

## Checklist de verificación rápida

- [ ] El nombre del archivo sigue exactamente `DD-##-MM-YYYY-brief.html`.
- [ ] Corrí `manage_briefs.py build` y el mensaje dice `[OK]` con el
      archivo correcto como "más reciente".
- [ ] **Antes de cualquier `git status`/`git add`:** confirmé que
      `briefs/` sigue apareciendo como no trackeada (`git status --short
      briefs/` → `?? briefs/` o nada). Si alguna vez aparece de otra
      forma, **detenerse y no hacer push** — revisar `.gitignore`.
- [ ] No se copia contenido de un brief hacia ningún archivo que sí se
      publique (`data/*.json`, `informes/`, `reportes/`) sin antes
      resumirlo/curarlo según la disciplina de contenido (SOP-11).

## Palabras clave relacionadas

`brief` · `manifest` · `degradación elegante` · `gitignored` ·
`disciplina de contenido` — ver definiciones completas en
`utilidades/glosario-palabras-clave.md`.
