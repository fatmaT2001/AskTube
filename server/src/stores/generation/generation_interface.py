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