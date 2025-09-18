from ..generation_interface import GenerationInterface
import openai
from ....utils.settings import get_settings
import json
from typing import List, Dict, Any
from ...prompts.map_prompt import MAP_PROMPT
from ...prompts.reduce_prompt import REDUCE_PROMPT
import asyncio

class LiteLLMProvider(GenerationInterface):
    def __init__(self):
        self.client = None
        self.temperature = 0.1
        self.max_tokens = 2048
        self.TOOLS = [
                    {
                        "name": "get_relevant_chunks",
                        "description": (
                            "Performs a semantic search over the knowledge base (KB) for the specified document IDs. "
                            "Returns the most relevant text chunks that match the user's query. "
                            "Useful for retrieving context or facts from large documents."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_query": {
                                    "type": "string",
                                    "description": "The search query or question from the user."
                                },
                                "top_k": {
                                    "type": "integer",
                                    "default": 3,
                                    "description": "The number of top matching chunks to return."
                                }
                            },
                            "required": ["user_query"]
                        }
                    }
                ]
        
        self.batch_size = 6


    def connect(self):
        self.client= openai.AsyncClient(
            api_key="any key",
            base_url= get_settings().LITELLM_BASE_URL,

        )

    def disconnect(self):
        self.client = None

    def get_tool_agrs(self,msg):
        if getattr(msg, "function_call", None):
            args = json.loads(msg.function_call.model_dump()["arguments"] or "{}")
            return args
        return None

    async def generate_answer(self, message:list[dict]):
        if self.client is None:
            raise Exception("LiteLLMProvider not connected")
        response = await self.client.chat.completions.create(
            model=get_settings().LITELLM_BASE_MODEL,
            messages=message,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            functions=self.TOOLS,
            function_call="auto"
        )
        #         
        if response and response.choices:
            if response.choices[0].message:
                msg = response.choices[0].message
                return msg
            
        return "No response from LiteLLM"
    
    
    async def _get_chunk_summary(self,chunk: str) -> List[str]:
        message = [
            {"role": "system", "content": MAP_PROMPT},
            {"role": "user", "content": chunk}
        ]

        response = await self.client.chat.completions.create(
            model=get_settings().LITELLM_MAP_REDUCE_MODEL,
            messages=message,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content
        print("Chunk summary:", content)
        return content
    
    
    async def _run_batched_tasks(self,chunks: List[str]):
        total_summaries = []

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]

            tasks = [
                    self._get_chunk_summary(chunk)
                    for chunk in batch
            ]

            batched_summaries = await asyncio.gather(*tasks)
            for chunk_data in batched_summaries:
                total_summaries.append(chunk_data)
            await asyncio.sleep(1.5) 

        return total_summaries
    

    async def generate_video_summary(self,chunks: List[str],video_title:str) -> Dict[str, List[str]]:

        total_summaries =  await self._run_batched_tasks(chunks=chunks)

        response = await self.client.chat.completions.create(
            model=get_settings().LITELLM_MAP_REDUCE_MODEL,
            temperature=0.0,
            messages=[
                {"role": "system", "content": REDUCE_PROMPT.format(video_title=video_title, max_final_words=360)},
                {"role": "user", "content":"\n".join(total_summaries)}
            ],
        )
        final_summary = response.choices[0].message.content
        print(f"final summay: {final_summary} ")
        return final_summary


