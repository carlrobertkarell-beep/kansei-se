window.KanseiBooking={"naprapati":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/naprapati-ny-resp-aterbesok-3263299","label":"Boka naprapati","price":"890 kr"},"ultraljud":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-naprapati-rehabcenter-48847/muskuloskeletalt-ultraljud-1946824","label":"Boka ultraljud","price":"1 290 kr"},"akupunktur":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/naprapati-ny-resp-aterbesok-3263299","label":"Boka naprapati","price":"890 kr"},"rehabilitering":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/naprapati-ny-resp-aterbesok-3263299","label":"Boka rehabbesök","price":"890 kr"},"prp":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/konsultation-infor-injektionsbehandling-3409513","label":"Boka konsultation","price":"890 kr"},"hyaluronsyra":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-naprapati-rehabcenter-48847/hyaluronsyra-sinovial-hl-64-3409516","label":"Boka hyaluron","price":"Från 2 490 kr"},"kortison":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/konsultation-infor-injektionsbehandling-3409513","label":"Boka konsultation","price":"890 kr"},"injektioner":{"url":"https://www.bokadirekt.se/boka-tjanst/kansei-rehabcenter-48847/konsultation-infor-injektionsbehandling-3409513","label":"Boka konsultation","price":"890 kr"}};
/* In-memory booking guidance. Only the two generic funnel events are measured. */
window.KanseiGuide = function(ctx) {
  'use strict';

  const {$, escapeHTML: html, areas, prepareLinks, listen, guide, content, openDialog} = ctx;

  const {goals, resolve} = window.KanseiGuideRoutes;
  const jointAreas = ['shoulder', 'knee', 'hip'];
  const legAreas = ['knee', 'lowerLeg', 'foot'];
  const calfSource = 'https://www.1177.se/sjukdomar--besvar/hjarta-och-blodkarl/blodkarl/blodpropp-i-benet/';
  const measured = new Set();
  const emptyState = () => ({area: null, pattern: null, goal: null, assessedJoint: null, intent: null, screen: 'areas', history: []});
  let state = emptyState();

  function measure(event) {
    if (window.KanseiMeasure !== true || measured.has(event)) return;
    measured.add(event);
    document.dispatchEvent(new CustomEvent('kansei:booking-guide', {detail: {event}}));
  }

  function heading(title) {
    return `<h2 id="guide-title" tabindex="-1">${html(title)}</h2>`;
  }

  function choice(attribute, value, title, description = '', selected = false) {
    return `<button class="guide-choice" type="button" ${attribute}="${html(value)}"${selected ? ' data-current-choice' : ''}><span><b>${html(title)}</b>${description ? `<small>${html(description)}</small>` : ''}</span></button>`;
  }

  function routeLink(href, label, cls = 'text-link') {
    const [path, anchor] = href.split('#');
    return `<a class="${cls}" href="${html(href)}" data-route="${html(path)}"${anchor ? ` data-destination-anchor="${html(anchor)}"` : ''}>${html(label)}</a>`;
  }

  function progress(label, number) {
    const back = state.screen === 'areas'
      ? '<span class="guide-task-label">Hitta rätt besök</span>'
      : '<button class="guide-back" type="button" data-guide-back>Tillbaka<span class="sr-only"> till föregående steg</span></button>';
    return `<div class="guide-progress">${back}<span class="guide-step">${number ? `Steg ${number} av 4` : html(label)}</span></div>${number ? `<div class="guide-progress-track" role="progressbar" aria-label="Steg i bokningsguiden" aria-valuemin="0" aria-valuemax="4" aria-valuenow="${number}" style="--guide-progress:${number * 25}%"></div>` : ''}`;
  }

  function areaChip(area) {
    return `<span class="guide-current-area">${html(area.label)}</span>`;
  }

  function restart() {
    return '<div class="guide-actions"><button class="guide-back" type="button" data-reset>Börja om</button></div>';
  }

  function bookingLink(visit, cls) {
    return `<a class="${cls}" data-measure="booking_click" data-placement="guide" href="${html(visit.url)}" target="_blank" rel="noopener noreferrer">${html(visit.label)}<span class="sr-only">, ny flik</span></a>`;
  }

  function action(route, main = false) {
    const visit = route.bookingKey && window.KanseiBooking[route.bookingKey];
    if (!main) return routeLink(route.href, route.label);
    if (!visit) return `<div class="guide-booking">${routeLink(route.href, route.label, 'button button-dark')}</div>`;
    return `<div class="guide-booking"><p class="guide-price"><span>Pris för besöket</span><strong>${html(visit.price)}</strong></p>${bookingLink(visit, 'button button-dark')}<small class="guide-booking-note">Välj tid och bekräfta på Bokadirekt.</small></div>`;
  }

  function renderResult(area, pattern) {
    const {primary, alternative, patientCase, nextSteps, related} = resolve({
      area: state.area, pattern: state.pattern, goal: state.goal, assessedJoint: state.assessedJoint
    });
    const selectedGoal = goals.find(item => item.id === state.goal);
    const summary = [pattern?.[1], selectedGoal?.label].filter(Boolean).map(html).join(' · ');
    const comparison = alternative ? `<details class="guide-comparison"><summary>Jämför två alternativ</summary><div class="guide-comparison-grid"><div><h3>${html(primary.title)}</h3><p>${html(primary.reason)}</p></div><div><h3>${html(alternative.title)}</h3><p>${html(alternative.reason)}</p>${action(alternative)}</div></div></details>` : '';
    const caseLink = patientCase ? `<div class="guide-case"><span class="eyebrow">PATIENTFALL FRÅN KANSEI</span>${routeLink(patientCase.href, patientCase.title)}</div>` : '';
    const steps = Array.isArray(nextSteps) ? nextSteps : [nextSteps];
    return progress('', 4) + areaChip(area) + heading('Ditt nästa steg') +
      `<p class="result-summary">${summary}</p>
       <div class="result-main"><span class="eyebrow">${primary.id === 'hyaluron' ? 'BEHANDLING ATT LÄSA OM' : 'FÖRSLAG PÅ BESÖK'}</span><h3>${html(primary.title)}</h3><p class="guide-visit-copy">${html(primary.reason)}</p>${action(primary, true)}</div>
       <section class="guide-result-next" aria-label="Efter ditt val"><h3>Vad händer sedan?</h3><ul class="guide-next-steps">${steps.filter(Boolean).map(step => `<li>${html(step)}</li>`).join('')}</ul></section>
       ${comparison}${caseLink}${related ? `<div class="result-links">${routeLink(related.href, related.title)}</div>` : ''}
       <div class="result-details"><details><summary>Vad tittar ni på?</summary><p>${html(area.focus)}</p></details><details><summary>Behöver jag ultraljud?</summary><p>${html(area.imaging)}</p></details></div>
       <p class="guide-small">Guiden hjälper dig att välja besök. Den kan inte bedöma dina besvär eller avgöra vilken behandling som passar.</p>
       <div class="guide-actions"><button class="guide-back" type="button" data-edit-goal>Ändra mål med besöket</button><button class="guide-back" type="button" data-reset>Börja om</button></div>`;
  }

  function render() {
    const area = areas[state.area];
    const pattern = area?.patterns.find(item => item[0] === state.pattern);
    let markup;
    switch (state.screen) {
      case 'areas': {
        const options = Object.entries(areas).filter(([key]) => state.intent !== 'injection' || jointAreas.includes(key));
        const title = state.intent === 'injection' ? 'Vilken led gäller det?' : 'Var har du besvär?';
        const intro = state.intent === 'injection'
          ? 'Välj området du vill veta mer om. Du får svara på om leden redan har bedömts.'
          : 'Välj området som besvärar dig mest. Vi hjälper dig att hitta ett första besök.';
        markup = progress('', 1) + heading(title) + `<p>${intro}</p><div class="guide-choices">${options.map(([key, item]) => choice('data-guide-area', key, item.label, '', key === state.area)).join('')}</div><div class="guide-actions"><button class="guide-back" type="button" data-guide-services>Jag söker en viss tjänst</button><button class="guide-back" type="button" data-guide-care>Akuta besvär?</button></div>`;
        break;
      }
      case 'patterns':
        markup = progress('', 1) + areaChip(area) + heading(area.question) +
          `<p>Välj det som ligger närmast hur du har det.</p><div class="guide-choices">${area.patterns.map(item => choice('data-pattern', item[0], item[1], item[2], state.pattern === item[0])).join('')}${choice('data-pattern', 'unclear', 'Svårt att beskriva', 'Jag vill börja med en bedömning.', state.pattern === 'unclear')}</div>` + restart();
        break;
      case 'goals': {
        const options = goals.filter(item => item.id !== 'injection' || jointAreas.includes(state.area));
        markup = progress('', 2) + areaChip(area) + heading('Vad vill du få hjälp med?') +
          `<p>Välj det som är viktigast med besöket just nu.</p><div class="guide-choices">${options.map(item => choice('data-goal', item.id, item.label, item.description, state.goal === item.id)).join('')}</div>` + restart();
        break;
      }
      case 'prior':
        markup = progress('', 2) + areaChip(area) + heading('Har ledbesväret redan bedömts?') +
          `<p>En tidigare bedömning hjälper oss att visa rätt information inför ett eventuellt injektionsbesök.</p><div class="guide-choices">${choice('data-prior', 'yes', 'Ja, leden är bedömd', 'Jag vill veta mer om injektionsalternativ.', state.assessedJoint === true)}${choice('data-prior', 'no', 'Nej, eller jag är osäker', 'Jag behöver hjälp att förstå vad som besvärar mig.', state.assessedJoint === false)}</div>` + restart();
        break;
      case 'safety':
        markup = progress('', 3) + areaChip(area) + heading('Behöver du sjukvård först?') +
          `<p>Kansei tar emot för planerade besök. Akuta eller snabbt försämrade besvär kan behöva bedömas av annan vård.</p>
           <div class="safety-box"><strong>Stämmer något av detta?</strong><ul><li>Ny skada med mycket ont eller svårt att belasta.</li><li>En röd, varm eller svullen led tillsammans med feber eller sjukdomskänsla.</li><li>Ny eller snabbt ökande svaghet. Ryggsmärta med nedsatt känsel i underlivet eller problem att kontrollera urin eller avföring.</li>${legAreas.includes(state.area) ? '<li>Ny svullnad och värme i ena vaden eller benet.</li>' : ''}</ul></div>
           <div class="guide-choices">${choice('data-safety', 'care', 'Ja, eller jag är osäker', 'Visa hur jag får hjälp att hitta rätt vård.')}${choice('data-safety', 'continue', 'Nej, fortsätt till bokningshjälpen')}</div>
           <p class="guide-small">Även andra symtom kan behöva bedömas. Kontakta 1177 om du känner oro eller är osäker.</p>` + restart();
        break;
      case 'care':
        markup = progress('Vårdhänvisning') + heading('Börja inte med en vanlig bokning.') +
          `<p>Ny skada, tydliga varningssymtom eller osäkerhet om hur bråttom det är behöver bedömas av sjukvården.</p><div class="warning-box"><strong>Kontakta vården utan att vänta på en bokning här.</strong>Ring 1177 för vägledning. Vid tecken på ett livshotande tillstånd, till exempel svår bröstsmärta eller andningssvårigheter, ring 112.</div><div class="result-links"><a class="button button-dark" href="tel:1177">Ring 1177</a><a class="button button-ghost" href="tel:112">Ring 112 vid akut fara</a></div><p class="guide-source">Läs hos <a href="${legAreas.includes(state.area) ? calfSource : 'https://www.1177.se/'}" target="_blank" rel="noopener noreferrer">1177<span class="sr-only">, ny flik</span></a>.</p>` + restart();
        break;
      case 'result':
        markup = renderResult(area, pattern);
        break;
      case 'services': {
        const services = [
          ['/naprapati/', 'Naprapati', 'Undersökning, behandling och uppföljning.'],
          ['/ultraljud/', 'Muskuloskeletalt ultraljud', 'För en riktad frågeställning.'],
          ['/hyaluronsyra/', 'Hyaluron', 'Läs om behandling, bedömning och bokning.'],
          ['/prp/', 'PRP (ACP)', 'Läs om PRP och hur besöket går till.'],
          ['/rehabilitering/', 'Rehab & uppföljning', 'Följ planen med din behandlare.']
        ];
        markup = progress('Välj tjänst') + heading('Välj besöket du söker.') +
          `<p>Här hittar du information om besöken och hur du bokar.</p><div class="guide-choices">${services.map(([path, title, text]) => `<a class="guide-choice" href="${path}" data-route="${path}"><span><b>${html(title)}</b><small>${html(text)}</small></span></a>`).join('')}</div>` + restart();
        break;
      }
    }
    content.innerHTML = markup;
    content.dataset.guideScreen = state.screen;
    prepareLinks(content);
    guide.scrollTop = 0;
    if (guide.open) $('#guide-title', content)?.focus({preventScroll: true});
    if (state.screen === 'result') measure('booking_guide_result_view');
  }

  function move(screen) {
    state.history.push(state.screen);
    state.screen = screen;
    render();
  }

  function chooseGoal(goal) {
    state.goal = goal;
    state.assessedJoint = goal === 'injection' && state.area === 'knee' && state.pattern === 'arthritis' ? true : null;
    move(goal === 'injection' && jointAreas.includes(state.area) && state.assessedJoint !== true ? 'prior' : 'safety');
  }

  function choosePattern(value) {
    const item = areas[state.area]?.patterns.find(pattern => pattern[0] === value);
    if (!item && value !== 'unclear') return;
    state.pattern = value;
    state.assessedJoint = null;
    if (item?.[4]) move('care');
    else if (state.intent) chooseGoal(state.intent);
    else move('goals');
  }

  function start(opener, area = null, screen = null, initialPattern = null, intent = null) {
    state = emptyState();
    if (goals.some(item => item.id === intent)) state.intent = intent;
    if (area && Object.hasOwn(areas, area)) {
      state.area = area;
      state.screen = 'patterns';
      state.history = ['areas'];
    }
    if (screen) state.screen = screen;
    openDialog(guide, opener);
    if (!screen) measure('booking_guide_start');
    if (state.area && initialPattern && areas[state.area].patterns.some(item => item[0] === initialPattern)) choosePattern(initialPattern);
    else render();
  }

  listen(content, 'click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    const {guideArea, pattern, goal, prior, safety} = button.dataset;
    if (guideArea && Object.hasOwn(areas, guideArea)) {
      Object.assign(state, {area: guideArea, pattern: null, goal: null, assessedJoint: null});
      measure('booking_guide_start');
      move('patterns');
    } else if (pattern) choosePattern(pattern);
    else if (goal && goals.some(item => item.id === goal)) chooseGoal(goal);
    else if (prior) {
      state.assessedJoint = prior === 'yes';
      move('safety');
    } else if (safety) move(safety === 'continue' ? 'result' : 'care');
    else if (button.hasAttribute('data-guide-back')) {
      state.screen = state.history.pop() || 'areas';
      render();
    } else if (button.hasAttribute('data-reset')) {
      state = emptyState();
      render();
    } else if (button.hasAttribute('data-edit-goal')) {
      state.intent = null;
      state.screen = 'goals';
      state.history = ['areas', 'patterns'];
      render();
    } else if (button.hasAttribute('data-guide-services')) move('services');
    else if (button.hasAttribute('data-guide-care')) move('care');
  });

  return {start, reset: () => { state = emptyState(); }};
};
