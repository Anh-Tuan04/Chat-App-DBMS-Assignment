const messageStream = document.getElementById('message-stream');

/*
HTML Skeleton Reference:
<span class="material-symbols-outlined [className]">content_copy</span>
*/
const createIcon = ({ name, className }) => {
  const icon = document.createElement('span');
  icon.classList.add('material-symbols-outlined');
  if (className) icon.classList.add(className);
  icon.textContent = name;
  return icon;
};

/*
HTML Skeleton Reference:
<div class="date-divider">
  <div class="date-divider-line-wrap">
    <div class="date-divider-line"></div>
  </div>
  <span class="date-divider-label">Today, October 24, 2024</span>
</div>
*/
const createDateDivider = ({ label }) => {
  const line = document.createElement('div');
  line.classList.add('date-divider-line');

  const lineWrap = document.createElement('div');
  lineWrap.classList.add('date-divider-line-wrap');
  lineWrap.appendChild(line);

  const labelText = document.createElement('span');
  labelText.classList.add('date-divider-label');
  labelText.textContent = label;

  const divider = document.createElement('div');
  divider.classList.add('date-divider');
  divider.appendChild(lineWrap);
  divider.appendChild(labelText);
  return divider;
};

/*
HTML Skeleton Reference:
<div class="message-avatar-wrap">
  <!-- with a photo -->
  <img class="message-avatar" alt="Marcus Vance" src="https://..." />
  <!-- without a photo -->
  <div class="message-avatar-initials">MV</div>
  <!-- only when status is given -->
  <span class="status-dot is-online"></span>
</div>
*/
const createMessageAvatar = ({ author, avatarUrl, initials, status }) => {
  const avatarWrap = document.createElement('div');
  avatarWrap.classList.add('message-avatar-wrap');

  if (avatarUrl) {
    const photo = document.createElement('img');
    photo.classList.add('message-avatar');
    photo.setAttribute('alt', author);
    photo.setAttribute('src', avatarUrl);
    avatarWrap.appendChild(photo);
  } else {
    const initialsBox = document.createElement('div');
    initialsBox.classList.add('message-avatar-initials');
    initialsBox.textContent = initials;
    avatarWrap.appendChild(initialsBox);
  }

  if (status) {
    const statusDot = document.createElement('span');
    statusDot.classList.add('status-dot', 'is-' + status);
    avatarWrap.appendChild(statusDot);
  }

  return avatarWrap;
};

/*
HTML Skeleton Reference:
<div class="message-header">
  <span class="message-author">Marcus Vance</span>
  <!-- only when roleLabel is given -->
  <span class="role-badge role-staff">Staff Eng</span>
  <span class="message-time">09:41 AM</span>
</div>
*/
const createMessageHeader = ({ author, roleVariant, roleLabel, time }) => {
  const authorName = document.createElement('span');
  authorName.classList.add('message-author');
  authorName.textContent = author;

  const timeText = document.createElement('span');
  timeText.classList.add('message-time');
  timeText.textContent = time;

  const header = document.createElement('div');
  header.classList.add('message-header');
  header.appendChild(authorName);
  if (roleLabel) {
    const roleBadge = document.createElement('span');
    roleBadge.classList.add('role-badge', 'role-' + roleVariant);
    roleBadge.textContent = roleLabel;
    header.appendChild(roleBadge);
  }
  header.appendChild(timeText);
  return header;
};

/*
HTML Skeleton Reference:
<p class="message-text [has-attachment]">
  Plain text part
  <code class="inline-code">inline code part</code>
  Plain text part
</p>
*/
// parts: [{ type: 'text' | 'code', value: '...' }]
const createMessageText = ({ parts, hasAttachment }) => {
  const paragraph = document.createElement('p');
  paragraph.classList.add('message-text');
  if (hasAttachment) paragraph.classList.add('has-attachment');

  parts.forEach(({ type, value }) => {
    if (type === 'code') {
      const inlineCode = document.createElement('code');
      inlineCode.classList.add('inline-code');
      inlineCode.textContent = value;
      paragraph.appendChild(inlineCode);
    } else {
      paragraph.appendChild(document.createTextNode(value));
    }
  });

  return paragraph;
};

/*
HTML Skeleton Reference:
<pre class="code-block-content" id="code-block-m2">
  <span class="token-keyword">export const</span> plain text <span class="token-string">'...'</span>
</pre>
*/
// tokens: [{ type: 'keyword' | 'function' | 'string' | 'muted' | null, text: '...' }]
const createCodeContent = ({ id, tokens }) => {
  const pre = document.createElement('pre');
  pre.classList.add('code-block-content');
  pre.id = id;

  tokens.forEach(({ type, text }) => {
    if (type) {
      const token = document.createElement('span');
      token.classList.add('token-' + type);
      token.textContent = text;
      pre.appendChild(token);
    } else {
      pre.appendChild(document.createTextNode(text));
    }
  });

  return pre;
};

