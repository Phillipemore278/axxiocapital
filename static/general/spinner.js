// static/js/pinner.js
(function () {
  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.classList.contains('pinner-form')) return;

    const button = form.querySelector('button[type="submit"]');
    if (!button || button.dataset.pinned === 'true') return;

    // 🛑 ALWAYS stop native submit
    e.preventDefault();

    // ✅ Run HTML validation manually
    if (!form.checkValidity()) {
      form.reportValidity(); // shows "Fill out this field"
      return; // ⛔ DO NOT SUBMIT
    }

    // Read config
    const spinnerText = button.dataset.spinnerText || 'Loading...';
    const spinnerClass = button.dataset.spinnerClass;

    // Save state
    button.dataset.originalHtml = button.innerHTML;
    button.dataset.pinned = 'true';

    // Disable button
    button.disabled = true;

    if (spinnerClass) {
      button.className = `btn ${spinnerClass}`;
    }

    button.innerHTML = `
      <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
      ${spinnerText}
    `;

    // ✅ Submit ONLY after validation passes
    form.submit();
  });
})();
