import { realTimeSocket } from '../real-time-socket.js';
import { getConversations } from '../conversation.js';
import { showError } from '../error.js';
import { showToast } from '../toast.js';

/* Notifications.
   GET  /api/notifications?limit=30[&before=<notification_id>]   newest first, [] when nothing
   POST /api/relationships/friend-requests/accept?request_id=    accept (200: { friend_id })
   Socket 'receive_notification'  server -> client, one notification, same shape as the GET items
   Socket 'read_notification'     client -> server, { notification_ids: [...] }, answered with an ack
   Item: { notification_id (string), notification_type, is_read, created_at,
           payload: { actor: { user_id, username, display_name, avatar_url }, request_id?, conversation_id?, group_name? } }
   Types: friend_request | friend_accepted | group_added. Any other type is ignored.
   is_read: true = already read. There is no decline endpoint yet, so a friend request only has Accept. */

const notificationList = document.getElementById('notification-list');
const notificationBadge = document.getElementById('notif-badge');
const notificationsModal = document.getElementById('notifications-modal');

const NOTIFICATIONS_PAGE_LIMIT = 30;
const ACK_TIMEOUT_MS = 5000;

let notifications = [];                  // items of the API, newest first
let hasOlderNotifications = true;        // false when the last older page came back empty
let isLoadingNotifications = false;

/* ---------- 1. Helpers ---------- */

// What each type looks like: its icon and its sentence
const NOTIFICATION_TYPES = {
  friend_request: {
    icon: 'person_add',
    text: (name) => name + ' sent you a friend request'
  },
  friend_accepted: {
    icon: 'how_to_reg',
    text: (name) => name + ' accepted your friend request'
  },
  group_added: {
    icon: 'group_add',
    text: (name, payload) => name + ' added you to ' + (payload.group_name || 'a group')
  }
};

// API item -> what the row shows. null for a type this client does not know.
const toNotificationView = (item) => {
  const type = NOTIFICATION_TYPES[item?.notification_type];
  const actor = item?.payload?.actor;
  if (!type || !actor) return null;

  const name = actor.display_name || actor.username || 'Someone';
  return {
    id: item.notification_id,
    icon: type.icon,
    message: type.text(name, item.payload),
    timeAgo: formatTimeAgo(item.created_at),
    isRead: Boolean(item.is_read),
    canAccept: item.notification_type === 'friend_request' && Boolean(item.payload.request_id),
    actorName: name
  };
};

function formatTimeAgo(iso) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (Number.isNaN(seconds)) return '';
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
  if (seconds < 7 * 86400) return Math.floor(seconds / 86400) + 'd ago';
  return new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' });
}

/* ---------- 2. Create HTML ---------- */

/*
HTML Skeleton Reference:
<div class="notif-icon">
  <span class="material-symbols-outlined">person_add</span>   <!-- group_add for group invites -->
</div>
*/
const createNotificationIcon = (iconName) => {
  const symbol = document.createElement('span');
  symbol.classList.add('material-symbols-outlined');
  symbol.textContent = iconName;

  const icon = document.createElement('div');
  icon.classList.add('notif-icon');
  icon.appendChild(symbol);
  return icon;
};

/*
HTML Skeleton Reference (only for a friend request):
<div class="btn-group">
  <button class="btn btn-primary" type="button" data-action="accept">Accept</button>
</div>
*/
const createNotificationActions = () => {
  const acceptButton = document.createElement('button');
  acceptButton.classList.add('btn', 'btn-primary');
  acceptButton.type = 'button';
  acceptButton.dataset.action = 'accept';
  acceptButton.textContent = 'Accept';

  const group = document.createElement('div');
  group.classList.add('btn-group');
  group.appendChild(acceptButton);
  return group;
};

