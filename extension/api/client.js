const backend_url = 'http://127.0.0.1:8000/chat'; 


export async function create_new_chat({ url }) {
  const response = await fetch(`${backend_url}/create_new_chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'

    },
    body: JSON.stringify({
      youtube_link: url,
    })
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  const chat = await response.json();
  console.log("Created chat:", chat);
  return {
    "id": chat.chat_id,
    "title": chat.chat_title
    
  }
}


export async function get_all_chats() {
const response = await fetch(`${backend_url}/get_all_chats`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'

    },
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  const data = await response.json();
  console.log("Created chat:", data);
    return (data.chats || []).map(chat => ({
    id: chat.chat_id,
    title: chat.chat_title
  }));

}


export async function send_message_to_chat(chatId, message) {
  const response = await fetch(`${backend_url}/send_message_to_chat/${chatId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'

    },
    body: JSON.stringify({
      message: message,
    })
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  const agent_response = await response.json();
  console.log("Created chat:", agent_response);
  return {
    "response": agent_response.message,
    
  }
}


export async function get_chat_messages(chatId) {
  const response = await fetch(`${backend_url}/get_chat_history/${chatId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'

    },
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  const data = await response.json();
  console.log("Created chat:", data);
    return (data.messages || []).map(msg => ({
    role: msg.role,
    content: msg.content,
    ts: msg.created_at
  }));

}