const printButton = document.getElementById('skriv-ut');
const question = document.getElementById('fragestallning');
const visitChoices = document.querySelectorAll('input[name="besok"]');
const printVisit = document.getElementById('utskrift-besok');
const printQuestion = document.getElementById('utskrift-fraga');

function fillPrintView() {
  const selectedVisit = document.querySelector('input[name="besok"]:checked');
  printVisit.textContent = selectedVisit?.value ?? '';
  printQuestion.textContent = question.value.trim();
}

printButton.hidden = false;
printButton.addEventListener('click', () => {
  fillPrintView();
  window.print();
});
window.addEventListener('beforeprint', fillPrintView);
window.addEventListener('pagehide', () => {
  question.value = '';
  visitChoices.forEach((choice) => { choice.checked = false; });
  fillPrintView();
});
