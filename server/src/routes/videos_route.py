from fastapi import APIRouter, Request, BackgroundTasks
from src.routes.routes_scheme import CreateNewVideoRequest
from src.models.db_scheme import video_scheme
from src.controllers import NLPController, VideoController
from src.models.enums.video_enum import VideoStatusEnum
from src.models.db_models import VideoModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from src.utils.settings import get_settings
from src.stores import VectorDBInterface
from src.stores import GenerationInterface


router = APIRouter(tags=["videos"])



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
    



@router.post("/videos")
async def add_new_video(request:Request,new_video: CreateNewVideoRequest,background_tasks: BackgroundTasks):
    """
    create a new chat based on youtube link
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    video_controller = VideoController()
    try:
        # first get the video id and title from the youtube link
        video_details=video_controller.get_video_info(new_video.youtube_link)
        if not video_details:
            return {"error": "Invalid YouTube link or unable to fetch video details"}
        
        video_id,video_title,is_transcript_availabe,transcript=video_details["video_id"],video_details["title"],video_details["transcript_available"],video_details["transcript"]
        if not is_transcript_availabe:
            print(f"No transcript available in the preferred languages {new_video.required_language}")
     
    except Exception as e:
        return {"error": f"Error processing YouTube link: {e}"}
    
    try:
        # create video object        
        video_obj = video_scheme(youtube_title=video_title,youtube_url=new_video.youtube_link,youtube_id=video_id,vector_status=VideoStatusEnum.PROCESSING.value,is_transcript_available=int(is_transcript_availabe))
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




@router.get("/videos/{video_id}/status")
async def check_video_status(request:Request,video_id:str):
    """
    check the video processing status
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    try:
        video_data=await video_model.get_video_by_id(video_id=int(video_id))
        if not video_data:
            return JSONResponse(content={"error": "Video not found"},status_code=404)
        video_status=video_data.vector_status
      
        return JSONResponse(content={"video_id":video_id,"status":video_status})
    except Exception as e:
        return {"error": f"Error getting video from database: {e}"}


@router.get("/videos")
async def get_all_videos(request:Request):
    """
    get all videos
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    try:
        videos=await video_model.get_all_user_videos()
        videos_list=[]
        for video in videos:
            video_data={"video_id":video.id,"video_title":video.youtube_title,"video_url":video.youtube_url,"video_status":video.vector_status,"is_transcript_available":bool(video.is_transcript_available),"created_at":str(video.created_at)}
            videos_list.append(video_data)
        return JSONResponse(content={"videos":videos_list})
    except Exception as e:
        return {"error": f"Error getting videos from database: {e}"}
    