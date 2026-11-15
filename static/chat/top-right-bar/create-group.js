const groupNameInput = document.getElementById('group-name-input');
const userList = document.getElementById('group-members');


function initials(name) {
    const parts = name.split(' ');
    if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase(); // name error if 1-letter word???
    }
    return (parts[0][0] + parts[1][0]).toUpperCase();
}
/*
<label class="user-row member-row">
  <div class="user-row-avatar">MV</div>
  <div class="user-row-info">
    <span class="user-row-name">Marcus Vance</span>
  </div>
  <input type="checkbox" value="Marcus Vance" />
</label>
*/
function createMemberRow(name) {
    const userRowLabel = document.createElement('label');
    userRowLabel.classList.add('user-row', 'member-row');

    const userRowAvatar = document.createElement('div');
    userRowAvatar.classList.add('user-row-avatar');
    userRowAvatar.textContent = initials(name);

    userRowLabel.appendChild(userRowAvatar);

    const userRowInfo = document.createElement('div');
    userRowInfo.classList.add('user-row-info');

    const userRowName = document.createElement('span');
    userRowName.classList.add('user-row-name');
    userRowName.textContent = name;

    userRowInfo.appendChild(userRowName);
    userRowLabel.appendChild(userRowInfo);

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = name;

    userRowLabel.appendChild(checkbox);

    return userRowLabel;
}

export async function getFriendsList() {
    // get friends list from server
    // TODO:
}


async function createGroup(membersList, groupName) {
    // TODO: fetch to server to create group with membersList and groupName
}