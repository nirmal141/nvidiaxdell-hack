"""Local embedding service using sentence-transformers on GPU."""
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Using a fast, lightweight model - downloads ~100MB on first use
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class LocalEmbeddingClient:
    """Local embedding client using sentence-transformers on GPU."""
    
    _instance: Optional['LocalEmbeddingClient'] = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the local embedding client."""
        if LocalEmbeddingClient._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformers model."""
        logger.info(f"Loading embedding model {MODEL_ID}...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        LocalEmbeddingClient._model = SentenceTransformer(MODEL_ID, device=device)
        
        logger.info(f"Embedding model loaded on {device}")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings with shape (len(texts), EMBEDDING_DIM)
        """
        if not texts:
            return np.array([])
        
        # Filter out empty texts
        valid_texts = [t if t else "empty" for t in texts]
        
        embeddings = self._model.encode(
            valid_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return embeddings
    
    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        return self.embed([text])[0]
    
    def embed_text(self, text: str):
        """Embed text - compatible with cloud client interface."""
        embedding = self.embed_single(text)
        # Return object with .embedding attribute
        class EmbedResponse:
            def __init__(self, emb):
                self.embedding = emb.tolist()
        return EmbedResponse(embedding)
    
    def embed_query(self, query: str):
        """Embed query - compatible with cloud client interface."""
        return self.embed_text(query)
    
    @property
    def embedding_dim(self) -> int:
        """Return the embedding dimension."""
        return EMBEDDING_DIM


# Test if run directly
if __name__ == "__main__":
    print("Testing local embeddings...")
    client = LocalEmbeddingClient()
    
    texts = [
        "A person walking down the street",
        "A car parked in the parking lot",
        "Someone running away from the scene"
    ]
    
    embeddings = client.embed(texts)
    print(f"Embedding shape: {embeddings.shape}")
    print(f"First embedding: {embeddings[0][:5]}...")
