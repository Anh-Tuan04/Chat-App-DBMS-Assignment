// import { io } from "socket.io-client"; // For IntelliSense. Don't forget note this when running or get interactive error in UI
import { showError } from "./error.js";
import { appendIncomingMessage } from './chat-area/messages-stream-adapter.js';

export const realTimeSocket = io({
  transports: ['polling']
});

realTimeSocket.on('connect', () => {
  console.log('Connected to the real-time socket server');
});

realTimeSocket.on('disconnect', () => {
  console.log('Disconnected from the real-time socket server');
});

realTimeSocket.on("connect_error", async (err) => {
  showError(err.message);
  if (err.message === "unauthorized") {
    await logout();
  }
});

// handlers for user profile
async function logout() {
  // fetch logout, clear session
  try {
    const res = await fetch(`/api/auth/logout`, {
      method: 'POST',
      credentials: 'include', // Include cookies for session management
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (res.ok) {
      // Clear local storage
      localStorage.clear();
      realTimeSocket.disconnect(); // Disconnect the socket before redirecting
      // Redirect to login page
      window.location.replace('/');
    } else {
      const errorData = await res.json();
      const errorMessage = errorData?.message || 'Logout failed';
      showError(errorMessage);
    }

  } catch (error) {
    showError('Logout failed: ' + error.message);

  }
}
