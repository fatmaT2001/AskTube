from fastapi import APIRouter,Request,BackgroundTasks
from .routes_scheme.chats_scheme import CreateNewChatRequest, SendMessageRequest, RoleMessage
from ..models.db_scheme import chat_scheme, video_scheme,message_scheme
from  ..controllers import NLPController,VideoController,AgMPentController
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



async def process_video_task(fastapi_request:Request,video_id:str,youtube_video_id:str,video_title:str,is_transcript_availabe:bool=False,youtube_transcript:str=None):
    """
    background task to process the video
    1. preprocess the transcript if available
    2. generate video summary
    3. create embeddings and save to vector db
    4. create video entry in the database
    """
    db_client = fastapi_request.app.state.db_client
    db_vector:VectorDBInterface= fastapi_request.app.state.vector_db 
    video_model=VideoModel(db_client)
    nlp_controller = NLPController()
    generation_tool:GenerationInterface= fastapi_request.app.state.generation_model

    if is_transcript_availabe and youtube_transcript:
        # step1: preprocess the transcript to generate chunks using chunk duration from settings
        try:
            processed_transcript=nlp_controller.prepare_youtube_transcript_for_embedding(transcript=youtube_transcript,chunk_duration=int(get_settings().CHUNK_DURATION * 60))
            print(f"Processed transcript into {len(processed_transcript)} chunks for embedding.")
        except Exception as e:
            print(f"Error preprocessing transcript: {e}")
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            return 

        # step2: generate video summary using the generation model
        try:
            if processed_transcript:
                chunks=[chunk["text"] for chunk in processed_transcript]
                print(f"number of chunks {len(chunks)}")
                video_summary= await generation_tool.generate_video_summary(chunks=chunks,video_title=video_title)
                print(f"Generated video summary.{video_summary}")
            else:
                video_summary="No transcript available to generate summary."
        except Exception as e:
            print(f"Error generating video summary: {e}")
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            return 
        
        try:
            await video_model.add_video_summary(video_id=video_id,summary=video_summary)
            print(f"Video summary updated in database for video ID: {video_id}")
        except Exception as e:
            print(f"Error updating video summary in database: {e}")
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            return

        # step3: create embeddings and save to vector db
        try:
            if processed_transcript:
                await db_vector.index(embedding_ready_data=processed_transcript,video_id=video_id)
                print(f"Transcript chunks embedded and saved to vector database for video ID: {video_id}")
        except Exception as e:
            print(f"Error saving embeddings to vector database: {e}")
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            return
        
        # step4: update video status to completed
        try:
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.READY.value)
            print(f"Video processing completed for video ID: {video_id}")

        except Exception as e:
            print(f"Error updating video status to completed: {e}")
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            return
        
    else:
        print("No transcript available; skipping processing steps.")
        await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
        return
    
    return
    



@router.post("/add_new_video")
async def add_new_video(request:Request,new_chat: CreateNewChatRequest,background_tasks: BackgroundTasks):
    """
    create a new chat based on youtube link
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    video_controller = VideoController()
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
    
    try:
        # create video object        
        video_obj = video_scheme(youtube_title=video_title,youtube_url=new_chat.youtube_link,youtube_id=video_id,vector_status=VideoStatusEnum.PROCESSING.value,is_transcript_available=int(is_transcript_availabe))
        video_created_data=await video_model.add_Video(video_data=video_obj)
        print(f"Video saved to database with ID: {video_created_data}")
    except Exception as e:
        return {"error": f"Error saving video to database: {e}"}

    # process the video in the background
    try:
        background_tasks.add_task(process_video_task,fastapi_request=request,video_id=video_created_data.id,youtube_video_id=video_id,is_transcript_availabe=is_transcript_availabe,youtube_transcript=transcript,video_title=video_title)
        print(f"Background task started for video ID: {video_created_data.id}")
    except Exception as e:
        return {"error": f"Error starting background task: {e}"}
    
    
    return JSONResponse(content={
        "video_id": video_created_data.id,
        "video_title": video_title,
        "transcript_language_exist": is_transcript_availabe
    })




@router.get("/check_video_status/{video_id}")
async def check_video_status(request:Request,video_id:str):
    """
    check the video processing status
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    chat_model=ChatModel(db_client)
    try:
        video_data=await video_model.get_video_by_id(video_id=int(video_id))
        if not video_data:
            return JSONResponse(content={"error": "Video not found"},status_code=404)
        video_status=video_data.vector_status

        if video_status==VideoStatusEnum.READY.value:
            # create a new chat entry in the database linked to the video
            try:
                chat_name=f"{video_data.youtube_title}:{datetime.now().strftime('%Y-%m-%d')}"
                chat_obj=chat_scheme(title=chat_name,video_id=video_data.id)
                chat_created_data=await chat_model.create_chat(chat_data=chat_obj)
                print(f"Chat saved to database with ID: {chat_created_data}")
                video_id=video_data.youtube_id
                return JSONResponse(content={"video_id":video_id,"chat_id":chat_created_data.id,"status":video_status,"video_summary":video_data.video_summary})
            except Exception as e:
                return {"error": f"Error saving chat to database: {e}"}
        else:
            return JSONResponse(content={"video_id":video_id,"status":video_status})
    except Exception as e:
        return {"error": f"Error getting video from database: {e}"}


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
    vector_db:VectorDBInterface= request.app.state.vector_db 
    generation:GenerationInterface= request.app.state.generation_model
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
        # get chat history
        history_messages=await message_model.get_chat_history(chat_id=chat_id)
        history=[{"role":msg.role,"content":msg.content} for msg in history_messages[-10:]] 
        agent_controller= AgMPentController(vector_db=vector_db,generation=generation,video_id="H6pWY2VQ9xI")
        assistant_response= await agent_controller.get_model_answer(user_query=message_request.message,history=[])
        print(f"Assistant response: {assistant_response}")
    except Exception as e:
        return {"error": f"Error getting chat history from database: {e}"}

    try:
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