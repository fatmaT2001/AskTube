import {send_message_to_chat, get_chat_messages, get_video_status} from "../../api/client.js";

// ---- read params (title, url, id, videoId) ----
const p = new URLSearchParams(location.search);
const chatTitle = p.get("title") || "Chat";
const chatUrl = p.get("url") || "";
const chatId = p.get("id") || null;
const videoId = p.get("videoId") || null;

// ---- DOM ----
const backBtn = document.getElementById("back-btn");
const titleEl = document.getElementById("chat-title");
const subEl = document.getElementById("chat-sub");
const wrap = document.getElementById("chat-wrap");
const content = document.getElementById("chat-content");
const input = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");
const statusEl = document.getElementById("video-status"); // New status element

// ---- init header ----
titleEl.textContent = chatTitle;
subEl.textContent = chatUrl;

// ---- state ----
let messages = [];
let videoReady = false;

// ---- helpers ----
function scrollToBottom() {
  requestAnimationFrame(() => {
    wrap.scrollTop = wrap.scrollHeight;
  });
}

function bubble({ role, content: text, ts }) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  if (ts) {
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    div.appendChild(meta);
  }
  return div;
}

function typingBubble() {
  const div = document.createElement("div");
  div.className = "msg assistant";
  const t = document.createElement("div");
  t.className = "typing";
  t.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
  div.appendChild(t);
  return div;
}

function render() {
  content.innerHTML = "";
  messages.forEach((m) => content.appendChild(bubble(m)));
  scrollToBottom();
}

async function checkVideoStatus() {
  if (!videoId) return;
  try {
    const status_data = await get_video_status(videoId);
    console.log("Video status:", status_data);
    statusEl.textContent = `Video Status: ${status_data.status}`;
    if (status_data.status === "READY") {
      videoReady = true;
      input.disabled = false;
      sendBtn.disabled = false;
    } else if (status_data.status === "FAILED") {
      statusEl.textContent = "Video processing failed. Please try again.";
      input.disabled = true;
      sendBtn.disabled = true;
    } else {
      setTimeout(checkVideoStatus, 5000); // Poll every 5 seconds
    }
  } catch (e) {
    console.error("Failed to fetch video status:", e);
    statusEl.textContent = "Error fetching video status.";
  }
}

// ---- send flow ----
async function sendMessage() {
  if (!videoReady) return;

  const text = input.value.trim();
  if (!text) return;

  // optimistic user bubble
  const userMsg = { role: "user", content: text, ts: Date.now() };
  messages.push(userMsg);
  render();

  // prepare UI
  input.value = "";
  sendBtn.disabled = true;

  // typing indicator
  const typing = typingBubble();
  content.appendChild(typing);
  scrollToBottom();

  try {
    const response = await send_message_to_chat(chatId, text);

    // fake assistant reply
    messages.push({
      role: "assistant",
      content: response.response,
      ts: Date.now(),
    });
  } finally {
    typing.remove();
    render();
    sendBtn.disabled = false;
    input.focus();
  }
}

// ---- events ----
sendBtn.addEventListener("click", sendMessage);

// Enter to send, Shift+Enter for newline
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// back to sidepanel
backBtn.addEventListener("click", () => {
  const panelUrl = chrome.runtime.getURL("pages/sidepanel/index.html");
  window.location.href = panelUrl;
});

async function boot() {
  if (!chatId) return;
  content.innerHTML = `<div class="loading">Loading messages…</div>`;
  try {
    messages = await get_chat_messages(chatId);
    render();
  } catch (e) {
    content.innerHTML = `<div class="error">Failed to load messages.</div>`;
    console.error("Failed to load messages:", e);
  }

  // Check video status
  checkVideoStatus();
}

// ---- boot ----
boot();
