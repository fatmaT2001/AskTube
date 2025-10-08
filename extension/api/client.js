const backend_url = 'http://127.0.0.1:8000'; 



//=====================================================================================
//========================================Video APIs===================================
export async function add_new_video(url) {
  console.log("Adding new video with URL:", url);
  const response = await fetch(`${backend_url}/videos`, {
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

  const video_created_data = await response.json();
  console.log("Created video:", video_created_data);
  return {
    "id": video_created_data.video_id,
    "title": video_created_data.video_title,
    
  }
}



export async function check_video_status({ videoId }) {
  const response = await fetch(`${backend_url}/videos/${videoId}/status`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'

    },
  });

  if (!response.ok) {
    throw new Error('Failed to create chat');
  }

  const video_created_status = await response.json();
  console.log("Created video:", video_created_status);
  return {
    "video_id":video_created_status.video_id,
    "status":video_created_status.status

  }
}

export async function get_all_videos() {
const response = await fetch(`${backend_url}/videos`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch videos');
  }
  const data = await response.json();
  console.log("Fetched videos:", data);
    return (data.videos || []).map(video => ({
    id: video.video_id,
    title: video.video_title,
    url: video.video_url,
    status: video.video_status,
    is_transcript_available: video.is_transcript_available,
    created_at: video.created_at
  }));
}


export async function delete_video(videoId) {
  const response = await fetch(`${backend_url}/videos/${videoId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete video');
  }
  const data = await response.json();
  console.log("Deleted video:", data);
  return data;
}

//=====================================================================================
//========================================Chat APIs====================================
export async function create_new_chat({ videoId }) {
  const response = await fetch(`${backend_url}/chats`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'

    },
    body: JSON.stringify({
      "video_id": videoId,
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
const response = await fetch(`${backend_url}/chats`, {
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
    title: chat.chat_title,
    created_at: chat.created_at
  }));

}


export async function send_message_to_chat(chatId, message) {
  
  const response = await fetch(`${backend_url}/chats/${chatId}/messages`, {
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
  const response = await fetch(`${backend_url}/chats/${chatId}/history`, {
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
  const chat_data={
    "id":data.chat_id,
    "title":data.chat_title,
    "messages":data.messages.map(msg=>({
      "role":msg.role,
      "content":msg.content,
      "ts":msg.created_at
    }))
  }
  return chat_data



}


export async function delete_chat(chatId) {
  const response = await fetch(`${backend_url}/chats/${chatId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete chat');
  }
  const data = await response.json();
  console.log("Deleted chat:", data);
  return data;
}

//=====================================================================================