/*
HTML Skeleton Reference:
<div class="user-row notif-item [is-unread]" data-notification-id="1789432156738291900">
  <div class="notif-icon">...</div>
  <div class="user-row-info">
    <span class="user-row-name">Priya Nair sent you a friend request</span>
    <span class="user-row-sub">5m ago</span>
    <div class="btn-group">...</div>   <!-- only for a friend request -->
  </div>
</div>
*/
const createNotificationItem = ({ id, icon, message, timeAgo, isRead, canAccept }) => {
  const name = document.createElement('span');
  name.classList.add('user-row-name');
  name.textContent = message;

  const sub = document.createElement('span');
  sub.classList.add('user-row-sub');
  sub.textContent = timeAgo;

  const info = document.createElement('div');
  info.classList.add('user-row-info');
  info.appendChild(name);
  info.appendChild(sub);
  if (canAccept) info.appendChild(createNotificationActions());

  const item = document.createElement('div');
  item.classList.add('user-row', 'notif-item');
  if (!isRead) item.classList.add('is-unread');
  item.dataset.notificationId = id;
  item.appendChild(createNotificationIcon(icon));
  item.appendChild(info);
  return item;
};

/*
HTML Skeleton Reference:
<p class="modal-hint">No notifications yet.</p>
*/
const createEmptyHint = () => {
  const hint = document.createElement('p');
  hint.classList.add('modal-hint');
  hint.textContent = 'No notifications yet.';
  return hint;
};

/*
HTML Skeleton Reference (end of the list, while there may be older ones):
<button class="btn btn-secondary" type="button" data-action="load-older">Load older</button>
*/
const createLoadOlderButton = () => {
  const button = document.createElement('button');
  button.classList.add('btn', 'btn-secondary');
  button.type = 'button';
  button.dataset.action = 'load-older';
  button.textContent = 'Load older';
  return button;
};

/* ---------- 3. Show ---------- */

// Number of unread notifications on the bell
const updateBadge = () => {
  const unreadCount = notifications.filter((item) => !item.is_read && toNotificationView(item)).length;
  notificationBadge.hidden = unreadCount === 0;
  notificationBadge.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
};

const renderNotifications = () => {
  const nodes = notifications
    .map(toNotificationView)
    .filter(Boolean)
    .map(createNotificationItem);

  if (nodes.length === 0) nodes.push(createEmptyHint());
  if (hasOlderNotifications && notifications.length > 0) nodes.push(createLoadOlderButton());
  notificationList.replaceChildren(...nodes);
};

const setItemBusy = (item, busy) => {
  if (!item) return;
  item.querySelectorAll('button').forEach((button) => { button.disabled = busy; });
};

/* ---------- 4. Requests ---------- */

// GET /api/notifications. With `before`, the page is added at the end of the list.
export async function getNotifications({ before = null } = {}) {
  if (isLoadingNotifications) return false;
  isLoadingNotifications = true;
  try {
    const url = '/api/notifications?limit=' + NOTIFICATIONS_PAGE_LIMIT +
      (before ? '&before=' + encodeURIComponent(before) : '');
    const response = await fetch(url, { method: 'GET', credentials: 'include' });
    const body = await response.json();

    if (!response.ok) {
      showError(body?.message || 'Failed to fetch notifications');
      return false;
    }
    if (!Array.isArray(body)) {
      showError('Invalid notifications response');
      return false;
    }

    if (before) {
      const knownIds = new Set(notifications.map((item) => item.notification_id));
      notifications = notifications.concat(body.filter((item) => !knownIds.has(item.notification_id)));
    } else {
      notifications = body;
    }
    // The server drops finished friend requests after taking a page, so a short page does not
    // mean "no more": only an empty page does.
    hasOlderNotifications = body.length > 0;
    return true;
  } catch (error) {
    showError('Failed to fetch notifications');
    return false;
  } finally {
    isLoadingNotifications = false;
  }
}

