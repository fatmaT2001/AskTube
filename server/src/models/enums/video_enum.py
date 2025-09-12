from enum import Enum

class VideoStatusEnum(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"