from abc import ABC, abstractmethod


class VectorDBInterface(ABC):
    """Abstract base class for vector database interfaces."""
    @abstractmethod
    def connect(self):
        """Connect to the vector database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the vector database."""
        pass

    @abstractmethod
    def index(self, embedding_ready_data: list, video_id: str):
        """Insert a vector with associated metadata into the database.
        Args:
            embedding_ready_data (list): A list of dictionaries containing 'text' and 'duration' of start and end in seconds.
            Example:
            [
                {
                    "text": "Sample text chunk",
                    "duration": {
                        "start": 0.0,
                        "end": 30.0
                    }
                },
                ...
            ]
            video_id (str): The ID of the video associated with the embeddings.
        """
        pass


    @abstractmethod
    def search(self,user_query: str, top_k: int,video_id: str):
        """Query the database for similar vectors."""
        pass

    @abstractmethod
    def delete(self, video_id: str):
        """Delete all assiosate recored of specific video from the database by video id."""
        pass

    