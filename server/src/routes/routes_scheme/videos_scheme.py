from pydantic import BaseModel, field_validator
from ...utils.settings import get_settings


class CreateNewVideoRequest(BaseModel):
    youtube_link: str
    required_language: str = "en"  

    @field_validator("required_language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in get_settings().PREFERRED_LANGS:
            raise ValueError(f"Language '{v}' is not supported. Allowed: {get_settings().PREFERRED_LANGS}")
        return v
    
