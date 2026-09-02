/**
 * mailto-consulta.js
 * Botón "Enviar consulta sobre este contexto".
 * Arma un correo prellenado (mailto:) hacia el destinatario fijo definido
 * en DESTINATARIO_FIJO, usando el título/resumen del informe como contexto.
 * Nunca envía nada automáticamente: solo abre el cliente de correo con un
 * borrador, y antes pide confirmación explícita al usuario (confirm()).
 *
 * Uso en el HTML del informe:
 *   <button class="btn-consulta"
 *           data-titulo="Nombre del informe"
 *           data-resumen="Resumen corto de una línea"
 *           onclick="enviarConsulta(this)">
 *     Enviar consulta sobre este informe
 *   </button>
 */

const DESTINATARIO_FIJO = "mlopezz@cafsa.fi.cr";

function enviarConsulta(boton) {
  const titulo = boton.dataset.titulo || document.title;
  const resumen = boton.dataset.resumen || "";
  const url = window.location.href;

  const asunto = `Consulta sobre informe: ${titulo}`;
  const cuerpo =
    `Contexto del informe: ${titulo}\n` +
    `Link: ${url}\n\n` +
    (resumen ? `Resumen: ${resumen}\n\n` : "") +
    `Consulta:\n`;

  const mailtoUrl =
    `mailto:${DESTINATARIO_FIJO}` +
    `?subject=${encodeURIComponent(asunto)}` +
    `&body=${encodeURIComponent(cuerpo)}`;

  const confirmado = window.confirm(
    `Se abrirá un borrador de correo dirigido a ${DESTINATARIO_FIJO} con el contexto de este informe.\n` +
    `El correo NO se envía automáticamente: podrás revisarlo y enviarlo tú mismo desde tu cliente de correo.\n\n` +
    `¿Deseas continuar?`
  );

  if (confirmado) {
    window.location.href = mailtoUrl;
  }
}

/**
 * Botón "Confirmar seguimiento" (módulo reportes/pendientes).
 * A diferencia de enviarConsulta() (que pregunta algo), este botón arma un
 * correo prellenado hacia DESTINATARIO_FIJO confirmando que la persona que
 * ve la página está atendiendo ese pendiente puntual. Mismo mecanismo de
 * confirmación previa; nunca se envía nada automáticamente.
 *
 * Uso en el HTML:
 *   <button class="btn-consulta"
 *           data-tema="PP-216 — Actualizar estado en Jira"
 *           onclick="confirmarSeguimiento(this)">
 *     Confirmar seguimiento
 *   </button>
 */
function confirmarSeguimiento(boton) {
  const tema = boton.dataset.tema || document.title;
  const url = window.location.href;

  const asunto = `Confirmo seguimiento: ${tema}`;
  const cuerpo =
    `Tema: ${tema}\n` +
    `Link: ${url}\n\n` +
    `Confirmo que estoy dando seguimiento a este pendiente.\n\n` +
    `Comentario adicional:\n`;

  const mailtoUrl =
    `mailto:${DESTINATARIO_FIJO}` +
    `?subject=${encodeURIComponent(asunto)}` +
    `&body=${encodeURIComponent(cuerpo)}`;

  const confirmado = window.confirm(
    `Se abrirá un borrador de correo dirigido a ${DESTINATARIO_FIJO} confirmando que estás dando seguimiento a este pendiente.\n` +
    `El correo NO se envía automáticamente: podrás revisarlo y enviarlo tú mismo desde tu cliente de correo.\n\n` +
    `¿Deseas continuar?`
  );

  if (confirmado) {
    window.location.href = mailtoUrl;
  }
}

/**
 * Botón "Redactar correo a <Persona>" (módulo reportes/pendientes).
 * A diferencia de confirmarSeguimiento() (que se envía a uno mismo como
 * registro), este botón arma un correo dirigido a la persona del
 * pendiente, con la solicitud/recomendación como cuerpo. NO tiene un
 * destinatario fijo: el sistema no guarda direcciones de correo reales de
 * terceros, así que el campo "Para" queda vacío y hay que completarlo a
 * mano antes de enviar. Mismo mecanismo de confirmación previa; nunca se
 * envía nada automáticamente.
 *
 * Uso en el HTML:
 *   <button class="btn-secundario btn-redactar"
 *           data-persona="María Cristina Hernández"
 *           data-tema="PP-216 — Actualizar estado en Jira"
 *           data-cuerpo="Tema: ...\nSolicitud: ..."
 *           onclick="redactarCorreo(this)">
 *     Redactar correo a María Cristina
 *   </button>
 */
function redactarCorreo(boton) {
  const persona = boton.dataset.persona || "la persona asignada";
  const tema = boton.dataset.tema || document.title;
  const cuerpo = boton.dataset.cuerpo || "";
  const url = window.location.href;

  const asunto = `Seguimiento: ${tema}`;
  const cuerpoCompleto = `${cuerpo}\n\nLink de referencia: ${url}\n`;

  const mailtoUrl =
    `mailto:` +
    `?subject=${encodeURIComponent(asunto)}` +
    `&body=${encodeURIComponent(cuerpoCompleto)}`;

  const confirmado = window.confirm(
    `Se abrirá un borrador de correo con la solicitud/recomendación para ${persona}.\n` +
    `El sistema no guarda su dirección de correo real, así que el campo "Para" queda ` +
    `vacío — deberás completarlo tú mismo antes de enviar.\n` +
    `El correo NO se envía automáticamente: podrás revisarlo en tu cliente de correo.\n\n` +
    `¿Deseas continuar?`
  );

  if (confirmado) {
    window.location.href = mailtoUrl;
  }
}
