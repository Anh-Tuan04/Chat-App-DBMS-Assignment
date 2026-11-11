import { showError } from './error.js';

/*
<!-- ===== Modal: Friends List ===== -->
<div class="modal" id="friends-modal" role="dialog" aria-modal="true" aria-labelledby="friends-title" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-dialog">
    <div class="modal-header">
      <h3 class="modal-title" id="friends-title">Friends</h3>
      <button class="modal-close" type="button" data-close title="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <div class="modal-body">
      <div class="modal-results" id="friends-list">

      <!-- 1 trong 2 phần tử này -->
        
        <!-- Trường hợp 1: Có URL ảnh đại diện + Trạng thái is-active -->
        <div class="user-row friend-row is-active" data-friend-list-id="1">
          <div class="friend-avatar-wrap">
            <img class="friend-avatar-img" src="https://example.com/avatar.jpg" alt="Gabriel Federick" />
            <span class="status-dot is-online"></span>
          </div>
          <div class="user-row-info">
            <span class="user-row-name">Gabriel Federick</span>
            <span class="user-row-sub">Online</span>
          </div>
        </div>

        <!-- Trường hợp 2: Không có URL ảnh (Fallback ký tự đầu "GF") + Trạng thái thường -->
        <div class="user-row friend-row" data-friend-list-id="2">
          <div class="friend-avatar-wrap">
            <div class="friend-avatar-initials">GF</div>
            <span class="status-dot is-idle"></span>
          </div>
          <div class="user-row-info">
            <span class="user-row-name">Gabriel Federick</span>
            <span class="user-row-sub">Away</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</div>
*/



const friendsList = document.getElementById('friends-list');

const friendsItems = [
    {
        id: 1,
        initials: 'GF',
        name: 'Gabriel Federick',
        state: 'online',
        avatarUrl: 'https://i.pravatar.cc/150?img=12'
    },
    {
        id: 2,
        initials: 'HH',
        name: 'Hannah Hill',
        state: 'idle',
        avatarUrl: null
    }
]

function createFriendRow({ id, initials, name, state, avatarUrl }) {
    // use createElement, manipulating dom, not innerHtml
    const friendRow = document.createElement('div');
    friendRow.setAttribute('data-friend-list-id', id);
    friendRow.classList.add('user-row', 'friend-row');

    if (state === 'online') {
        friendRow.classList.add('is-active');
    }

    const avatarWrap = document.createElement('div');
    avatarWrap.classList.add('friend-avatar-wrap');

    if (avatarUrl) {
        const avatarImg = document.createElement('img');
        avatarImg.classList.add('friend-avatar-img');
        avatarImg.src = avatarUrl;
        avatarImg.alt = name;
        avatarWrap.appendChild(avatarImg);
    } else {
        const avatarInitials = document.createElement('div');
        avatarInitials.classList.add('friend-avatar-initials');
        avatarInitials.textContent = initials;
        avatarWrap.appendChild(avatarInitials);
    }

    const statusDot = document.createElement('span');
    statusDot.classList.add('status-dot');

    if (state === 'online') {
        statusDot.classList.add('is-online');
    } else if (state === 'idle') {
        statusDot.classList.add('is-idle');
    } else {
        statusDot.classList.add('is-offline');
    }

    avatarWrap.appendChild(statusDot);
    friendRow.appendChild(avatarWrap);

    const info = document.createElement('div');
    info.classList.add('user-row-info');

    const nameLabel = document.createElement('span');
    nameLabel.classList.add('user-row-name');
    nameLabel.textContent = name;
    info.appendChild(nameLabel);

    const subLabel = document.createElement('span');
    subLabel.classList.add('user-row-sub');

    if (state === 'online') {
        subLabel.textContent = 'Online';
    } else if (state === 'idle') {
        subLabel.textContent = 'Away';
    } else {
        subLabel.textContent = 'Offline';
    }

    info.appendChild(subLabel);
    friendRow.appendChild(info);

    return friendRow;
}


// function fetch to server to get friends list (Not used)
export async function fetchFriends() {
    const res = await fetch('/api/friends');
    if (!res.ok) {
        showError('Failed to fetch friends list');
        return;
    }
    const data = await res.json();
    if (!Array.isArray(data)) {
        showError('Invalid friends list data');
        return;
    }

    // update friendsItems



}

export function renderFriends() {
    if (!friendsList) return;

    friendsList.replaceChildren();

    friendsItems.forEach((friend) => {
        friendsList.append(createFriendRow(friend));
    });
}
