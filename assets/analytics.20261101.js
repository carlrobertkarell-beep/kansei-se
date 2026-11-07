/* Public clinic analytics. Basic consent: no Google requests before an explicit opt-in. */
(() => {
  'use strict';
  const id = document.querySelector('meta[name="kansei-ga4"]')?.content || '';
  if (!/^G-[A-Z0-9]{6,20}$/.test(id) ||
      !['kansei.se', 'www.kansei.se'].includes(location.hostname) ||
      !document.body.classList.contains('clinic-site')) return;
  const key = 'kansei-statistics-v3', maxAge = 180 * 86400000;
  const sourceKey = 'kansei-referral-v1', sourceMaxAge = 30 * 60000;
  const groups = ['chatgpt','perplexity','copilot','gemini','google','bing','other','unknown'];
  let granted = false, configured = false, panel, opener, source = 'unknown', sourceAt = 0;
  window.KanseiMeasure = false;
  window['ga-disable-' + id] = true;
  const read = () => {
    try {
      for (const storedKey of [key, 'kansei-statistics-v2', 'kansei-statistics-v1']) {
        const v = JSON.parse(localStorage.getItem(storedKey));
        if (!v || typeof v.allowed !== 'boolean' || !Number.isFinite(v.at) ||
            Date.now() < v.at || Date.now() - v.at >= maxAge) continue;
        // Earlier refusals still apply; earlier approval does not enable campaign data.
        return storedKey === key || v.allowed === false ? v.allowed : null;
      }
      return null;
    } catch { return null; }
  };
  const save = allowed => {
    try { localStorage.setItem(key, JSON.stringify({allowed, at: Date.now()})); localStorage.removeItem('kansei-statistics-v1'); localStorage.removeItem('kansei-statistics-v2'); } catch {}
  };
  const cleanReferrer = () => {
    try {
      const u = new URL(document.referrer);
      return ['http:', 'https:'].includes(u.protocol) ? u.origin + '/' : '';
    } catch { return ''; }
  };
  const pageLocation = () => {
    try {
      const canonical = new URL(document.querySelector('link[rel="canonical"]')?.href || location.href);
      if (!['kansei.se','www.kansei.se'].includes(canonical.hostname)) return 'https://www.kansei.se/';
      const safe = new URL('https://www.kansei.se' + canonical.pathname);
      if (!granted) return safe.href;
      const incoming = new URL(location.href).searchParams;
      // Google aggregate campaign metadata, never individual click IDs or free text.
      for (const [name, pattern] of [
        ['gbraid', /^[A-Za-z0-9_-]{1,512}$/],
        ['gad_source', /^[0-9]{1,3}$/],
        ['gad_campaignid', /^[0-9]{1,20}$/]
      ]) {
        const values = incoming.getAll(name);
        if (values.length === 1 && pattern.test(values[0])) safe.searchParams.set(name, values[0]);
      }
      // Preserve this exact manual pair only when native aggregate metadata is absent.
      // Campaign names, terms, content, GCLID, DCLID and WBRAID remain excluded.
      if (!safe.search && incoming.getAll('utm_source').length === 1 &&
          incoming.get('utm_source') === 'google' && incoming.getAll('utm_medium').length === 1 &&
          incoming.get('utm_medium') === 'cpc') {
        safe.searchParams.set('utm_source', 'google');
        safe.searchParams.set('utm_medium', 'cpc');
      }
      return safe.href;
    } catch {}
    return 'https://www.kansei.se/';
  };
  // Strict referral-domain allowlist. No conversation IDs, form values or free-text campaign values.
  const classify = host => {
    const is = domain => host === domain || host.endsWith('.' + domain);
    if (is('chatgpt.com') || is('chat.openai.com')) return 'chatgpt';
    if (is('perplexity.ai')) return 'perplexity';
    if (is('copilot.microsoft.com') || is('copilot.cloud.microsoft')) return 'copilot';
    if (is('gemini.google.com')) return 'gemini';
    if (is('google.com') || is('google.se')) return 'google';
    if (is('bing.com')) return 'bing';
    return host ? 'other' : 'unknown';
  };
  const rememberSource = () => {
    if (!granted) return;
    if (sourceAt && Date.now() - sourceAt >= sourceMaxAge) source = 'unknown';
    sourceAt = Date.now();
    try { sessionStorage.setItem(sourceKey, JSON.stringify({group:source, at:Date.now()})); } catch {}
  };
  const resolveSource = () => {
    let host = '';
    try { host = new URL(document.referrer).hostname; } catch {}
    if (host && !['kansei.se','www.kansei.se'].includes(host)) source = classify(host);
    else {
      source = 'unknown';
      try {
        const v = JSON.parse(sessionStorage.getItem(sourceKey));
        if (v && groups.includes(v.group) && Number.isFinite(v.at) && Date.now() >= v.at && Date.now() - v.at < sourceMaxAge) source = v.group;
      } catch {}
    }
    sourceAt = Date.now();
    rememberSource();
  };
  const payload = () => ({
    send_to:id, page_location:pageLocation(), page_referrer:cleanReferrer(),
    page_title:document.title, referral_group:source, measurement_version:'20261101'
  });
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
    source = 'unknown';
    try { sessionStorage.removeItem(sourceKey); } catch {}
    removeCookies();
  };
  const enable = () => {
    granted = true;
    window['ga-disable-' + id] = false;
    window.KanseiMeasure = true;
    resolveSource();
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
    window.gtag('event', 'page_view', payload());
    const script = document.createElement('script');
    script.async = true;
    script.referrerPolicy = 'no-referrer';
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
    document.head.append(script);
  };
  document.addEventListener('kansei:booking-intent', e => {
    if (!granted || e.detail?.event !== 'booking_click') return;
    const placement = ['header','footer','guide','menu','content','price_list','article_visit','case_card','service_card'].includes(e.detail.placement)
      ? e.detail.placement : 'content';
    rememberSource();
    // The existing key event is emitted exactly once. Service events are a separate breakdown,
    // never additional conversions and never a booking confirmation.
    const fields = {...payload(), placement};
    window.gtag('event', 'booking_click', fields);
    const serviceEvent = {
      ultrasound:'booking_ultrasound_click', hyaluron:'booking_hyaluron_click',
      naprapathy:'booking_naprapathy_click', prp:'booking_prp_click',
      consultation:'booking_consultation_click', wellness:'booking_wellness_click',
      general:'booking_general_click'
    }[e.detail.service] || 'booking_general_click';
    window.gtag('event', serviceEvent, fields);
  });
  document.addEventListener('kansei:booking-guide', e => {
    const event = e.detail?.event;
    if (!granted || !['booking_guide_start', 'booking_guide_result_view'].includes(event)) return;
    rememberSource();
    // The same public guide identity applies regardless of the starting page or answers.
    window.gtag('event', event, {
      send_to:id, page_location:'https://www.kansei.se/hjalp-mig-boka/',
      page_title:'Hjälp mig boka rätt | Kansei', page_referrer:cleanReferrer(),
      referral_group:source, measurement_version:'20261107', placement:'guide'
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
    panel.setAttribute('aria-describedby','kansei-statistics-description');
    panel.hidden = true;
    panel.innerHTML = '<div class="kansei-statistics-inner"><div class="kansei-statistics-copy"><h2 id="kansei-statistics-heading">Valfri statistik</h2><p id="kansei-statistics-description">Vi mäter sidbesök, hur annonser leder hit och hur bokningshjälpen och länkar till olika besök används. Du kan ändra ditt val.</p></div><div class="kansei-statistics-controls"><div class="kansei-statistics-actions"><button type="button" data-statistics="no">Avstå</button><button type="button" data-statistics="yes">Godkänn</button></div><a class="kansei-statistics-info" href="/cookie/">Om cookies och ditt val</a></div></div>';
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
    (document.querySelector('.footer-preferences') || document.querySelector('.footer .wrap') || document.querySelector('.footer') || document.body).append(settings);
    const choice = read();
    if (choice === true) enable();
    else if (choice === false) deny();
    else { deny(); panel.hidden = false; }
  };
  window.addEventListener('storage', e => {
    if (e.key !== key && e.key !== null) return;
    if (read() === true) enable();
    else { deny(); if (panel) panel.hidden = read() !== null; }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once:true});
  else mount();
})();
