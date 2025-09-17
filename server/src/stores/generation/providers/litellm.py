from ..generation_interface import GenerationInterface
import openai
from ....utils.settings import get_settings
import json
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



        