// Socket 'read_notification': the unread ones become read on the server; the bell updates.
// The rows keep their unread look until the list is drawn again.
const markNotificationsRead = async () => {
  // only the ones this client can show: a type it does not know was never seen by the user
  const unreadIds = notifications
    .filter((item) => !item.is_read && toNotificationView(item))
    .map((item) => item.notification_id);
  if (unreadIds.length === 0 || !realTimeSocket.connected) return;

  const ids = unreadIds.slice(0, 100);
  try {
    const response = await realTimeSocket
      .timeout(ACK_TIMEOUT_MS)
      .emitWithAck('read_notification', { notification_ids: ids });

    if (response.status !== 'success') {
      showError(response.message || 'Could not mark notifications as read');
      return;
    }
    const doneIds = new Set(response.notification_ids || ids);
    notifications.forEach((item) => {
      if (doneIds.has(item.notification_id)) item.is_read = true;
    });
    updateBadge();
  } catch (error) {
    showError('The server did not respond. Could not mark notifications as read.');
  }
};

// action: 'accept'. POST /api/relationships/friend-requests/accept?request_id={payload.request_id}
// 200: { "friend_id": 7 }   404: the request is not pending any more   Errors: { "message": "..." }
export async function handleNotificationAction(notificationId, action) {
  if (action !== 'accept') return;   // there is no decline endpoint yet

  const item = notifications.find((entry) => entry.notification_id === notificationId);
  const requestId = item?.payload?.request_id;
  if (!requestId) {
    showError('Friend request is missing its ID');
    return;
  }

  const row = notificationList.querySelector(
    '.notif-item[data-notification-id="' + CSS.escape(notificationId) + '"]'
  );
  setItemBusy(row, true);

  try {
    const response = await fetch(
      '/api/relationships/friend-requests/accept?request_id=' + encodeURIComponent(requestId),
      { method: 'POST', credentials: 'include' }
    );
    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      showError(body?.message || 'Could not accept the friend request');
      if (response.status === 404) {
        // Not pending any more (accepted elsewhere, or the sender was blocked): remove the row
        notifications = notifications.filter((entry) => entry !== item);
        renderNotifications();
        updateBadge();
      } else {
        setItemBusy(row, false);
      }
      return;
    }

    // The server does not list accepted requests, so the row goes away
    notifications = notifications.filter((entry) => entry !== item);
    renderNotifications();
    updateBadge();
    showToast('You are now friends with ' + (item.payload.actor.display_name || item.payload.actor.username));
  } catch (error) {
    showError('Could not accept the friend request');
    setItemBusy(row, false);
  }
}

const loadOlderNotifications = async () => {
  const oldest = notifications[notifications.length - 1];
  if (!oldest) return;
  if (await getNotifications({ before: oldest.notification_id })) renderNotifications();
};

/* ---------- 5. Modal and events ---------- */

// chat.js calls this each time the notifications modal opens
export async function prepareNotificationsModal() {
  renderNotifications();                       // what we already have, at once
  if (await getNotifications()) {
    renderNotifications();
    updateBadge();
    markNotificationsRead();                   // opening the list = seeing them
  }
}

// The badge must be right before the modal is ever opened
const refreshNotifications = async () => {
  if (await getNotifications()) updateBadge();
};

// One click listener for the list: the button says what it does with data-action,
// the row says which notification with data-notification-id.
notificationList.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) return;

  if (button.dataset.action === 'load-older') {
    loadOlderNotifications();
    return;
  }
  const row = button.closest('.notif-item');
  if (row) handleNotificationAction(row.dataset.notificationId, button.dataset.action);
});

// A new notification arrives in real time
realTimeSocket.on('receive_notification', (item) => {
  const view = toNotificationView(item);
  if (!view) return;   // unknown type
  if (notifications.some((entry) => entry.notification_id === item.notification_id)) return;

  notifications.unshift(item);
  updateBadge();
  if (!notificationsModal.hidden) renderNotifications();
  showToast(view.message);

  // Added to a group: the new conversation must appear in the sidebar
  if (item.notification_type === 'group_added') getConversations();
});

// After a lost connection, notifications may have arrived in between
realTimeSocket.io.on('reconnect', refreshNotifications);

refreshNotifications();