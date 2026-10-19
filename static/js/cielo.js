(function () {
  'use strict';
  if (document.querySelector('.cielo-logistica')) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var avion = '<svg viewBox="0 0 64 64" aria-hidden="true"><path fill="currentColor" d="M62 32 38 28 22 8h-5l8 20H10L4 22H1l4 10-4 10h3l6-6h15l-8 20h5l16-20 24-4z"/></svg>';
  var caja = '<svg viewBox="0 0 64 64" aria-hidden="true"><path fill="currentColor" d="M8 20 32 8l24 12-24 12z"/><path fill="currentColor" opacity=".75" d="M8 20v24l24 12V32z"/><path fill="currentColor" opacity=".55" d="M32 32v24l24-12V20z"/><path fill="#fff" opacity=".35" d="M32 8v24l.01 0V8z"/></svg>';
  var camion = '<svg viewBox="0 0 64 64" aria-hidden="true"><path fill="currentColor" d="M4 18h32v26H4z"/><path fill="currentColor" d="M36 26h16l8 10v8H36z"/><circle cx="16" cy="48" r="6" fill="currentColor"/><circle cx="48" cy="48" r="6" fill="currentColor"/><circle cx="16" cy="48" r="2.5" fill="#fff"/><circle cx="48" cy="48" r="2.5" fill="#fff"/></svg>';

  var capa = document.createElement('div');
  capa.className = 'cielo-logistica';
  capa.setAttribute('aria-hidden', 'true');
  capa.innerHTML =
    '<span class="cielo-item cielo-avion" style="--y:11%;--d:26s;--delay:-4s">' + avion + '</span>' +
    '<span class="cielo-item cielo-caja" style="--y:28%;--d:19s;--delay:-8s">' + caja + '</span>' +
    '<span class="cielo-item cielo-camion vuelta" style="--y:46%;--d:24s;--delay:-2s">' + camion + '</span>' +
    '<span class="cielo-item cielo-caja vuelta" style="--y:62%;--d:21s;--delay:-12s">' + caja + '</span>' +
    '<span class="cielo-item cielo-avion vuelta" style="--y:76%;--d:30s;--delay:-16s">' + avion + '</span>' +
    '<span class="cielo-item cielo-caja" style="--y:88%;--d:17s;--delay:-6s">' + caja + '</span>';

  function poner() {
    if (!document.body || document.querySelector('.cielo-logistica')) return;
    document.body.appendChild(capa);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', poner);
  else poner();
})();
