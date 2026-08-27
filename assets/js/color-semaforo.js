/**
 * color-semaforo.js
 * ==================
 * Semáforo de color para porcentajes de avance (0% a 100%), mostrado en
 * el color del TEXTO del número — no en un badge ni en el fondo.
 *
 * Fórmula: interpola rojo -> ámbar -> verde (los mismos tonos que ya usa
 * el sitio para estado-rojo/amarillo/verde) usando un suavizado coseno:
 *
 *   e(t) = (1 - cos(π · t)) / 2      con t = pct / 100
 *
 * En vez de una interpolación lineal (que cambia de color al mismo ritmo
 * de punta a punta), esta curva "en S" cambia más despacio cerca de 0% y
 * de 100%, y más rápido cerca del 50% — el mismo guiño a π que ya usa
 * `.persona-card` en su transición de hover (0.314s), ahora aplicado a
 * un cálculo real en vez de un detalle decorativo.
 *
 * Uso en HTML (coloreado automático al cargar la página):
 *   <span class="pct-semaforo" data-pct="72">72%</span>
 *
 * Para porcentajes donde "más alto" es peor (ej. entropía = % de
 * pendientes que siguen abiertos), agregar data-invertido="true":
 *   <span class="pct-semaforo" data-pct="85" data-invertido="true">85%</span>
 *
 * Uso en JS (ej. datalabels de Chart.js):
 *   color: (ctx) => colorSemaforoPct(ctx.dataset.data[ctx.dataIndex])
 */
(function (global) {
  var ROJO = [198, 40, 40];    // --status-red    #c62828
  var AMBAR = [184, 134, 11];  // --status-yellow #b8860b
  var VERDE = [46, 125, 50];   // --status-green  #2e7d32

  function lerp(a, b, t) {
    return Math.round(a + (b - a) * t);
  }

  function mezclar(c1, c2, t) {
    return [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)];
  }

  function aHex(rgb) {
    return "#" + rgb.map(function (v) {
      var h = Math.max(0, Math.min(255, v)).toString(16);
      return h.length === 1 ? "0" + h : h;
    }).join("");
  }

  function colorSemaforoPct(pct, invertido) {
    var p = Math.max(0, Math.min(100, Number(pct) || 0));
    var t = p / 100;
    if (invertido) t = 1 - t;
    var e = (1 - Math.cos(Math.PI * t)) / 2;
    var rgb = e <= 0.5
      ? mezclar(ROJO, AMBAR, e / 0.5)
      : mezclar(AMBAR, VERDE, (e - 0.5) / 0.5);
    return aHex(rgb);
  }

  function initPctSemaforo(root) {
    (root || document).querySelectorAll(".pct-semaforo[data-pct]").forEach(function (el) {
      var invertido = el.dataset.invertido === "true";
      el.style.color = colorSemaforoPct(el.dataset.pct, invertido);
    });
  }

  global.colorSemaforoPct = colorSemaforoPct;
  global.initPctSemaforo = initPctSemaforo;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { initPctSemaforo(); });
  } else {
    initPctSemaforo();
  }
})(window);
