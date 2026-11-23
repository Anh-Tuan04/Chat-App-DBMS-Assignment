import { showError } from '../error.js';
import { showToast } from '../toast.js';
import { openChatWithUser } from '../chat-area/messages.js';
import { realTimeSocket } from '../real-time-socket.js';

/* Friends list.
   GET    /api/relationships/friends            sorted by display name, [] when no friends
   DELETE /api/relationships/friends?user_id=   unfriend (200: { friend_id }, 404: not a friend any more)
   Item: { friend_id, friend_username, friend_display_name, friend_avatar_url, friend_online_status }
   friend_online_status: online | idle | do_not_disturb | offline
   Click a row = chat with that friend. Remove asks once more before it unfriends. */

const friendsList = document.getElementById('friends-list');
const friendsSearchInput = document.getElementById('friends-search-input');
const friendsModal = document.getElementById('friends-modal');

const CONFIRM_TIMEOUT_MS = 3000;

let friends = [];               // items of the API
let hasLoadedFriends = false;   // false until the first GET succeeds
let isLoadingFriends = false;
let loadFailed = false;         // the last GET failed: say so instead of "Loading…"

/* ---------- 1. Helpers ---------- */

// What each online status looks like: the dot class and the label under the name
const FRIEND_STATUSES = {
  online:         { dotClass: 'is-online',  label: 'Online' },
  idle:           { dotClass: 'is-idle',    label: 'Away' },
  do_not_disturb: { dotClass: 'is-dnd',     label: 'Do not disturb' },
  offline:        { dotClass: 'is-offline', label: 'Offline' }
};

