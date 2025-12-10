"""NVIDIA NIM API Client for VLM, Embedding, and LLM models."""
import base64
import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)


class NIMClientError(Exception):
    """Exception for NIM API errors."""
    pass


@dataclass
class VLMResponse:
    """Response from VLM model."""
    description: str
    raw_response: Dict[str, Any]


@dataclass
class EmbeddingResponse:
    """Response from embedding model."""
    embedding: List[float]
    raw_response: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM model."""
    content: str
    raw_response: Dict[str, Any]


class BaseNIMClient:
    """Base client for NVIDIA NIM endpoints."""
    
    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: int = 120):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self.session = requests.Session()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # Add API key if provided (for NVIDIA Cloud API)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self.session.headers.update(headers)
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to NIM endpoint."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise NIMClientError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise NIMClientError(f"Could not connect to NIM endpoint: {url}")
        except requests.exceptions.HTTPError as e:
            raise NIMClientError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise NIMClientError(f"Unexpected error: {str(e)}")


class VLMClient(BaseNIMClient):
    """Client for VILA VLM (Vision Language Model)."""
    
    def __init__(self, base_url: str, model: str = "nvidia/vila", api_key: str = "", timeout: int = 120):
        super().__init__(base_url, model, api_key, timeout)
    
    def _encode_image(self, image: np.ndarray) -> str:
        """Convert numpy image to base64 string."""
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def describe_frame(
        self, 
        image: np.ndarray, 
        prompt: str = "Describe what is happening in this video frame in detail. Include people, objects, actions, and setting."
    ) -> VLMResponse:
        """
        Get description of a video frame.
        
        Args:
            image: numpy array of the frame (RGB format)
            prompt: instruction for the VLM
            
        Returns:
            VLMResponse with description
        """
        image_b64 = self._encode_image(image)
        
        # OpenAI-compatible chat completion format
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.2
        }
        
        response = self._make_request("chat/completions", payload)
        
        try:
            description = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise NIMClientError(f"Unexpected VLM response format: {response}")
        
        return VLMResponse(description=description, raw_response=response)


class EmbeddingClient(BaseNIMClient):
    """Client for NV-Embed-QA embedding model."""
    
    def __init__(self, base_url: str, model: str = "nvidia/nv-embed-qa", api_key: str = "", timeout: int = 60):
        super().__init__(base_url, model, api_key, timeout)
    
    def embed_text(self, text: str) -> EmbeddingResponse:
        """
        Generate embedding for a text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            EmbeddingResponse with embedding vector
        """
        payload = {
            "model": self.model,
            "input": text,
            "input_type": "passage"
        }
        
        response = self._make_request("embeddings", payload)
        
        try:
            embedding = response["data"][0]["embedding"]
        except (KeyError, IndexError):
            raise NIMClientError(f"Unexpected embedding response format: {response}")
        
        return EmbeddingResponse(embedding=embedding, raw_response=response)
    
    def embed_query(self, query: str) -> EmbeddingResponse:
        """
        Generate embedding for a query (for search).
        
        Args:
            query: Search query text
            
        Returns:
            EmbeddingResponse with embedding vector
        """
        payload = {
            "model": self.model,
            "input": query,
            "input_type": "query"
        }
        
        response = self._make_request("embeddings", payload)
        
        try:
            embedding = response["data"][0]["embedding"]
        except (KeyError, IndexError):
            raise NIMClientError(f"Unexpected embedding response format: {response}")
        
        return EmbeddingResponse(embedding=embedding, raw_response=response)
    
    def embed_batch(self, texts: List[str], input_type: str = "passage") -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            input_type: 'passage' or 'query'
            
        Returns:
            List of EmbeddingResponse objects
        """
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type
        }
        
        response = self._make_request("embeddings", payload)
        
        try:
            embeddings = [
                EmbeddingResponse(embedding=item["embedding"], raw_response=response)
                for item in response["data"]
            ]
        except (KeyError, IndexError):
            raise NIMClientError(f"Unexpected embedding response format: {response}")
        
        return embeddings


class LLMClient(BaseNIMClient):
    """Client for Llama LLM."""
    
    def __init__(self, base_url: str, model: str = "meta/llama", api_key: str = "", timeout: int = 120):
        super().__init__(base_url, model, api_key, timeout)
    
    def generate_answer(
        self,
        question: str,
        context: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate answer based on question and retrieved context.
        
        Args:
            question: User's question
            context: List of relevant frame descriptions with timestamps
            system_prompt: Optional system prompt override
            
        Returns:
            LLMResponse with generated answer
        """
        if system_prompt is None:
            system_prompt = """You are a helpful AI assistant that answers questions about video content.
You are given descriptions of video frames at specific timestamps and a user question.
Answer the question based on the provided context. Include relevant timestamps in your answer.
If the information is not in the context, say so honestly.
Format timestamps as [MM:SS] when mentioning specific moments."""

        # Format context for the prompt
        context_text = "\n".join([
            f"[{self._format_timestamp(c['timestamp'])}] {c['description']}"
            for c in context
        ])
        
        user_message = f"""Video Context:
{context_text}

Question: {question}

Please answer based on the video content described above."""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = self._make_request("chat/completions", payload)
        
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise NIMClientError(f"Unexpected LLM response format: {response}")
        
        return LLMResponse(content=content, raw_response=response)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


class NIMClientFactory:
    """Factory for creating NIM clients from config."""
    
    @staticmethod
    def create_vlm_client(config) -> VLMClient:
        return VLMClient(
            base_url=config.nim.vlm_url,
            model=config.nim.vlm_model,
            api_key=config.nim.api_key,
            timeout=config.nim.timeout
        )
    
    @staticmethod
    def create_embedding_client(config) -> EmbeddingClient:
        return EmbeddingClient(
            base_url=config.nim.embedding_url,
            model=config.nim.embedding_model,
            api_key=config.nim.api_key,
            timeout=config.nim.timeout
        )
    
    @staticmethod
    def create_llm_client(config) -> LLMClient:
        return LLMClient(
            base_url=config.nim.llm_url,
            model=config.nim.llm_model,
            api_key=config.nim.api_key,
            timeout=config.nim.timeout
        )
