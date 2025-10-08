// keep your original client.js function names
import { get_all_videos, add_new_video, check_video_status, get_all_chats,delete_chat,delete_video } from "../../api/client.js";

const $ = (s) => document.querySelector(s);
const ui = {
  url: $("#yt-url"),
  add: $("#add-video"),
  list: $("#video-list"),
  empty: $("#empty-videos"),
  alerts: $("#alerts"),
  chatList: $("#chat-list"),
  emptyChats: $("#empty-chats"),
  tabs: document.querySelectorAll(".tab"),
  pages: document.querySelectorAll(".tab-page"),
};

let videos = [];
let chats = [];

function showAlert(msg, type = "info") {
  const alertClass = type === "error" ? "err" : type === "success" ? "success" : "info";
  ui.alerts.innerHTML = `<div class="alert ${alertClass}">${msg}</div>`;
  setTimeout(() => (ui.alerts.innerHTML = ""), 4000); // Show longer for processing updates
}

function statusPill(status) {
  const s = (status || "").toLowerCase();
  const cls =
    s === "ready" ? "ok" :
    s === "processing" ? "wait" :
    s === "received" ? "wait" :
    s === "failed" ? "err" : "";

  // Add spinning icon for processing status
  const icon = (s === "processing" || s === "received") ? "⏳" : "";
  const displayText = status ? status.toUpperCase() : "UNKNOWN";

  return `<span class="pill ${cls} ${(s === "processing" || s === "received") ? "processing" : ""}">${icon} ${displayText}</span>`;
}

function render() {
  ui.list.innerHTML = "";
  if (!videos.length) {
    ui.list.innerHTML = `<p id="empty-videos" class="empty">No videos yet. Add one to start!</p>`;
    return;
  }

  videos.forEach(v => {
    const card = document.createElement("div");
    card.className = "video-card";
    
    // Only show chat icon if video is ready
    const showChatIcon = v.status && v.status.toLowerCase() === "ready";
    const chatIconHtml = showChatIcon 
      ? `<button class="chat-icon" data-open="${v.id}" title="Open Chat">💬</button>`
      : '';
    
    card.innerHTML = `
      <div class="meta">
        <h3>${v.title || "Untitled"}</h3>
        <a href="${v.url}" target="_blank" rel="noreferrer">${v.url}</a>
        <div class="row">
          ${statusPill(v.status)}
          <div class="card-actions">
            ${chatIconHtml}
            <button class="delete-icon" data-delete-video="${v.id}" title="Delete Video">🗑️</button>
          </div>
        </div>
      </div>
    `;
    ui.list.appendChild(card);
  });
}

function renderChats() {
  ui.chatList.innerHTML = "";
  if (!chats.length) {
    ui.chatList.innerHTML = `<p id="empty-chats" class="empty">No chats yet. Create a video first!</p>`;
    return;
  }

  chats.forEach(chat => {
    const card = document.createElement("div");
    card.className = "video-card"; // Reuse video card styling
    card.innerHTML = `
      <div class="meta">
        <h3>${chat.title || "Untitled Chat"}</h3>
        <div class="row">
          <span class="created-at">${chat.created_at}</span>
          <div class="card-actions">
            <button class="chat-icon" data-chat-id="${chat.id}" title="Open Chat">💬</button>
            <button class="delete-icon" data-delete-chat="${chat.id}" title="Delete Chat">🗑️</button>
          </div>
        </div>
      </div>
    `;
    ui.chatList.appendChild(card);
  });
}

async function boot() {
  try {
    ui.empty && (ui.empty.textContent = "Loading…");
    
    // Load both videos and chats
    const [videosData, chatsData] = await Promise.all([
      get_all_videos(),
      get_all_chats()
    ]);
    
    videos = videosData;
    chats = chatsData;
    
    render();
    renderChats();
  } catch (err) {
    console.error(err);
    ui.list.innerHTML = `<p id="empty-videos" class="empty">Failed to load videos.</p>`;
    showAlert("Could not load data", "error");
  }
}

// Store active polling intervals
let pollingIntervals = new Map();

async function onAdd() {
  const url = ui.url.value.trim();
  if (!url) return;
  ui.add.disabled = true;
  console.log("Adding video:", url);
  
  // Show loading state
  const originalText = ui.add.textContent;
  ui.add.textContent = "Processing...";
  
  try {
    const created = await add_new_video(url);  
    
    // Map the API response to match our expected structure
    const newVideo = {
      id: created.id,
      title: created.title || "Untitled",
      url: url,
      status: "received"
    };
    
    videos.unshift(newVideo);
    ui.url.value = "";
    render();
    showAlert("Video added - processing...", "info");
    
    // Start polling for status updates
    startStatusPolling(created.id);
  } catch (err) {
    console.error(err);
    showAlert("Failed to add video", "error");
  } finally {
    ui.add.disabled = false;
    ui.add.textContent = originalText;
  }
}

