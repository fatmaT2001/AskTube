from pydantic import BaseModel,field_validator
from ...utils.settings import get_settings
from enum import Enum




class CreateNewChatRequest(BaseModel):
    video_id: int


class SendMessageRequest(BaseModel):
    message: str



class RoleMessage(str,Enum):
    USER = "user"
    ASSISTANT = "assistant"