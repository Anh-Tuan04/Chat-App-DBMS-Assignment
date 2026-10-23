(function () {
  const loginForm = document.getElementById('login-form');
  const passwordInput = document.getElementById('login-password');
  const passwordToggleBtn = document.getElementById('password-toggle-btn');
  const passwordToggleIcon = document.getElementById('password-toggle-icon');

  // Show / hide password
  if (passwordToggleBtn && passwordInput && passwordToggleIcon) {
    passwordToggleBtn.addEventListener('click', function () {
      const isHidden = passwordInput.getAttribute('type') === 'password';
      passwordInput.setAttribute('type', isHidden ? 'text' : 'password');
      passwordToggleIcon.textContent = isHidden ? 'visibility_off' : 'visibility';
    });
  }

  // Prevent default submit (hook up your auth call here)
  if (loginForm) {
    loginForm.addEventListener('submit', function (event) {
      event.preventDefault();
      // const identifier = document.getElementById('login-identifier').value;
      // const password = passwordInput.value;
    });
  }

  // Placeholder navigation links
  document.querySelectorAll('[data-path]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      // Route to link.dataset.path ("forgot-password" | "register")
    });
  });
})();
