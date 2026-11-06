/* Progressive enhancement: content is always visible without this script. */
(() => {
  'use strict';
  if (!document.body.classList.contains('clinic-site')) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const active = new Set();
  const header = document.querySelector('.site-header');
  let frame = 0;
  function updateHeader() {
    frame = 0;
    header?.classList.toggle('is-scrolled', scrollY > 24);
  }
  addEventListener('scroll', () => {
    if (!frame) frame = requestAnimationFrame(updateHeader);
  }, { passive: true });
  updateHeader();

  // Show a close glyph on the existing menu control; dialog logic stays native.
  const toggle = document.querySelector('[data-site-menu]');
  const glyph = toggle?.querySelector('use');
  if (toggle && glyph) {
    const sync = () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      glyph.setAttribute('href', open ? '#i-close' : '#i-menu');
      toggle.setAttribute('aria-label', open ? 'Stäng meny' : 'Öppna meny');
    };
    new MutationObserver(sync).observe(toggle, { attributes: true, attributeFilter: ['aria-expanded'] });
    sync();
  }

  if (!('IntersectionObserver' in window) || !Element.prototype.animate) return;
  const seen = new WeakSet();
  const observer = new IntersectionObserver(entries => {
    let stagger = 0;
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const element = entry.target;
      observer.unobserve(element);
      seen.add(element);
      if (reduced.matches || document.hidden || element.contains(document.activeElement)) continue;
      const animation = element.animate([
        { opacity: .3, transform: 'translateY(14px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ], { duration: 560, delay: Math.min(stagger++ * 45, 90), easing: 'cubic-bezier(.22,.75,.25,1)' });
      active.add(animation);
      const clear = () => active.delete(animation);
      animation.addEventListener('finish', clear, { once: true });
      animation.addEventListener('cancel', clear, { once: true });
    }
  }, { threshold: .08 });
  const selector = 'main h2, main figure, main .service-choice, main .hub-region, main .us-region, main .knowledge-result, main .discovery-link, main .ha-choice, main .case-library-card';
  function observeContent() {
    document.querySelectorAll(selector).forEach(element => {
      if (seen.has(element) || element.closest('dialog,details,[hidden],.us-viewer,.case-viewer,.case-stage,.scan-stage,.pc-stage,.atlas-demo,.premium-motion-media') || element.matches('figure:has(video)')) return;
      const box = element.getBoundingClientRect();
      // Never delay the first screen, an anchor destination, or restored scroll position.
      if (reduced.matches || box.top < innerHeight || box.width === 0 || element.matches(':target') || element.querySelector(':target')) {
        seen.add(element);
        return;
      }
      // Do not animate the title separately when the enclosing card also enters.
      const parent = element.parentElement?.closest(selector);
      if (parent) return;
      observer.observe(element);
    });
  }
  observeContent();
  const finishAll = () => { for (const animation of active) animation.finish(); active.clear(); };
  reduced.addEventListener('change', () => {
    if (reduced.matches) { observer.disconnect(); finishAll(); }
    else observeContent();
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) finishAll(); });
  document.addEventListener('focusin', finishAll);
  addEventListener('beforeprint', finishAll);
})();
