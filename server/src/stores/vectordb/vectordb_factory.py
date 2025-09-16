from .vectordb_enum import VectorDBType
from .providers.pinecone import PineconeDB


class VectorDBFactory:
    def __init__(self):
        pass

    def create_vectordb(self, db_type: VectorDBType):
        if db_type == VectorDBType.PINECONE.value:
            return PineconeDB()
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")