/*
HTML Skeleton Reference:
<div class="code-block">
  <div class="code-block-header">
    <div class="code-block-title">
      <span class="material-symbols-outlined">data_object</span>
      <span>tokenObserver.ts</span>
    </div>
    <button class="code-copy-btn" type="button" data-copy-target="code-block-m2">
      <span class="material-symbols-outlined">content_copy</span>
      <span>Copy Code</span>
    </button>
  </div>
  <pre class="code-block-content" id="code-block-m2">...</pre>
</div>
*/
const createCodeBlock = ({ id, fileName, tokens }) => {
  const fileNameText = document.createElement('span');
  fileNameText.textContent = fileName;

  const title = document.createElement('div');
  title.classList.add('code-block-title');
  title.appendChild(createIcon({ name: 'data_object' }));
  title.appendChild(fileNameText);

  const copyLabel = document.createElement('span');
  copyLabel.textContent = 'Copy Code';

  const copyButton = document.createElement('button');
  copyButton.classList.add('code-copy-btn');
  copyButton.type = 'button';
  copyButton.dataset.copyTarget = id;
  copyButton.appendChild(createIcon({ name: 'content_copy' }));
  copyButton.appendChild(copyLabel);

  const header = document.createElement('div');
  header.classList.add('code-block-header');
  header.appendChild(title);
  header.appendChild(copyButton);

  const codeBlock = document.createElement('div');
  codeBlock.classList.add('code-block');
  codeBlock.appendChild(header);
  codeBlock.appendChild(createCodeContent({ id, tokens }));
  return codeBlock;
};

/*
HTML Skeleton Reference:
<div class="file-card">
  <div class="file-card-info">
    <div class="file-card-icon">
      <span class="material-symbols-outlined">picture_as_pdf</span>
    </div>
    <div class="file-card-details">
      <div class="file-card-name-row">
        <span class="file-card-name">Q3_Design_Review_v2.pdf</span>
        <span class="material-symbols-outlined file-card-verified" title="Verified Architecture Document">verified</span>
      </div>
      <span class="file-card-meta">4.2 MB • PDF Document</span>
    </div>
  </div>
  <button class="file-card-download-btn" type="button" title="Download Document">
    <span class="material-symbols-outlined">download</span>
  </button>
</div>
*/
const createFileCard = ({ icon, fileName, verifiedTitle, meta }) => {
  const iconBox = document.createElement('div');
  iconBox.classList.add('file-card-icon');
  iconBox.appendChild(createIcon({ name: icon }));

  const name = document.createElement('span');
  name.classList.add('file-card-name');
  name.textContent = fileName;

  const nameRow = document.createElement('div');
  nameRow.classList.add('file-card-name-row');
  nameRow.appendChild(name);
  if (verifiedTitle) {
    const verified = createIcon({ name: 'verified', className: 'file-card-verified' });
    verified.setAttribute('title', verifiedTitle);
    nameRow.appendChild(verified);
  }

  const metaText = document.createElement('span');
  metaText.classList.add('file-card-meta');
  metaText.textContent = meta;

  const details = document.createElement('div');
  details.classList.add('file-card-details');
  details.appendChild(nameRow);
  details.appendChild(metaText);

  const info = document.createElement('div');
  info.classList.add('file-card-info');
  info.appendChild(iconBox);
  info.appendChild(details);

  const downloadButton = document.createElement('button');
  downloadButton.classList.add('file-card-download-btn');
  downloadButton.type = 'button';
  downloadButton.setAttribute('title', 'Download Document');
  downloadButton.appendChild(createIcon({ name: 'download' }));

  const fileCard = document.createElement('div');
  fileCard.classList.add('file-card');
  fileCard.appendChild(info);
  fileCard.appendChild(downloadButton);
  return fileCard;
};

/*
HTML Skeleton Reference:
<button class="image-card-action-btn" type="button" title="Zoom in">
  <span class="material-symbols-outlined">zoom_in</span>
</button>
*/
const createImageActionButton = ({ icon, title }) => {
  const button = document.createElement('button');
  button.classList.add('image-card-action-btn');
  button.type = 'button';
  button.setAttribute('title', title);
  button.appendChild(createIcon({ name: icon }));
  return button;
};

