"""
Service Qdrant pour la recherche vectorielle (RAG)
"""
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct, 
    Filter, FieldCondition, MatchValue
)
from typing import List, Dict, Any, Optional
import logging
import uuid

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """Gestionnaire de la base vectorielle Qdrant"""
    
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._connected = False
        self._collection_name = settings.QDRANT_COLLECTION
    
    async def connect(self):
        """Établit la connexion à Qdrant"""
        try:
            self._client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=30
            )
            # Vérifie la connexion
            self._client.get_collections()
            self._connected = True
            logger.info("Connexion à Qdrant établie avec succès")
            
            # Initialise la collection si nécessaire
            await self._ensure_collection()
            
        except Exception as e:
            logger.error(f"Erreur de connexion à Qdrant: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Ferme la connexion Qdrant"""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Connexion Qdrant fermée")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def health_check(self) -> bool:
        """Vérifie l'état de Qdrant"""
        if not self._client:
            return False
        try:
            self._client.get_collections()
            return True
        except Exception:
            return False
    
    async def _ensure_collection(self):
        """Crée la collection si elle n'existe pas"""
        try:
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self._collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self._collection_name}' créée")
                
                # Crée les index pour les filtres
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name="numero",
                    field_schema="integer"
                )
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name="theme_principal",
                    field_schema="keyword"
                )
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name="type",
                    field_schema="keyword"
                )
                logger.info("Index créés sur la collection")
            else:
                logger.info(f"Collection '{self._collection_name}' existe déjà")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la collection: {e}")
            raise
    
    async def upsert_article(
        self,
        article_id: int,
        embedding: List[float],
        payload: Dict[str, Any]
    ):
        """Insère ou met à jour un article dans Qdrant"""
        if not self._connected:
            raise ConnectionError("Non connecté à Qdrant")
        
        try:
            point = PointStruct(
                id=article_id,
                vector=embedding,
                payload={
                    **payload,
                    "type": "article"
                }
            )
            
            self._client.upsert(
                collection_name=self._collection_name,
                points=[point]
            )
            logger.debug(f"Article {article_id} indexé dans Qdrant")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation de l'article {article_id}: {e}")
            raise
    
    async def upsert_qa(
        self,
        qa_id: int,
        question_embedding: List[float],
        payload: Dict[str, Any]
    ):
        """Insère une paire Q&A dans Qdrant"""
        if not self._connected:
            raise ConnectionError("Non connecté à Qdrant")
        
        try:
            # Utilise un ID différent pour les Q&A (offset de 10000)
            point_id = 10000 + qa_id
            
            point = PointStruct(
                id=point_id,
                vector=question_embedding,
                payload={
                    **payload,
                    "type": "qa"
                }
            )
            
            self._client.upsert(
                collection_name=self._collection_name,
                points=[point]
            )
            logger.debug(f"Q&A {qa_id} indexé dans Qdrant")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation Q&A {qa_id}: {e}")
            raise
    
    async def upsert_batch(
        self,
        points: List[Dict[str, Any]]
    ):
        """Insère un lot de points dans Qdrant"""
        if not self._connected:
            raise ConnectionError("Non connecté à Qdrant")
        
        try:
            qdrant_points = [
                PointStruct(
                    id=p["id"],
                    vector=p["embedding"],
                    payload=p["payload"]
                )
                for p in points
            ]
            
            self._client.upsert(
                collection_name=self._collection_name,
                points=qdrant_points,
                wait=True
            )
            logger.info(f"{len(points)} points indexés dans Qdrant")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation batch: {e}")
            raise
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = None,
        score_threshold: float = None,
        filter_type: Optional[str] = None,
        filter_theme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche les documents les plus similaires
        
        Args:
            query_embedding: Embedding de la requête
            limit: Nombre max de résultats
            score_threshold: Score minimum de similarité
            filter_type: Filtrer par type (article, qa)
            filter_theme: Filtrer par thème principal
        
        Returns:
            Liste des résultats avec score et payload
        """
        if not self._connected:
            raise ConnectionError("Non connecté à Qdrant")
        
        limit = limit or settings.RAG_TOP_K
        score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD
        
        try:
            # Construit les filtres
            must_conditions = []
            
            if filter_type:
                must_conditions.append(
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=filter_type)
                    )
                )
            
            if filter_theme:
                must_conditions.append(
                    FieldCondition(
                        key="theme_principal",
                        match=MatchValue(value=filter_theme)
                    )
                )
            
            query_filter = Filter(must=must_conditions) if must_conditions else None
            
            # Exécute la recherche
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True
            )
            
            # Formate les résultats
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            logger.debug(f"Recherche: {len(formatted_results)} résultats trouvés")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle: {e}")
            raise
    
    async def search_articles(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recherche uniquement dans les articles"""
        return await self.search(
            query_embedding=query_embedding,
            limit=limit,
            filter_type="article"
        )
    
    async def search_qa(
        self,
        query_embedding: List[float],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Recherche uniquement dans les Q&A d'entraînement"""
        return await self.search(
            query_embedding=query_embedding,
            limit=limit,
            filter_type="qa"
        )
    
    async def hybrid_search(
        self,
        query_embedding: List[float],
        article_limit: int = 5,
        qa_limit: int = 2
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recherche hybride dans les articles ET les Q&A
        Retourne les deux types de résultats séparément
        """
        articles = await self.search_articles(query_embedding, limit=article_limit)
        qa_pairs = await self.search_qa(query_embedding, limit=qa_limit)
        
        return {
            "articles": articles,
            "qa_pairs": qa_pairs
        }
    
    async def get_article_by_numero(self, numero: int) -> Optional[Dict[str, Any]]:
        """Récupère un article par son numéro"""
        if not self._connected:
            return None
        
        try:
            results = self._client.scroll(
                collection_name=self._collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="numero",
                            match=MatchValue(value=numero)
                        ),
                        FieldCondition(
                            key="type",
                            match=MatchValue(value="article")
                        )
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            points = results[0]
            if points:
                return points[0].payload
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération article {numero}: {e}")
            return None
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de la collection"""
        if not self._connected:
            return {}
        
        try:
            info = self._client.get_collection(self._collection_name)
            return {
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value
            }
        except Exception as e:
            logger.error(f"Erreur stats collection: {e}")
            return {}
    
    async def delete_collection(self):
        """Supprime la collection (attention!)"""
        if not self._connected:
            return
        
        try:
            self._client.delete_collection(self._collection_name)
            logger.warning(f"Collection '{self._collection_name}' supprimée")
        except Exception as e:
            logger.error(f"Erreur suppression collection: {e}")


# Instance singleton
vector_store = VectorStore()


async def get_vector_store() -> VectorStore:
    """Dependency pour obtenir le vector store"""
    return vector_store
