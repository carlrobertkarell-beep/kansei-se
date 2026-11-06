/* Small silent excerpts of existing Kansei films, without a media-library dependency. */
(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  document.querySelectorAll('[data-clinic-motion]').forEach(frame => {
    const video = frame.querySelector('video');
    const button = frame.querySelector('button');
    const image = frame.querySelector('img');
    if (!video || !button || !('IntersectionObserver' in window)) return;
    let visible = false, wanted = !reduced.matches && !connection?.saveData;
    let manual = false, failed = false, ready = false;
    video.muted = true;
    function label() {
      button.textContent = video.paused ? 'Spela film' : 'Pausa film';
      button.setAttribute('aria-label', button.textContent + ': ' + (video.getAttribute('aria-label') || 'från kliniken'));
    }
    function update() {
      if (failed) return;
      if (!wanted || !visible || document.hidden || !ready) { video.pause(); label(); return; }
      if (!video.src) { video.src = video.dataset.src; video.load(); }
      const play = video.play();
      if (play) play.catch(() => { if (visible && !document.hidden && wanted) wanted = false; label(); });
    }
    button.hidden = false;
    button.addEventListener('click', () => { manual = true; ready = true; wanted = video.paused; update(); });
    video.addEventListener('playing', () => { frame.classList.add('has-frame'); label(); });
    video.addEventListener('pause', label);
    video.addEventListener('error', () => { failed = true; video.pause(); frame.classList.remove('has-frame'); button.hidden = true; });
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].intersectionRatio >= .35;
      update();
    }, {threshold:[0,.35,.75]});
    observer.observe(frame);
    document.addEventListener('visibilitychange', update);
    function preferences() {
      if (reduced.matches || connection?.saveData) {
        manual = false; wanted = false; video.pause(); frame.classList.remove('has-frame'); label();
      } else if (!manual) { wanted = true; update(); }
    }
    reduced.addEventListener('change', preferences);
    connection?.addEventListener('change', preferences);
    const reveal = () => { setTimeout(() => { ready = true; update(); }, 900); };
    if (image?.complete) reveal(); else if (image) { image.addEventListener('load', reveal, {once:true}); image.addEventListener('error', reveal, {once:true}); } else reveal();
    label();
  });
})();
