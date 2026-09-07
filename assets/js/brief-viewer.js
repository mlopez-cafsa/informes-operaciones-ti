/*
 * brief-viewer.js
 * ================
 * Muestra (si existe) el brief diario más reciente en un <dialog> nativo,
 * usando un <iframe> para aislar el CSS propio del brief.
 *
 * Degradación elegante a propósito (2026-09-07): briefs/ y su manifest
 * están excluidos de git porque traen correos y datos reales de negocio.
 * En el sitio publicado (GitHub Pages) esa carpeta nunca se despliega, así
 * que el fetch de abajo siempre da 404 ahí — el catch lo absorbe en
 * silencio y el botón se queda oculto (atributo `hidden` del HTML).
 * En la copia local de Marco, tras correr
 * `python3 scripts/manage_briefs.py build`, el manifest sí existe y el
 * botón aparece con el brief del día.
 */
(function () {
  const boton = document.getElementById('btn-abrir-brief');
  const dialogo = document.getElementById('dialog-brief');
  if (!boton || !dialogo) return;

  const iframe = document.getElementById('iframe-brief');
  const btnCerrar = document.getElementById('btn-cerrar-brief');
  const titulo = document.getElementById('titulo-dialog-brief');

  fetch('briefs/manifest.json', { cache: 'no-store' })
    .then(function (respuesta) {
      if (!respuesta.ok) throw new Error('manifest no disponible');
      return respuesta.json();
    })
    .then(function (manifiesto) {
      const reciente = manifiesto && manifiesto.mas_reciente;
      if (!reciente || !reciente.archivo) return; // nada que mostrar

      boton.hidden = false;
      boton.textContent = reciente.es_de_hoy ? 'Brief de hoy' : 'Brief (' + reciente.etiqueta + ')';

      boton.addEventListener('click', function () {
        const destino = 'briefs/' + reciente.archivo;
        if (iframe.getAttribute('src') !== destino) {
          iframe.setAttribute('src', destino);
        }
        titulo.textContent = reciente.etiqueta;
        if (typeof dialogo.showModal === 'function') {
          dialogo.showModal();
        } else {
          dialogo.setAttribute('open', '');
        }
      });
    })
    .catch(function () {
      // Silencioso a propósito — ver nota de degradación elegante arriba.
    });

  btnCerrar.addEventListener('click', function () {
    dialogo.close();
  });

  // Cerrar al hacer click en el backdrop (fuera del recuadro del dialog).
  dialogo.addEventListener('click', function (evento) {
    const rect = dialogo.getBoundingClientRect();
    const dentro = (
      evento.clientX >= rect.left && evento.clientX <= rect.right &&
      evento.clientY >= rect.top && evento.clientY <= rect.bottom
    );
    if (!dentro) dialogo.close();
  });

  // Al cerrar (backdrop, botón X o ESC), liberar el iframe.
  dialogo.addEventListener('close', function () {
    iframe.setAttribute('src', 'about:blank');
  });
})();
