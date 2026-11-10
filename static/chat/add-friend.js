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

            <!-- the button depends on the person's state: -->

            <!-- 1. not a friend yet -->
            <button class="btn btn-primary" type="button" data-user-id="u2">Add friend</button>

            <!-- 2. request already sent -->
            <button class="btn btn-secondary" type="button" data-user-id="u2" disabled>Requested</button>

            <!-- 3. already a friend -->
            <button class="btn btn-secondary" type="button" data-user-id="u2" disabled>Friends</button>
        </div>
*/
const createUserRow = ({
  id, 
  initials, 
  name, 
  // handle, 
  state}) => {
    const userRow = document.createElement('div');
    userRow.classList.add('user-row');

    const userRowAvatar = document.createElement('div');
    userRowAvatar.classList.add('user-row-avatar');
    userRowAvatar.textContent = initials;

    const userRowInfo = document.createElement('div');
    userRowInfo.classList.add('user-row-info');
    const userRowName = document.createElement('span');
    userRowName.classList.add('user-row-name');
    userRowName.textContent = name;
    // const userRowSub = document.createElement('span');
    // userRowSub.classList.add('user-row-sub');
    // userRowSub.textContent = `@${handle}`;
    userRowInfo.appendChild(userRowName);
    // userRowInfo.appendChild(userRowSub);

    const userRowButton = document.createElement('button');
    userRowButton.type = 'button';
    userRowButton.dataset.userId = id;

    if (state === 'not-friend') {
        userRowButton.classList.add('btn', 'btn-primary');
        userRowButton.textContent = 'Add friend';
    } else if (state === 'requested') {
        userRowButton.classList.add('btn', 'btn-secondary');
        userRowButton.disabled = true;
        userRowButton.textContent = 'Requested';
    } else if (state === 'friend') {
        userRowButton.classList.add('btn', 'btn-secondary');
        userRowButton.disabled = true;
        userRowButton.textContent = 'Friends';
    }

    userRow.appendChild(userRowAvatar);
    userRow.appendChild(userRowInfo);
    userRow.appendChild(userRowButton);
    return userRow;
}