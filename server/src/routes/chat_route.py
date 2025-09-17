from fastapi import APIRouter,Request
from .routes_scheme.chats_scheme import CreateNewChatRequest, SendMessageRequest, RoleMessage
from ..models.db_scheme import chat_scheme, video_scheme,message_scheme
from  ..controllers import NLPController,VideoController
from ..models.enums.video_enum import VideoStatusEnum
from ..models.db_models import VideoModel,ChatModel,MessageModel
from fastapi.responses import JSONResponse
from datetime import datetime
from ..utils.settings import get_settings
from ..stores import VectorDBInterface
from ..stores import GenerationInterface
from ..stores.generation.providers.litellm import LiteLLMProvider

router = APIRouter(prefix="/chat", tags=["chat"])

"""
To Do Routes
1) create new chat 
2) send message to chat and get the response 
3) get all chats
3) get chat by id
4) delete chat by id
"""


@router.post("/create_new_chat")
async def create_new_chat(request:Request,new_chat: CreateNewChatRequest):
    """
    create a new chat based on youtube link
    1. check if the youtube link is valid and get the video id and title, and transcript availability
    2. check if the video is already in the database and the status is completed
    3. if not, create a new video entry in the database with status processing
    4. create a new chat entry in the database linked to the video
    5. return the chat id and title
    """


    db_client = request.app.state.db_client
    db_vector:VectorDBInterface= request.app.state.vector_db 
    video_model=VideoModel(db_client)
    chat_model=ChatModel(db_client)
    video_controller = VideoController()
    nlp_controller = NLPController()

    ## to do: check if it in the database and the status is completed


    try:
        # first get the video id and title from the youtube link
        video_details=video_controller.get_video_info(new_chat.youtube_link)
        if not video_details:
            return {"error": "Invalid YouTube link or unable to fetch video details"}
        
        video_id,video_title,is_transcript_availabe,transcript=video_details["video_id"],video_details["title"],video_details["transcript_available"],video_details["transcript"]
        if not is_transcript_availabe:
            print(f"No transcript available in the preferred languages {new_chat.required_language}")
     
    except Exception as e:
        return {"error": f"Error processing YouTube link: {e}"}
    
    # preprocessing the transcript if available
    try:
        if is_transcript_availabe and transcript:
            processed_transcript=nlp_controller.prepare_youtube_transcript_for_embedding(transcript=transcript,chunk_duration=int(get_settings().CHUNK_DURATION * 60))
            print(f"Processed transcript into {len(processed_transcript)} chunks for embedding.")
    except Exception as e:
        return {"error": f"Error preprocessing transcript: {e}"}

    try:
        if is_transcript_availabe and transcript:
            # create embeddings and save to vector db
            await db_vector.index(embedding_ready_data=processed_transcript,video_id=video_id)
            print(f"Transcript chunks embedded and saved to vector database for video ID: {video_id}")
    except Exception as e:
        return {"error": f"Error saving embeddings to vector database: {e}"}    

    try:
        # create video object
        
        video_obj = video_scheme(youtube_title=video_title,youtube_url=new_chat.youtube_link,youtube_id=video_id,vector_database_status=VideoStatusEnum.PROCESSING.value,is_transcript_available=int(is_transcript_availabe))
        video_created_data=await video_model.add_Video(video_data=video_obj)
        print(f"Video saved to database with ID: {video_created_data}")
    except Exception as e:
        return {"error": f"Error saving video to database: {e}"}

    try:
        chat_name=f"{video_title}:{datetime.now().strftime('%Y-%m-%d')}"
        chat_obj=chat_scheme(title=chat_name,video_id=video_created_data.id)
        chat_created_data=await chat_model.create_chat(chat_data=chat_obj)
        print(f"Chat saved to database with ID: {chat_created_data}")

    except Exception as e:
        return {"error": f"Error saving chat to database: {e}"}
    
    return JSONResponse(content={
        "video_id": video_id,
        "video_title": video_title,
        "transcript_language_exist": is_transcript_availabe,
        "chat_id": chat_created_data.id,
        "chat_title": chat_created_data.title
    })


