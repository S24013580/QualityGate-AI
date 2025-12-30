"""
Base class for LLM clients
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        pass

