"""Model Router - Routes requests to appropriate AI models based on task type and user tier."""

import json
from typing import Optional, Dict, Any, List
from enum import Enum


class ModelType(Enum):
    """Available models in Workers AI."""
    # Vision models
    MOONDREAM = "@cf/moondream/moondream3.1-9B-A2B"
    
    # Reasoning models (premium)
    DEEPSEEK_R1 = "@cf/deepseek/deepseek-r1-distill-qwen-32b"
    
    # General chat models
    LLAMA_4_SCOUT = "@cf/meta/llama-4-scout-17b-16e-instruct"
    LLAMA_3_3_70B = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    LLAMA_3_1_70B = "@cf/meta/llama-3.1-70b-instruct"
    LLAMA_3_8B = "@cf/meta/llama-3-8b-instruct"
    LLAMA_3_2_3B = "@cf/meta/llama-3.2-3b-instruct"
    
    # Embedding models
    BGE_M3 = "@cf/baai/bge-m3"
    BGE_BASE = "@cf/baai/bge-base-en-v1.5"
    BGE_SMALL = "@cf/baai/bge-small-en-v1.5"


class TaskType(Enum):
    """Task types for model routing."""
    VISION_PRECHECK = "vision_precheck"      # Moondream - quick body detection
    REASONING_PREMIUM = "reasoning_premium"  # DeepSeek R1 - complex reasoning
    CHAT_GENERAL = "chat_general"            # Llama 4 Scout - general chat
    RECOMMENDATIONS = "recommendations"      # Llama 4 Scout - recommendations
    EMBEDDING = "embedding"                  # BGE-M3 - embeddings
    FAST_CHAT = "fast_chat"                  # Llama 3.2 3B - fast responses
    STYLE_ADVICE = "style_advice"            # DeepSeek R1 / Llama 4 Scout - style advice


