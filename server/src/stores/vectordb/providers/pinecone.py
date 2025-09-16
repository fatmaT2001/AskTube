from pinecone import PineconeAsyncio
from pinecone.db_data import IndexAsyncio
from ..vectordb_interface import VectorDBInterface
from ....utils.settings import get_settings



class PineconeDB(VectorDBInterface):
    def __init__(self):
        self.reranking_model = get_settings().PINECONE_RERANKING_MODEL
        self.pc=None
        self.pc_index=None

    async def connect(self):
        pc = PineconeAsyncio(api_key=get_settings().PINECONE_API_KEY)
        self.pc = pc
        self.pc_index = self.pc.IndexAsyncio(host=get_settings().PINECONE_HOST_URL)
        return 
    

    async def disconnect(self):
        if self.pc is not None:
            await self.pc.close()
        if self.pc_index is not None:
            await self.pc_index.close()

        return

    async def index(self, embedding_ready_data: list, video_id: str):
        # Prepare data for indexing
        prepared_records = []
        print(f"videoid is {video_id}")
        for i, item in enumerate(embedding_ready_data):
            vector = {
                "_id": f"{video_id}_chunk_{i}",
                "text": f"From {item['duration']['start']} to {item['duration']['end']}: {item['text']}",
                "source": str(video_id),
                
            }
            prepared_records.append(vector)
        
        # Upsert vectors to Pinecone index
        await self.pc_index.upsert_records(namespace="default", records=prepared_records)

        return 
        
        


    async def search(self, user_query: list, top_k: int,video_id: str):
        """
        Perform a similarity search with optional metadata filtering.
        :param query_embedding: The embedding vector to query against.
        :param top_k: The number of top similar results to return.
        """
        filtered_results= await self.pc_index.search(
                namespace="default", 
                query={
                    "inputs": {"text": user_query}, 
                    "top_k": 10,
                    "filter": {"source": str(video_id)},
                },
                rerank={
                        "model":self.reranking_model,
                        "top_n": top_k,
                        "rank_fields": ["text"]
                    }   
                    )
        
        return filtered_results


    def delete(self, video_id):
        pass 