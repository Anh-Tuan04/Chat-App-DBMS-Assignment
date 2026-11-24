import { showError } from '../error.js';
import { showToast } from '../toast.js';

/* Add friend modal.
   Nothing is sent while typing: pressing Enter in the box sends the search.
   GET  /api/users/search?username={keyword}                      -> [{ user_id, username, display_name, avatar_url, friend_status }]
        friend_status: null | 'requested' | 'friend'
   POST /api/relationships/friend-requests?user_id={user_id}      -> 201 { receiver_id }
        404 user not found or blocked, 409 already friends or a request already exists
   Errors: { "message": "..." } */

const addFriendInput = document.getElementById('add-friend-input');
const addFriendResults = document.getElementById('add-friend-results');

const MAX_KEYWORD_LENGTH = 50;
let latestSearchId = 0;   // an answer is ignored when a newer search started or the modal was reset

/*
<div class="modal" id="add-friend-modal" role="dialog" aria-modal="true" aria-labelledby="add-friend-title" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-dialog">
    <div class="modal-header">...</div>
    <div class="modal-body">
      <div class="modal-search">
        <span class="material-symbols-outlined">search</span>
        <input id="add-friend-input" type="text" placeholder="Search by name or handle" autocomplete="off" />
      </div>
      <div class="modal-results" id="add-friend-results">
        ....
      </div>
    </div>
  </div>
</div>
*/

/* ---------- 1. Create HTML ---------- */

/*
HTML Skeleton Reference (one of these in #add-friend-results, depending on the state):
<p class="modal-hint">Type a name or handle and press Enter.</p>     <!-- nothing searched yet -->
<p class="modal-hint">No users found for "query".</p>                <!-- no match -->
<div class="user-row">...</div>                                      <!-- one row per match -->
*/
const createHint = (text) => {
  const hint = document.createElement('p');
  hint.classList.add('modal-hint');
  hint.textContent = text;
  return hint;
};

const getInitials = (name = '') => {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

/*
HTML Skeleton Reference (the button depends on friend_status):
<button class="btn btn-primary" type="button" data-action="send-friend-request" data-user-id="7">Add friend</button>  <!-- null -->
<button class="btn btn-secondary" type="button" data-user-id="7" disabled>Requested</button>                          <!-- 'requested' -->
<button class="btn btn-secondary" type="button" data-user-id="7" disabled>Friends</button>                            <!-- 'friend' -->
*/
const createRequestButton = ({ userId, friendStatus }) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.dataset.userId = userId;

  if (friendStatus === 'friend') {
    button.classList.add('btn', 'btn-secondary');
    button.textContent = 'Friends';
    button.disabled = true;
  } else if (friendStatus === 'requested') {
    button.classList.add('btn', 'btn-secondary');
    button.textContent = 'Requested';
    button.disabled = true;
  } else {
    button.classList.add('btn', 'btn-primary');
    button.dataset.action = 'send-friend-request';
    button.textContent = 'Add friend';
  }
  return button;
};

/*
HTML Skeleton Reference:
<div class="user-row" data-user-id="7">
  <div class="user-row-avatar">TB</div>
  <div class="user-row-info">
    <span class="user-row-name">Tom Becker</span>
    <span class="user-row-sub">@tbecker</span>
  </div>
  <button class="btn btn-primary" type="button" data-action="send-friend-request" data-user-id="7">Add friend</button>
</div>
*/
const createUserRow = ({ user_id, username, display_name, friend_status }) => {
  const name = display_name || username;

  const avatar = document.createElement('div');
  avatar.classList.add('user-row-avatar');
  avatar.textContent = getInitials(name);

  const nameLabel = document.createElement('span');
  nameLabel.classList.add('user-row-name');
  nameLabel.textContent = name;

  const handle = document.createElement('span');
  handle.classList.add('user-row-sub');
  handle.textContent = '@' + username;

  const info = document.createElement('div');
  info.classList.add('user-row-info');
  info.appendChild(nameLabel);
  info.appendChild(handle);

  const row = document.createElement('div');
  row.classList.add('user-row');
  row.dataset.userId = user_id;
  row.appendChild(avatar);
  row.appendChild(info);
  row.appendChild(createRequestButton({ userId: user_id, friendStatus: friend_status }));
  return row;
};

/* ---------- 2. Show ---------- */

const renderSearchResults = (users, query) => {
  if (users.length === 0) {
    addFriendResults.replaceChildren(createHint('No users found for "' + query + '".'));
    return;
  }
  addFriendResults.replaceChildren(...users.map(createUserRow));
};

// chat.js calls this each time the modal opens: an empty box and the first hint
export function prepareAddFriendModal() {
  latestSearchId += 1;
  addFriendInput.value = '';
  addFriendResults.replaceChildren(createHint('Type a name or handle and press Enter.'));
}

const setRequested = (button) => {
  button.disabled = true;
  button.classList.remove('btn-primary');
  button.classList.add('btn-secondary');
  button.removeAttribute('data-action');
  button.textContent = 'Requested';
};

const restoreAddButton = (button) => {
  button.disabled = false;
  button.textContent = 'Add friend';
};

/* ---------- 3. Requests ---------- */

// POST /api/relationships/friend-requests?user_id={user_id}
const handleSendFriendRequest = async (button) => {
  const userId = button.dataset.userId;
  if (!/^\d+$/.test(userId || '')) {
    showError('Invalid user selected');
    return;
  }

  button.disabled = true;
  button.textContent = 'Sending...';

  try {
    const response = await fetch(
      '/api/relationships/friend-requests?user_id=' + encodeURIComponent(userId),
      { method: 'POST', credentials: 'include' }
    );
    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      showError(body?.message || 'Could not send the friend request');
      // A request already exists: the button should say so instead of offering to send it again
      if (response.status === 409 && body?.message === 'Friend request already exists') {
        setRequested(button);
      } else {
        restoreAddButton(button);
      }
      return;
    }

    setRequested(button);
    showToast('Friend request sent');
  } catch (error) {
    showError('Could not send the friend request');
    restoreAddButton(button);
  }
};

/* ---------- 4. Events (one listener for each kind) ---------- */

// Enter sends the search. GET /api/users/search?username={keyword}
addFriendInput.addEventListener('keydown', async (event) => {
  if (event.key !== 'Enter' || event.isComposing) return;
  event.preventDefault();

  const query = addFriendInput.value.trim();
  if (!query) return;

  const searchId = ++latestSearchId;
  addFriendResults.replaceChildren(createHint('Searching...'));

  try {
    const response = await fetch(
      '/api/users/search?username=' + encodeURIComponent(query.slice(0, MAX_KEYWORD_LENGTH)),
      { method: 'GET', credentials: 'include' }
    );
    const body = await response.json();
    if (searchId !== latestSearchId) return;   // the modal was reset or a newer search started

    if (!response.ok) {
      showError(body?.message || 'Could not search users');
      addFriendResults.replaceChildren(createHint('Search failed. Please try again.'));
      return;
    }
    if (!Array.isArray(body)) {
      showError('Invalid user search response');
      addFriendResults.replaceChildren(createHint('Search failed. Please try again.'));
      return;
    }
    renderSearchResults(body, query);
  } catch (error) {
    if (searchId !== latestSearchId) return;
    showError('Could not search users');
    addFriendResults.replaceChildren(createHint('Search failed. Please try again.'));
  }
});

// One click listener for every button of every row: the button says what it does with
// data-action, and data-user-id says who it is about.
addFriendResults.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) return;
  if (button.dataset.action === 'send-friend-request') handleSendFriendRequest(button);
});