class ModelRouter:
    """Routes requests to appropriate models based on task type, user tier, and context."""
    
    def __init__(self, env):
        self.env = env
        self.ai = env.AI
    
    # Model routing rules: (task_type, is_premium) -> model
    ROUTING_RULES = {
        # Vision pre-check (always Moondream - fast, cheap)
        (TaskType.VISION_PRECHECK, True): ModelType.MOONDREAM,
        (TaskType.VISION_PRECHECK, False): ModelType.MOONDREAM,
        
        # Premium reasoning
        (TaskType.REASONING_PREMIUM, True): ModelType.DEEPSEEK_R1,
        (TaskType.REASONING_PREMIUM, False): ModelType.LLAMA_4_SCOUT,  # Fallback for free users
        
        # General chat & recommendations
        (TaskType.CHAT_GENERAL, True): ModelType.LLAMA_4_SCOUT,
        (TaskType.CHAT_GENERAL, False): ModelType.LLAMA_3_3_70B,
        
        (TaskType.RECOMMENDATIONS, True): ModelType.LLAMA_4_SCOUT,
        (TaskType.RECOMMENDATIONS, False): ModelType.LLAMA_3_3_70B,
        
        # Fast chat for quick responses
        (TaskType.FAST_CHAT, True): ModelType.LLAMA_3_2_3B,
        (TaskType.FAST_CHAT, False): ModelType.LLAMA_3_2_3B,
        
        # Embeddings
        (TaskType.EMBEDDING, True): ModelType.BGE_M3,
        (TaskType.EMBEDDING, False): ModelType.BGE_M3,
        
        # Style advice (chat with product context)
        (TaskType.STYLE_ADVICE, True): ModelType.DEEPSEEK_R1,
        (TaskType.STYLE_ADVICE, False): ModelType.LLAMA_4_SCOUT,
    }
    
    # Streaming support
    STREAMING_MODELS = {
        ModelType.LLAMA_4_SCOUT,
        ModelType.LLAMA_3_3_70B,
        ModelType.LLAMA_3_1_70B,
        ModelType.DEEPSEEK_R1,
        ModelType.LLAMA_3_2_3B,
    }
    
    # Vision-capable models
    VISION_MODELS = {
        ModelType.MOONDREAM,
    }
    
    def _get_model(self, task_type: TaskType, is_premium: bool) -> ModelType:
        """Determine which model to use based on task and user tier."""
        return self.ROUTING_RULES.get((task_type, is_premium), ModelType.LLAMA_4_SCOUT)
    
    def _supports_streaming(self, model: ModelType) -> bool:
        return model in self.STREAMING_MODELS
    
    def _supports_vision(self, model: ModelType) -> bool:
        return model in self.VISION_MODELS
    
    async def run(
        self,
        task_type: TaskType,
        messages: List[Dict[str, Any]],
        is_premium: bool = False,
        stream: bool = False,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Any:
        """
        Run inference with appropriate model.
        
        Args:
            task_type: Type of task (determines model selection)
            messages: Chat messages in OpenAI format
            is_premium: Whether user has premium subscription
            stream: Whether to stream response
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional model-specific parameters
        """
        is_premium = bool(is_premium)
        model = self._get_model(task_type, is_premium)
        supports_streaming = stream and self._supports_streaming(model)
        
        # Build request
        request = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add model-specific parameters
        if task_type == TaskType.EMBEDDING:
            request = {"text": messages[0].get("content", "")}
        
        # Add streaming flag if supported
        if supports_streaming:
            request["stream"] = True
        
        # Run inference
        try:
            result = await self.ai.run(
                model.value,
                request,
            )
            return result
        except Exception as e:
            import json as _json
            print(_json.dumps({
                "event": "model_router_error",
                "task_type": task_type.value,
                "model": model.value,
                "is_premium": is_premium,
                "error": str(e),
            }))
            raise
    
    async def run_stream(
        self,
        task_type: TaskType,
        messages: List[Dict[str, Any]],
        is_premium: bool = False,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ):
        """Run streaming inference with appropriate model."""
        is_premium = bool(is_premium)
        model = self._get_model(task_type, is_premium)
        
        if not self._supports_streaming(model):
            # Fallback: run non-streaming and yield single chunk
            result = await self.run(task_type, messages, is_premium, False, max_tokens, temperature)
            yield {"content": self._extract_content(result)}
            return
        
        request = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        try:
            async for chunk in self.ai.run_stream(model.value, request):
                yield chunk
        except Exception as e:
            import json as _json
            print(_json.dumps({
                "event": "model_router_stream_error",
                "task_type": task_type.value,
                "model": model.value,
                "error": str(e),
            }))
            raise
    
    def _extract_content(self, result: Any) -> str:
        """Extract text content from model result."""
        if not result:
            return ""
        
        if isinstance(result, dict):
            if "response" in result:
                return str(result["response"])
            if "choices" in result:
                choices = result["choices"]
                if isinstance(choices, list) and choices:
                    choice = choices[0]
                    if isinstance(choice, dict):
                        message = choice.get("message", {})
                        if isinstance(message, dict):
                            return str(message.get("content", ""))
            if "content" in result:
                return str(result["content"])
            if "advice" in result:
                return str(result["advice"])
        return str(result)
    
    async def embed(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Generate embeddings using BGE-M3."""
        result = await self.ai.run(
            ModelType.BGE_M3.value,
            {"text": texts}
        )
        
        # Extract embeddings from various response formats
        if isinstance(result, dict) and "data" in result:
            return [item["embedding"] for item in result["data"]]
        elif isinstance(result, list):
            return result
        return []
    
    async def vision_check(
        self,
        image_url: str,
        question: str = "Is there a person with a visible human body in this image? Answer yes or no.",
    ) -> Dict[str, Any]:
        """Quick vision check using Moondream."""
        return await self.run(
            task_type=TaskType.VISION_PRECHECK,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": image_url},
                    {"type": "text", "text": question}
                ]
            }],
            is_premium=True,  # Always use Moondream for vision
            max_tokens=100,
            temperature=0.1,
        )