from enum import Enum

class GenerationType(str, Enum):
    LITELLM="litellm"
    GROQ="groq"