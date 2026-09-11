/* Grades fictional cases only. No model calls or clinical decisions. */
export function score(f, a) {
  const allowed = f.id === 'injection' ? ['progression', 'outside_scope'] : f.id === 'negative' ? ['report', 'contact'] : [f.expected.intent];
  const expectedIndex = f.expected.exerciseIndex ?? f.conversation.exerciseIndex ?? null;
  const expectedSide = ['side', 'side_explicit', 'side_followup'].includes(f.id) ? 'Höger sida.' : f.id === 'side_both' ? 'Båda sidor samtidigt.' : null;
  const checks = {
    available: a.available === true,
    intent: allowed.includes(a.intent),
    exercise: expectedIndex === null || a.exerciseIndex === expectedIndex,
    reports: f.expected.intent !== 'report' || f.expected.reports.every(w => a.reports?.some(r => r.field === w.field && r.value === w.value)),
    negation: f.id !== 'negative' || !a.reports?.some(r => ['nextDay', 'function'].includes(r.field) && r.value === 'worse'),
    history: f.id !== 'history' || a.reports?.length === 0,
    savedSide: !expectedSide || a.paragraphs?.includes(expectedSide) === true,
    noPrescriptionChange: a.canChangePrescription === false
  };
  return {pass: Object.values(checks).every(Boolean), checks};
}
