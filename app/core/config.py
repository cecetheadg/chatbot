"""
Configuration centralisée du Chatbot L0027
Statut Général des Agents de l'État - République de Guinée
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # Application
    APP_NAME: str = "Chatbot L0027 - Statut des Agents de l'État"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Assistant IA pour la loi L/2019/0027/AN - Statut Général des Agents de l'État de Guinée"
    DEBUG: bool = Field(default=False)
    
    # API
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_PREFIX: str = "/api/v1"
    
    # Base de données PostgreSQL
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="chatbot_user")
    POSTGRES_PASSWORD: str = Field(default="chatbot_password")
    POSTGRES_DB: str = Field(default="chatbot_l0027")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    CACHE_TTL: int = Field(default=3600)  # 1 heure
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Qdrant (Vector DB)
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION: str = Field(default="loi_l0027")
    VECTOR_SIZE: int = Field(default=1536)  # OpenAI embeddings dimension
    
    # LLM Providers
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    
    # Anthropic (Claude)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    CLAUDE_MODEL: str = Field(default="claude-sonnet-4-20250514")
    
    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None)
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com")
    
    # LLM par défaut
    DEFAULT_LLM_PROVIDER: str = Field(default="openai")  # openai, anthropic, deepseek
    
    # RAG Configuration
    RAG_TOP_K: int = Field(default=5)
    RAG_SCORE_THRESHOLD: float = Field(default=0.7)
    MAX_CONTEXT_LENGTH: int = Field(default=4000)
    
    # Limites
    MAX_QUESTION_LENGTH: int = Field(default=500)
    MAX_RESPONSE_LENGTH: int = Field(default=2000)
    RATE_LIMIT_PER_MINUTE: int = Field(default=300)  # Increased for high traffic
    
    # Database Connection Pooling (High Performance)
    DB_POOL_SIZE: int = Field(default=50)  # Connection pool size
    DB_MAX_OVERFLOW: int = Field(default=100)  # Max overflow connections
    DB_POOL_RECYCLE: int = Field(default=3600)  # Recycle connections after 1 hour
    DB_POOL_TIMEOUT: int = Field(default=30)  # Timeout for getting connection
    
    # Redis Connection Pool
    REDIS_MAX_CONNECTIONS: int = Field(default=100)  # Max Redis connections
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)  # Socket timeout in seconds
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)  # Connection timeout
    
    # Caching Configuration (Aggressive for performance)
    CACHE_TTL: int = Field(default=3600)  # 1 hour default
    CACHE_TTL_SHORT: int = Field(default=300)  # 5 minutes for frequent queries
    CACHE_TTL_LONG: int = Field(default=86400)  # 24 hours for static content
    
    # Request Timeout
    REQUEST_TIMEOUT: int = Field(default=60)  # 60 seconds max request time
    KEEP_ALIVE_TIMEOUT: int = Field(default=65)  # Keep-alive timeout
    
    # Chemins des données
    DATA_DIR: str = Field(default="./data")
    LAW_FILE: str = Field(default="loi_L0027_enrichie.json")
    QA_FILE: str = Field(default="qa_entrainement_L0027.json")
    
    # ========================================================================
    # CORS ET IFRAME CONFIGURATION
    # ========================================================================
    
    # CORS Configuration (pour les requêtes API: fetch, XHR)
    CORS_ORIGINS: List[str] = Field(
        default=[
            "https://chatbot.dfgp.fonctionpublique.gov.gn", 
            "https://dgfp.fonctionpublique.gov.gn",
            "https://www.dgfp.fonctionpublique.gov.gn",
            "https://www.chatbot.dfgp.fonctionpublique.gov.gn",
            "https://mmafp.cloud",
            "https://www.mmafp.cloud",
            "https://chatbot.mmafp.cloud",
            "https://fomba.mmafp.cloud"

        ],
        description="List of allowed CORS origins for API requests"
    )
    
    # Frame Ancestors Configuration (pour l'embedding en iframe)
    FRAME_ANCESTORS: List[str] = Field(
        default=[
            "https://chatbot.dfgp.fonctionpublique.gov.gn", 
            "https://dgfp.fonctionpublique.gov.gn",
            "https://www.dgfp.fonctionpublique.gov.gn",
            "https://www.chatbot.dfgp.fonctionpublique.gov.gn",
            "https://mmafp.cloud",
            "https://www.mmafp.cloud",
            "https://chatbot.mmafp.cloud",
            "https://fomba.mmafp.cloud"
        ],
        description="List of domains allowed to embed the chatbot in iframe (CSP frame-ancestors)"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """
        Retourne les origines CORS autorisées pour les requêtes API.
        En mode DEBUG, autorise toutes les origines (*).
        """
        if self.DEBUG:
            return ["*"]
        return self.CORS_ORIGINS
    
    @property
    def frame_ancestors(self) -> List[str]:
        """
        Retourne les domaines autorisés pour afficher le chatbot en iframe.
        Utilisé par le middleware FrameOptionsMiddleware pour configurer
        l'en-tête Content-Security-Policy: frame-ancestors.
        
        Note: En mode DEBUG, localhost est automatiquement ajouté par le middleware.
        """
        return self.FRAME_ANCESTORS
    
    # ========================================================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance singleton des paramètres"""
    return Settings()


