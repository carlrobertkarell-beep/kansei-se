/* Shareable video timestamps; no storage, tracking or external requests. */
(() => {
  'use strict';
  const video = document.getElementById('hyaluron-film');
  if (!video) return;
  const declared = Number(video.dataset.duration);
  const maxDuration = Number.isFinite(declared) && declared > 0 ? declared : Infinity;
  function seek(value, play) {
    if (!Number.isFinite(value) || value < 0 || value > maxDuration) return;
    const apply = () => {
      video.currentTime = Math.min(value, video.duration || maxDuration);
      if (play) video.play().catch(() => {});
    };
    if (video.readyState >= 1) apply();
    else {
      video.addEventListener('loadedmetadata', apply, {once: true});
      video.load();
    }
  }
  const initial = new URL(location.href).searchParams.get('t');
  if (initial !== null && /^\d+(?:\.\d+)?$/.test(initial)) seek(Number(initial), false);
  document.querySelectorAll('[data-video-start]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const value = Number(link.dataset.videoStart);
      const url = new URL(location.href);
      url.searchParams.set('t', String(value));
      history.replaceState(null, '', url.pathname + url.search);
      seek(value, true);
      video.focus({preventScroll: true});
      video.scrollIntoView({block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
    });
  });
})();