/*
HTML Skeleton Reference:
<div class="image-card">
  <div class="image-card-preview">
    <img class="image-card-img" alt="Interface design wireframe diagram" src="https://..." />
    <div class="image-card-overlay">
      <div class="image-card-info">
        <span class="image-card-filename">thread_spec_v04.png</span>
        <span class="image-card-meta">2560 × 1440 • 840 KB</span>
      </div>
      <div class="image-card-actions">
        <button class="image-card-action-btn" type="button" title="Zoom in">...</button>
        <button class="image-card-action-btn" type="button" title="Download file">...</button>
      </div>
    </div>
  </div>
</div>
*/
const createImageCard = ({ src, alt, fileName, meta }) => {
  const picture = document.createElement('img');
  picture.classList.add('image-card-img');
  picture.setAttribute('alt', alt);
  picture.setAttribute('src', src);

  const fileNameText = document.createElement('span');
  fileNameText.classList.add('image-card-filename');
  fileNameText.textContent = fileName;

  const metaText = document.createElement('span');
  metaText.classList.add('image-card-meta');
  metaText.textContent = meta;

  const info = document.createElement('div');
  info.classList.add('image-card-info');
  info.appendChild(fileNameText);
  info.appendChild(metaText);

  const actions = document.createElement('div');
  actions.classList.add('image-card-actions');
  actions.appendChild(createImageActionButton({ icon: 'zoom_in', title: 'Zoom in' }));
  actions.appendChild(createImageActionButton({ icon: 'download', title: 'Download file' }));

  const overlay = document.createElement('div');
  overlay.classList.add('image-card-overlay');
  overlay.appendChild(info);
  overlay.appendChild(actions);

  const preview = document.createElement('div');
  preview.classList.add('image-card-preview');
  preview.appendChild(picture);
  preview.appendChild(overlay);

  const imageCard = document.createElement('div');
  imageCard.classList.add('image-card');
  imageCard.appendChild(preview);
  return imageCard;
};

// attachment.kind decides which factory builds the attachment
const attachmentFactories = {
  code: (attachment, messageId) => createCodeBlock({
    id: 'code-block-' + messageId,
    fileName: attachment.fileName,
    tokens: attachment.tokens
  }),
  file: (attachment) => createFileCard(attachment),
  image: (attachment) => createImageCard(attachment)
};

/*
HTML Skeleton Reference:
<div class="message [message-new] [message-own] " data-message-id="...">
  <div class="message-avatar-wrap">...</div>
  <div class="message-body">
    <div class="message-header">...</div>
    <p class="message-text [has-attachment]">...</p>
    <!-- optional: code-block | file-card | image-card -->
  </div>
</div>
*/
const createMessage = ({
  id, author, avatarUrl, initials, status,
  roleVariant, roleLabel, time, parts, attachment, isNew = false, isOwn = false
}) => {
  const body = document.createElement('div');
  body.classList.add('message-body');
  body.appendChild(createMessageHeader({ author, roleVariant, roleLabel, time }));
  if (parts && parts.length) {
    body.appendChild(createMessageText({ parts, hasAttachment: Boolean(attachment) }));
  }
  if (attachment) {
    body.appendChild(attachmentFactories[attachment.kind](attachment, id));
  }

  const message = document.createElement('div');
  message.classList.add('message');
  if (isNew) message.classList.add('message-new');
  if (isOwn) message.classList.add('message-own');
  message.dataset.messageId = id;
  message.appendChild(createMessageAvatar({ author, avatarUrl, initials, status }));
  message.appendChild(body);
  return message;
};

/*
HTML Skeleton Reference (#message-stream after the call):
<div class="message-stream" id="message-stream" data-conversation-id="1"></div>
*/
// Call when the user clicks a conversation, before the first page is requested.
// messagesStream: document.getElementById('message-stream')
const createNewMessageStream = (messageStream, conversationId) => {
  messageStream.replaceChildren();
  messageStream.dataset.conversationId = conversationId;
  messageStream.scrollTop = 0;
};


const clearMessageStream = (messageStream) => {
  messageStream.replaceChildren();
  delete messageStream.dataset.conversationId;
  messageStream.scrollTop = 0;
}

/*
HTML Skeleton Reference (content of #message-stream):
<div class="date-divider">...</div>
<div class="message">...</div>   <!-- one per message -->
*/
// messagesStream: document.getElementById('message-stream')
const renderMessageStream = (messageStream, { dateLabel, messages }) => {
  messageStream.replaceChildren(
    createDateDivider({ label: dateLabel }),
    ...messages.map(createMessage)
  );
};

export { messageStream, createDateDivider, createMessage, createNewMessageStream, renderMessageStream, clearMessageStream };