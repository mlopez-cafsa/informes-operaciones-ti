/*
 * modo-vista.js
 * =============
 * Diferencia lo que se muestra según dónde corre el sitio (2026-09-07):
 *
 * - localhost / 127.0.0.1 (Marco, corriendo `python -m http.server`)
 *   → vista LOCAL completa: recuadros de "Recomendación" (notas internas
 *     de Marco), botones de acción ("Confirmar seguimiento" / "Redactar
 *     correo"), y textos dirigidos a Marco en segunda persona.
 * - cualquier otro dominio (ej. GitHub Pages, donde entra Jefatura/PMO/
 *   Gerencia a revisar el estado) → vista PÚBLICA resumida: solo lo que
 *   le sirve a quien revisa desde afuera (estado, % de avance, prioridad,
 *   criticidad, links de Jira). Nada de notas ni botones de acción que
 *   son tareas de Marco, no de quien solo está consultando.
 *
 * Mismo HTML, mismo build — nada se genera ni se mantiene dos veces. Ver
 * las reglas `[data-modo-local]` en assets/css/style.css.
 *
 * IMPORTANTE: este script se carga SIN `defer`, lo más arriba posible en
 * <head>, a propósito — la clase en <html> tiene que existir antes de que
 * el navegador empiece a pintar el <body>, para que no haya parpadeo
 * mostrando por una fracción de segundo lo que no corresponde.
 */
(function () {
  var LOCALES = ["localhost", "127.0.0.1", ""];
  window.__modoVista = LOCALES.indexOf(window.location.hostname) !== -1 ? "local" : "publico";
  document.documentElement.classList.add("modo-" + window.__modoVista);

  // Textos personalizados (segunda persona, dirigidos a Marco): a
  // diferencia de la clase de arriba (que evita parpadeo por CSS), acá un
  // parpadeo de una fracción de segundo en un texto no es un problema —
  // no es contenido sensible, es solo tono. Por eso se resuelve en
  // DOMContentLoaded en vez de bloquear el parseo del documento.
  document.addEventListener("DOMContentLoaded", function () {
    if (window.__modoVista !== "local") return;
    document.querySelectorAll("[data-texto-local]").forEach(function (el) {
      el.textContent = el.getAttribute("data-texto-local");
    });
  });
})();
