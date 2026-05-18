"""
Service de cache Redis pour les réponses fréquentes
"""
import asyncio
import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Dict, Any, List
import logging
from datetime import timedelta

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisCache:
    """Gestionnaire de cache Redis"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._connect_lock = asyncio.Lock()
    
    async def connect(self):
        """Établit la connexion à Redis"""
        try:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await self._client.ping()
            self._connected = True
            logger.info("Connexion à Redis établie avec succès")
        except Exception as e:
            logger.error(f"Erreur de connexion à Redis: {e}")
            self._connected = False
    
    async def ensure_connection(self) -> bool:
        """S'assure qu'une connexion Redis est disponible (tentative de reconnexion si nécessaire)"""
        if self._connected:
            return True
        
        async with self._connect_lock:
            if self._connected:
                return True
            await self.connect()
            return self._connected
    
    async def disconnect(self):
        """Ferme la connexion Redis"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Connexion Redis fermée")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def health_check(self) -> bool:
        """Vérifie l'état de Redis"""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False
    
    @staticmethod
    def hash_question(question: str) -> str:
        """Génère un hash SHA256 de la question normalisée"""
        normalized = question.lower().strip()
        # Supprime les caractères spéciaux et espaces multiples
        normalized = ' '.join(normalized.split())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    # ============ Cache des réponses ============
    
    async def get_cached_response(self, question: str) -> Optional[Dict[str, Any]]:
        """Récupère une réponse en cache"""
        if not await self.ensure_connection():
            return None
        
        try:
            question_hash = self.hash_question(question)
            key = f"response:{question_hash}"
            
            data = await self._client.get(key)
            if data:
                # Incrémenter le compteur de hits
                await self._client.incr(f"hits:{question_hash}")
                logger.debug(f"Cache HIT pour question hash: {question_hash[:16]}...")
                return json.loads(data)
            
            logger.debug(f"Cache MISS pour question hash: {question_hash[:16]}...")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache: {e}")
            return None
    
    async def set_cached_response(
        self, 
        question: str, 
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Stocke une réponse en cache"""
        if not await self.ensure_connection():
            return
        
        try:
            question_hash = self.hash_question(question)
            key = f"response:{question_hash}"
            ttl = ttl or settings.CACHE_TTL
            
            await self._client.setex(
                key,
                ttl,
                json.dumps(response, default=str, ensure_ascii=False)
            )
            logger.debug(f"Réponse mise en cache: {question_hash[:16]}... (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache: {e}")
    
    async def invalidate_cache(self, question: str):
        """Invalide le cache pour une question"""
        if not await self.ensure_connection():
            return
        
        try:
            question_hash = self.hash_question(question)
            key = f"response:{question_hash}"
            await self._client.delete(key)
            logger.debug(f"Cache invalidé: {question_hash[:16]}...")
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache: {e}")
    
    async def clear_all_cache(self):
        """Vide tout le cache des réponses"""
        if not await self.ensure_connection():
            return
        
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match="response:*", count=100)
                if keys:
                    await self._client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            logger.info(f"Cache vidé: {deleted} entrées supprimées")
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {e}")
    
    # ============ Sessions utilisateur ============
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les données de session"""
        if not await self.ensure_connection():
            return None
        
        try:
            key = f"session:{session_id}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de session: {e}")
            return None
    
    async def set_session(
        self, 
        session_id: str, 
        data: Dict[str, Any],
        ttl: int = 86400  # 24 heures par défaut
    ):
        """Stocke les données de session"""
        if not await self.ensure_connection():
            return
        
        try:
            key = f"session:{session_id}"
            await self._client.setex(
                key,
                ttl,
                json.dumps(data, default=str, ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"Erreur lors du stockage de session: {e}")
    
    async def update_session_history(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        max_history: int = 12  # Augmenté pour meilleur contexte de conversation
    ):
        """Ajoute un message à l'historique de session"""
        if not await self.ensure_connection():
            return
        
        try:
            key = f"history:{session_id}"
            message = json.dumps({
                "role": role,
                "content": content
            }, ensure_ascii=False)
            
            await self._client.rpush(key, message)
            await self._client.ltrim(key, -max_history * 2, -1)  # Garde les derniers messages
            await self._client.expire(key, 86400)  # 24h TTL
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'historique: {e}")
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """Récupère l'historique de conversation"""
        if not await self.ensure_connection():
            return []
        
        try:
            key = f"history:{session_id}"
            messages = await self._client.lrange(key, 0, -1)
            result = [json.loads(m) for m in messages]
            logger.info(f"DEBUG: get_session_history for {session_id} returning = {result}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    # ============ Rate limiting ============
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int = None,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Vérifie le rate limit pour un identifiant
        Retourne (autorisé, requêtes restantes)
        """
        if not await self.ensure_connection():
            return True, limit or settings.RATE_LIMIT_PER_MINUTE
        
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        
        try:
            key = f"ratelimit:{identifier}"
            current = await self._client.get(key)
            
            if current is None:
                await self._client.setex(key, window, 1)
                return True, limit - 1
            
            count = int(current)
            if count >= limit:
                ttl = await self._client.ttl(key)
                return False, 0
            
            await self._client.incr(key)
            return True, limit - count - 1
            
        except Exception as e:
            logger.error(f"Erreur rate limiting: {e}")
            return True, limit
    
    # ============ Statistiques ============
    
    async def increment_stat(self, stat_name: str, amount: int = 1):
        """Incrémente un compteur de statistiques"""
        if not await self.ensure_connection():
            return
        
        try:
            key = f"stat:{stat_name}"
            await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erreur statistiques: {e}")
    
    async def get_stats(self) -> Dict[str, int]:
        """Récupère toutes les statistiques"""
        if not await self.ensure_connection():
            return {}
        
        try:
            stats = {}
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match="stat:*", count=100)
                for key in keys:
                    stat_name = key.replace("stat:", "")
                    value = await self._client.get(key)
                    stats[stat_name] = int(value) if value else 0
                if cursor == 0:
                    break
            return stats
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {}
    
    # ============ Questions populaires ============
    
    async def track_question(self, question: str, category: str = None):
        """Enregistre une question pour les statistiques"""
        if not await self.ensure_connection():
            return
        
        try:
            # Incrémente le compteur global
            await self._client.incr("stat:total_questions")
            
            # Track catégorie
            if category:
                await self._client.hincrby("stat:categories", category, 1)
            
            # Track questions fréquentes
            question_hash = self.hash_question(question)
            await self._client.zincrby("popular_questions", 1, question_hash)
            
            # Stocke le mapping hash -> question
            await self._client.hset("question_mapping", question_hash, question)
            
        except Exception as e:
            logger.error(f"Erreur tracking question: {e}")
    
    async def get_popular_questions(self, limit: int = 10) -> List[str]:
        """Récupère les questions les plus populaires"""
        if not await self.ensure_connection():
            return []
        
        try:
            # Top N questions par score
            top_hashes = await self._client.zrevrange("popular_questions", 0, limit - 1)
            
            questions = []
            for hash_val in top_hashes:
                question = await self._client.hget("question_mapping", hash_val)
                if question:
                    questions.append(question)
            
            return questions
        except Exception as e:
            logger.error(f"Erreur récupération questions populaires: {e}")
            return []
    
    async def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de conversation récent pour une session
        Retourne les derniers échanges question-réponse
        """
        try:
            if not await self.ensure_connection():
                return []
            
            # Utilise la méthode existante mais avec une limite
            history = await self.get_session_history(session_id)
            
            # Reformate pour une utilisation conversationnelle
            conversation = []
            for i in range(0, min(len(history), limit * 2), 2):
                if i + 1 < len(history):
                    conversation.append({
                        "question": history[i].get("content", ""),
                        "answer": history[i + 1].get("content", ""),
                        "timestamp": history[i].get("timestamp")
                    })
            
            return list(reversed(conversation))  # Plus récent en premier
            
        except Exception as e:
            logger.error(f"Erreur récupération historique conversation: {e}")
            return []
    
    async def save_conversation_turn(self, session_id: str, question: str, answer: str) -> bool:
        """
        Sauvegarde un échange question-réponse dans l'historique de conversation
        """
        try:
            # Utilise la méthode existante avec les bons paramètres (session_id, role, content)
            await self.update_session_history(session_id, "user", question)
            await self.update_session_history(session_id, "assistant", answer)
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde conversation: {e}")
            return False
    
    async def clear_conversation_history(self, session_id: str) -> bool:
        """
        Efface l'historique de conversation pour une session
        """
        try:
            if not await self.ensure_connection():
                return False
            
            # Efface l'historique de session
            key = f"session_history:{session_id}"
            await self._client.delete(key)
            
            logger.info(f"Historique conversation effacé pour session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur effacement historique: {e}")
            return False
    
    def _is_follow_up_question(self, question: str, history: List[Dict[str, Any]]) -> bool:
        """
        Détermine si une question est une question de suivi basée sur l'historique
        """
        if not history or len(history) == 0:
            return False
        
        question_lower = question.lower().strip()
        
        # Indicateurs de questions de suivi
        follow_up_indicators = [
            "et", "aussi", "également", "de plus", "autre",
            "comment", "pourquoi", "qu'est-ce que", "que se passe",
            "dans ce cas", "si", "mais", "cependant", "par contre",
            "plus de détails", "expliquez", "précisez", "exemple",
            "c'est quoi", "ça veut dire quoi", "par exemple"
        ]
        
        # Pronoms et références contextuelles
        contextual_words = ["cela", "ça", "ceci", "il", "elle", "ils", "elles"]
        
        # Vérification des indicateurs
        has_indicators = any(indicator in question_lower for indicator in follow_up_indicators)
        has_context_refs = any(word in question_lower for word in contextual_words)
        
        return has_indicators or has_context_refs


# Instance singleton
redis_cache = RedisCache()


async def get_cache() -> RedisCache:
    """Dependency pour obtenir le cache Redis"""
    return redis_cache
