import { messageStream } from './messages-stream.js';
import { realTimeSocket } from '../real-time-socket.js';
import { setConversationPreview } from '../conversation.js';
import { showError } from '../error.js';
import { showToast } from '../toast.js';

/* Message menu: "Delete for you" and "Delete for everyone".
   Open it with the "..." button of a message (shown on hover) or a right click on the message.
   The menu is put INSIDE the message element, so it scrolls with that message.
   Close it with the X button, a click anywhere outside it, or Esc.

   Socket events (no ack, the answer is an event):
     emit 'delete_message_for_me'  { conversation_id, message_id }
       -> 'message_deleted_for_me' { conversation_id, message_id }      (every tab of this user)
     emit 'recall_message'         { conversation_id, message_id }      (own messages only)
       -> 'message_recalled'       { conversation_id, message_id, recalled_by, [latest_message] }
                                                                         (every member, sender included)
     any failure
       -> 'delete_message_error'   { status, action, message, conversation_id, message_id }
                                                                         (only the requesting socket)
   Payload shapes: src/modules/real_time_socket/emitters/messages.py */

const PENDING_TIMEOUT_MS = 10000;   // no answer by then: give the message back
const MENU_GAP_PX = 8;

let openMenu = null;                // the .message-menu on screen, or null
const pendingDeletes = new Map();   // message_id -> { action, timer } for requests of THIS tab

/* ---------- 1. Helpers ---------- */

const findMessageElement = (messageId) =>
  messageStream.querySelector('.message[data-message-id="' + CSS.escape(String(messageId)) + '"]');

const isOwnMessage = (messageElement) => messageElement.classList.contains('message-own');

// Removes a message from the stream, and its date divider when no message of that day is left
const removeMessageElement = (messageElement) => {
  if (openMenu && messageElement.contains(openMenu)) closeMessageMenu();

  const previous = messageElement.previousElementSibling;
  const next = messageElement.nextElementSibling;
  messageElement.remove();

  const dayIsEmpty = !next || next.classList.contains('date-divider');
  if (previous && previous.classList.contains('date-divider') && dayIsEmpty) previous.remove();
};

/* ---------- 2. Create HTML ---------- */

/*
HTML Skeleton Reference:
<span class="material-symbols-outlined">close</span>
*/
const createIcon = (name) => {
  const icon = document.createElement('span');
  icon.classList.add('material-symbols-outlined');
  icon.textContent = name;
  return icon;
};

/*
HTML Skeleton Reference:
<button class="message-menu-item [is-danger]" type="button" role="menuitem" data-action="delete-for-me" [disabled]>
  <span class="material-symbols-outlined">visibility_off</span>
  <span class="message-menu-text">
    <span class="message-menu-label">Delete for you</span>
    <span class="message-menu-hint">Other members still see it</span>
  </span>
</button>
*/
const createMenuItem = ({ action, icon, label, hint, isDanger = false, disabled = false }) => {
  const labelText = document.createElement('span');
  labelText.classList.add('message-menu-label');
  labelText.textContent = label;

  const hintText = document.createElement('span');
  hintText.classList.add('message-menu-hint');
  hintText.textContent = hint;

  const text = document.createElement('span');
  text.classList.add('message-menu-text');
  text.appendChild(labelText);
  text.appendChild(hintText);

  const item = document.createElement('button');
  item.classList.add('message-menu-item');
  if (isDanger) item.classList.add('is-danger');
  item.type = 'button';
  item.setAttribute('role', 'menuitem');
  item.dataset.action = action;
  item.disabled = disabled;
  item.appendChild(createIcon(icon));
  item.appendChild(text);
  return item;
};

/*
HTML Skeleton Reference:
<div class="message-menu [opens-up]" role="menu" aria-label="Message options">
  <div class="message-menu-header">
    <span class="message-menu-title">Delete message</span>
    <button class="message-menu-close" type="button" data-action="close-message-menu" title="Close" aria-label="Close">
      <span class="material-symbols-outlined">close</span>
    </button>
  </div>
  <button class="message-menu-item" ... data-action="delete-for-me">...</button>
  <button class="message-menu-item is-danger" ... data-action="recall-message" [disabled]>...</button>
</div>
*/
const createMessageMenu = ({ isOwn }) => {
  const title = document.createElement('span');
  title.classList.add('message-menu-title');
  title.textContent = 'Delete message';

  const closeButton = document.createElement('button');
  closeButton.classList.add('message-menu-close');
  closeButton.type = 'button';
  closeButton.dataset.action = 'close-message-menu';
  closeButton.title = 'Close';
  closeButton.setAttribute('aria-label', 'Close');
  closeButton.appendChild(createIcon('close'));

  const header = document.createElement('div');
  header.classList.add('message-menu-header');
  header.appendChild(title);
  header.appendChild(closeButton);

  const menu = document.createElement('div');
  menu.classList.add('message-menu');
  menu.setAttribute('role', 'menu');
  menu.setAttribute('aria-label', 'Message options');
  menu.appendChild(header);
  menu.appendChild(createMenuItem({
    action: 'delete-for-me',
    icon: 'visibility_off',
    label: 'Delete for you',
    hint: 'Other members still see it'
  }));
  menu.appendChild(createMenuItem({
    action: 'recall-message',
    icon: 'delete',
    label: 'Delete for everyone',
    hint: isOwn ? 'Removed for all members' : 'Only the sender can do this',
    isDanger: true,
    disabled: !isOwn
  }));
  return menu;
};

/* ---------- 3. Open / close ---------- */

