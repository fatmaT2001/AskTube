from fastapi import APIRouter,Request
from .routes_scheme.chats_scheme import CreateNewChatRequest
from ..models.db_scheme import chat, video
from  ..controllers import VideoController
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/chat", tags=["chat"])



@router.post("create_new_chat")
async def create_new_chat(request:Request,new_chat: CreateNewChatRequest):
    db_client = request.app.state.db_client
    video_controller = VideoController()
    ## to do: check if it in the database and the status is completed

    try:
        # first get the video id and title from the youtube link
        video_details=video_controller.get_video_info(new_chat.youtube_link)
        if not video_details:
            return {"error": "Invalid YouTube link or unable to fetch video details"}
        
        video_id,video_title,is_transcript_availabe,transcript=video_details["video_id"],video_details["title"],video_details["transcript_available"],video_details["transcript"]
        if not is_transcript_availabe:
            return {"error": f"No transcript available in the preferred languages {new_chat.required_language}"}
     
    except Exception as e:
        return {"error": f"Error processing YouTube link: {e}"}
    

    return JSONResponse(content={
        "video_id": video_id,
        "video_title": video_title,
        "transcript_language_exist": is_transcript_availabe,
    })