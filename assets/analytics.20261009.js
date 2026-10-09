/* Public clinic analytics: no Google requests before explicit consent. */
(() => {
  'use strict';
  const id = document.querySelector('meta[name="kansei-ga4"]')?.content || '';
  if (!/^G-[A-Z0-9]{6,20}$/.test(id) ||
      !['kansei.se', 'www.kansei.se'].includes(location.hostname) ||
      !document.body.classList.contains('clinic-site')) return;
  const key = 'kansei-statistics-v1', maxAge = 180 * 86400000;
  let granted = false, configured = false, panel, opener;
  window.KanseiMeasure = false;
  window['ga-disable-' + id] = true;
  const read = () => {
    try {
      const v = JSON.parse(localStorage.getItem(key));
      return v && typeof v.allowed === 'boolean' && Number.isFinite(v.at) &&
        Date.now() >= v.at && Date.now() - v.at < maxAge ? v.allowed : null;
    } catch { return null; }
  };
  const save = allowed => {
    try { localStorage.setItem(key, JSON.stringify({allowed, at: Date.now()})); } catch {}
  };
  const cleanReferrer = () => {
    try {
      const u = new URL(document.referrer);
      return ['http:', 'https:'].includes(u.protocol) ? u.origin + '/' : '';
    } catch { return ''; }
  };
  const pageLocation = () => {
    try {
      const u = new URL(document.querySelector('link[rel="canonical"]')?.href || location.href);
      if (['kansei.se','www.kansei.se'].includes(u.hostname))
        return 'https://www.kansei.se' + u.pathname;
    } catch {}
    return 'https://www.kansei.se/';
  };
  const removeCookies = () => {
    for (const part of document.cookie.split(';')) {
      const name = part.trim().split('=')[0];
      if (!/^_ga(?:_|$)/.test(name)) continue;
      for (const domain of ['', '; Domain=kansei.se', '; Domain=.kansei.se', '; Domain=' + location.hostname])
        document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax; Secure' + domain;
    }
  };
  const deny = () => {
    granted = false;
    window.KanseiMeasure = false;
    window['ga-disable-' + id] = true;
    removeCookies();
  };
  const enable = () => {
    granted = true;
    window['ga-disable-' + id] = false;
    window.KanseiMeasure = true;
    if (configured) return;
    configured = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage:'granted', ad_storage:'denied',
      ad_user_data:'denied', ad_personalization:'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', id, {
      send_page_view:false, allow_google_signals:false,
      allow_ad_personalization_signals:false, cookie_expires:15552000,
      cookie_update:false, page_location:pageLocation(),
      page_referrer:cleanReferrer(), page_title:document.title
    });
    window.gtag('event', 'page_view', {
      send_to:id, page_location:pageLocation(),
      page_referrer:cleanReferrer(), page_title:document.title
    });
    const script = document.createElement('script');
    script.async = true;
    script.referrerPolicy = 'no-referrer';
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.append(script);
  };
  document.addEventListener('kansei:booking-intent', e => {
    if (!granted || e.detail?.event !== 'booking_click') return;
    // No service, symptoms, clinician identity, link text, user input or URLs.
    const placement = ['header','footer','guide','menu','content'].includes(e.detail.placement)
      ? e.detail.placement : 'content';
    window.gtag('event', 'booking_click', {
      send_to:id, placement, page_location:pageLocation(),
      page_referrer:cleanReferrer(), page_title:document.title
    });
  });
  const close = () => { panel.hidden = true; opener?.focus({preventScroll:true}); };
  const show = button => {
    opener = button || null;
    panel.hidden = false;
    panel.querySelector('button').focus({preventScroll:true});
  };
  const mount = () => {
    panel = document.createElement('section');
    panel.className = 'kansei-statistics';
    panel.setAttribute('aria-labelledby','kansei-statistics-heading');
    panel.hidden = true;
    panel.innerHTML = '<div class="kansei-statistics-inner"><h2 id="kansei-statistics-heading">Statistik på webbplatsen</h2><p>Vi använder Google Analytics för att förstå hur besökare hittar hit och använder hemsidan, inklusive klick till bokningen. Statistikcookies är valfria. Du kan ändra ditt val när som helst via Statistikinställningar. <a href="/cookie/">Läs om statistik och cookies</a>.</p><div class="kansei-statistics-actions"><button type="button" data-statistics="no">Nej tack</button><button type="button" data-statistics="yes">Godkänn statistik</button></div></div>';
    document.body.append(panel);
    panel.addEventListener('click', e => {
      const button = e.target.closest('[data-statistics]');
      if (!button) return;
      const allowed = button.dataset.statistics === 'yes';
      save(allowed);
      if (allowed) enable(); else deny();
      close();
    });
    const settings = document.createElement('button');
    settings.type = 'button';
    settings.className = 'kansei-statistics-settings';
    settings.textContent = 'Statistikinställningar';
    settings.addEventListener('click', () => show(settings));
    (document.querySelector('.footer') || document.body).append(settings);
    const choice = read();
    if (choice === true) enable();
    else if (choice === false) deny();
    else panel.hidden = false; // No focus stealing on first arrival.
  };
  window.addEventListener('storage', e => {
    if (e.key !== key && e.key !== null) return;
    if (read() === true) enable();
    else { deny(); if (panel) panel.hidden = read() !== null; }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once:true});
  else mount();
})();
