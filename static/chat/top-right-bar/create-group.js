import { addConversationItem } from '../conversation.js';
import { showError } from '../error.js';
import { showToast } from '../toast.js';
import { searchUsers } from './user-search.js';

const groupNameInput = document.getElementById('group-name-input');
const memberSearchInput = document.getElementById('group-member-search');
const userList = document.getElementById('group-members');
const selectedMembersList = document.getElementById('selected-group-members');
const memberCount = document.getElementById('group-member-count');
const createGroupButton = document.getElementById('create-group-submit');
const groupModal = document.getElementById('create-group-modal');
const MAX_GROUP_MEMBERS = 99;

const selectedMembers = new Map();
let searchTimer = null;
let searchVersion = 0;
let isSubmitting = false;

function getInitials(name = '') {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return '?';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/*
HTML Skeleton Reference:
<p class="modal-hint">Search for users to add to the group.</p>
*/
function createHint(text) {
    const hint = document.createElement('p');
    hint.classList.add('modal-hint');
    hint.textContent = text;
    return hint;
}

// Replaces everything in `container` (#group-members) with one hint
function renderHint(container, text) {
    container.replaceChildren(createHint(text));
}

function updateCreateButton() {
    const hasName = Boolean(groupNameInput.value.trim());
    const hasMembers = selectedMembers.size > 0;
    createGroupButton.disabled = isSubmitting || !hasName || !hasMembers;
}

/*
HTML Skeleton Reference (one per selected member, inside #selected-group-members;
a click removes the member, see the listener on selectedMembersList):
<button class="btn btn-secondary selected-member-chip" type="button"
        data-user-id="7" aria-label="Remove Jane Doe">Jane Doe ×</button>
*/
function createSelectedMemberChip(user) {
    const name = user.display_name || user.username;
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.classList.add('btn', 'btn-secondary', 'selected-member-chip');
    chip.dataset.userId = String(user.user_id);
    chip.textContent = `${name} ×`;
    chip.setAttribute('aria-label', `Remove ${name}`);
    return chip;
}

/*
HTML Skeleton Reference (content of #selected-group-members):
<button class="btn btn-secondary selected-member-chip" ...>Jane Doe ×</button>
<button class="btn btn-secondary selected-member-chip" ...>Mike ×</button>
*/
function renderSelectedMembers() {
    memberCount.textContent = String(selectedMembers.size);
    selectedMembersList.replaceChildren(
        ...Array.from(selectedMembers.values(), createSelectedMemberChip)
    );
    updateCreateButton();
}

/*
HTML Skeleton Reference (one per search result, inside #group-members):
<label class="user-row member-row">
  <div class="user-row-avatar">JD</div>
  <div class="user-row-info">
    <span class="user-row-name">Jane Doe</span>
    <span class="user-row-sub">@jane_doe</span>
  </div>
  <input type="checkbox" aria-label="Add Jane Doe to the group" [checked] [disabled] />
         <!-- disabled when not checked and 99 members are already selected -->
</label>
*/
function createMemberRow(user) {
    const name = user.display_name || user.username;
    const row = document.createElement('label');
    row.classList.add('user-row', 'member-row');

    const avatar = document.createElement('div');
    avatar.classList.add('user-row-avatar');
    avatar.textContent = getInitials(name);
    row.appendChild(avatar);

    const info = document.createElement('div');
    info.classList.add('user-row-info');
    const displayName = document.createElement('span');
    displayName.classList.add('user-row-name');
    displayName.textContent = name;
    const username = document.createElement('span');
    username.classList.add('user-row-sub');
    username.textContent = `@${user.username}`;
    info.append(displayName, username);
    row.appendChild(info);

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = selectedMembers.has(Number(user.user_id));
    checkbox.disabled = !checkbox.checked && selectedMembers.size >= MAX_GROUP_MEMBERS;
    checkbox.setAttribute('aria-label', `Add ${name} to the group`);
    checkbox.addEventListener('change', () => {
        const userId = Number(user.user_id);
        if (checkbox.checked) {
            selectedMembers.set(userId, user);
        } else {
            selectedMembers.delete(userId);
        }
        renderSelectedMembers();
        renderUsers(currentSearchResults);
    });
    row.appendChild(checkbox);
    return row;
}

let currentSearchResults = [];

/*
HTML Skeleton Reference (content of #group-members):
<label class="user-row member-row">...</label>   <!-- one per user, see createMemberRow -->
   or, when there are no results:
<p class="modal-hint">No users found.</p>
*/
function renderUsers(users) {
    userList.replaceChildren();
    if (!users.length) {
        renderHint(userList, 'No users found.');
        return;
    }
    users.forEach((user) => userList.appendChild(createMemberRow(user)));
}

export function initializeCreateGroup() {
    window.clearTimeout(searchTimer);
    searchVersion += 1;
    currentSearchResults = [];
    selectedMembers.clear();
    isSubmitting = false;
    groupNameInput.value = '';
    memberSearchInput.value = '';
    renderHint(userList, 'Search for users to add to the group.');
    selectedMembersList.replaceChildren();
    memberCount.textContent = '0';
    updateCreateButton();
}

groupNameInput.addEventListener('input', updateCreateButton);

memberSearchInput.addEventListener('input', () => {
    window.clearTimeout(searchTimer);
    const query = memberSearchInput.value.trim();
    const version = ++searchVersion;
    currentSearchResults = [];
    if (!query) {
        renderHint(userList, 'Search for users to add to the group.');
        return;
    }
    if (query.length > 50) {
        renderHint(userList, 'Search term must be 50 characters or fewer.');
        return;
    }

    renderHint(userList, 'Searching users...');
    searchTimer = window.setTimeout(async () => {
        try {
            const users = await searchUsers(query);
            if (version !== searchVersion) return;
            currentSearchResults = users;
            renderUsers(users);
        } catch (error) {
            if (version !== searchVersion) return;
            showError(error.message);
            renderHint(userList, 'Could not load users.');
        }
    }, 250);
});

selectedMembersList.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-user-id]');
    if (!button) return;
    selectedMembers.delete(Number(button.dataset.userId));
    renderSelectedMembers();
    renderUsers(currentSearchResults);
});

createGroupButton.addEventListener('click', async () => {
    const groupName = groupNameInput.value.trim();
    const memberIds = Array.from(selectedMembers.keys());
    if (!groupName || memberIds.length === 0 || isSubmitting) return;

    isSubmitting = true;
    updateCreateButton();
    try {
        const response = await fetch('/api/conversations/new-group', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ group_name: groupName, member_ids: memberIds })
        });
        const body = await response.json();
        if (!response.ok) {
            showError(body?.message || 'Could not create group');
            return;
        }
        if (!body || typeof body !== 'object' || !body.conversation_id) {
            showError('Invalid create-group response');
            return;
        }

        groupModal.hidden = true;
        showToast('Group created');
        // 201: { conversation_id, conversation_type, receiver_id, receiver_display_name, conversation_img_url }
        // Draw the new group's row from the response (no list fetch). The members get it
        // through their 'group_added' notification.
        addConversationItem({
            conversation_id: body.conversation_id,
            conversation_type: body.conversation_type || 'group',
            receiver_id: null,
            display_name: body.receiver_display_name || groupName,
            conversation_img_url: body.conversation_img_url,
            latest_message: null,
            unread_count: 0
        });
    } catch (error) {
        showError(error?.message || 'Could not create group');
    } finally {
        isSubmitting = false;
        updateCreateButton();
    }
});
