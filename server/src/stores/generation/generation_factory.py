from .providers.litellm import LiteLLMProvider
from .generation_interface import GenerationInterface
from .generation_enum import GenerationType


class GenerationFactory:
    def __init__(self):
        pass

    def create_provider(self, provider_name: GenerationType) -> GenerationInterface:
        if provider_name == GenerationType.LITELLM.value:
            return LiteLLMProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")