const getInitials = (name = '') => {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// API item -> what the row shows
const toFriendView = (item) => {
  const name = item.friend_display_name || item.friend_username || 'Unknown';
  return {
    id: item.friend_id,
    name,
    username: item.friend_username || '',
    initials: getInitials(name),
    avatarUrl: item.friend_avatar_url,
    status: FRIEND_STATUSES[item.friend_online_status] || FRIEND_STATUSES.offline
  };
};

const matchesQuery = (view, query) =>
  !query ||
  view.name.toLowerCase().includes(query) ||
  view.username.toLowerCase().includes(query);

const findFriend = (friendId) => friends.find((item) => String(item.friend_id) === String(friendId));

/* ---------- 2. Create HTML ---------- */

/*
HTML Skeleton Reference:
<div class="friend-avatar-wrap">
  <img class="friend-avatar-img" src="https://example.com/avatar.jpg" alt="Gabriel Federick" />
       or <div class="friend-avatar-initials">GF</div>   <!-- no avatar URL -->
  <span class="status-dot is-online"></span>
</div>
*/
const createFriendAvatar = ({ name, initials, avatarUrl, status }) => {
  const wrap = document.createElement('div');
  wrap.classList.add('friend-avatar-wrap');

  if (avatarUrl) {
    const img = document.createElement('img');
    img.classList.add('friend-avatar-img');
    img.src = avatarUrl;
    img.alt = name;
    wrap.appendChild(img);
  } else {
    const fallback = document.createElement('div');
    fallback.classList.add('friend-avatar-initials');
    fallback.textContent = initials;
    wrap.appendChild(fallback);
  }

  const dot = document.createElement('span');
  dot.classList.add('status-dot', status.dotClass);
  wrap.appendChild(dot);
  return wrap;
};

/*
HTML Skeleton Reference:
<div class="user-row friend-row [is-active]" data-friend-list-id="7" title="Chat with Jane Doe">
  <div class="friend-avatar-wrap">...</div>
  <div class="user-row-info">
    <span class="user-row-name">Jane Doe</span>
    <span class="user-row-sub">@jane_doe · Online</span>
  </div>
  <button class="btn btn-danger" type="button" data-action="remove-friend">Remove</button>
</div>
*/
const createFriendRow = (view) => {
  const nameLabel = document.createElement('span');
  nameLabel.classList.add('user-row-name');
  nameLabel.textContent = view.name;

  const subLabel = document.createElement('span');
  subLabel.classList.add('user-row-sub');
  subLabel.textContent = (view.username ? '@' + view.username + ' · ' : '') + view.status.label;

  const info = document.createElement('div');
  info.classList.add('user-row-info');
  info.appendChild(nameLabel);
  info.appendChild(subLabel);

  const removeButton = document.createElement('button');
  removeButton.classList.add('btn', 'btn-danger');
  removeButton.type = 'button';
  removeButton.dataset.action = 'remove-friend';
  removeButton.textContent = 'Remove';

  const row = document.createElement('div');
  row.classList.add('user-row', 'friend-row');
  if (view.status === FRIEND_STATUSES.online) row.classList.add('is-active');
  row.dataset.friendListId = String(view.id);
  row.title = 'Chat with ' + view.name;
  row.appendChild(createFriendAvatar(view));
  row.appendChild(info);
  row.appendChild(removeButton);
  return row;
};

/*
HTML Skeleton Reference:
<p class="modal-hint">No friends yet.</p>
*/
const createHint = (text) => {
  const hint = document.createElement('p');
  hint.classList.add('modal-hint');
  hint.textContent = text;
  return hint;
};

/* ---------- 3. Show ---------- */

const renderFriendsList = () => {
  if (!hasLoadedFriends) {
    friendsList.replaceChildren(createHint(loadFailed ? 'Could not load friends.' : 'Loading friends…'));
    return;
  }
  if (friends.length === 0) {
    friendsList.replaceChildren(createHint('No friends yet. Use Add friend to find people.'));
    return;
  }

  const rawQuery = friendsSearchInput.value.trim();
  const query = rawQuery.toLowerCase();
  const rows = friends
    .map(toFriendView)
    .filter((view) => matchesQuery(view, query))
    .map(createFriendRow);

  if (rows.length === 0) {
    friendsList.replaceChildren(createHint('No friends match "' + rawQuery + '".'));
    return;
  }
  friendsList.replaceChildren(...rows);
};

/* ---------- 4. Requests ---------- */

// GET /api/relationships/friends
export async function getFriends() {
  if (isLoadingFriends) return false;
  isLoadingFriends = true;
  try {
    const response = await fetch('/api/relationships/friends', { method: 'GET', credentials: 'include' });
    const body = await response.json().catch(() => null);

    if (!response.ok) {
      showError(body?.message || 'Failed to fetch friends list');
      return false;
    }
    if (!Array.isArray(body)) {
      showError('Invalid friends list data');
      return false;
    }

    friends = body;
    hasLoadedFriends = true;
    return true;
  } catch (error) {
    showError('Failed to fetch friends list');
    return false;
  } finally {
    isLoadingFriends = false;
  }
}

// DELETE /api/relationships/friends?user_id={friend_id}
// 200: { "friend_id": 7 }   404: not a friend any more   Errors: { "message": "..." }
const removeFriend = async (friendId, button) => {
  const item = findFriend(friendId);
  if (!item) return;
  const name = toFriendView(item).name;

  button.disabled = true;
  button.textContent = 'Removing…';

  try {
    const response = await fetch(
      '/api/relationships/friends?user_id=' + encodeURIComponent(friendId),
      { method: 'DELETE', credentials: 'include' }
    );
    const body = await response.json().catch(() => ({}));

    if (!response.ok && response.status !== 404) {
      showError(body?.message || 'Could not remove ' + name);
      resetRemoveButton(button);
      return;
    }

    // 404: already not friends (removed from the other side): the row goes away too
    friends = friends.filter((entry) => entry !== item);
    renderFriendsList();
    if (response.ok) showToast(name + ' was removed from your friends');
    else showError(body?.message || name + ' is not your friend any more');
  } catch (error) {
    showError('Could not remove ' + name);
    resetRemoveButton(button);
  }
};

/* ---------- 5. Remove needs a second click ---------- */

const confirmTimers = new WeakMap();   // button -> timer that puts "Remove" back

const resetRemoveButton = (button) => {
  clearTimeout(confirmTimers.get(button));
  confirmTimers.delete(button);
  delete button.dataset.confirming;
  button.disabled = false;
  button.textContent = 'Remove';
};

const askToConfirm = (button) => {
  button.dataset.confirming = 'true';
  button.textContent = 'Confirm?';
  confirmTimers.set(button, setTimeout(() => resetRemoveButton(button), CONFIRM_TIMEOUT_MS));
};

/* ---------- 6. Modal and events ---------- */

// chat.js calls this each time the friends modal opens
export async function prepareFriendsModal() {
  friendsSearchInput.value = '';
  loadFailed = false;
  renderFriendsList();                 // what we already have (or "Loading…"), at once
  loadFailed = !(await getFriends());
  renderFriendsList();
}

friendsSearchInput.addEventListener('input', renderFriendsList);

// Enter in the search box: open the chat when exactly one friend matches
friendsSearchInput.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;
  const rows = friendsList.querySelectorAll('[data-friend-list-id]');
  if (rows.length === 1) rows[0].click();
});

// One click listener for the list: the button says what it does with data-action,
// the row says which friend with data-friend-list-id (the friend's user id).
friendsList.addEventListener('click', (event) => {
  const row = event.target.closest('[data-friend-list-id]');
  if (!row) return;

  const button = event.target.closest('[data-action="remove-friend"]');
  if (button) {
    if (button.disabled) return;
    if (button.dataset.confirming) {
      clearTimeout(confirmTimers.get(button));
      removeFriend(row.dataset.friendListId, button);
    } else {
      askToConfirm(button);
    }
    return;
  }

  // Click on the row itself: chat with this friend
  const item = findFriend(row.dataset.friendListId);
  if (!item) return;
  openChatWithUser({ userId: item.friend_id, name: toFriendView(item).name });
  friendsModal.hidden = true;
});

// Someone accepted our request: refresh the list if it is on screen
// (when the modal is closed, the next open fetches it anyway)
realTimeSocket.on('receive_notification', async (item) => {
  if (item?.notification_type !== 'friend_accepted' || friendsModal.hidden) return;
  if (await getFriends()) renderFriendsList();
});
