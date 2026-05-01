"""
Semantic AI Service
Generates dense vector embeddings for text using Sentence Transformers
"""
import json
from typing import List, Dict, Optional
import numpy as np

HAS_ML = True # We assume True and handle errors in the function

class SemanticEmbeddingService:
    """Service to generate and compare semantic embeddings"""
    
    _model = None

    @classmethod
    def get_model(cls):
        """Lazy load the transformer model to save memory"""
        if not HAS_ML:
            return None
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # We use a very lightweight, fast model suitable for CPU
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("Warning: ML dependencies not installed.")
                return None
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> Optional[List[float]]:
        """Generate a vector embedding for a given text string"""
        model = cls.get_model()
        if not model or not text or len(text.strip()) == 0:
            return None
            
        try:
            # Generate the embedding (normalize for better cosine similarity)
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
            
    @classmethod
    def calculate_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Cosine Similarity between two embedding vectors"""
        if not vec1 or not vec2:
            return 0.0
            
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            v1 = np.array(vec1).reshape(1, -1)
            v2 = np.array(vec2).reshape(1, -1)
            similarity = cosine_similarity(v1, v2)[0][0]
            # Convert (-1 to 1) scale to a standard (0 to 1) percentage
            return max(0.0, float(similarity))
        except Exception:
            return 0.0

    @staticmethod
    def construct_listing_text(title: str, description: str, category: str, brand: str) -> str:
        """Combine relevant listing fields into a semantic block without structural labels"""
        components = []
        if title: components.append(title)
        if category: components.append(category)
        if brand: components.append(brand)
        if description: components.append(description)
        return " ".join(components)
