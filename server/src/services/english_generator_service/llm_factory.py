
from .vertex_provider import VertexProvider
from .openai_provider import OpenAIProvider

def build_llm_provider(provider_name, client_31=None, client_25=None):

    if provider_name == "openai":
        return OpenAIProvider()

    return VertexProvider(
        client_31=client_31,
        client_25=client_25
    )