import {create_new_chat,get_all_chats} from "../../api/client.js"


let chats =[];

const els = {
  url: document.getElementById("yt-url"),
  create: document.getElementById("create"),
  list: document.getElementById("list"),
  empty: document.getElementById("empty"),
};

function render() {
  els.list.innerHTML = "";
  if (!chats.length) {
    els.empty.classList.remove("hidden");
    return;
  }
  els.empty.classList.add("hidden");

  chats.forEach((c) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <div class="item-title">${c.title ?? "Untitled chat"}</div>
      <div class="item-url">${c.url}</div>
    `;
    // FIX: use `c`, not `chat`
    div.addEventListener("click", () => openChatPage(c));
    els.list.appendChild(div);
  });
}

els.create.addEventListener("click", async () => {
  const url = els.url.value.trim();
  if (!url) return;

  // loading state
  els.create.disabled = true;
  const originalText = els.create.textContent;
  els.create.textContent = "Creating…";

  try {
    // TODO: call your backend here. For now, simulate latency:
    const chat=await create_new_chat({url});
    chats.push(chat);
    els.url.value = "";
    render();
    openChatPage(chat);
  } catch (e) {
    console.error(e);
    alert("Failed to create chat.");
  } finally {
    els.create.disabled = false;
    els.create.textContent = originalText;
  }
});

// ---------- navigation to chat page ----------
function openChatPage(chat) {
  const params = new URLSearchParams({
    id: String(chat.id),        
    title: chat.title ?? "",
    url: chat.url ?? "",
  });

  // FIX: correct path & use chrome.runtime.getURL for extensions
  const chatUrl = chrome.runtime.getURL(
    "pages/chat/chat.html"
  ) + "?" + params.toString();

  window.location.href = chatUrl;
}

// Load chats from backend on boot
async function boot() {
  try {
    chats = await get_all_chats();
    render();
  } catch (e) {
    console.error(e);
    els.empty.textContent = "Failed to load chats.";
    els.empty.classList.remove("hidden");
  }
}
// boot
boot();
