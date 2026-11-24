import { showError } from '../error.js';
import { showToast } from '../toast.js';

/* Blocked users list.
   GET    /api/blocks?limit=&before=   newest block first, [] when nobody is blocked
                                       next page: before = block_id of the last row on screen
   DELETE /api/blocks?user_id=         unblock (200: { unblocked_id }, 404: not blocked any more)
   Item: { block_id, blocked_id, blocked_username, blocked_display_name, blocked_avatar_url, created_at }
   Each row has an Unblock button. When the server confirms, the row is removed. */

const blockedList = document.getElementById('blocked-users-list');

const PAGE_LIMIT = 50;

let blockedUsers = [];        // items of the API, in the order shown
let hasLoaded = false;        // false until the first page arrives
let loadFailed = false;       // the first page failed: say so instead of "Loading…"
let hasMore = false;          // the last page was full, so there may be older blocks
let isLoadingMore = false;
let loadSeq = 0;              // bumped on each open; answers for an older open are ignored

/* ---------- 1. Helpers ---------- */

const getInitials = (name = '') => {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

const formatBlockedDate = (isoString) => {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
};

// API item -> what the row shows
const toBlockedView = (item) => {
  const name = item.blocked_display_name || item.blocked_username || 'Unknown';
  return {
    id: item.blocked_id,
    name,
    username: item.blocked_username || '',
    initials: getInitials(name),
    avatarUrl: item.blocked_avatar_url,
    blockedOn: formatBlockedDate(item.created_at)
  };
};

const findBlocked = (userId) => blockedUsers.find((item) => String(item.blocked_id) === String(userId));

/* ---------- 2. Create HTML ---------- */

/*
HTML Skeleton Reference:
<div class="friend-avatar-wrap">
  <img class="friend-avatar-img" src="https://example.com/avatar.jpg" alt="Jane Doe" />
       or <div class="friend-avatar-initials">JD</div>   <!-- no avatar URL -->
</div>
*/
const createBlockedAvatar = ({ name, initials, avatarUrl }) => {
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
  return wrap;
};

/*
HTML Skeleton Reference:
<div class="user-row blocked-row" data-blocked-user-id="7">
  <div class="friend-avatar-wrap">...</div>
  <div class="user-row-info">
    <span class="user-row-name">Jane Doe</span>
    <span class="user-row-sub">@jane_doe · Blocked Nov 20, 2026</span>
  </div>
  <button class="btn btn-secondary" type="button" data-action="unblock-user">Unblock</button>
</div>
*/
const createBlockedRow = (view) => {
  const nameLabel = document.createElement('span');
  nameLabel.classList.add('user-row-name');
  nameLabel.textContent = view.name;

  const subParts = [];
  if (view.username) subParts.push('@' + view.username);
  if (view.blockedOn) subParts.push('Blocked ' + view.blockedOn);

  const subLabel = document.createElement('span');
  subLabel.classList.add('user-row-sub');
  subLabel.textContent = subParts.join(' · ');

  const info = document.createElement('div');
  info.classList.add('user-row-info');
  info.appendChild(nameLabel);
  info.appendChild(subLabel);

  const unblockButton = document.createElement('button');
  unblockButton.classList.add('btn', 'btn-secondary');
  unblockButton.type = 'button';
  unblockButton.dataset.action = 'unblock-user';
  unblockButton.textContent = 'Unblock';

  const row = document.createElement('div');
  row.classList.add('user-row', 'blocked-row');
  row.dataset.blockedUserId = String(view.id);
  row.appendChild(createBlockedAvatar(view));
  row.appendChild(info);
  row.appendChild(unblockButton);
  return row;
};

/*
HTML Skeleton Reference:
<button class="btn btn-secondary blocked-load-more" type="button" data-action="load-more-blocked">Load more</button>
*/
const createLoadMoreButton = () => {
  const button = document.createElement('button');
  button.classList.add('btn', 'btn-secondary', 'blocked-load-more');
  button.type = 'button';
  button.dataset.action = 'load-more-blocked';
  button.textContent = isLoadingMore ? 'Loading…' : 'Load more';
  button.disabled = isLoadingMore;
  return button;
};

/*
HTML Skeleton Reference:
<p class="modal-hint">You have not blocked anyone.</p>
*/
const createHint = (text) => {
  const hint = document.createElement('p');
  hint.classList.add('modal-hint');
  hint.textContent = text;
  return hint;
};

/* ---------- 3. Show ---------- */

const renderBlockedList = () => {
  if (!hasLoaded) {
    blockedList.replaceChildren(createHint(loadFailed ? 'Could not load blocked users.' : 'Loading blocked users…'));
    return;
  }
  if (blockedUsers.length === 0) {
    blockedList.replaceChildren(createHint('You have not blocked anyone.'));
    return;
  }

  const rows = blockedUsers.map(toBlockedView).map(createBlockedRow);
  if (hasMore) rows.push(createLoadMoreButton());
  blockedList.replaceChildren(...rows);
};

/* ---------- 4. Requests ---------- */

// GET /api/blocks?limit={limit}&before={block_id}
// Returns the page (an array), or null on error.
const fetchBlockedPage = async (beforeBlockId) => {
  let url = '/api/blocks?limit=' + PAGE_LIMIT;
  if (beforeBlockId != null) url += '&before=' + encodeURIComponent(beforeBlockId);

  try {
    const response = await fetch(url, { method: 'GET', credentials: 'include' });
    const body = await response.json().catch(() => null);

    if (!response.ok) {
      showError(body?.message || 'Failed to fetch blocked users');
      return null;
    }
    if (!Array.isArray(body)) {
      showError('Invalid blocked users data');
      return null;
    }
    return body;
  } catch (error) {
    showError('Failed to fetch blocked users');
    return null;
  }
};

const loadMoreBlocked = async () => {
  if (isLoadingMore || !hasMore || blockedUsers.length === 0) return;
  const seq = loadSeq;
  isLoadingMore = true;
  renderBlockedList();

  const lastBlockId = blockedUsers[blockedUsers.length - 1].block_id;
  const page = await fetchBlockedPage(lastBlockId);
  isLoadingMore = false;
  if (seq !== loadSeq) return;   // the modal was reopened meanwhile

  if (page) {
    // Skip anyone already on screen (a row can shift pages after an unblock)
    const shown = new Set(blockedUsers.map((item) => String(item.blocked_id)));
    blockedUsers = blockedUsers.concat(page.filter((item) => !shown.has(String(item.blocked_id))));
    hasMore = page.length === PAGE_LIMIT;
  }
  renderBlockedList();
};

// DELETE /api/blocks?user_id={user_id}
// 200: { "unblocked_id": 7 }   404: not blocked any more   Errors: { "message": "..." }
const unblockUser = async (userId, row, button) => {
  const item = findBlocked(userId);
  if (!item) return;
  const name = toBlockedView(item).name;

  button.disabled = true;
  button.textContent = 'Unblocking…';

  const restoreButton = () => {
    button.disabled = false;
    button.textContent = 'Unblock';
  };

  try {
    const response = await fetch(
      '/api/blocks?user_id=' + encodeURIComponent(userId),
      { method: 'DELETE', credentials: 'include' }
    );
    const body = await response.json().catch(() => ({}));

    if (!response.ok && response.status !== 404) {
      showError(body?.message || 'Could not unblock ' + name);
      restoreButton();
      return;
    }
    if (response.ok && String(body?.unblocked_id) !== String(userId)) {
      showError('Unexpected response while unblocking ' + name);
      restoreButton();
      return;
    }

    // 200: unblocked. 404: the block was already gone. Either way the row goes.
    blockedUsers = blockedUsers.filter((entry) => entry !== item);
    row.remove();
    if (blockedUsers.length === 0) renderBlockedList();

    if (response.ok) showToast(name + ' was unblocked');
    else showError(body?.message || name + ' is not blocked any more');
  } catch (error) {
    showError('Could not unblock ' + name);
    restoreButton();
  }
};

/* ---------- 5. Modal and events ---------- */

// chat.js calls this each time the blocked users modal opens
export async function prepareBlockedUsersModal() {
  const seq = ++loadSeq;
  blockedUsers = [];
  hasLoaded = false;
  loadFailed = false;
  hasMore = false;
  isLoadingMore = false;
  renderBlockedList();                 // "Loading…" at once

  const page = await fetchBlockedPage(null);
  if (seq !== loadSeq) return;         // reopened meanwhile: the newer call renders

  if (page) {
    blockedUsers = page;
    hasLoaded = true;
    hasMore = page.length === PAGE_LIMIT;
  } else {
    loadFailed = true;
  }
  renderBlockedList();
}

// One click listener for the list: the button says what it does with data-action,
// the row says which user with data-blocked-user-id (the blocked user's id).
blockedList.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button || button.disabled) return;

  if (button.dataset.action === 'load-more-blocked') {
    loadMoreBlocked();
    return;
  }

  if (button.dataset.action === 'unblock-user') {
    const row = button.closest('[data-blocked-user-id]');
    if (row) unblockUser(row.dataset.blockedUserId, row, button);
  }
});
