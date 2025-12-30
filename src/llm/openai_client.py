"""
OpenAI/ChatGPT LLM Client
Uses OpenAI API for high-quality code generation
"""

import os
from typing import Optional, Dict, Any
from .base_client import BaseLLMClient

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API (ChatGPT)"""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None,
                 temperature: float = 0.2, max_tokens: int = 2000, timeout: int = 120):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            )
        
        super().__init__(model, temperature, max_tokens)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.timeout = timeout
        
        # Model mapping for common aliases
        self.model_map = {
            "chatgpt": "gpt-4o-mini",
            "gpt4": "gpt-4o-mini",
            "gpt-4": "gpt-4o-mini",
            "gpt-3.5": "gpt-4o-mini",
        }
        if self.model in self.model_map:
            self.model = self.model_map[self.model]
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI API with streaming support
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, stream, etc.)
            
        Returns:
            Generated text
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        use_streaming = kwargs.get('stream', True)  # Default to streaming
        
        if use_streaming:
            return self._generate_streaming(prompt, temperature, max_tokens)
        else:
            return self._generate_non_streaming(prompt, temperature, max_tokens)
    
    def _generate_streaming(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate with streaming to show progress"""
        try:
            print(f"Requesting generation from OpenAI ({self.model})...")
            print("Progress: ", end="", flush=True)
            
            full_response = ""
            chunk_count = 0
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Java developer specializing in writing comprehensive unit tests. Generate only valid, compilable Java test code following JUnit 5 best practices."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                timeout=self.timeout
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    chunk_count += 1
                    
                    # Show progress every 20 chunks
                    if chunk_count % 20 == 0:
                        print(".", end="", flush=True)
            
            print()  # New line after progress
            
            if not full_response:
                raise ValueError("OpenAI returned empty response")
            
            print(f"Generated {len(full_response)} characters in {chunk_count} chunks")
            return full_response
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                raise ConnectionError(
                    f"OpenAI request timed out after {self.timeout}s. "
                    f"Try increasing timeout in config.yaml"
                )
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(f"OpenAI API authentication failed: {e}")
            else:
                raise ConnectionError(f"Failed to connect to OpenAI: {e}")
    
    def _generate_non_streaming(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate without streaming (faster but no progress)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Java developer specializing in writing comprehensive unit tests. Generate only valid, compilable Java test code following JUnit 5 best practices."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                raise ConnectionError(
                    f"OpenAI request timed out after {self.timeout}s. "
                    f"Try increasing timeout in config.yaml"
                )
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(f"OpenAI API authentication failed: {e}")
            else:
                raise ConnectionError(f"Failed to connect to OpenAI: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        try:
            if not self.api_key:
                return False
            # Simple test request - just check if we can list models
            try:
                # Use a simple, fast endpoint to test connectivity
                # Note: models.list() doesn't accept limit parameter in newer API
                models = list(self.client.models.list())
                # If we get here, the API is working
                return True
            except Exception as e:
                # If it's an auth error, provide better feedback
                error_str = str(e).lower()
                error_msg = str(e)
                
                if 'api key' in error_str or 'authentication' in error_str or '401' in error_str or 'invalid' in error_str:
                    raise ValueError(f"OpenAI API key is invalid or expired. Error: {error_msg}")
                elif 'rate limit' in error_str or '429' in error_str:
                    # Rate limit means service is available, just throttled
                    return True
                elif 'timeout' in error_str:
                    # Timeout - might be network issue, but service exists
                    return False
                else:
                    # Other errors - log but don't fail completely
                    # Could be temporary network issues
                    print(f"Warning: OpenAI availability check failed: {error_msg}")
                    return False
        except ValueError:
            # Re-raise ValueError (invalid API key)
            raise
        except Exception as e:
            # Other exceptions - service might be temporarily unavailable
            print(f"Warning: OpenAI availability check error: {e}")
            return False

