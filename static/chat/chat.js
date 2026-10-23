(function () {
  const messageStream = document.getElementById('message-stream');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');

  // Small helper: create an element with a class and optional text
  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  // Build a message element for the current user.
  // Using textContent (not innerHTML) keeps user input safe from HTML injection.
  function createMessageElement(text) {
    const message = createElement('div', 'message message-new');

    const avatarWrap = createElement('div', 'message-avatar-wrap');
    avatarWrap.appendChild(createElement('div', 'message-avatar-initials', 'AM'));
    avatarWrap.appendChild(createElement('span', 'status-dot is-online'));

    const header = createElement('div', 'message-header');
    header.appendChild(createElement('span', 'message-author', 'Alex Mercer'));
    header.appendChild(createElement('span', 'role-badge role-lead', 'Lead'));
    header.appendChild(createElement('span', 'message-time', 'Just now'));

    const body = createElement('div', 'message-body');
    body.appendChild(header);
    body.appendChild(createElement('p', 'message-text', text));

    message.appendChild(avatarWrap);
    message.appendChild(body);
    return message;
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    messageStream.appendChild(createMessageElement(text));
    chatInput.value = '';
    messageStream.scrollTop = messageStream.scrollHeight;
  }

  // Enter sends the message
  chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  // Copy code buttons: <button data-copy-target="id-of-code-element">
  document.querySelectorAll('[data-copy-target]').forEach(function (button) {
    button.addEventListener('click', function () {
      const target = document.getElementById(button.dataset.copyTarget);
      if (target && navigator.clipboard) {
        navigator.clipboard.writeText(target.innerText);
      }
    });
  });
})();
