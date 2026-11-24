import { showError } from './error.js';
import { conversationList } from './conversation.js';
import { openChatWithUser } from './chat-area/messages-actions.js';

/* Sidebar search (users only for now).
   Nothing is sent while typing. Pressing Enter in the search box sends the search;
   the results replace the conversation list, and clearing the box brings it back.
   Each result row has buttons depending on `friend_status`:
     null               -> [Add friend] [Block]
     'requested'        -> [Requested]  [Block]
     'incoming_request' -> [Accept]     [Block]
     'friend'           -> [Friends]    [Block]
     'blocked'          -> [Unblock]
   Requests:
     search      -> GET    /api/users/search?username={keyword}
     add friend  -> POST   /api/relationships/friend-requests?user_id={user_id}
     block       -> POST   /api/blocks?user_id={user_id}
     unblock     -> DELETE /api/blocks?user_id={user_id}  */

const searchInput = document.getElementById('sidebar-search-input');
const clearButton = document.getElementById('sidebar-search-clear');

const MAX_KEYWORD_LENGTH = 50;

let latestSearchId = 0;   // a response is ignored when a newer search was started

/* ---------- 1. Helpers ---------- */

const getInitials = (name = '') => {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// Text and class of the main button for each relationship state
const PRIMARY_BUTTONS = {
  none: { label: 'Add friend', className: 'btn-primary', action: 'add-friend', disabled: false },
  requested: { label: 'Requested', className: 'btn-secondary', action: 'requested', disabled: true },
  incoming_request: { label: 'Accept', className: 'btn-primary', action: 'accept-friend-request', disabled: false },
  friend: { label: 'Friends', className: 'btn-secondary', action: 'friends', disabled: true },
  blocked: { label: 'Unblock', className: 'btn-secondary', action: 'unblock', disabled: false }
};

// API value (null | 'friend' | 'requested' | 'incoming_request' | 'blocked') -> key of PRIMARY_BUTTONS
const toStatusKey = (friendStatus) => (PRIMARY_BUTTONS[friendStatus] ? friendStatus : 'none');

/* ---------- 2. Create HTML ---------- */

/*
HTML Skeleton Reference:
<button class="btn btn-primary" type="button" data-action="add-friend" [disabled]>Add friend</button>
*/
const createActionButton = ({ label, className, action, disabled }) => {
  const button = document.createElement('button');
  button.classList.add('btn', className);
  button.type = 'button';
  button.dataset.action = action;
  button.disabled = disabled;
  button.textContent = label;
  return button;
};

/*
HTML Skeleton Reference:
<button class="btn btn-secondary btn-icon" type="button" data-action="block" title="Block user">
  <span class="material-symbols-outlined">block</span>
</button>
*/
const createBlockButton = () => {
  const icon = document.createElement('span');
  icon.classList.add('material-symbols-outlined');
  icon.textContent = 'block';

  const button = document.createElement('button');
  button.classList.add('btn', 'btn-secondary', 'btn-icon');
  button.type = 'button';
  button.dataset.action = 'block';
  button.setAttribute('title', 'Block user');
  button.appendChild(icon);
  return button;
};

/*
HTML Skeleton Reference:
<div class="btn-group">
  <!-- main button, one of: -->
  <button class="btn btn-primary" type="button" data-action="add-friend">Add friend</button>     <!-- not a friend -->
  <button class="btn btn-secondary" type="button" data-action="requested" disabled>Requested</button>
  <button class="btn btn-secondary" type="button" data-action="friends" disabled>Friends</button>
  <button class="btn btn-secondary" type="button" data-action="unblock">Unblock</button>         <!-- blocked -->

  <!-- block button: every state except blocked -->
  <button class="btn btn-secondary btn-icon" type="button" data-action="block" title="Block user">...</button>
</div>
*/
const createUserRowActions = ({ friendStatus }) => {
  const statusKey = toStatusKey(friendStatus);

  const group = document.createElement('div');
  group.classList.add('btn-group');
  group.appendChild(createActionButton(PRIMARY_BUTTONS[statusKey]));
  if (statusKey !== 'blocked') group.appendChild(createBlockButton());
  return group;
};

/*
HTML Skeleton Reference:
<div class="user-row" data-user-id="12" data-friend-status="requested">
  <div class="user-row-avatar">JS</div>
  <div class="user-row-info">
    <span class="user-row-name">Johnny Smith</span>
    <span class="user-row-sub">@johnny</span>
  </div>
  <div class="btn-group">...</div>
</div>
*/
const createUserRow = ({ userId, username, displayName, friendStatus, friendRequestId }) => {
  const avatar = document.createElement('div');
  avatar.classList.add('user-row-avatar');
  avatar.textContent = getInitials(displayName);

  const name = document.createElement('span');
  name.classList.add('user-row-name');
  name.textContent = displayName;

  const sub = document.createElement('span');
  sub.classList.add('user-row-sub');
  sub.textContent = '@' + username;

  const info = document.createElement('div');
  info.classList.add('user-row-info');
  info.appendChild(name);
  info.appendChild(sub);

  const row = document.createElement('div');
  row.classList.add('user-row');
  row.dataset.userId = userId;
  row.dataset.friendStatus = toStatusKey(friendStatus);
  if (friendRequestId != null) row.dataset.friendRequestId = friendRequestId;
  row.appendChild(avatar);
  row.appendChild(info);
  row.appendChild(createUserRowActions({ friendStatus }));
  return row;
};

/*
HTML Skeleton Reference:
<div class="search-section">
  <div class="search-section-title">People</div>
  <div class="user-row">...</div>   <!-- one per user -->
</div>
*/
const createSearchSection = ({ title, users }) => {
  const sectionTitle = document.createElement('div');
  sectionTitle.classList.add('search-section-title');
  sectionTitle.textContent = title;

  const section = document.createElement('div');
  section.classList.add('search-section');
  section.appendChild(sectionTitle);
  users.forEach((user) => {
    section.appendChild(createUserRow({
      userId: user.user_id,
      username: user.username,
      displayName: user.display_name,
      friendStatus: user.friend_status,
      friendRequestId: user.friend_request_id
    }));
  });
  return section;
};

/*
HTML Skeleton Reference:
<p class="search-empty">No users found for "john".</p>
*/
const createSearchMessage = (text) => {
  const message = document.createElement('p');
  message.classList.add('search-empty');
  message.textContent = text;
  return message;
};

/*
HTML Skeleton Reference (same classes as the conversation list, so it scrolls the same way):
<div class="conversation-list search-results" id="sidebar-search-results" hidden>
  <div class="search-section">...</div>   <!-- or a .search-empty message -->
</div>
*/
const createSearchResults = () => {
  const results = document.createElement('div');
  results.classList.add('conversation-list', 'search-results');
  results.id = 'sidebar-search-results';
  results.hidden = true;
  return results;
};

/* ---------- 3. Show and hide ---------- */

/*
HTML Skeleton Reference (added to the sidebar, right after #conversation-list):
<div class="conversation-list search-results" id="sidebar-search-results" hidden></div>
*/
const searchResults = createSearchResults();
conversationList.after(searchResults);

const showSearchResults = (nodes) => {
  searchResults.replaceChildren(...nodes);
  searchResults.hidden = false;
  conversationList.hidden = true;
};

const showConversationList = () => {
  searchResults.hidden = true;
  searchResults.replaceChildren();
  conversationList.hidden = false;
};

const renderUserResults = (users, query) => {
  if (users.length === 0) {
    showSearchResults([createSearchMessage('No users found for "' + query + '".')]);
    return;
  }
  showSearchResults([createSearchSection({ title: 'People', users })]);
};

// Rebuilds the buttons of one row after its relationship changed
// friendStatus: null | 'requested' | 'friend' | 'blocked'  (or a key of PRIMARY_BUTTONS)
const updateUserRow = (row, friendStatus) => {
  row.dataset.friendStatus = toStatusKey(friendStatus);
  if (row.dataset.friendStatus !== 'incoming_request') {
    delete row.dataset.friendRequestId;
  }
  row.querySelector('.btn-group').replaceWith(createUserRowActions({ friendStatus }));
};

// Disables every button of a row while its request is running (no double clicks)
const setRowBusy = (row, busy) => {
  row.querySelectorAll('button').forEach((button) => { button.disabled = busy; });
};

/* ---------- 4. Search ---------- */

// Empties the box and brings the conversation list back.
// latestSearchId makes a search that is still running ignore its answer.
const clearSearch = () => {
  latestSearchId += 1;
  searchInput.value = '';
  clearButton.hidden = true;
  showConversationList();
};

/* ---------- 5. Relationship requests (add friend, block, unblock) ---------- */

// Sends the request and returns the JSON body. Throws an Error whose message is safe to show.
const callRelationshipApi = async (method, url) => {
  let response;
  try {
    response = await fetch(url, { method, credentials: 'include' });
  } catch (error) {
    throw new Error('Could not send request to server');
  }

  let body;
  try {
    body = await response.json();
  } catch (error) {
    throw new Error('Invalid response from server');
  }

  if (!response.ok) {
    throw new Error(body?.message || 'Request failed');
  }
  return body;
};

// Runs one request for a row. The row shows its new state only after the server said yes;
// on an error it goes back to the state it had.
const changeRelationship = async (row, { method, url, nextStatus }) => {
  const previousStatus = row.dataset.friendStatus;
  setRowBusy(row, true);

  try {
    await callRelationshipApi(method, url);
    updateUserRow(row, nextStatus);
  } catch (error) {
    showError(error.message);
    updateUserRow(row, previousStatus);
  }
};

// POST {BASE_URL}/api/relationships/friend-requests?user_id={user_id}
// 201: { "receiver_id": 7 }   Errors: { "message": "..." }
const handleAddFriend = (row) => changeRelationship(row, {
  method: 'POST',
  url: '/api/relationships/friend-requests?user_id=' + encodeURIComponent(row.dataset.userId),
  nextStatus: 'requested'
});

const handleAcceptFriendRequest = (row) => {
  const requestId = row.dataset.friendRequestId;
  if (!requestId) {
    showError('Friend request is missing its ID');
    return;
  }
  return changeRelationship(row, {
    method: 'POST',
    url: '/api/relationships/friend-requests/accept?request_id=' + encodeURIComponent(requestId),
    nextStatus: 'friend'
  });
};

// POST {BASE_URL}/api/blocks?user_id={user_id}
// 201: { "blocked_id": 7 }   Errors: { "message": "..." }
// Blocking also removes an existing friendship and pending friend requests.
const handleBlock = (row) => changeRelationship(row, {
  method: 'POST',
  url: '/api/blocks?user_id=' + encodeURIComponent(row.dataset.userId),
  nextStatus: 'blocked'
});

// DELETE {BASE_URL}/api/blocks?user_id={user_id}
// 200: { "unblocked_id": 7 }   Errors: { "message": "..." }
// The old friendship is not restored, so the row goes back to "Add friend".
const handleUnblock = (row) => changeRelationship(row, {
  method: 'DELETE',
  url: '/api/blocks?user_id=' + encodeURIComponent(row.dataset.userId),
  nextStatus: null
});

// Click on a user row (not on one of its buttons): open the existing conversation with this
// user, or prepare a new chat. Nothing is sent to the server.
const handleClickUserRow = (row) => {
    const userId = row.dataset.userId;
    if (!userId) return;
    const name = row.querySelector('.user-row-name').textContent;
    const hasConversation = openChatWithUser({ userId, name });
    if (hasConversation) clearSearch();   // back to the conversation list, the chat is open
}

const actionHandlers = {
  'add-friend': handleAddFriend,
  'accept-friend-request': handleAcceptFriendRequest,
  block: handleBlock,
  unblock: handleUnblock
};

/* ---------- 6. Events (one listener for each kind) ---------- */

// Typing sends nothing. It only shows the clear button, and brings the
// conversation list back when the box is emptied by hand.
searchInput.addEventListener('input', () => {
  clearButton.hidden = searchInput.value === '';

  if (!searchInput.value.trim()) {
    latestSearchId += 1;
    showConversationList();
  }
});

// Enter sends the search
searchInput.addEventListener('keydown', async (event) => {
    if (event.key !== 'Enter' || event.isComposing) return;
    event.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;
    const searchId = ++latestSearchId;
    try {
        const res = await fetch(`/api/users/search?username=${encodeURIComponent(query.slice(0, MAX_KEYWORD_LENGTH))}`, { method: 'GET', credentials: 'include' });
        if (searchId !== latestSearchId) return;   // the box was cleared or a newer search started
        if (!res.ok) {
            const errorBody = await res.json();
            showError(errorBody?.message || 'Could not search users');
            return;
        }
        const users = await res.json();
        if (searchId !== latestSearchId) return;
        if (!Array.isArray(users)) {
            showError('Invalid user search response');
            return;
        }
        renderUserResults(users, query);
    } catch (error) {
        showError(error?.message || 'Could not search users');
        return;
    }
});

clearButton.addEventListener('click', () => {
  clearSearch();
  searchInput.focus();
});

// One listener for every button in every result row; the button says what it does
// with data-action and the row says who it is about with data-user-id.
searchResults.addEventListener('click', (event) => {
  
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) {
    const row = event.target.closest('.user-row');
    if (row) handleClickUserRow(row);
    return;
  }

  const row = button.closest('.user-row');
  const handler = actionHandlers[button.dataset.action];
  if (row && handler) handler(row);
});
