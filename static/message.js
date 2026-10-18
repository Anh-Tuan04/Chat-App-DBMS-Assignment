document.getElementById('message-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (!message) return;

    try {
        const response = await fetch('/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: message })
        });
        if (response.status === 401) {
            // The session is gone (e.g. the server restarted): sign in again
            window.location.href = '/';
            return;
        }

        if (response.ok) {
            const container = document.getElementById('messages-container');

            const wrapper = document.createElement('div');
            wrapper.className = 'message user';

            const avatar = document.createElement('div');
            avatar.className = 'avatar-placeholder';

            const content = document.createElement('div');
            content.className = 'message-content user';
            content.textContent = message;   // sanitize user's input

            wrapper.append(avatar, content);
            container.append(wrapper);
            container.scrollTop = container.scrollHeight;
            messageInput.value = '';
        } else {
            console.error('Server did not accept the message:', response.status);
        }
    } catch (err) {
        console.error('Could not reach server:', err);
    }
});