import {send_message_to_chat, get_chat_messages, check_video_status, create_new_chat, get_all_videos} from "../../api/client.js";

// ---- read params ----
const p = new URLSearchParams(location.search);
console.log(p);

// Parameters can be either:
// 1. videoId (for creating new chat from video)
// 2. chatId (for opening existing chat)
const paramVideoId = p.get("videoId");
const paramChatId = p.get("chatId");

// ---- DOM ----
const backBtn = document.getElementById("back-btn");
const titleEl = document.getElementById("chat-title");
const subEl = document.getElementById("chat-sub");
const wrap = document.getElementById("chat-wrap");
const content = document.getElementById("chat-content");
const input = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");
const statusEl = document.getElementById("video-status");

// ---- state ----
let messages = [];
let videoReady = false;
let chatId = null;
let videoId = null;
let chatTitle = "Chat";
let videoUrl = "";

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
    const status_data = await check_video_status({ videoId });
    console.log("Video status:", status_data);
    statusEl.textContent = `Video Status: ${status_data.status}`;
    if (status_data.status === "READY") {
      videoReady = true;
      input.disabled = false;
      sendBtn.disabled = false;
      statusEl.style.color = "var(--ok)";
    } else if (status_data.status === "FAILED") {
      statusEl.textContent = "Video processing failed. Please try again.";
      statusEl.style.color = "var(--err)";
      input.disabled = true;
      sendBtn.disabled = true;
    } else {
      statusEl.style.color = "var(--warn)";
      setTimeout(checkVideoStatus, 5000); // Poll every 5 seconds
    }
  } catch (e) {
    console.error("Failed to fetch video status:", e);
    statusEl.textContent = "Error fetching video status.";
    statusEl.style.color = "var(--err)";
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

// ---- initialization functions ----
async function initializeFromVideo(videoId) {
  try {
    // Create new chat for this video
    const newChat = await create_new_chat({ videoId });
    
    // Set global state
    chatId = newChat.id;
    chatTitle = newChat.title;
    
    // Update UI
    titleEl.textContent = chatTitle;
    subEl.textContent = `Video ID: ${videoId}`; // We can show video ID or get video details separately if needed
    
    return { videoId, chat: newChat };
  } catch (e) {
    console.error("Failed to initialize from video:", e);
    content.innerHTML = `<div class="error">Failed to create chat: ${e.message}</div>`;
    throw e;
  }
}

async function initializeFromChat(chatId) {
  try {
    // Get chat messages first to validate chat exists
    const chatMessages = await get_chat_messages(chatId);
    
    // For now, we'll use the chat ID as title since backend doesn't provide chat details with video association
    chatTitle = `Chat ${chatId}`;
    
    // Update UI
    titleEl.textContent = chatTitle;
    subEl.textContent = `Chat ID: ${chatId}`;
    
    return { messages: chatMessages };
  } catch (e) {
    console.error("Failed to initialize from chat:", e);
    content.innerHTML = `<div class="error">Failed to load chat: ${e.message}</div>`;
    throw e;
  }
}

async function boot() {
  content.innerHTML = `<div class="loading">Initializing chat…</div>`;
  
  try {
    if (paramVideoId) {
      // Scenario 1: Creating new chat from video
      const { videoId: vId } = await initializeFromVideo(paramVideoId);
      videoId = vId;
      messages = []; // New chat, no messages yet
      
    } else if (paramChatId) {
      // Scenario 2: Opening existing chat
      chatId = paramChatId;
      const { messages: chatMessages } = await initializeFromChat(paramChatId);
      messages = chatMessages || [];
      
    } else {
      throw new Error("No chat ID or video ID provided");
    }
    
    // Render messages
    render();
    
    // Check video status if we have a video
    if (videoId) {
      checkVideoStatus();
    } else {
      // If no video, enable chat immediately
      videoReady = true;
      input.disabled = false;
      sendBtn.disabled = false;
      statusEl.textContent = "Ready";
      statusEl.style.color = "var(--ok)";
    }
    
  } catch (e) {
    console.error("Failed to initialize chat:", e);
    content.innerHTML = `<div class="error">Failed to initialize chat: ${e.message}</div>`;
  }
}

// ---- boot ----
boot();
