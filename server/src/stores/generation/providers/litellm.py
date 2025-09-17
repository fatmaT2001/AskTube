from ..generation_interface import GenerationInterface
import openai
from ....utils.settings import get_settings

class LiteLLMProvider(GenerationInterface):
    def __init__(self):
        self.client = None
        self.temperature = 0.1
        self.max_tokens = 2048


    def connect(self):
        self.client= openai.AsyncClient(
            api_key="any key",
            base_url= get_settings().LITELLM_BASE_URL
        )

    def disconnect(self):
        self.client = None


    async def generate_answer(self, message:list[dict]):
        if self.client is None:
            raise Exception("LiteLLMProvider not connected")
        response = await self.client.chat.completions.create(
            model=get_settings().LITELLM_BASE_MODEL,
            messages=message,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if response and response.choices:
            if response.choices[0].message:
                return response.choices[0].message.content
            
        return "No response from LiteLLM"



        


