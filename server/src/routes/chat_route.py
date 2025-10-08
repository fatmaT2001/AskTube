from fastapi import APIRouter,Request
from .routes_scheme import CreateNewChatRequest, SendMessageRequest, RoleMessage
from ..models.db_scheme import message_scheme,chat_scheme
from  ..controllers import AgMPentController
from ..models.enums.video_enum import VideoStatusEnum
from ..models.db_models import VideoModel,ChatModel,MessageModel
from fastapi.responses import JSONResponse
from ..stores import VectorDBInterface
from ..stores import GenerationInterface

router = APIRouter(tags=["chats"])


@router.get("/chats")
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
        chats_list=[{"chat_id":chat.id,"chat_title":chat.title,"created_at":str(chat.created_at)} for chat in chats]
        return JSONResponse(content={"chats":chats_list})
    except Exception as e:
        return {"error": f"Error getting chats from database: {e}"}
    


@router.post("/chats")
async def create_new_chat(request:Request,chat_request:CreateNewChatRequest):
    """
    create a new chat for a video
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    video_model=VideoModel(db_client)
    try:
        video_data=await video_model.get_video_by_id(video_id=chat_request.video_id)
        if not video_data or video_data.vector_status != VideoStatusEnum.READY.value:
            return JSONResponse(content={"error": "Associated video is not ready for chat"},status_code=400)
    except Exception as e:
        return {"error": f"Error getting associated video from database: {e}"}
    
    try:
        chat_title=f"Chat for {video_data.youtube_title} at {video_data.created_at.strftime('%Y-%m-%d %H:%M')}"
        chat_obj=chat_scheme(video_id=chat_request.video_id,title=chat_title)
        chat_created_data=await chat_model.create_chat(chat_data=chat_obj)
        print(f"Created new chat with ID: {chat_created_data.id} for video ID: {chat_request.video_id} and title: {chat_obj.title}")
        return JSONResponse(content={"chat_id":chat_created_data.id,"chat_title":chat_obj.title})
    except Exception as e:
        return {"error": f"Error creating new chat in database: {e}"}


@router.get("/chats/{chat_id}")
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
    





@router.post("/chats/{chat_id}/messages")
async def send_message_to_chat(request:Request,chat_id:int,message_request:SendMessageRequest):
    """
    send message to chat and get the response
    """
    db_client = request.app.state.db_client
    chat_model=ChatModel(db_client)
    video_model=VideoModel(db_client)
    message_model=MessageModel(db_client)
    vector_db:VectorDBInterface= request.app.state.vector_db 
    generation:GenerationInterface= request.app.state.generation_model
    try:
        chat_data=await chat_model.get_chat_by_id(chat_id=chat_id)
        if not chat_data:
            return JSONResponse(content={"error": "Chat not found"},status_code=404)
    except Exception as e:
        return {"error": f"Error getting chat from database: {e}"}
    
    # get video info from chat
    try:
        video_data=await video_model.get_video_by_id(video_id=chat_data.video_id)
        if not video_data or video_data.vector_status != VideoStatusEnum.READY.value:
            return JSONResponse(content={"error": "Associated video is not ready for chat"},status_code=400)
    except Exception as e:  
        return {"error": f"Error getting associated video from database: {e}"}
    

    try:
        message_obj=message_scheme(chat_id=chat_id,role=RoleMessage.USER.value,content=message_request.message)
        message_created_data=await message_model.add_message(message_data=message_obj,chat_id=chat_id)
    except Exception as e:
        return {"error": f"Error saving message to database: {e}"}
    
    try:
        # get chat history
        history_messages=await message_model.get_chat_history(chat_id=chat_id)
        history=[{"role":msg.role,"content":msg.content} for msg in history_messages[-10:]] 
        agent_controller= AgMPentController(vector_db=vector_db,generation=generation,video_id=video_data.id)
        assistant_response= await agent_controller.get_model_answer(user_query=message_request.message,history=history,summary=video_data.video_summary )
    except Exception as e:
        return {"error": f"Error getting chat history from database: {e}"}

    try:
        # Extract content from ChatCompletionMessage if needed
        assistant_content = assistant_response.content if hasattr(assistant_response, 'content') else str(assistant_response)
        assistant_message_obj=message_scheme(chat_id=chat_id,role=RoleMessage.ASSISTANT.value,content=assistant_content)
        assistant_message_created_data=await message_model.add_message(message_data=assistant_message_obj,chat_id=chat_id)
    except Exception as e:
        return {"error": f"Error saving assistant message to database: {e}"}


    return JSONResponse(content={"message": assistant_content})




@router.get("/chats/{chat_id}/history")
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
        return JSONResponse(content={"chat_id":chat_id,"chat_title":chat_data.title,"messages":messages_list})
    except Exception as e:
        return {"error": f"Error getting messages from database: {e}"}



@router.delete("/chats/{chat_id}")
async def delete_chat_by_id(request:Request,chat_id:int):
    """
    delete chat by id
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
    # delete all messages associated with the chat
    try:
        await message_model.delete_messages_by_chat_id(chat_id=chat_id)
    except Exception as e:
        return {"error": f"Error deleting messages from database: {e}"}
    # delete the chat
    try:    
    
        await chat_model.delete_chat(chat_id=chat_id)
        return JSONResponse(content={"message": "Chat deleted successfully"})
    except Exception as e:
        return {"error": f"Error deleting chat from database: {e}"}



