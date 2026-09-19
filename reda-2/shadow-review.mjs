// Review support only. This summary never authorizes or applies a plan change.
const verdicts = new Set(['agree', 'disagree', 'uncertain']);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const list = value => Array.isArray(value) ? value : [];
const reviewOf = decision => {
  const review = Array.isArray(decision.review) ? decision.review[0] : decision.review;
  return verdicts.has(review?.verdict) ? review.verdict : null;
};

export function shadowReview({frame, activePlanId, decisions = [], cases = [], now = new Date()} = {}) {
  if (frame?.status !== 'approved' || frame.execution !== 'shadow') return null;
  const step = frame.current_step;
  const scoped = list(decisions).filter(d => d.id && d.frame_id === frame.id &&
    d.plan_id === frame.current_plan_id && d.step === step);
  const unique = [...new Map(scoped.map(d => [d.id, d])).values()]
    .sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0));
  const counts = {total: unique.length, agree: 0, disagree: 0, uncertain: 0, unreviewed: 0};
  for (const d of unique) counts[reviewOf(d) || 'unreviewed']++;
  const findings = [];
  const today = new Intl.DateTimeFormat('sv-SE', {timeZone: 'Europe/Stockholm'}).format(now);
  const policy = frame.policy;
  if (!activePlanId || frame.current_plan_id !== activePlanId) findings.push('Ramen hör inte till den aktuella planversionen.');
  if (!policy?.validFrom || !policy?.validUntil || today < policy.validFrom || today > policy.validUntil) findings.push('Ramens giltighet behöver kontrolleras.');
  const openCases = list(cases).filter(c => c.status !== 'resolved').length;
  if (openCases) findings.push(`${openCases} visade ärenden behöver bedömas. Kvitterade ärenden räknas fortfarande som öppna.`);
  if (counts.disagree) findings.push('Det finns avvikande bedömningar att följa upp.');
  if (counts.uncertain) findings.push('Du har markerat otillräckligt underlag i granskningen.');
  const latest = unique[0];
  if (latest?.applied) findings.push('Ett tillämpat beslut finns i granskningsläget. Kontrollera historiken.');
  if (latest && !['advance', 'complete'].includes(latest.action)) findings.push('EI:s senaste beslut innebär att avvakta eller bedöma underlaget.');
  const next = unique.find(d => !reviewOf(d));
  return {counts, findings, nextId: next?.id || null, step: Number.isInteger(step) ? step + 1 : null,
    state: findings.length ? 'attention' : counts.unreviewed ? 'review' : counts.total ? 'reviewed' : 'empty',
    // Readiness cannot be inferred from a bounded decision history or review count.
    canEnableAutomatic: false};
}

export function renderShadowReview(summary) {
  if (!summary) return '';
  const {counts: c, findings, state, step} = summary;
  const title = {attention:'Följ upp innan du går vidare', review:'Jämför EI med din bedömning', reviewed:'De visade besluten är granskade', empty:'Börja samla granskningsunderlag'}[state];
  const metric = (value, label) => `<div><strong>${value}</strong><span>${label}</span></div>`;
  return `<section class="shadow-review" data-shadow-state="${esc(state)}" aria-label="Granskning av EI">
    <p class="eyebrow">Granskningsläge${step ? ' · steg ' + step : ''}</p><h4>${esc(title)}</h4>
    <p>Följ hur EI bedömer patientens underlag innan du tar ställning till automatisk progression.</p>
    <div class="shadow-review-counts">${metric(c.agree,'Instämmer')}${metric(c.disagree,'Avvikande')}${metric(c.uncertain,'Otillräckligt underlag')}${metric(c.unreviewed,'Ogranskade')}</div>
    ${findings.length ? '<ul>' + findings.map(f => '<li>' + esc(f) + '</li>').join('') : ''}
    ${summary.nextId ? '<button type="button" class="btn ghost" data-next-shadow-review>Granska nästa beslut</button>' : !c.total ? '<p>Pröva aktuellt underlag för att spara EI:s första bedömning.</p>' : ''}
    <p class="shadow-review-note">Visar beslut för aktuell ram, planversion och nivå bland de senaste 20 besluten. Flera beslut kan bygga på samma träningssvar. Översikten ger inget automatiskt klartecken och ändrar ingen ordination.</p>
  </section>`;
}
