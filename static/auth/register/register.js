(function () {
  const registerForm = document.getElementById('register-form');
  const passwordInput = document.getElementById('signup-password');
  const passwordToggleBtn = document.getElementById('password-toggle-btn');
  const passwordToggleIcon = document.getElementById('password-toggle-icon');
  const strengthBars = [
    document.getElementById('strength-bar-1'),
    document.getElementById('strength-bar-2'),
    document.getElementById('strength-bar-3'),
    document.getElementById('strength-bar-4')
  ];

  // Strength levels, indexed by score - 1
  const STRENGTH_LEVELS = ['weak', 'fair', 'good', 'strong'];

  // Show / hide password
  if (passwordToggleBtn && passwordInput && passwordToggleIcon) {
    passwordToggleBtn.addEventListener('click', function () {
      const isHidden = passwordInput.getAttribute('type') === 'password';
      passwordInput.setAttribute('type', isHidden ? 'text' : 'password');
      passwordToggleIcon.textContent = isHidden ? 'visibility_off' : 'visibility';
    });
  }

  // Password strength meter
  function calculateStrengthScore(value) {
    let score = 0;
    if (value.length >= 6) score++;
    if (value.length >= 10) score++;
    if (/[A-Z]/.test(value) && /[0-9]/.test(value)) score++;
    if (/[^A-Za-z0-9]/.test(value)) score++;
    return score;
  }

  function updateStrengthBars(score) {
    // Reset all bars
    strengthBars.forEach(function (bar) {
      bar.className = 'strength-bar';
    });

    if (score === 0) return;

    const level = STRENGTH_LEVELS[score - 1];
    for (let i = 0; i < score; i++) {
      strengthBars[i].classList.add('is-' + level);
    }
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', function () {
      updateStrengthBars(calculateStrengthScore(passwordInput.value));
    });
  }

  // Prevent default submit (hook up your sign-up call here)
  if (registerForm) {
    registerForm.addEventListener('submit', function (event) {
      event.preventDefault();
      // const displayName = document.getElementById('signup-display-name').value;
      // const username = document.getElementById('signup-username').value;
      // const password = passwordInput.value;
    });
  }

  // Placeholder navigation link
  document.querySelectorAll('[data-path]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      // Route to link.dataset.path ("login")
    });
  });
})();
