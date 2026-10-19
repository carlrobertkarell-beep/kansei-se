/* Shared responsive captions. Native tracks remain the fallback and fullscreen source. */
(() => {
  'use strict';
  document.querySelectorAll('video.film-player').forEach(video => {
    const element = video.querySelector('track[kind="captions"]');
    if (!element || !element.track || !video.textTracks) return;
    const track = element.track;
    const box = document.createElement('div');
    box.className = 'film-live-captions';
    box.hidden = true;
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', 'Undertexter');
    box.setAttribute('aria-live', 'off');
    video.insertAdjacentElement('afterend', box);
    const mobile = matchMedia('(max-width: 640px)');
    let started = video.currentTime > 0;
    let platformFullscreen = false;
    let pictureInPicture = false;

    function render() {
      const fullscreen = platformFullscreen || video.webkitDisplayingFullscreen ||
        (document.fullscreenElement && document.fullscreenElement.contains(video));
      const outside = mobile.matches && !fullscreen && !pictureInPicture &&
        track.mode === 'showing' && started && !video.ended;
      const text = Array.from(track.activeCues || [])
        .map(cue => cue.text.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim())
        .join(' ');
      // Update only when the cue changes; never announce every frame to screen readers.
      if (box.textContent !== text) box.textContent = text;
      box.hidden = !outside;
      video.classList.toggle('film-captions-outside', Boolean(outside));
    }

    track.addEventListener('cuechange', render);
    element.addEventListener('load', render);
    video.textTracks.addEventListener('change', render);
    video.addEventListener('play', () => { started = true; render(); });
    ['loadedmetadata', 'timeupdate', 'seeked', 'pause', 'ended'].forEach(event =>
      video.addEventListener(event, render));
    document.addEventListener('fullscreenchange', render);
    video.addEventListener('webkitbeginfullscreen', () => { platformFullscreen = true; render(); });
    video.addEventListener('webkitendfullscreen', () => { platformFullscreen = false; render(); });
    video.addEventListener('enterpictureinpicture', () => { pictureInPicture = true; render(); });
    video.addEventListener('leavepictureinpicture', () => { pictureInPicture = false; render(); });
    if (mobile.addEventListener) mobile.addEventListener('change', render);
    else mobile.addListener(render);
    render();
  });
})();
