"""Milvus Lite vector database handler for video descriptions."""
from pymilvus import MilvusClient, DataType
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector search."""
    video_id: str
    timestamp: float
    description: str
    score: float


class VectorStore:
    """
    Milvus Lite vector database for storing and searching video frame descriptions.
    """
    
    def __init__(
        self,
        db_path: str = "./data/milvus/video_qa.db",
        collection_name: str = "video_descriptions",
        embedding_dim: int = 1024
    ):
        """
        Initialize vector store.
        
        Args:
            db_path: Path to Milvus Lite database file
            collection_name: Name of the collection
            embedding_dim: Dimension of embedding vectors
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.client = MilvusClient(db_path)
        
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        if not self.client.has_collection(self.collection_name):
            logger.info(f"Creating collection: {self.collection_name}")
            
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embedding_dim,
                metric_type="COSINE",
                auto_id=True
            )
            
            logger.info(f"Collection created: {self.collection_name}")
    
    def insert_descriptions(
        self,
        video_id: str,
        descriptions: List[Dict[str, Any]]
    ) -> int:
        """
        Insert frame descriptions with embeddings.
        
        Args:
            video_id: Video identifier
            descriptions: List of dicts with 'timestamp', 'description', 'embedding'
            
        Returns:
            Number of inserted records
        """
        if not descriptions:
            return 0
        
        data = []
        for desc in descriptions:
            data.append({
                "video_id": video_id,
                "timestamp": float(desc["timestamp"]),
                "description": desc["description"],
                "vector": desc["embedding"]
            })
        
        result = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        
        logger.info(f"Inserted {len(data)} descriptions for video {video_id}")
        return len(data)
    
    def search(
        self,
        query_embedding: List[float],
        video_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Search for similar descriptions.
        
        Args:
            query_embedding: Query embedding vector
            video_id: Optional filter by video ID
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        filter_expr = f'video_id == "{video_id}"' if video_id else None
        
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            filter=filter_expr,
            output_fields=["video_id", "timestamp", "description"]
        )
        
        search_results = []
        if results and len(results) > 0:
            for hit in results[0]:
                search_results.append(SearchResult(
                    video_id=hit["entity"].get("video_id", ""),
                    timestamp=hit["entity"].get("timestamp", 0.0),
                    description=hit["entity"].get("description", ""),
                    score=hit["distance"]
                ))
        
        return search_results
    
    def delete_video_descriptions(self, video_id: str) -> int:
        """
        Delete all descriptions for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Number of deleted records
        """
        result = self.client.delete(
            collection_name=self.collection_name,
            filter=f'video_id == "{video_id}"'
        )
        logger.info(f"Deleted descriptions for video {video_id}")
        return result.get("delete_count", 0) if isinstance(result, dict) else 0
    
    def get_video_description_count(self, video_id: str) -> int:
        """
        Get count of descriptions for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            Number of descriptions
        """
        results = self.client.query(
            collection_name=self.collection_name,
            filter=f'video_id == "{video_id}"',
            output_fields=["video_id"]
        )
        return len(results)
    
    def close(self):
        """Close the database connection."""
        self.client.close()
