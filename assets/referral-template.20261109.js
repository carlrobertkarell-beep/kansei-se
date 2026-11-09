const printButton = document.getElementById('skriv-ut');
const question = document.getElementById('fragestallning');
const visitChoices = document.querySelectorAll('input[name="besok"]');
const printVisit = document.getElementById('utskrift-besok');
const printQuestion = document.getElementById('utskrift-fraga');

function updatePreview() {
  const selectedVisit = document.querySelector('input[name="besok"]:checked');
  printVisit.textContent = selectedVisit?.value ?? '';
  printQuestion.textContent = question.value.trim();
}

printButton.hidden = false;
question.addEventListener('input', updatePreview);
visitChoices.forEach((choice) => choice.addEventListener('change', updatePreview));
updatePreview();
printButton.addEventListener('click', () => {
  updatePreview();
  window.print();
});
window.addEventListener('beforeprint', updatePreview);
window.addEventListener('pagehide', () => {
  question.value = '';
  visitChoices.forEach((choice) => { choice.checked = false; });
  updatePreview();
});
