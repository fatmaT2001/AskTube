from abc import ABC, abstractmethod
from typing import List, Dict, Any
class GenerationInterface(ABC):
    @abstractmethod
    def connect(self):
        """Establish a connection to the generation service."""
        pass

    @abstractmethod
    def disconnect(self):
        """Terminate the connection to the generation service."""
        pass

    @abstractmethod
    def generate_answer(self, message: list[dict]) -> str:
        """Generate text based on the provided prompt."""
        pass
    @abstractmethod
    def get_tool_agrs(self,msg):
        """Extract tool arguments from the model's message."""
        pass

    @abstractmethod
    def generate_video_summary(self,chunks: List[str],video_title:str) -> Dict[str, List[str]]:
        """Generate text using the provided tool arguments."""
        pass