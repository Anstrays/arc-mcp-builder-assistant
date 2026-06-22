// Minimal Arc Job Escrow Starter - dependency-free local interactions only.
document.getElementById('next').addEventListener('click', advance);
const steps = ['s-post', 's-accept', 's-fund', 's-submit', 's-release'];
let index = 0;
function advance() {
  if (index < steps.length - 1) {
    document.getElementById(steps[index]).className = 'done';
    index++;
    document.getElementById(steps[index]).className = 'active';
  }
  if (index === steps.length - 1) {
    document.getElementById('next').disabled = true;
  }
}
