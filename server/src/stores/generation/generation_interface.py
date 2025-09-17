from abc import ABC, abstractmethod

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