@router.get("/get_all_chats")
async def get_all_chats(request:Request):
    """
    get all chats
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    print("Fetching all chats from the database...")
    try:
        chats=await chat_model.get_all_chats()
        print(f"Retrieved {len(chats)} chats from the database.")
        chats_list=[{"chat_id":chat.id,"chat_title":chat.title} for chat in chats]
        return JSONResponse(content={"chats":chats_list})
    except Exception as e:
        return {"error": f"Error getting chats from database: {e}"}
    


@router.get("/get_chat_by_id/{chat_id}")
async def get_chat_by_id(request:Request,chat_id:int):
    """
    get chat by id
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client=db_client)
    try:
        chat=await chat_model.get_chat_by_id(chat_id=chat_id)
        if not chat:
            return JSONResponse(content={"error": "Chat not found"},status_code=404)
        chat_data={"chat_id":chat.id,"chat_title":chat.title}
        return JSONResponse(content={"chat":chat_data})
    except Exception as e:
        return {"error": f"Error getting chat from database: {e}"}
    


@router.post("/send_message_to_chat/{chat_id}")
async def send_message_to_chat(request:Request,chat_id:int,message_request:SendMessageRequest):
    """
    send message to chat and get the response
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    message_model=MessageModel(db_client)
    try:
        chat_data=await chat_model.get_chat_by_id(chat_id=chat_id)
        if not chat_data:
            return JSONResponse(content={"error": "Chat not found"},status_code=404)
    except Exception as e:
        return {"error": f"Error getting chat from database: {e}"}
    
    try:
        message_obj=message_scheme(chat_id=chat_id,role=RoleMessage.USER.value,content=message_request.message)
        message_created_data=await message_model.add_message(message_data=message_obj,chat_id=chat_id)
        print(f"Message saved to database with ID: {message_created_data}")
    except Exception as e:
        return {"error": f"Error saving message to database: {e}"}
    
    try:
        assistant_response="This is a placeholder response from the assistant."
        assistant_message_obj=message_scheme(chat_id=chat_id,role=RoleMessage.ASSISTANT.value,content=assistant_response)
        assistant_message_created_data=await message_model.add_message(message_data=assistant_message_obj,chat_id=chat_id)
        print(f"Assistant Message saved to database with ID: {assistant_message_created_data}")
    except Exception as e:
        return {"error": f"Error saving assistant message to database: {e}"}


    return JSONResponse(content={"message": assistant_response})




@router.get("/get_chat_history/{chat_id}")
async def get_chat_history(request:Request,chat_id:int):
    """
    get chat history by chat id
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    message_model=MessageModel(db_client)
    try:
        chat_data=await chat_model.get_chat_by_id(chat_id=chat_id)
        print(chat_data.messages)
        if not chat_data:
            return JSONResponse(content={"error": "Chat not found"},status_code=404)
    except Exception as e:
        return {"error": f"Error getting chat from database: {e}"}
    
    try:
        messages=await message_model.get_chat_history(chat_id=chat_id)
        messages_list=[{"message_id":message.id,"role":message.role,"content":message.content,"created_at":str(message.created_at)} for message in messages]
        return JSONResponse(content={"chat_id":chat_id,"messages":messages_list})
    except Exception as e:
        return {"error": f"Error getting messages from database: {e}"}



@router.delete("/delete_chat_by_id/{chat_id}")
async def delete_chat_by_id(request:Request,chat_id:int):
    """
    delete chat by id
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    try:
        chat_data=await chat_model.get_chat_by_id(chat_id=chat_id)
        if not chat_data:
            return JSONResponse(content={"error": "Chat not found"},status_code=404)
        await chat_model.delete_chat(chat_id=chat_id)
        return JSONResponse(content={"message": "Chat deleted successfully"})
    except Exception as e:
        return {"error": f"Error deleting chat from database: {e}"}





@router.get("/search")
async def search_result(request:Request,query:str,video_id:str):
    """
    get search result from vector db

    """
    db_vector:VectorDBInterface= request.app.state.vector_db 
    try:

        search_results=await db_vector.search(user_query=query,video_id=video_id,top_k=5)
        print(f"Search results: {search_results}")
        return JSONResponse(content={"results":search_results})
    except Exception as e:
        return {"error": f"Error getting search results from vector database: {e}"}






@router.get("/get_answer")
async def search_result(query:str):
    """
    get search result from vector db

    """
    lite_llm= LiteLLMProvider()
    lite_llm.connect()

    try:
        massges=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
        ]
        response= await lite_llm.generate_answer(message=massges)
        return JSONResponse(content={"response":response})
    except Exception as e:
        return {"error": f"Error getting response from LLM: {e}"}