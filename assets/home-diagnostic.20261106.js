/* Registered clinical images, a native comparison control and optional findings. */
(() => {
  'use strict';
  document.querySelectorAll('[data-home-diagnostic]').forEach(root => {
    const stage = root.querySelector('[data-diagnostic-stage]');
    const image = root.querySelector('[data-diagnostic-anatomy]');
    const range = root.querySelector('[data-diagnostic-range]');
    const output = root.querySelector('[data-diagnostic-value]');
    const state = root.querySelector('[data-diagnostic-state]');
    const modes = Array.from(root.querySelectorAll('[data-diagnostic-mode-button]'));
    const findings = root.querySelector('[data-diagnostic-findings-button]');
    const marker = root.querySelector('.hd-findings');
    if (!stage || !image || !range || !findings || !modes.length) return;
    let position = 50, mode = 'original', marked = false, ready = false, pointer = null;
    let dragStart = null, dragging = false;
    function render(announce = false) {
      const split = mode === 'original' ? 0 : mode === 'anatomy' ? 100 : position;
      stage.style.setProperty('--hd-split', split + '%');
      range.value = String(split);
      range.setAttribute('aria-valuetext', split + ' procent illustrerad anatomi, ' + (100 - split) + ' procent ultraljud');
      output.textContent = split + ' / ' + (100 - split);
      root.dataset.diagnosticMode = mode;
      root.dataset.diagnosticFindings = String(marked);
      modes.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.diagnosticModeButton === mode)));
      findings.setAttribute('aria-pressed', String(marked));
      marker.setAttribute('aria-hidden', String(!marked));
      image.parentElement.setAttribute('aria-hidden', String(split === 0));
      if (announce) state.textContent = (mode === 'compare' ? 'Jämförelse av original och illustrerad anatomi.' : mode === 'anatomy' ? 'Illustrerad anatomi visas.' : 'Ultraljudsbilden visas.') + (marked ? ' Kalk och rupturområdet är markerade.' : '');
    }
    function setPosition(value) {
      if (!ready) return;
      position = Math.max(0, Math.min(100, Math.round(value)));
      mode = position === 0 ? 'original' : position === 100 ? 'anatomy' : 'compare';
      render();
    }
    modes.forEach(button => button.addEventListener('click', () => {
      if (button.disabled) return;
      mode = button.dataset.diagnosticModeButton;
      if (mode === 'compare' && (position === 0 || position === 100)) position = 50;
      render(true);
    }));
    range.addEventListener('input', () => setPosition(Number(range.value)));
    findings.addEventListener('click', () => { marked = !marked; render(true); });
    function fromPointer(event) {
      const bounds = stage.getBoundingClientRect();
      if (bounds.width) setPosition((event.clientX - bounds.left) / bounds.width * 100);
    }
    stage.addEventListener('pointerdown', event => {
      if (!ready || !event.isPrimary || event.button !== 0) return;
      pointer = event.pointerId;
      dragStart = { x: event.clientX, y: event.clientY };
      dragging = event.pointerType !== 'touch';
      stage.setPointerCapture(pointer);
      if (dragging) { stage.classList.add('is-dragging'); fromPointer(event); }
    });
    stage.addEventListener('pointermove', event => {
      if (event.pointerId !== pointer) return;
      if (!dragging) {
        const dx = Math.abs(event.clientX - dragStart.x), dy = Math.abs(event.clientY - dragStart.y);
        // Wait for a deliberate horizontal gesture; ordinary vertical scrolling
        // remains the browser's pan-y gesture and never moves the divider.
        if (dx < 6 || dx <= dy) return;
        dragging = true;
        stage.classList.add('is-dragging');
      }
      fromPointer(event);
    });
    function endPointer(event) {
      if (event.pointerId !== pointer) return;
      if (event.type === 'pointerup' && !dragging && dragStart && Math.abs(event.clientX - dragStart.x) < 6 && Math.abs(event.clientY - dragStart.y) < 6) fromPointer(event);
      if (stage.hasPointerCapture(pointer)) stage.releasePointerCapture(pointer);
      pointer = null;
      dragStart = null;
      dragging = false;
      stage.classList.remove('is-dragging');
    }
    stage.addEventListener('pointerup', endPointer);
    stage.addEventListener('pointercancel', endPointer);
    stage.addEventListener('lostpointercapture', () => { pointer = null; dragStart = null; dragging = false; stage.classList.remove('is-dragging'); });
    root.querySelector('[data-diagnostic-ui]').hidden = false;
    render();
    function enable() {
      if (ready || !image.naturalWidth) return;
      ready = true;
      root.classList.add('is-ready');
      range.disabled = false;
      modes.forEach(button => { button.disabled = false; });
      mode = 'compare';
      render();
      state.textContent = 'Dra över bilden eller använd reglaget för att jämföra.';
    }
    function failedImage() {
      if (ready) return;
      state.textContent = 'Originalbilden visas. Läs hela undersökningen via länken till patientfallet.';
    }
    image.addEventListener('load', enable, { once: true });
    image.addEventListener('error', failedImage, { once: true });
    if (image.complete && image.naturalWidth) enable();
    else {
      let requested = false;
      function loadAnatomy() {
        if (requested) return;
        requested = true;
        // This layer starts display:none. A lazy image inside it cannot become
        // visible until ready, so explicitly start loading near the chapter.
        image.loading = 'eager';
        if (image.complete && image.naturalWidth) enable();
        else if (typeof image.decode === 'function') image.decode().then(enable).catch(() => {
          if (image.complete && !image.naturalWidth) failedImage();
        });
      }
      if ('IntersectionObserver' in window) {
        const loader = new IntersectionObserver(entries => {
          if (entries.some(entry => entry.isIntersecting)) { loader.disconnect(); loadAnatomy(); }
        }, { rootMargin: '400px 0px', threshold: 0 });
        loader.observe(root);
      } else loadAnatomy();
    }
  });
})();
