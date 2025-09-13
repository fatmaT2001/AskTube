from .base_scheme import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text,func
from sqlalchemy.orm import relationship
from ..enums import TablesEnum

class Message(SQLAlchemyBase):
    __tablename__ = TablesEnum.MESSAGES.value  

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    chat = relationship("Chat", back_populates="messages")