function closeMessageMenu() {
  if (!openMenu) return;
  const messageElement = openMenu.closest('.message');
  if (messageElement) {
    messageElement.classList.remove('has-menu-open');
    messageElement.querySelector('.message-menu-btn')?.setAttribute('aria-expanded', 'false');
  }
  openMenu.remove();
  openMenu = null;
}

const openMessageMenu = (messageElement) => {
  closeMessageMenu();
  if (messageElement.classList.contains('is-deleting')) return;   // a delete is already on its way

  const menu = createMessageMenu({ isOwn: isOwnMessage(messageElement) });
  messageElement.appendChild(menu);
  messageElement.classList.add('has-menu-open');
  messageElement.querySelector('.message-menu-btn')?.setAttribute('aria-expanded', 'true');
  openMenu = menu;

  // Open downwards when there is room inside the stream, otherwise upwards
  const streamBox = messageStream.getBoundingClientRect();
  const menuBox = menu.getBoundingClientRect();
  const spaceBelow = streamBox.bottom - menuBox.top;
  const spaceAbove = menuBox.top - streamBox.top;
  if (spaceBelow < menuBox.height + MENU_GAP_PX && spaceAbove > spaceBelow) {
    menu.classList.add('opens-up');
  }

  menu.querySelector('.message-menu-item:not(:disabled)')?.focus();
};

/* ---------- 4. Requests ---------- */

const clearPending = (messageId) => {
  const pending = pendingDeletes.get(String(messageId));
  if (!pending) return null;
  clearTimeout(pending.timer);
  pendingDeletes.delete(String(messageId));
  findMessageElement(messageId)?.classList.remove('is-deleting');
  return pending;
};

// action: 'delete_for_me' | 'recall'
const requestDelete = (messageElement, action) => {
  const conversationId = messageStream.dataset.conversationId;
  const messageId = messageElement.dataset.messageId;
  if (!conversationId || !messageId) return;

  if (!realTimeSocket.connected) {
    showError('Not connected to the server. Please try again.');
    return;
  }

  // Faded until the server answers; the answer removes it, an error gives it back
  messageElement.classList.add('is-deleting');
  const timer = setTimeout(() => {
    if (!clearPending(messageId)) return;
    showError('The server did not respond. The message was not deleted.');
  }, PENDING_TIMEOUT_MS);
  pendingDeletes.set(String(messageId), { action, timer });

  const event = action === 'recall' ? 'recall_message' : 'delete_message_for_me';
  realTimeSocket.emit(event, { conversation_id: conversationId, message_id: messageId });
};

/* ---------- 5. Events of the page ---------- */

// "..." button, X button and the two options: everything is inside the stream
messageStream.addEventListener('click', (event) => {
  const actionElement = event.target.closest('[data-action]');
  if (!actionElement || actionElement.disabled) return;
  const messageElement = actionElement.closest('.message');
  if (!messageElement) return;

  switch (actionElement.dataset.action) {
    case 'open-message-menu':
      if (openMenu && messageElement.contains(openMenu)) closeMessageMenu();   // second click closes
      else openMessageMenu(messageElement);
      break;
    case 'close-message-menu':
      closeMessageMenu();
      break;
    case 'delete-for-me':
      closeMessageMenu();
      requestDelete(messageElement, 'delete_for_me');
      break;
    case 'recall-message':
      closeMessageMenu();
      requestDelete(messageElement, 'recall');
      break;
  }
});

// Right click on a message opens the same menu
messageStream.addEventListener('contextmenu', (event) => {
  const messageElement = event.target.closest('.message');
  if (!messageElement) return;
  event.preventDefault();
  if (event.target.closest('.message-menu')) return;   // right click inside the menu: keep it
  openMessageMenu(messageElement);
});

// A click anywhere outside the menu closes it (the "..." button handles itself above)
document.addEventListener('click', (event) => {
  if (!openMenu) return;
  if (openMenu.contains(event.target)) return;
  if (event.target.closest('[data-action="open-message-menu"]')) return;
  closeMessageMenu();
});

// Right click on another place of the page also closes it
document.addEventListener('contextmenu', (event) => {
  if (openMenu && !event.target.closest('.message')) closeMessageMenu();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeMessageMenu();
});

/* ---------- 6. Events from the server ---------- */

// Hidden for this user only: remove it here and in this user's other tabs
realTimeSocket.on('message_deleted_for_me', (payload) => {
  const conversationId = String(payload?.conversation_id ?? '');
  const messageId = String(payload?.message_id ?? '');
  const pending = clearPending(messageId);

  if (conversationId === messageStream.dataset.conversationId) {
    const messageElement = findMessageElement(messageId);
    if (messageElement) removeMessageElement(messageElement);
  }
  if (pending) showToast('Message deleted for you');
});

// Deleted for everyone: remove it from the stream and fix the sidebar preview
realTimeSocket.on('message_recalled', (payload) => {
  const conversationId = String(payload?.conversation_id ?? '');
  const messageId = String(payload?.message_id ?? '');
  const pending = clearPending(messageId);

  if (conversationId === messageStream.dataset.conversationId) {
    const messageElement = findMessageElement(messageId);
    if (messageElement) removeMessageElement(messageElement);
  }

  // latest_message is left out when the server could not read it: keep the preview then
  if (payload && 'latest_message' in payload) {
    const latest = payload.latest_message;
    setConversationPreview({
      conversationId,
      message: latest ? latest.content : null,
      createAt: latest ? latest.created_at : null
    });
  }

  if (pending) showToast('Message deleted for everyone');   // only the tab that asked
});

// The server refused: give the message back and say why
realTimeSocket.on('delete_message_error', (payload) => {
  if (payload?.message_id) clearPending(payload.message_id);
  showError(payload?.message || 'The message could not be deleted.');
});
