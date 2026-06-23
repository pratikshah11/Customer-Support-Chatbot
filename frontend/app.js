/**
 * app.js — WebSocket chat client
 *
 * Handles connection, message rendering, typing indicators,
 * session management, and auto-reconnect logic.
 *
 * IMPORTANT: Replace WEBSOCKET_URL below with the actual
 * WebSocket URL from your `terraform output websocket_url` command.
 */

// ============================================================
// Configuration — UPDATE THIS after terraform apply
// ============================================================
const WEBSOCKET_URL = "%%WEBSOCKET_URL%%"; // Replaced by deploy.sh

// ============================================================
// State
// ============================================================
let socket = null;
let sessionId = null;
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let reconnectTimer = null;
let isWaitingForResponse = false;

// ============================================================
// Session ID — persisted in localStorage per browser session
// ============================================================
function getOrCreateSessionId() {
  let id = sessionStorage.getItem("chatbot_session_id");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("chatbot_session_id", id);
  }
  return id;
}

// ============================================================
// WebSocket Connection
// ============================================================
function connect() {
  sessionId = getOrCreateSessionId();
  setConnectionStatus("connecting");

  socket = new WebSocket(WEBSOCKET_URL);

  socket.onopen = () => {
    isConnected = true;
    reconnectAttempts = 0;
    setConnectionStatus("connected");
    console.log("✅ WebSocket connected, session:", sessionId);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (err) {
      console.error("Failed to parse server message:", err);
    }
  };

  socket.onclose = (event) => {
    isConnected = false;
    setConnectionStatus("error");
    console.warn("WebSocket closed:", event.code, event.reason);
    hideTypingIndicator();
    enableInput();

    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay / 1000}s (attempt ${reconnectAttempts + 1})`);
      reconnectTimer = setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, delay);
    } else {
      appendErrorMessage("Connection lost. Please refresh the page.");
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    setConnectionStatus("error");
  };
}

function disconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  if (socket) socket.close();
}

// ============================================================
// Handle messages from the server
// ============================================================
function handleServerMessage(data) {
  switch (data.type) {
    case "typing":
      data.status ? showTypingIndicator() : hideTypingIndicator();
      break;

    case "message":
      hideTypingIndicator();
      appendBotMessage(data.content);
      enableInput();
      isWaitingForResponse = false;
      break;

    case "error":
      hideTypingIndicator();
      appendErrorMessage(data.content || "An error occurred.");
      enableInput();
      isWaitingForResponse = false;
      break;

    default:
      console.warn("Unknown message type:", data.type);
  }
}

// ============================================================
// Send a message
// ============================================================
function sendMessage() {
  const input = document.getElementById("message-input");
  const text = input.value.trim();

  if (!text || !isConnected || isWaitingForResponse) return;

  // Append user message to UI
  appendUserMessage(text);
  input.value = "";
  autoResize(input);

  // Disable input while waiting
  disableInput();
  isWaitingForResponse = true;

  // Hide welcome screen
  hideWelcomeScreen();

  // Send to WebSocket
  socket.send(JSON.stringify({
    action: "sendMessage",
    message: text,
    session_id: sessionId,
  }));
}

function sendSuggestion(text) {
  const input = document.getElementById("message-input");
  input.value = text;
  sendMessage();
}

// ============================================================
// Message Rendering
// ============================================================
function appendUserMessage(text) {
  const container = document.getElementById("messages-container");
  const msgEl = createMessageElement("user", escapeHtml(text));
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendBotMessage(text) {
  const container = document.getElementById("messages-container");
  const msgEl = createMessageElement("bot", formatBotMessage(text));
  container.appendChild(msgEl);
  scrollToBottom();
}

function appendErrorMessage(text) {
  const container = document.getElementById("messages-container");
  const msgEl = document.createElement("div");
  msgEl.className = "message";
  msgEl.innerHTML = `
    <div class="avatar bot-avatar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>
    <div>
      <div class="bubble error">${escapeHtml(text)}</div>
      <p class="message-time">${getTime()}</p>
    </div>
  `;
  container.appendChild(msgEl);
  scrollToBottom();
}

function createMessageElement(role, htmlContent) {
  const isUser = role === "user";
  const el = document.createElement("div");
  el.className = `message ${role}`;

  const avatarHtml = isUser
    ? `<div class="avatar user-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
       </div>`
    : `<div class="avatar bot-avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
       </div>`;

  el.innerHTML = `
    ${isUser ? "" : avatarHtml}
    <div>
      <div class="bubble ${role}">${htmlContent}</div>
      <p class="message-time">${getTime()}</p>
    </div>
    ${isUser ? avatarHtml : ""}
  `;
  return el;
}

// ============================================================
// Typing Indicator
// ============================================================
function showTypingIndicator() {
  document.getElementById("typing-container").classList.add("visible");
  scrollToBottom();
}

function hideTypingIndicator() {
  document.getElementById("typing-container").classList.remove("visible");
}

// ============================================================
// Connection Status
// ============================================================
function setConnectionStatus(status) {
  const dot = document.getElementById("status-dot");
  const text = document.getElementById("status-text");

  dot.className = `status-dot ${status}`;

  const labels = {
    connected: "Connected",
    connecting: "Connecting...",
    error: "Disconnected",
  };
  text.textContent = labels[status] || "Unknown";
}

// ============================================================
// UI Helpers
// ============================================================
function hideWelcomeScreen() {
  const ws = document.getElementById("welcome-screen");
  if (ws) ws.style.display = "none";
}

function enableInput() {
  const input = document.getElementById("message-input");
  const btn = document.getElementById("send-btn");
  input.disabled = false;
  btn.disabled = !input.value.trim();
  input.focus();
}

function disableInput() {
  document.getElementById("message-input").disabled = true;
  document.getElementById("send-btn").disabled = true;
}

function scrollToBottom() {
  const container = document.getElementById("messages-container");
  container.scrollTop = container.scrollHeight;
}

function getTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Basic markdown-like formatting for bot messages.
 * Converts **bold**, `code`, and bullet lists to HTML.
 */
function formatBotMessage(text) {
  let html = escapeHtml(text);
  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Code: `text`
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Line breaks
  html = html.replace(/\n/g, "<br>");
  return html;
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

// ============================================================
// Actions
// ============================================================
function startNewChat() {
  sessionStorage.removeItem("chatbot_session_id");
  sessionId = getOrCreateSessionId();

  // Clear messages
  const container = document.getElementById("messages-container");
  container.innerHTML = "";

  // Re-show welcome screen
  const welcomeHtml = `
    <div class="welcome-screen" id="welcome-screen">
      <div class="welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h2>How can I help you today?</h2>
      <p>Ask me anything — I'm here to help with your questions and issues.</p>
      <div class="suggestion-chips">
        <button class="chip" onclick="sendSuggestion('How do I reset my password?')" id="chip-1">🔑 Reset my password</button>
        <button class="chip" onclick="sendSuggestion('What are your business hours?')" id="chip-2">🕐 Business hours</button>
        <button class="chip" onclick="sendSuggestion('How do I track my order?')" id="chip-3">📦 Track my order</button>
        <button class="chip" onclick="sendSuggestion('I need to speak with a human agent')" id="chip-4">👤 Talk to a human</button>
      </div>
    </div>`;
  container.innerHTML = welcomeHtml;

  enableInput();
  isWaitingForResponse = false;
}

function clearChat() {
  startNewChat();
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
}

// ============================================================
// Event Listeners
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");

  // Enable send button only when there's text
  input.addEventListener("input", () => {
    sendBtn.disabled = !input.value.trim() || !isConnected || isWaitingForResponse;
    autoResize(input);
  });

  // Enter to send, Shift+Enter for new line
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Connect to WebSocket
  connect();
});

// Clean up on page unload
window.addEventListener("beforeunload", disconnect);
