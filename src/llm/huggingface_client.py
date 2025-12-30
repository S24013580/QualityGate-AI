"""
Hugging Face LLM Client
Alternative free LLM option using transformers
"""

from typing import Optional, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from .base_client import BaseLLMClient


class HuggingFaceClient(BaseLLMClient):
    """Client for Hugging Face transformers (free, local)"""
    
    def __init__(self, model: str = "codellama/CodeLlama-7b-Instruct-hf",
                 temperature: float = 0.2, max_tokens: int = 2000,
                 device: Optional[str] = None):
        super().__init__(model, temperature, max_tokens)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            if self.device == "cpu":
                self.model = self.model.to(self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to load Hugging Face model: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Hugging Face model
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        if self.tokenizer is None or self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")
        
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the output
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    def is_available(self) -> bool:
        """Check if model is loaded and available"""
        return self.model is not None and self.tokenizer is not None

