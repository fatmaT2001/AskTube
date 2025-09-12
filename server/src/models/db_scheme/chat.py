from .base_scheme import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

class Chat(SQLAlchemyBase):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), index=True, nullable=False)
    video = relationship("Video", back_populates="chats")

    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at.asc()",
    )