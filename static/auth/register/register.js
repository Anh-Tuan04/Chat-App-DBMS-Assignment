(function () {
  localStorage.clear(); // Clear local storage on page load for demo purposes
  const BASE_URL = 'http://localhost:5000'; // Replace with your actual backend URL

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

  /* ---------- Toast ---------- */
  const TOAST_DURATION_MS = 2500;
  const TOAST_ICONS = {
    info: 'info',
    success: 'check_circle',
    error: 'error',
  };

  /*
  HTML Skeleton Reference:
  <div class="toast toast-error" role="status" aria-live="polite">
    <span class="material-symbols-outlined toast-icon">error</span>
    <span class="toast-message">Login failed</span>
  </div>
  */

  // Programmatic DOM Construction:
  function createToast(text, type) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');

    const icon = document.createElement('span');
    icon.className = 'material-symbols-outlined toast-icon';
    icon.textContent = TOAST_ICONS[type];

    const message = document.createElement('span');
    message.className = 'toast-message';
    message.textContent = text;

    toast.append(icon, message);

    return toast;
  }

  let activeToast = null;
  let toastTimer = null;

  function showToast(text, type) {
    type = TOAST_ICONS[type] ? type : 'info';

    // Only one toast at a time: replace the current one
    clearTimeout(toastTimer);
    if (activeToast) activeToast.remove();

    activeToast = createToast(text, type);
    document.body.appendChild(activeToast);

    toastTimer = setTimeout(function () {
      if (activeToast) activeToast.remove();
      activeToast = null;
    }, TOAST_DURATION_MS);
  }

  // Show / hide password
  if (passwordToggleBtn && passwordInput && passwordToggleIcon) {
    passwordToggleBtn.addEventListener('click', function () {
      const isHidden = passwordInput.getAttribute('type') === 'password';
      passwordInput.setAttribute('type', isHidden ? 'text' : 'password');
      passwordToggleIcon.textContent = isHidden ? 'visibility_off' : 'visibility';
    });
  }

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
    registerForm.addEventListener('submit', async function (event) {
      event.preventDefault();
      const displayName = document.getElementById('signup-display-name').value;
      const username = document.getElementById('signup-username').value;
      const password = passwordInput.value;

  
      try {
        // Call your sign-up function here
        let res = await fetch(`/api/auth/register`, {
          method: 'POST',
          credentials: 'include', // Include cookies for session management
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            displayName: displayName,
            username: username,
            password: password
          }),
        });

        if (!res.ok) {
          const errorData = await res.json();
          showToast(errorData.message || 'Registration failed', 'error');
        }

        //save user data to local storage
        const userData = await res.json();
        localStorage.setItem('user', JSON.stringify(userData));

        window.location.href = '/chat'; // Redirect to chat page on success

      } catch (error) {
        showToast(error.message, 'error');
      }
  
    });
  }

  // Placeholder navigation link
  document.querySelectorAll('[data-path]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      // Route to link.dataset.path ("login")

      if (link.dataset.path === 'login') {
        window.location.replace('/');
      }
    });
  });
})();
