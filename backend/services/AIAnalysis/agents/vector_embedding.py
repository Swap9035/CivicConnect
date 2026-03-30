import chromadb
from langchain_mistralai import MistralAIEmbeddings
from typing import Optional, Dict
import numpy as np
from services.AIAnalysis.utils.config import settings
from services.AIAnalysis.shared.schemas import GrievanceData, VectorCheckResult

class VectorEmbeddingAgent:
    def __init__(self):
        self.embeddings = MistralAIEmbeddings(
            api_key=settings.MISTRAL_API_KEY
        )
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="grievances")
    
    async def check_duplicate(self, grievance: GrievanceData) -> VectorCheckResult:
        """
        Convert grievance to vector and check for duplicates in the same area
        """
        # Create combined text for embedding
        combined_text = f"{grievance.title}. {grievance.full_description}"
        
        # Generate embedding
        vector = self.embeddings.embed_query(combined_text)
        
        # Query similar vectors with metadata filter
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=5,
            where={
                "$and": [
                    {"area_ward_name": grievance.area_ward_name},
                    {"category": grievance.category}
                ]
            },
            include=["metadatas", "distances"]
        )
        
        # Check if any match exceeds threshold (ChromaDB returns cosine distance, lower is more similar)
        if results['distances'] and len(results['distances'][0]) > 0:
            best_distance = results['distances'][0][0]
            best_metadata = results['metadatas'][0][0]
            
            # Convert distance to similarity (1 - distance for cosine)
            similarity = 1 - best_distance
            
            if similarity >= settings.SIMILARITY_THRESHOLD:
                return VectorCheckResult(
                    is_duplicate=True,
                    parent_form_id=best_metadata.get("form_id"),
                    similarity_score=float(similarity)
                )
        
        # No duplicate found - store this grievance vector
        await self._store_vector(grievance, vector)
        
        return VectorCheckResult(
            is_duplicate=False,
            parent_form_id=None,
            similarity_score=None
        )
    
    async def _store_vector(self, grievance: GrievanceData, vector: list):
        """Store the grievance vector in ChromaDB"""
        metadata = {
            "form_id": grievance.form_id,
            "user_id": grievance.user_id,
            "title": grievance.title,
            "category": grievance.category,
            "area_ward_name": grievance.area_ward_name,
            "is_recurring": grievance.is_recurring
        }
        
        self.collection.add(
            embeddings=[vector],
            metadatas=[metadata],
            ids=[grievance.form_id]
        )
