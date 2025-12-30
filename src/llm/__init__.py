"""
LLM Integration Module
Supports multiple LLM providers: Ollama, Hugging Face, and OpenAI
"""

from .ollama_client import OllamaClient
from .huggingface_client import HuggingFaceClient
from .base_client import BaseLLMClient

try:
    from .openai_client import OpenAIClient
    __all__ = ['OllamaClient', 'HuggingFaceClient', 'OpenAIClient', 'BaseLLMClient']
except ImportError:
    __all__ = ['OllamaClient', 'HuggingFaceClient', 'BaseLLMClient']

