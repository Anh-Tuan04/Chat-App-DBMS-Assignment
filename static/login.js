const form = document.getElementById('login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginButton = document.getElementById('login-button');
const errorBox = document.getElementById('login-error');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.textContent = '';
    loginButton.disabled = true;

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: usernameInput.value,
                password: passwordInput.value
            })
        });

        if (response.ok) {
            // Server accepted the login, go to the app page
            const result = await response.json();
            window.location.href = result.redirect;
            return;
        }

        if (response.status === 401) {
            errorBox.textContent = 'Sai tên người dùng hoặc mật khẩu.';
        } else if (response.status === 503) {
            errorBox.textContent = 'Dịch vụ đăng nhập tạm thời không khả dụng.';
        } else {
            errorBox.textContent = 'Đăng nhập thất bại.';
        }
    } catch (err) {
        console.error('Could not reach server:', err);
        errorBox.textContent = 'Không thể kết nối tới máy chủ.';
    } finally {
        loginButton.disabled = false;
    }
});