# Instructions système pour le chatbot
SYSTEM_PROMPT = """Tu es Fomba, un assistant juridique professionnel spécialisé dans la fonction publique guinéenne et expert de la Loi L/2019/0027/AN portant Statut Général des Agents de l'État.

🎯 **TON RÔLE ÉLARGI**
- Expert principal: Loi L/2019/0027/AN (Statut des Agents de l'État)
- Expert secondaire: Fonction publique guinéenne en général
- Conseiller professionnel: Questions RH et administratives connexes
- Conversationnel: Capable de tenir une discussion professionnelle naturelle

📚 **TES COMPÉTENCES PRINCIPALES**
- Expliquer les articles de L0027 avec précision
- Contextualiser dans la fonction publique guinéenne
- Maintenir une conversation professionnelle fluide
- Orienter vers L0027 quand pertinent
- Reconnaître et répondre aux questions de suivi
- Relier naturellement les sujets généraux aux dispositions légales

🗣️ **STYLE CONVERSATIONNEL**
- Professionnel mais accessible et chaleureux
- Utilise le contexte de la conversation précédente
- Relie intelligemment les sujets à L0027
- Pose des questions de clarification si nécessaire
- Maintient le fil de la discussion
- Comprend les références ("cela", "ça", "dans ce cas")
- Accepte les salutations et politesse professionnelle

⚖️ **TES PRINCIPES CONVERSATIONNELS**
1. **Intelligence contextuelle** : Utilise l'historique pour mieux comprendre
2. **Précision juridique** : Cite les articles L0027 quand applicable
3. **Flexibilité professionnelle** : Accepte les questions connexes
4. **Guidance douce** : Oriente vers L0027 de manière naturelle
5. **Continuité** : Maintiens la cohérence dans la conversation

❌ **LIMITES CLAIRES**
- Évite les sujets non professionnels/juridiques/administratifs
- Redirige avec tact vers la fonction publique guinéenne
- Reste factuel et basé sur la loi L0027
- Ne remplace pas une consultation juridique personnalisée

📋 **APPROCHE CONVERSATIONNELLE**
- Comprend que certaines questions sont des suites logiques
- Accepte les demandes de clarification et d'exemples
- Relie les questions générales aux articles spécifiques de L0027
- Maintient un ton professionnel mais humain

🇬🇳 Tu es au service de l'excellence de la fonction publique guinéenne avec une approche moderne et conversationnelle."""


SUGGESTION_PROMPT = """En te basant sur la question de l'utilisateur et le contexte de la conversation, propose 3 questions pertinentes et complémentaires que l'utilisateur pourrait vouloir poser ensuite.

Les questions doivent :
1. Être en rapport avec le sujet abordé
2. Approfondir ou compléter la réponse donnée
3. Aider l'utilisateur à mieux comprendre ses droits/obligations

Format de réponse : Liste de 3 questions courtes et claires."""


OFF_TOPIC_RESPONSE = """Je comprends votre question, mais mon expertise se concentre sur la fonction publique guinéenne et particulièrement la **Loi L/2019/0027/AN** portant **Statut Général des Agents de l'État**.

Puis-je vous aider à reformuler votre question dans ce contexte ? Par exemple, si cela concerne :

**📋 Administration et RH :**
- Les droits et obligations des fonctionnaires
- Les procédures de recrutement ou d'avancement  
- Les questions de carrière ou de rémunération

**⚖️ Aspects juridiques :**
- Le régime disciplinaire ou les congés
- Les positions administratives (détachement, disponibilité)
- La retraite et la cessation de service

**🤝 Statuts professionnels :**
- Les différences entre fonctionnaires et contractuels
- Les conditions d'accès à la fonction publique

Y a-t-il un aspect spécifique de la fonction publique guinéenne qui vous intéresse ? Je suis là pour vous accompagner dans la compréhension de vos droits et obligations professionnels."""