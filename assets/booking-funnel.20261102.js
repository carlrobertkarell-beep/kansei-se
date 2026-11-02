/* Public booking steps only. Uses the existing statistics consent and GA4 bridge. */
(() => {
  'use strict';
  const titles = {
    '/ultraljud/axel/': 'Ultraljud av axel i Stockholm',
    '/ultraljud/kna/': 'Ultraljud av knä i Stockholm',
    '/hyaluronsyra/kna/': 'Hyaluroninjektion i knä i Stockholm'
  };
  const path = location.pathname.replace(/\/?$/, '/');
  const id = document.querySelector('meta[name="kansei-ga4"]')?.content || '';
  if (!['kansei.se', 'www.kansei.se'].includes(location.hostname) ||
      !document.body.classList.contains('clinic-site') || !titles[path] ||
      !/^G-[A-Z0-9]{6,20}$/.test(id)) return;

  const permitted = () => window.KanseiMeasure === true && typeof window.gtag === 'function';
  const pageLocation = () => {
    try {
      const canonical = new URL(document.querySelector('link[rel="canonical"]')?.href || location.href);
      if (['kansei.se', 'www.kansei.se'].includes(canonical.hostname) && canonical.pathname === path)
        return 'https://www.kansei.se' + canonical.pathname;
    } catch {}
    return 'https://www.kansei.se' + path;
  };
  const referrer = () => {
    try {
      const url = new URL(document.referrer);
      return ['http:', 'https:'].includes(url.protocol) ? url.origin + '/' : '';
    } catch { return ''; }
  };
  const send = (event, placement = 'content') => {
    if (!permitted()) return;
    window.gtag('event', event, {
      send_to: id, page_location: pageLocation(), page_title: titles[path],
      page_referrer: referrer(), placement, measurement_version: '20261102'
    });
  };

  let observer, active = false, viewed = false;
  const targets = new Map();
  const cancelView = state => {
    if (state.timer !== undefined) window.clearTimeout(state.timer);
    state.timer = undefined;
  };
  const scheduleView = state => {
    cancelView(state);
    if (!state.visible || viewed || document.hidden || !permitted()) return;
    state.timer = window.setTimeout(() => {
      state.timer = undefined;
      if (!state.visible || viewed || document.hidden || !permitted()) return;
      viewed = true;
      send('booking_options_view');
      targets.forEach(cancelView);
      observer?.disconnect();
    }, 1000);
  };
  const synchronize = () => {
    if (!permitted()) {
      active = false;
      targets.forEach(cancelView);
      targets.clear();
      observer?.disconnect();
      observer = undefined;
      return;
    }
    if (active || viewed) return;
    active = true;
    const markers = document.querySelectorAll('[data-booking-options]');
    if (!markers.length || typeof window.IntersectionObserver !== 'function') return;
    observer = new window.IntersectionObserver(entries => {
      if (!permitted()) { synchronize(); return; }
      for (const entry of entries) {
        const state = targets.get(entry.target);
        if (!state) continue;
        const visible = entry.isIntersecting && entry.intersectionRatio >= 0.25;
        if (visible === state.visible) continue;
        state.visible = visible;
        scheduleView(state);
      }
    }, {threshold: [0, 0.25]});
    markers.forEach(target => {
      targets.set(target, {visible: false, timer: undefined});
      observer.observe(target);
    });
  };

  document.addEventListener('click', event => {
    if (event.defaultPrevented || !permitted()) return;
    const anchor = event.target.closest?.('a[href]');
    if (!anchor) return;
    try {
      const destination = new URL(anchor.getAttribute('href'), location.href);
      if (destination.origin !== location.origin || destination.pathname !== location.pathname ||
          destination.search !== location.search || !['#boka', '#pris'].includes(destination.hash)) return;
      const requested = anchor.dataset.placement;
      const placement = ['header', 'footer', 'guide', 'menu', 'content', 'price_list', 'service_card'].includes(requested)
        ? requested : anchor.closest('.site-header') ? 'header'
          : anchor.closest('.footer') ? 'footer' : anchor.closest('#site-menu') ? 'menu' : 'content';
      send('booking_options_open', placement);
    } catch {}
  });
  document.addEventListener('visibilitychange', () => targets.forEach(scheduleView));
  // The existing bridge owns consent. Check its public flag so later opt-in and withdrawal work.
  window.setInterval(synchronize, 250);
  synchronize();
})();
