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
    import traceback
    import asyncio
    
    print(f"🚀 Starting video processing task for video ID: {video_id}")
    print(f"📊 Task parameters: youtube_video_id={youtube_video_id}, video_title={video_title}, is_transcript_available={is_transcript_availabe}")
    
    try:
        db_client = fastapi_request.app.state.db_client
        db_vector:VectorDBInterface= fastapi_request.app.state.vector_db 
        video_model=VideoModel(db_client)
        nlp_controller = NLPController()
        generation_tool:GenerationInterface= fastapi_request.app.state.generation_model
        print(f"Initialized all components for video ID: {video_id}")
    except Exception as e:
        print(f"Failed to initialize components for video ID {video_id}: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return

    if is_transcript_availabe and youtube_transcript:
        print(f"Transcript available for video ID: {video_id}, starting processing pipeline...")
        
        # step1: preprocess the transcript to generate chunks using chunk duration from settings
        print(f"Step 1: Preprocessing transcript for video ID: {video_id}")
        try:
            chunk_duration = int(get_settings().CHUNK_DURATION * 60)
            print(f" Using chunk duration: {chunk_duration} seconds")
            
            processed_transcript=nlp_controller.prepare_youtube_transcript_for_embedding(
                transcript=youtube_transcript,
                chunk_duration=chunk_duration
            )
            print(f" Step 1 completed: Processed transcript into {len(processed_transcript)} chunks for embedding.")
        except Exception as e:
            print(f" Step 1 failed - Error preprocessing transcript for video ID {video_id}: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f"Updated video status to FAILED for video ID: {video_id}")
            except Exception as status_error:
                print(f"Failed to update video status: {status_error}")
            return 

        # step2: generate video summary using the generation model
        print(f" Step 2: Generating video summary for video ID: {video_id}")
        try:
            if processed_transcript:
                chunks=[chunk["text"] for chunk in processed_transcript]
                print(f"Processing {len(chunks)} chunks for summary generation")
                
                print(f"Calling generation tool for video summary...")
                video_summary= await asyncio.wait_for(
                    generation_tool.generate_video_summary(chunks=chunks,video_title=video_title),
                    timeout=300  # 5 minute timeout
                )
                print(f"Step 2 completed: Generated video summary (length: {len(video_summary)} chars)")
            else:
                video_summary="No transcript available to generate summary."
                print(f"No processed transcript, using default summary")
        except asyncio.TimeoutError:
            print(f"Step 2 timeout - Video summary generation timed out for video ID: {video_id}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f"Updated video status to FAILED due to timeout for video ID: {video_id}")
            except Exception as status_error:
                print(f" Failed to update video status: {status_error}")
            return
        except Exception as e:
            print(f" Step 2 failed - Error generating video summary for video ID {video_id}: {str(e)}")
            print(f" Full traceback: {traceback.format_exc()}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f" Updated video status to FAILED for video ID: {video_id}")
            except Exception as status_error:
                print(f" Failed to update video status: {status_error}")
            return 
        
        print(f" Step 2.5: Saving video summary to database for video ID: {video_id}")
        try:
            await video_model.add_video_summary(video_id=video_id,summary=video_summary)
            print(f" Step 2.5 completed: Video summary updated in database for video ID: {video_id}")
        except Exception as e:
            print(f"Step 2.5 failed - Error updating video summary in database for video ID {video_id}: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f" Updated video status to FAILED for video ID: {video_id}")
            except Exception as status_error:
                print(f" Failed to update video status: {status_error}")
            return

        # step3: create embeddings and save to vector db
        print(f"Step 3: Creating embeddings and saving to vector DB for video ID: {video_id}")
        try:
            if processed_transcript:
                print(f" Indexing {len(processed_transcript)} chunks in vector database...")
                await asyncio.wait_for(
                    db_vector.index(embedding_ready_data=processed_transcript,video_id=video_id),
                    timeout=600  # 10 minute timeout for embedding
                )
                print(f" Step 3 completed: Transcript chunks embedded and saved to vector database for video ID: {video_id}")
            else:
                print(f" No processed transcript to embed for video ID: {video_id}")
        except asyncio.TimeoutError:
            print(f" Step 3 timeout - Vector database indexing timed out for video ID: {video_id}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f" Updated video status to FAILED due to timeout for video ID: {video_id}")
            except Exception as status_error:
                print(f" Failed to update video status: {status_error}")
            return
        except Exception as e:
            print(f"Step 3 failed - Error saving embeddings to vector database for video ID {video_id}: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f"Updated video status to FAILED for video ID: {video_id}")
            except Exception as status_error:
                print(f"Failed to update video status: {status_error}")
            return
        
        # step4: update video status to completed
        print(f" Step 4: Updating video status to READY for video ID: {video_id}")
        try:
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.READY.value)
            print(f" Step 4 completed: Video processing completed successfully for video ID: {video_id}")

        except Exception as e:
            print(f" Step 4 failed - Error updating video status to completed for video ID {video_id}: {str(e)}")
            print(f" Full traceback: {traceback.format_exc()}")
            try:
                await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
                print(f" Updated video status to FAILED for video ID: {video_id}")
            except Exception as status_error:
                print(f" Failed to update video status: {status_error}")
            return
        
    else:
        print(f" No transcript available for video ID: {video_id}; skipping processing steps.")
        print(f" is_transcript_availabe: {is_transcript_availabe}, youtube_transcript length: {len(youtube_transcript) if youtube_transcript else 0}")
        try:
            await video_model.update_video_status(video_id=video_id,new_status=VideoStatusEnum.FAILED.value)
            print(f" Updated video status to FAILED (no transcript) for video ID: {video_id}")
        except Exception as status_error:
            print(f" Failed to update video status: {status_error}")
        return
    
    print(f"Video processing task completed successfully for video ID: {video_id}")
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
        print(f"Initiating background task for video ID: {video_created_data.id}")
        print(f"Task parameters: youtube_video_id={video_id}, title='{video_title}', transcript_available={is_transcript_availabe}, transcript_length={len(transcript) if transcript else 0}")
        
        background_tasks.add_task(
            process_video_task,
            fastapi_request=request,
            video_id=video_created_data.id,
            youtube_video_id=video_id,
            is_transcript_availabe=is_transcript_availabe,
            youtube_transcript=transcript,
            video_title=video_title
        )
        print(f"Background task successfully queued for video ID: {video_created_data.id}")
    except Exception as e:
        print(f" Error starting background task for video ID {video_created_data.id}: {e}")
        import traceback
        print(f" Full traceback: {traceback.format_exc()}")
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
    

@router.delete("/videos/{video_id}")
async def delete_video_by_id(request:Request,video_id:str):
    """
    delete video by id
    """
    db_client = request.app.state.db_client
    video_model=VideoModel(db_client)
    try:    
        await video_model.delete_video_by_id(video_id=int(video_id))
        return JSONResponse(content={"message": "Video deleted successfully"})
    except Exception as e:
        return {"error": f"Error deleting video from database: {e}"}