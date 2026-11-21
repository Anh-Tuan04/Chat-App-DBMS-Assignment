import { appendIncomingMessage } from './messages-stream-adapter.js';
import { realTimeSocket } from '../real-time-socket.js';
import { handleNewMessageComing } from '../conversation.js';
import { showError } from '../error.js';


const currentUser = JSON.parse(
  localStorage.getItem('user') || '{}'
);
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-btn');
export const messageStreamElement = document.getElementById('message-stream');

const ACK_TIMEOUT_MS = 5000;

const handleSubmitMessage = async (messageStream) => {
  const text = chatInput.value.trim();
  if (!text) return;

  const conversationId = messageStream.dataset.conversationId;   // changed: from the stream
  if (!conversationId) {
    showError('Select a conversation first.');
    return;
  }
  if (!realTimeSocket.connected) {
    showError('Not connected to the server. Please try again.');
    return;
  }

  const payload = {
    sender_info: {
      user_id: currentUser.user_id,
      username: currentUser.username,
      display_name: currentUser.display_name,
      avatar_url: currentUser.avatar_url
    },
    conversation_id: conversationId,
    message: text
  };

  chatInput.value = '';
  chatInput.focus();
  const restoreText = () => { if (!chatInput.value) chatInput.value = text; };

  try {
    const response = await realTimeSocket
      .timeout(ACK_TIMEOUT_MS)
      .emitWithAck('send_message', payload);

    if (response.status !== 'success') {
      showError(response.message);
      restoreText();
      return;
    }

    // changed: the stream may now belong to another conversation
    if (messageStream.dataset.conversationId !== conversationId) return;

    appendIncomingMessage(messageStream, {
      ...payload,
      message_id: response.message_id,
      created_at: response.created_at
    });
    messageStream.scrollTop = messageStream.scrollHeight;
  } catch (error) {
    showError('The server did not respond. The message may not have been sent.');
    restoreText();
  }
};

sendButton.addEventListener('click', () => handleSubmitMessage(messageStreamElement));

chatInput.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  handleSubmitMessage(messageStreamElement);
});


realTimeSocket.on('receive_message', (payload) => {
  const openConversationId = messageStreamElement.dataset.conversationId;

  if (String(payload.conversation_id) === openConversationId) {
    appendIncomingMessage(messageStreamElement, payload);
    return;
  }

  // Message for another conversation: update the sidebar item (preview, time, bold, unread badge)
  // handleNewMessageComing({
  //   conversationId: String(payload.conversation_id),
  //   message: payload.message,
  //   createAt: payload.created_at
  // });
});