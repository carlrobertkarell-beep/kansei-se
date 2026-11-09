const copyButton = document.getElementById('kopiera');
const question = document.getElementById('fragestallning');
const visitChoices = document.querySelectorAll('input[name="besok"]');
const referralText = document.getElementById('hanvisningstext');
const copyStatus = document.getElementById('kopierings-hjalp');

function updatePreview() {
  const visit = document.querySelector('input[name="besok"]:checked')?.value;
  const questionText = question.value.trim();
  const lines = visit ? ['Hänvisning till Kansei', `Önskemål om besök: ${visit}`] : [];

  if (visit && questionText) lines.push(`Frågeställning: ${questionText}`);

  referralText.value = lines.join('\n');
  copyButton.disabled = !visit;
  copyStatus.textContent = visit
    ? 'Skicka sedan texten via den säkra kanal som du och Kansei kommit överens om.'
    : 'Välj ett önskemål för att kopiera texten.';
}

copyButton.hidden = false;
question.addEventListener('input', updatePreview);
visitChoices.forEach((choice) => choice.addEventListener('change', updatePreview));
updatePreview();

copyButton.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(referralText.value);
    copyStatus.textContent = 'Hänvisningen är kopierad. Klistra in den i den säkra kanalen.';
  } catch {
    referralText.focus();
    referralText.select();
    copyStatus.textContent = 'Texten är markerad. Kopiera den och klistra in den i den säkra kanalen.';
  }
});

window.addEventListener('pagehide', () => {
  question.value = '';
  visitChoices.forEach((choice) => { choice.checked = false; });
  updatePreview();
});
