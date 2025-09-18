from .base_scheme import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Index
from ..enums.video_enum import VideoStatusEnum
from sqlalchemy.orm import relationship
from ..enums import TablesEnum

class Video(SQLAlchemyBase):
    __tablename__ = TablesEnum.VIDEOS.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_title = Column(String, nullable=False)
    youtube_url = Column(String, nullable=False, unique=True)
    youtube_id = Column(String, nullable=False, unique=False)
    vector_status = Column(
        String,
        nullable=False,
        default=VideoStatusEnum.PROCESSING.value,
        server_default=VideoStatusEnum.PROCESSING.value,
    )
    is_transcript_available = Column(Integer, nullable=False, default=0, server_default="0")
    video_summary = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


    chats = relationship(
        "Chat",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

