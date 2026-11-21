import { showError } from '../error.js';
import { showToast } from '../toast.js';

const addFriendInput = document.getElementById('add-friend-input');
const addFriendResults = document.getElementById('add-friend-results');


/*
<div class="modal" id="add-friend-modal" role="dialog" aria-modal="true" aria-labelledby="add-friend-title" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-dialog">

    <div class="modal-header">
      <h3 class="modal-title" id="add-friend-title">Add friend</h3>
      <button class="modal-close" type="button" data-close title="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

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





/*
        <!-- one of these three, depending on the state -->
        <!-- nothing typed yet -->
        <p class="modal-hint">Type a name or handle to find people.</p>


        <!-- no match -->
        <p class="modal-hint">No users found for "query".</p>


        <!-- one row per match (createUserRow) -->
        <div class="user-row">
            <div class="user-row-avatar">TB</div>

            <div class="user-row-info">
                <span class="user-row-name">Tom Becker</span>
                <span class="user-row-sub">@tbecker</span>
            </div>

            <!-- the button depends on the relationship status: -->

            <!-- 1. not a friend yet -->
            <button class="btn btn-primary" type="button" data-user-id="u2">Add friend</button>

            <!-- 2. request already sent -->
            <button class="btn btn-secondary" type="button" data-user-id="u2" disabled>Requested</button>

            <!-- 3. already a friend -->
            <button class="btn btn-secondary" type="button" data-user-id="u2" disabled>Friends</button>

            <!-- 4. this user has already sent a request -->
            <button class="btn btn-primary" type="button" data-user-id="u2">Accept request</button>
        </div>
*/
const createUserRow = ({
    user_id,
    username,
    display_name,
    relationship_status,
}) => {
    const name = display_name || username;
    const initials = name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0].toUpperCase())
        .join('');
    const userRow = document.createElement('div');
    userRow.classList.add('user-row');
    userRow.dataset.userId = user_id;

    const userRowAvatar = document.createElement('div');
    userRowAvatar.classList.add('user-row-avatar');
    userRowAvatar.textContent = initials;

    const userRowInfo = document.createElement('div');
    userRowInfo.classList.add('user-row-info');
    const userRowName = document.createElement('span');
    userRowName.classList.add('user-row-name');
    userRowName.textContent = name;
    const userRowHandle = document.createElement('span');
    userRowHandle.classList.add('user-row-sub');
    userRowHandle.textContent = `@${username}`;
    userRowInfo.appendChild(userRowName);
    userRowInfo.appendChild(userRowHandle);
    userRow.appendChild(userRowAvatar);
    userRow.appendChild(userRowInfo);

    const requestButton = document.createElement('button');
    requestButton.type = 'button';
    requestButton.dataset.userId = user_id;
    if (relationship_status === 'friend') {
        requestButton.classList.add('btn', 'btn-secondary');
        requestButton.textContent = 'Friends';
        requestButton.disabled = true;
    } else if (relationship_status === 'requested') {
        requestButton.classList.add('btn', 'btn-secondary');
        requestButton.textContent = 'Requested';
        requestButton.disabled = true;
    } else if (relationship_status === 'received') {
        requestButton.classList.add('btn', 'btn-primary');
        requestButton.dataset.action = 'send-friend-request';
        requestButton.textContent = 'Accept request';
    } else if (relationship_status === 'none') {
        requestButton.classList.add('btn', 'btn-primary');
        requestButton.dataset.action = 'send-friend-request';
        requestButton.textContent = 'Add friend';
    } else {
        requestButton.classList.add('btn', 'btn-secondary');
        requestButton.textContent = 'Unavailable';
        requestButton.disabled = true;
    }
    userRow.appendChild(requestButton);

    return userRow;
}

function renderSearchResults(results) {
    addFriendResults.replaceChildren();
    if (!results.length) {
        const hint = document.createElement('p');
        hint.classList.add('modal-hint');
        hint.textContent = `No users found for "${addFriendInput.value.trim()}".`;
        addFriendResults.appendChild(hint);
        return;
    }
    addFriendResults.append(...results.map(createUserRow));
}

export async function fetchSearchUser(queryName) {
    try {
        const response = await fetch(
            `/api/users/search?username=${encodeURIComponent(queryName)}`,
            { credentials: 'same-origin' }
        );
        if (!response.ok) {
          showError('Failed to search users');
          return [];
        }
        const data = await response.json();
        if (!Array.isArray(data)) {
            showError('Invalid search results');
            return [];
        }
        return data;
    } catch {
        showError('An error occurred while searching users');
        return [];
    }
}

function setRequestButtonState(button, label) {
    button.disabled = true;
    button.classList.remove('btn-primary');
    button.classList.add('btn-secondary');
    button.textContent = label;
}

async function sendFriendRequest(button) {
    const userId = button.dataset.userId;
    if (!/^\d+$/.test(userId || '')) {
        showError('Invalid user selected');
        return;
    }

    button.disabled = true;
    button.textContent = 'Sending...';

    let response;
    try {
        response = await fetch(
            `/api/relationships/friend-request?user_id=${encodeURIComponent(userId)}`,
            {
                method: 'POST',
                credentials: 'same-origin',
                headers: { Accept: 'application/json' },
            }
        );
    } catch {
        button.disabled = false;
        button.textContent = 'Add friend';
        showError('Could not send friend request');
        return;
    }

    let payload;
    try {
        payload = await response.json();
    } catch {
        button.disabled = false;
        button.textContent = 'Add friend';
        showError('Invalid response from server');
        return;
    }

    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
        button.disabled = false;
        button.textContent = 'Add friend';
        showError('Invalid response from server');
        return;
    }

    if (response.status === 409) {
        if (payload.message === 'Already friend') {
            setRequestButtonState(button, 'Friends');
            return;
        }
        if (payload.message === 'Friend request already exists') {
            setRequestButtonState(button, 'Requested');
            return;
        }
    }

    if (!response.ok) {
        button.disabled = false;
        button.textContent = 'Add friend';
        showError(payload.message || 'Could not send friend request');
        return;
    }

    if (Number(payload.receiver_id) !== Number(userId)
        || !['requested', 'friends'].includes(payload.status)) {
        button.disabled = false;
        button.textContent = 'Add friend';
        showError('Server returned an unexpected friend request result');
        return;
    }

    if (payload.status === 'friends') {
        setRequestButtonState(button, 'Friends');
        showToast('Friend request accepted');
    } else {
        setRequestButtonState(button, 'Requested');
        showToast('Friend request sent');
    }
}

export function initializeUserSearch() {
    let debounceTimer;
    let searchVersion = 0;

    addFriendInput.addEventListener('input', () => {
        window.clearTimeout(debounceTimer);
        const query = addFriendInput.value.trim();
        const currentVersion = ++searchVersion;

        if (!query) {
            addFriendResults.replaceChildren();
            const hint = document.createElement('p');
            hint.classList.add('modal-hint');
            hint.textContent = 'Type a username to find people.';
            addFriendResults.appendChild(hint);
            return;
        }

        debounceTimer = window.setTimeout(async () => {
            const results = await fetchSearchUser(query);
            if (currentVersion === searchVersion) {
                renderSearchResults(results);
            }
        }, 250);
    });

    addFriendResults.addEventListener('click', (event) => {
        const button = event.target.closest(
            'button[data-action="send-friend-request"]'
        );
        if (!button || button.disabled) return;
        sendFriendRequest(button);
    });
}