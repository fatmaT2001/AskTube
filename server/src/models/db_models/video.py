from .base_model import BaseModel
from ..db_scheme import video_scheme
from sqlalchemy import text as sql_text
from ..enums import TablesEnum, VideoStatusEnum

class VideoModel(BaseModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.table_name = TablesEnum.VIDEOS.value
        
    
    async def add_Video(self,video_data:video_scheme)->video_scheme:
        async with self.db_clint() as session:
            async with session.begin():
                session.add(video_data)
            await session.commit()
            await session.refresh(video_data)
        return video_data
    

    async def get_video_by_id(self, video_id: int) -> video_scheme | None:
        async with self.db_clint() as session:
            result = await session.execute(
                sql_text(f"SELECT * FROM {self.table_name} WHERE id = :video_id"),
                {"video_id": video_id}
            )
            video = result.fetchone()
            return video if video else None
    

    async def update_video_status(self, video_id: int, new_status: VideoStatusEnum) -> None:
        async with self.db_clint() as session:
            async with session.begin():
                await session.execute(
                    sql_text(f"UPDATE {self.table_name} SET status = :new_status WHERE id = :video_id"),
                    {"new_status": new_status, "video_id": video_id}
                )
            await session.commit()
           
    

    async def get_video_by_youtube_id(self, youtube_id: str) -> video_scheme | None:
        async with self.db_clint() as session:
            result = await session.execute(
                sql_text(f"SELECT * FROM {self.table_name} WHERE youtube_id = :youtube_id"),
                {"youtube_id": youtube_id}
            )
            video = result.fetchone()
            return video if video else None