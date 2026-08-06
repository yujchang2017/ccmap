"""
Embedding service for handling OpenAI embeddings and similarity calculations.
"""

import numpy as np
import pandas as pd
from functools import lru_cache
from typing import List, Tuple, Optional
from openai import OpenAI


class EmbeddingService:
    """Service for handling embeddings and similarity calculations."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        embedding_dim: int = 3072,
    ):
        self.model = model
        self.embedding_dim = int(embedding_dim)
        self.client = OpenAI(api_key=api_key) if api_key else None

    def _zero(self) -> np.ndarray:
        return np.zeros(self.embedding_dim, dtype=np.float32)

    def _sanitize_text(self, text: str) -> str:
        # OpenAI embeddings endpoint may reject empty/invalid strings.
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\x00", "").strip()
        if len(text) > 6000:
            text = text[:6000]
        return text
            
    @lru_cache(maxsize=1000)
    def get_openai_embedding(self, text: str) -> np.ndarray:
        """Get OpenAI embedding for a single text with caching."""
        if self.client is None:
            print("OpenAI API key not set.")
            return self._zero()

        try:
            text = self._sanitize_text(text)
            if not text:
                return self._zero()

            resp = self.client.embeddings.create(model=self.model, input=[text])
            return np.array(resp.data[0].embedding, dtype=np.float32)
        except Exception as e:
            print(f"Error getting OpenAI embedding for '{text[:50]}...': {e}")
            return self._zero()

    def get_openai_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 100,
    ) -> np.ndarray:
        """Get OpenAI embeddings for multiple texts in batches."""
        if self.client is None:
            print("OpenAI API key not set. Returning zero vectors.")
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)

        use_model = model or self.model
        embeddings: list[np.ndarray] = []

        texts_str = [str(txt) if not pd.isna(txt) else "" for txt in texts]

        for i in range(0, len(texts_str), batch_size):
            batch = texts_str[i : i + batch_size]

            sanitized_inputs: list[str] = []
            sanitized_to_original_indices: list[int] = []
            batch_embeddings: list[np.ndarray | None] = [None] * len(batch)

            for j, txt in enumerate(batch):
                txt_s = self._sanitize_text(txt)
                if not txt_s:
                    continue
                sanitized_inputs.append(txt_s)
                sanitized_to_original_indices.append(j)

            try:
                if sanitized_inputs:
                    resp = self.client.embeddings.create(model=use_model, input=sanitized_inputs)
                    data_sorted = sorted(resp.data, key=lambda x: getattr(x, "index", 0))
                    for item, original_j in zip(data_sorted, sanitized_to_original_indices, strict=False):
                        batch_embeddings[original_j] = np.array(item.embedding, dtype=np.float32)
            except Exception as e:
                print(f"Batch embedding failed at index {i}: {e}")
                for txt_s, original_j in zip(sanitized_inputs, sanitized_to_original_indices, strict=False):
                    try:
                        resp = self.client.embeddings.create(model=use_model, input=[txt_s])
                        batch_embeddings[original_j] = np.array(resp.data[0].embedding, dtype=np.float32)
                    except Exception as e_single:
                        print(f"Single embedding failed for '{txt_s[:50]}...': {e_single}")

            for j in range(len(batch_embeddings)):
                if batch_embeddings[j] is None:
                    batch_embeddings[j] = self._zero()

            embeddings.extend(batch_embeddings)

        return np.vstack(embeddings) if embeddings else np.zeros((0, self.embedding_dim), dtype=np.float32)

    def calculate_similarities(self, query_embedding: np.ndarray, 
                             target_embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarities between query and target embeddings."""
        norm_target_emb = np.linalg.norm(target_embeddings, axis=1)
        norm_query_emb = np.linalg.norm(query_embedding)

        similarities = np.zeros(len(target_embeddings), dtype=np.float32)
        if norm_query_emb > 1e-8:
            non_zero_norm_indices = norm_target_emb > 1e-8
            if np.any(non_zero_norm_indices):
                similarities[non_zero_norm_indices] = np.dot(
                    target_embeddings[non_zero_norm_indices], query_embedding
                ) / (norm_target_emb[non_zero_norm_indices] * norm_query_emb)

        return similarities

    def find_most_similar_keyideas(self, query_text: str, keyidea_texts: List[str], 
                                  keyidea_embeddings: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find most similar keyideas to query text."""
        query_embedding = self.get_openai_embedding(query_text)
        if np.all(query_embedding == 0):
            return []

        return self.find_most_similar_keyideas_by_embedding(
            query_embedding, keyidea_texts, keyidea_embeddings, top_k
        )

    def find_most_similar_keyideas_by_embedding(self, query_embedding: np.ndarray, keyidea_texts: List[str],
                                               keyidea_embeddings: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find most similar keyideas to an already-computed query embedding
        (例如：使用預先運算好的 content embedding，避免即時呼叫 API)。"""
        if query_embedding is None or np.all(query_embedding == 0):
            return []

        similarities = self.calculate_similarities(query_embedding, keyidea_embeddings)
        
        keyidea_with_sim = [
            (keyidea_texts[i], float(similarities[i]))
            for i in range(len(keyidea_texts))
        ]
        
        return sorted(keyidea_with_sim, key=lambda x: x[1], reverse=True)[:top_k]

    def find_similar_resources(self, keyidea: str, resource_embeddings: np.ndarray,
                              resource_df: pd.DataFrame, top_k: int = 20,
                              query_embedding: Optional[np.ndarray] = None) -> pd.DataFrame:
        """Find resources most similar to a keyidea.

        query_embedding 優先使用預先運算好的 keyidea 向量（免 API）；
        未提供時才退回即時呼叫 API。"""
        keyidea_embedding = query_embedding if query_embedding is not None \
            else self.get_openai_embedding(keyidea)
        if np.all(keyidea_embedding == 0):
            return pd.DataFrame()

        similarities = self.calculate_similarities(keyidea_embedding, resource_embeddings)
        
        resource_df_copy = resource_df.copy()
        resource_df_copy['similarity'] = similarities
        
        return resource_df_copy.sort_values(by='similarity', ascending=False).head(top_k)