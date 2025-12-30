"""
Ollama LLM Client
Free, local LLM integration
"""

import requests
from typing import Optional, Dict, Any
from .base_client import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Client for Ollama LLM (free, local)"""
    
    def __init__(self, model: str = "codellama", base_url: str = "http://localhost:11434",
                 temperature: float = 0.2, max_tokens: int = 2000, timeout: int = 60):
        super().__init__(model, temperature, max_tokens)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama API with streaming support
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        use_streaming = kwargs.get('stream', True)  # Default to streaming
        
        url = f"{self.base_url}/api/generate"
        
        if use_streaming:
            return self._generate_streaming(url, prompt, temperature, max_tokens)
        else:
            return self._generate_non_streaming(url, prompt, temperature, max_tokens)
    
    def _generate_streaming(self, url: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate with streaming to show progress"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            import json
            
            print(f"Requesting generation from Ollama (streaming mode - this may take a while)...")
            print("Progress: ", end="", flush=True)
            
            full_response = ""
            chunk_count = 0
            
            response = requests.post(url, json=payload, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = line.decode('utf-8')
                        data = json.loads(chunk)
                        
                        if 'response' in data:
                            token = data['response']
                            full_response += token
                            chunk_count += 1
                            
                            # Show progress every 50 chunks
                            if chunk_count % 50 == 0:
                                print(".", end="", flush=True)
                        
                        # Check if done
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            print()  # New line after progress
            if not full_response:
                raise ValueError("Ollama returned empty response")
            
            print(f"Generated {len(full_response)} characters in {chunk_count} chunks")
            return full_response
            
        except requests.exceptions.Timeout as e:
            raise ConnectionError(
                f"Ollama request timed out after {self.timeout}s. "
                f"The model may need more time. Try increasing timeout in config.yaml"
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def _generate_non_streaming(self, url: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate without streaming (fallback)"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            print(f"Requesting generation from Ollama (this may take a while)...")
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            generated_text = result.get('response', '')
            if not generated_text:
                raise ValueError("Ollama returned empty response")
            return generated_text
        except requests.exceptions.Timeout as e:
            raise ConnectionError(
                f"Ollama request timed out after {self.timeout}s. "
                f"The model may need more time. Try increasing timeout in config.yaml"
            )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            return any(self.model in name for name in model_names)
        except:
            return False

