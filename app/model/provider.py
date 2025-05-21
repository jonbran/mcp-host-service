"""Model provider implementations for different API services."""

import abc
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer

from app.config.config import ModelConfig, ModelProviderType

logger = logging.getLogger(__name__)


class ModelProvider(abc.ABC):
    """Base abstract class for model providers."""

    def __init__(self, config: ModelConfig):
        """Initialize the model provider.
        
        Args:
            config: Model configuration
        """
        self.config = config
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the model provider."""
        pass
    
    @abc.abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response based on conversation history.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response text
        """
        pass


class HuggingFaceProvider(ModelProvider):
    """Provider for HuggingFace models."""

    def __init__(self, config: ModelConfig):
        """Initialize the HuggingFace provider.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        self.model: Optional[PreTrainedModel] = None
        self.tokenizer: Optional[PreTrainedTokenizer] = None
        
        logger.info(f"Initialized HuggingFace provider for {config.model_id}")
    
    async def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        logger.info(f"Loading model {self.config.model_id}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_id)
        
        # Load model with appropriate configuration
        device_map = "auto" if self.config.device == "cuda" else None
        
        # Set appropriate flags for CPU vs GPU
        if self.config.device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                device_map=device_map,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            
            if self.config.optimize:
                logger.info("Optimizing model for inference")
                self.model = self.model.to_bettertransformer()
        else:
            # CPU-only loading with 8-bit quantization disabled
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                device_map=None,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
                load_in_8bit=False,
                load_in_4bit=False,
            )
        
        logger.info(f"Model loaded on {self.config.device}")
    
    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation history for the model.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Formatted conversation string
        """
        # Get model name from the model ID
        model_name = self.config.model_id.lower()
        
        # DeepSeek format
        if "deepseek" in model_name:
            return self._format_deepseek_conversation(messages)
        # Llama format
        elif "llama" in model_name:
            return self._format_llama_conversation(messages)
        # Generic format for other models
        else:
            return self._format_generic_conversation(messages)
    
    def _format_deepseek_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation for DeepSeek models.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted conversation string
        """
        formatted = ""
        
        for i, message in enumerate(messages):
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system" and i == 0:
                # System messages are handled differently if they're the first message
                formatted += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}\n"
            elif role == "system":
                # For system messages that are not the first, format them as special instructions
                formatted += f"<|system|>\n{content}\n"
        
        # Add the assistant prefix for the response
        formatted += "<|assistant|>\n"
        
        return formatted
    
    def _format_llama_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation for Llama models.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted conversation string
        """
        formatted = ""
        
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system":
                formatted += f"<s>[INST] <<SYS>>\n{content}\n<</SYS>>\n"
            elif role == "user":
                # If previous was a system message, continue that instruction
                if formatted.endswith("<</SYS>>\n"):
                    formatted += f"{content} [/INST]\n"
                else:
                    formatted += f"<s>[INST] {content} [/INST]\n"
            elif role == "assistant":
                formatted += f"{content} </s>\n"
        
        # If the last message was from user, just add the closing tag for assistant
        if formatted.endswith("[/INST]\n"):
            return formatted
        
        # Otherwise, open a new block for assistant response
        return formatted
    
    def _format_generic_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation for generic models.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted conversation string
        """
        formatted = ""
        
        for message in messages:
            role = message.get("role", "").upper()
            content = message.get("content", "")
            
            if role == "SYSTEM":
                formatted += f"SYSTEM: {content}\n\n"
            elif role == "USER":
                formatted += f"USER: {content}\n\n"
            elif role == "ASSISTANT":
                formatted += f"ASSISTANT: {content}\n\n"
        
        formatted += "ASSISTANT: "
        
        return formatted
    
    async def generate_response(
        self, messages: List[Dict[str, Any]]
    ) -> str:
        """Generate a response based on conversation history.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response text
        """
        if not self.model or not self.tokenizer:
            await self.initialize()
        
        # Format the conversation for the model
        prompt = self._format_conversation(messages)
        
        # Tokenize the prompt
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Truncate if input is too long
        max_input_length = self.config.max_sequence_length // 2  # Leave half for generation
        if inputs["input_ids"].shape[1] > max_input_length:
            logger.warning(f"Input too long ({inputs['input_ids'].shape[1]} tokens), truncating to {max_input_length} tokens")
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=max_input_length
            )
        
        inputs = {k: v.to(self.config.device) for k, v in inputs.items()}
        
        # Generate response
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=min(300, self.config.max_sequence_length - inputs["input_ids"].shape[1]),
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode the output
        response = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        return response


class OpenAIProvider(ModelProvider):
    """Provider for OpenAI API models."""
    
    def __init__(self, config: ModelConfig):
        """Initialize the OpenAI provider.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        self.client = None
        
        # Get API key from config or environment variable
        self.api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided in config or environment")
        
        # Get API base URL if provided (for Azure OpenAI etc.)
        self.api_base = self.config.api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        logger.info(f"Initialized OpenAI provider for {config.model_id}")
    
    async def initialize(self) -> None:
        """Initialize the OpenAI API client."""
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )
        logger.info(f"OpenAI API client initialized with base URL {self.api_base}")
    
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response using the OpenAI API.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response text
        """
        if not self.client:
            await self.initialize()
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        # Standardize the role names
        formatted_messages = []
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            # Map role names to OpenAI's expected format
            if role == "user":
                formatted_role = "user"
            elif role == "assistant":
                formatted_role = "assistant"
            elif role == "system":
                formatted_role = "system"
            else:
                logger.warning(f"Unknown role {role}, using 'user'")
                formatted_role = "user"
            
            formatted_messages.append({"role": formatted_role, "content": content})
        
        # Prepare the API request
        request_data = {
            "model": self.config.model_id,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": 300,  # Limit response length
        }
        
        # Call the OpenAI API
        try:
            response = await self.client.post("/chat/completions", json=request_data)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.text}")
            raise RuntimeError(f"OpenAI API error: {e}")
        
        except Exception as e:
            logger.exception(f"Error calling OpenAI API: {e}")
            raise RuntimeError(f"Error generating response: {str(e)}")


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic API models."""
    
    def __init__(self, config: ModelConfig):
        """Initialize the Anthropic provider.
        
        Args:
            config: Model configuration
        """
        super().__init__(config)
        self.client = None
        
        # Get API key from config or environment variable
        self.api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Anthropic API key provided in config or environment")
        
        # Base URL is fixed for Anthropic
        self.api_base = "https://api.anthropic.com"
        
        # Version header
        self.anthropic_version = "2023-06-01"  # Update as needed
        
        logger.info(f"Initialized Anthropic provider for {config.model_id}")
    
    async def initialize(self) -> None:
        """Initialize the Anthropic API client."""
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("Anthropic API client initialized")
    
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response using the Anthropic API.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Generated response text
        """
        if not self.client:
            await self.initialize()
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        
        # Extract system message if present
        system_message = None
        formatted_messages = []
        
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            # For Anthropic, system message is handled separately
            if role == "system" and system_message is None:
                system_message = content
            elif role == "user":
                formatted_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                formatted_messages.append({"role": "assistant", "content": content})
            elif role != "system":
                # Treat unknown roles as user
                logger.warning(f"Unknown role {role}, using 'user'")
                formatted_messages.append({"role": "user", "content": content})
        
        # Prepare the API request
        request_data = {
            "model": self.config.model_id,
            "messages": formatted_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": 300,  # Limit response length
        }
        
        # Add system message if present
        if system_message:
            request_data["system"] = system_message
        
        # Call the Anthropic API
        try:
            response = await self.client.post("/v1/messages", json=request_data)
            response.raise_for_status()
            
            data = response.json()
            return data["content"][0]["text"]
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API error: {e.response.text}")
            raise RuntimeError(f"Anthropic API error: {e}")
        
        except Exception as e:
            logger.exception(f"Error calling Anthropic API: {e}")
            raise RuntimeError(f"Error generating response: {str(e)}")


def get_provider(config: ModelConfig) -> ModelProvider:
    """Factory function to get the appropriate provider based on configuration.
    
    Args:
        config: Model configuration
        
    Returns:
        Model provider instance
        
    Raises:
        ValueError: If provider type is unsupported
    """
    if config.provider == ModelProviderType.HUGGINGFACE:
        return HuggingFaceProvider(config)
    elif config.provider == ModelProviderType.OPENAI:
        return OpenAIProvider(config)
    elif config.provider == ModelProviderType.ANTHROPIC:
        return AnthropicProvider(config)
    else:
        raise ValueError(f"Unsupported provider type: {config.provider}")