async function startStatusPolling(videoId) {
  // Clear any existing polling for this video
  if (pollingIntervals.has(videoId)) {
    clearInterval(pollingIntervals.get(videoId));
  }
  
  const pollInterval = setInterval(async () => {
    try {
      const statusResponse = await check_video_status({ videoId });
      
      // Find and update the video in our array
      const videoIndex = videos.findIndex(v => v.id === videoId);
      if (videoIndex !== -1) {
        videos[videoIndex].status = statusResponse.status;
        render(); // Re-render to show updated status
        
        // If video is ready or failed, stop polling
        if (statusResponse.status === "ready" || statusResponse.status === "failed") {
          clearInterval(pollInterval);
          pollingIntervals.delete(videoId);

          if (statusResponse.status === "ready") {
            showAlert("Video processing complete!", "success");
          } else {
            showAlert("Video processing failed", "error");
          }
        }
      }
    } catch (err) {
      console.error("Status polling error:", err);
      // Don't stop polling on single error, server might be temporarily unavailable
    }
  }, 10000); // Poll every 10 seconds
  
  pollingIntervals.set(videoId, pollInterval);
}

async function deleteVideo(videoId) {
  if (!confirm("Are you sure you want to delete this video? This action cannot be undone.")) {
    return;
  }
  
  console.log("Deleting video ID:", videoId, "Type:", typeof videoId);
  console.log("Videos before deletion:", videos.length);
  console.log("Video IDs in array:", videos.map(v => ({id: v.id, type: typeof v.id})));
  
  try {
    await delete_video(videoId);
    
    // Convert videoId to number to ensure type matching
    const numericVideoId = parseInt(videoId, 10);
    console.log("Converted video ID:", numericVideoId, "Type:", typeof numericVideoId);
    
    // Remove from local array using both string and numeric comparison
    const originalLength = videos.length;
    videos = videos.filter(v => v.id != videoId && v.id !== numericVideoId);
    console.log("Videos after deletion:", videos.length, "Removed:", originalLength - videos.length);
    
    // Clear any polling for this video (check both types)
    if (pollingIntervals.has(videoId)) {
      clearInterval(pollingIntervals.get(videoId));
      pollingIntervals.delete(videoId);
    }
    if (pollingIntervals.has(numericVideoId)) {
      clearInterval(pollingIntervals.get(numericVideoId));
      pollingIntervals.delete(numericVideoId);
    }
    
    // Force re-render
    render();
    console.log("Render called, list should be updated");
    showAlert("Video deleted successfully", "success");
  } catch (err) {
    console.error("Delete video error:", err);
    showAlert("Failed to delete video", "error");
  }
}

async function deleteChatHandler(chatId) {
  if (!confirm("Are you sure you want to delete this chat? This action cannot be undone.")) {
    return;
  }
  
  console.log("Deleting chat ID:", chatId, "Type:", typeof chatId);
  console.log("Chats before deletion:", chats.length);
  console.log("Chat IDs in array:", chats.map(c => ({id: c.id, type: typeof c.id})));
  
  try {
    await delete_chat(chatId);
    
    // Convert chatId to number to ensure type matching
    const numericChatId = parseInt(chatId, 10);
    console.log("Converted chat ID:", numericChatId, "Type:", typeof numericChatId);
    
    // Remove from local array using both string and numeric comparison
    const originalLength = chats.length;
    chats = chats.filter(c => c.id != chatId && c.id !== numericChatId);
    console.log("Chats after deletion:", chats.length, "Removed:", originalLength - chats.length);
    
    renderChats();
    console.log("renderChats called, chat list should be updated");
    showAlert("Chat deleted successfully", "success");
  } catch (err) {
    console.error("Delete chat error:", err);
    showAlert("Failed to delete chat", "error");
  }
}

document.addEventListener("click", (e) => {
  const videoId = e.target?.dataset?.open;
  const chatId = e.target?.dataset?.chatId;
  const deleteVideoId = e.target?.dataset?.deleteVideo;
  const deleteChatId = e.target?.dataset?.deleteChat;
  
  if (videoId) {
    // Create new chat for video
    const url = new URL("../chat/chat.html", location.href);
    url.searchParams.set("videoId", videoId);
    location.href = url.toString();
  } else if (chatId) {
    // Open existing chat
    const url = new URL("../chat/chat.html", location.href);
    url.searchParams.set("chatId", chatId);
    location.href = url.toString();
  } else if (deleteVideoId) {
    // Delete video
    deleteVideo(deleteVideoId);
  } else if (deleteChatId) {
    // Delete chat
    deleteChatHandler(deleteChatId);
  }
});

// Tab switching logic
ui.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // Remove active class from all tabs and pages
    ui.tabs.forEach((t) => t.classList.remove("active"));
    ui.pages.forEach((p) => p.classList.remove("active"));

    // Add active class to the clicked tab and corresponding page
    tab.classList.add("active");
    const targetPage = document.getElementById(tab.dataset.tab);
    targetPage.classList.add("active");
  });
});

ui.add.addEventListener("click", onAdd);
ui.url.addEventListener("keydown", (e) => {
  if (e.key === "Enter") onAdd();
});

boot();
