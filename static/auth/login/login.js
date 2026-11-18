(function () {
  localStorage.clear(); // Clear local storage on page load for demo purposes
  const BASE_URL = 'http://localhost:5000'; // Replace with your actual backend URL

  const loginForm = document.getElementById('login-form');
  const passwordInput = document.getElementById('login-password');
  const passwordToggleBtn = document.getElementById('password-toggle-btn');
  const passwordToggleIcon = document.getElementById('password-toggle-icon');

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

  // Prevent default submit (hook up your auth call here)
  if (loginForm) {
    loginForm.addEventListener('submit', async function (event) {
      event.preventDefault();
      const identifier = document.getElementById('login-identifier').value;
      const password = passwordInput.value;
        try {
          let res = await fetch(`/api/auth/login`, {
            method: 'POST',
            credentials: 'include', // Include cookies for session management
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              username: identifier,
              password: password
            }),
          });

          if (res.ok) {
            //navigate page to chat.html
            //save user data to local storage
            const userData = await res.json();
            localStorage.setItem('user', JSON.stringify(userData));

            window.location.href = '/chat';
          } else {
            const errorData = await res.json();
            const errorMessage = errorData?.message || 'Login failed';
            showToast(errorMessage, 'error');
          }
        } catch (error) {
          showToast('An error occurred during login', 'error');
        }

      // Once the auth call is wired up, report the outcome with:
      //   showToast('Welcome back!', 'success');
      //   showToast(errorMessage || 'Login failed', 'error');
      // (make this handler `async` if you use await)
    });
  }

  // Placeholder navigation links
  document.querySelectorAll('[data-path]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      // Route to link.dataset.path ("forgot-password" | "register")
      showToast('Navigation not implemented in this demo', 'info');
      if (link.dataset.path === 'register') {
        window.location.replace('/register');
      }
    });
  });
})();