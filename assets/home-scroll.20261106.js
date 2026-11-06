/* A single scroll clock for the homepage. No scroll hijacking, animation library or data collection. */
(() => {
  'use strict';
  const body = document.body;
  if (!body.classList.contains('home-chapters') || body.dataset.homeScrollReady) return;
  body.dataset.homeScrollReady = 'true';
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const compact = matchMedia('(max-width: 760px)');
  const records = [];
  const active = new Set();
  let frame = 0, measuring = true, enabled = !preference.matches;
  const clamp = value => Math.max(0, Math.min(1, value));
  const ease = value => 1 - Math.pow(1 - clamp(value), 3);
  const write = (node, property, value) => node.style.setProperty(property, value);

  function add(node, type) {
    if (!node) return;
    const record = { node, type, top: 0, height: 0, words: [] };
    records.push(record);
    return record;
  }
  document.querySelectorAll('.home-intro-image').forEach(node => add(node, 'hero'));
  document.querySelectorAll('.home-diagnostic .hd-instrument').forEach(node => add(node, 'panel'));
  document.querySelectorAll('.home-visit').forEach(node => add(node, 'visit'));
  document.querySelectorAll('.home-human-portrait').forEach(node => add(node, 'human'));
  document.querySelectorAll('.home-reviews-stage').forEach(node => add(node, 'reviews'));
  document.querySelectorAll('[data-scroll-reveal]').forEach(node => add(node, 'reveal'));

  document.querySelectorAll('[data-scroll-text]').forEach(node => {
    const record = add(node, 'text');
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, {
      acceptNode: text => text.textContent.trim() && !text.parentElement.closest('script,style,svg,[aria-hidden="true"],.home-scroll-word') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    });
    const texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    for (const text of texts) {
      const fragment = document.createDocumentFragment();
      for (const part of text.textContent.split(/(\s+)/)) {
        if (!part || /^\s+$/.test(part)) { fragment.append(document.createTextNode(part)); continue; }
        const span = document.createElement('span');
        span.className = 'home-scroll-word';
        span.textContent = part;
        fragment.append(span);
        record.words.push(span);
      }
      text.replaceWith(fragment);
    }
    record.minimum = parseFloat(getComputedStyle(node).fontSize) >= 30 ? .56 : .76;
  });

  function measure() {
    body.classList.add('home-scroll-measuring');
    const y = window.scrollY;
    for (const record of records) {
      const rect = record.node.getBoundingClientRect();
      record.top = rect.top + y;
      record.height = rect.height;
    }
    body.classList.remove('home-scroll-measuring');
    measuring = false;
  }

  function render(record, y, viewport) {
    const top = record.top - y;
    const travel = clamp((viewport - top) / (viewport + record.height));
    const enter = ease((viewport * .96 - top) / (viewport * .46));
    const node = record.node;
    if (record.type === 'hero') {
      const expansion = ease((travel - (compact.matches ? .42 : .54)) / .4);
      write(node, '--home-photo-expand', (1 + expansion * (compact.matches ? .145 : .09)).toFixed(4));
      write(node, '--home-photo-scale', (1.08 + travel * .08).toFixed(4));
      write(node, '--home-photo-pan', ((.5 - travel) * (compact.matches ? 22 : 46)).toFixed(2) + 'px');
      write(node, '--home-caption-pan', (-travel * (compact.matches ? 6 : 14)).toFixed(2) + 'px');
      write(node, '--home-photo-corner', Math.round((compact.matches ? 48 : 70) * (1 - expansion) + expansion * 7) + 'px');
    } else if (record.type === 'panel') {
      write(node, '--home-panel-rise', ((1 - enter) * (compact.matches ? 48 : 76)).toFixed(2) + 'px');
      write(node, '--home-panel-pitch', ((1 - enter) * (compact.matches ? 7 : 10)).toFixed(3) + 'deg');
      write(node, '--home-panel-scale', (.87 + enter * .13).toFixed(4));
      write(node, '--home-panel-shadow-y', (24 + enter * 20).toFixed(1) + 'px');
      write(node, '--home-panel-shadow-alpha', (.3 + enter * .23).toFixed(3));
    } else if (record.type === 'visit') {
      write(node, '--home-row-shift', ((1 - enter) * (compact.matches ? 16 : 30)).toFixed(2) + 'px');
      write(node, '--home-row-rise', ((1 - enter) * 20).toFixed(2) + 'px');
      write(node, '--home-row-opacity', (.62 + enter * .38).toFixed(3));
      write(node, '--home-line-progress', enter.toFixed(4));
    } else if (record.type === 'human') {
      write(node, '--home-human-pan', ((.5 - travel) * (compact.matches ? 22 : 45)).toFixed(2) + 'px');
    } else if (record.type === 'reviews') {
      write(node, '--home-review-rise', ((1 - enter) * 50).toFixed(2) + 'px');
      node.classList.toggle('is-scroll-entered', enter > .5);
    } else if (record.type === 'reveal') {
      write(node, '--home-reveal-rise', ((1 - enter) * 45).toFixed(2) + 'px');
      write(node, '--home-reveal-scale', (.96 + enter * .04).toFixed(4));
    } else if (record.type === 'text') {
      const progress = clamp((viewport * .88 - top) / (viewport * .48 + Math.min(record.height, viewport) * .3));
      const count = record.words.length;
      record.words.forEach((word, index) => {
        const step = clamp((progress - index / Math.max(1, count) * .68) / .32);
        write(word, '--home-word-opacity', (record.minimum + step * (1 - record.minimum)).toFixed(3));
        write(word, '--home-word-rise', ((1 - step) * 5).toFixed(2) + 'px');
      });
    }
  }

  function update() {
    frame = 0;
    if (!enabled || document.hidden) return;
    if (measuring) measure();
    const y = window.scrollY, viewport = window.innerHeight;
    for (const record of active) render(record, y, viewport);
  }
  function schedule() { if (enabled && !frame) frame = requestAnimationFrame(update); }
  function remeasure() { measuring = true; schedule(); }

  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
    for (const entry of entries) {
      const record = records.find(item => item.node === entry.target);
      if (!record) continue;
      if (entry.isIntersecting) active.add(record);
      else active.delete(record);
    }
    schedule();
  }, { rootMargin: '30% 0px', threshold: 0 }) : null;
  records.forEach(record => {
    if (observer) observer.observe(record.node); else active.add(record);
  });
  // Poses are a pure function of scroll position, without inertia. Pointer/focus
  // events never finish an entrance or change geometry, so beginning a vertical
  // gesture cannot snap a partly visible panel. Horizontal image drags keep the
  // page at the same scroll position and therefore keep its pose unchanged.

  function applyPreference() {
    enabled = !preference.matches;
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
    body.classList.toggle('has-home-scroll', enabled);
    if (enabled) { measuring = true; schedule(); }
  }
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('resize', remeasure, { passive: true });
  addEventListener('pageshow', remeasure);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) remeasure(); });
  document.addEventListener('load', event => { if (event.target instanceof HTMLImageElement) remeasure(); }, true);
  document.fonts?.ready.then(remeasure);
  if ('ResizeObserver' in window) new ResizeObserver(remeasure).observe(body);
  if (preference.addEventListener) preference.addEventListener('change', applyPreference);
  else preference.addListener(applyPreference);
  addEventListener('beforeprint', () => {
    body.classList.remove('has-home-scroll');
    if (frame) { cancelAnimationFrame(frame); frame = 0; }
  });
  addEventListener('afterprint', applyPreference);
  applyPreference();
})();
