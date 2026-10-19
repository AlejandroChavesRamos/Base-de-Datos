/* =====================================================================
   ui.js — avisos animados y ventana de confirmación.
   1) Convierte los mensajes de Django (messages) en ventanas animadas.
   2) Reemplaza el confirm() del navegador en formularios con data-confirmar.
   ===================================================================== */
(function () {
  'use strict';

  var T = 'class="ui-trazo" pathLength="100"';
  var T2 = 'class="ui-trazo t2" pathLength="100"';
  var ICONOS = {
    success:   '<svg viewBox="0 0 100 100" aria-hidden="true"><path ' + T + ' d="M22 52 L43 73 L80 29"/></svg>',
    error:     '<svg viewBox="0 0 100 100" aria-hidden="true"><path ' + T + ' d="M30 30 L70 70"/><path ' + T2 + ' d="M70 30 L30 70"/></svg>',
    eliminado: '<svg viewBox="0 0 100 100" aria-hidden="true">' +
                 '<g class="ui-tapa"><path ' + T + ' d="M22 30 H78"/><path ' + T + ' d="M40 30 V24 a4 4 0 0 1 4 -4 H56 a4 4 0 0 1 4 4 V30"/></g>' +
                 '<path ' + T2 + ' d="M29 40 L33 76 a6 6 0 0 0 6 5 H61 a6 6 0 0 0 6 -5 L71 40"/>' +
                 '<path ' + T2 + ' d="M44 50 V69 M56 50 V69"/></svg>',
    warning:   '<svg viewBox="0 0 100 100" aria-hidden="true"><path ' + T + ' d="M50 24 V58"/><path ' + T2 + ' d="M50 76 V77"/></svg>',
    info:      '<svg viewBox="0 0 100 100" aria-hidden="true"><path ' + T + ' d="M50 42 V76"/><path ' + T2 + ' d="M50 23 V24"/></svg>'
  };

  var TITULOS = {
    success: '¡Listo!', eliminado: 'Eliminado', error: 'No se pudo completar',
    warning: 'Atención', info: 'Información'
  };

  var COLORES_CHISPAS = ['#2fb86b', '#7be0a8', '#f5b942', '#4aa8e0', '#e0892f'];

  function chispas() {
    var h = '';
    for (var i = 0; i < 10; i++) {
      h += '<span class="ui-chispa" style="--a:' + (i * 36) + 'deg;--c:' + COLORES_CHISPAS[i % COLORES_CHISPAS.length] + '"></span>';
    }
    return h;
  }

  /* ---------- Ventana genérica ----------
     o = { tipo, titulo, texto, chispas, auto, botones:[{texto, clase, valor, icono, foco}], valorEsc }
     Devuelve una Promise que se resuelve con el valor del botón pulsado. */
  function abrir(o) {
    return new Promise(function (resolve) {
      var ov = document.createElement('div');
      ov.className = 'ui-overlay';
      ov.setAttribute('role', 'alertdialog');
      ov.setAttribute('aria-modal', 'true');
      ov.innerHTML =
        '<div class="ui-caja ui-' + o.tipo + '">' +
          '<div class="ui-icono">' + ICONOS[o.tipo] + (o.chispas ? chispas() : '') + '</div>' +
          '<h3 class="ui-titulo"></h3>' +
          '<p class="ui-texto"></p>' +
          '<div class="ui-botones"></div>' +
          (o.auto ? '<div class="ui-barra-wrap"><div class="ui-barra"></div></div>' : '') +
        '</div>';

      // textContent (no innerHTML) para que ningún texto pueda inyectar HTML
      ov.querySelector('.ui-titulo').textContent = o.titulo || '';
      ov.querySelector('.ui-texto').textContent = o.texto || '';

      var valorEsc = (o.valorEsc === undefined) ? true : o.valorEsc;
      var cerrado = false;

      function cerrar(valor) {
        if (cerrado) return;
        cerrado = true;
        document.removeEventListener('keydown', onKey);
        ov.classList.remove('visible');
        ov.classList.add('saliendo');
        setTimeout(function () {
          ov.remove();
          if (!document.querySelector('.ui-overlay')) document.body.style.overflow = '';
          resolve(valor);
        }, 260);
      }

      function onKey(e) { if (e.key === 'Escape') cerrar(valorEsc); }

      var cont = ov.querySelector('.ui-botones');
      (o.botones || []).forEach(function (b) {
        var el = document.createElement('button');
        el.type = 'button';
        el.className = 'btn ' + b.clase;
        if (b.icono) {
          var i = document.createElement('i');
          i.className = 'bi ' + b.icono;
          el.appendChild(i);
          el.appendChild(document.createTextNode(' '));
        }
        el.appendChild(document.createTextNode(b.texto));
        el.addEventListener('click', function () { el.disabled = true; cerrar(b.valor); });
        cont.appendChild(el);
        if (b.foco) setTimeout(function () { el.focus(); }, 80);
      });

      ov.addEventListener('click', function (e) {
        if (o.auto || e.target === ov) cerrar(valorEsc);   // los avisos se cierran con un clic
      });

      var barra = ov.querySelector('.ui-barra');
      if (barra) barra.addEventListener('animationend', function () { cerrar(true); });

      document.body.appendChild(ov);
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', onKey);
      void ov.offsetWidth;                                  // fuerza el reflow para animar
      requestAnimationFrame(function () { ov.classList.add('visible'); });
    });
  }

  /* ---------- API pública ---------- */
  function avisar(tipo, texto, titulo) {
    var auto = (tipo === 'success' || tipo === 'eliminado' || tipo === 'info');
    return abrir({
      tipo: tipo,
      titulo: titulo || TITULOS[tipo],
      texto: texto,
      chispas: tipo === 'success',
      auto: auto,
      botones: auto ? [] : [{ texto: 'Entendido', clase: 'btn-marca', valor: true, foco: true }]
    });
  }

  function confirmar(o) {
    o = o || {};
    return abrir({
      tipo: 'warning',
      titulo: o.titulo || '¿Estás seguro?',
      texto: o.texto || '',
      valorEsc: false,
      botones: [
        { texto: 'Cancelar', clase: 'btn-outline-secondary', valor: false, foco: true },
        { texto: o.ok || 'Sí, continuar', clase: 'btn-peligro', valor: true, icono: o.icono }
      ]
    });
  }

  window.UI = { avisar: avisar, confirmar: confirmar };

  /* ---------- 1) Mensajes de Django -> ventanas animadas ---------- */
  function tipoDe(tags) {
    var t = (tags || '').split(/\s+/);
    if (t.indexOf('eliminado') > -1) return 'eliminado';
    if (t.indexOf('danger') > -1 || t.indexOf('error') > -1) return 'error';
    if (t.indexOf('warning') > -1) return 'warning';
    if (t.indexOf('info') > -1 || t.indexOf('debug') > -1) return 'info';
    return 'success';
  }

  function mostrarMensajes() {
    var caja = document.getElementById('mensajes-django');
    if (!caja) return;
    var cola = Promise.resolve();                           // se muestran de uno en uno
    Array.prototype.forEach.call(caja.querySelectorAll('span'), function (s) {
      var tags = s.getAttribute('data-tags') || '';
      var tipo = tipoDe(tags);
      var titulo = null;
      if (tipo === 'success' && /\bpedido\b/.test(tags)) titulo = '¡Pedido realizado!';
      if (tipo === 'eliminado' && /\bcancelado\b/.test(tags)) titulo = 'Pedido cancelado';
      cola = cola.then(function () { return avisar(tipo, s.textContent.trim(), titulo); });
    });
  }

  /* ---------- 2) Confirmación en formularios con data-confirmar ---------- */
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!(f instanceof HTMLFormElement) || !f.hasAttribute('data-confirmar')) return;
    e.preventDefault();
    confirmar({
      titulo: f.getAttribute('data-titulo') || '¿Eliminar este registro?',
      texto: f.getAttribute('data-confirmar'),
      ok: f.getAttribute('data-ok') || 'Sí, eliminar',
      icono: f.getAttribute('data-icono') || 'bi-trash3'
    }).then(function (ok) {
      if (ok) HTMLFormElement.prototype.submit.call(f);     // submit() no vuelve a disparar este evento
    });
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mostrarMensajes);
  else mostrarMensajes();
})();
