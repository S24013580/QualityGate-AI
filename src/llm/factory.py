"""
LLM Client Factory
Creates appropriate LLM client based on configuration
"""

import yaml
from typing import Dict, Any
from .ollama_client import OllamaClient
from .huggingface_client import HuggingFaceClient
from .base_client import BaseLLMClient

try:
    from .openai_client import OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIClient = None


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """
    Create an LLM client based on configuration
    
    Args:
        config: Configuration dictionary with 'llm' section
        
    Returns:
        Initialized LLM client
    """
    llm_config = config.get('llm', {})
    provider = llm_config.get('provider', 'ollama')
    model = llm_config.get('model', 'codellama')
    temperature = llm_config.get('temperature', 0.2)
    max_tokens = llm_config.get('max_tokens', 2000)
    
    if provider == 'ollama':
        base_url = llm_config.get('base_url', 'http://localhost:11434')
        timeout = llm_config.get('timeout', 60)
        return OllamaClient(
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
    elif provider == 'huggingface':
        device = llm_config.get('device', None)
        return HuggingFaceClient(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            device=device
        )
    elif provider == 'openai' or provider == 'chatgpt':
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            )
        api_key = llm_config.get('api_key', None)
        timeout = llm_config.get('timeout', 120)
        return OpenAIClient(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Supported: ollama, huggingface, openai")


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

