"""
Modèles Pydantic pour les schémas de requêtes et réponses
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LLMProvider(str, Enum):
    """Fournisseurs LLM supportés"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


class QuestionCategory(str, Enum):
    """Catégories de questions"""
    DEFINITIONS_GENERALES = "definitions_generales"
    RECRUTEMENT = "recrutement"
    DROITS_AGENTS = "droits_agents"
    OBLIGATIONS_AGENTS = "obligations_agents"
    CONGES = "conges"
    DISCIPLINE_SANCTIONS = "discipline_sanctions"
    RECOMPENSES = "recompenses"
    REMUNERATION = "remuneration"
    CARRIERE_AVANCEMENT = "carriere_avancement"
    POSITIONS_ADMINISTRATIVES = "positions_administratives"
    CESSATION_SERVICE = "cessation_service"
    CONTRACTUELS = "contractuels"
    AUTRE = "autre"


# ============ Requêtes ============

class QuestionRequest(BaseModel):
    """Requête pour poser une question"""
    question: str = Field(
        ..., 
        min_length=5, 
        max_length=500,
        description="La question à poser sur la loi L0027",
        examples=["Quel est l'âge de la retraite pour un fonctionnaire ?"]
    )
    session_id: Optional[str] = Field(
        default=None, 
        description="ID de session pour le suivi des conversations"
    )
    llm_provider: Optional[LLMProvider] = Field(
        default=None,
        description="Fournisseur LLM à utiliser (openai, anthropic, deepseek)"
    )
    include_suggestions: bool = Field(
        default=True,
        description="Inclure des suggestions de questions"
    )
    
    @field_validator('question')
    @classmethod
    def clean_question(cls, v: str) -> str:
        return v.strip()


class FeedbackRequest(BaseModel):
    """Requête pour soumettre un feedback"""
    response_id: str = Field(..., description="ID de la réponse évaluée")
    rating: int = Field(..., ge=1, le=5, description="Note de 1 à 5")
    comment: Optional[str] = Field(default=None, max_length=500)
    helpful: bool = Field(default=True)


class SearchRequest(BaseModel):
    """Requête de recherche dans les articles"""
    query: str = Field(..., min_length=3, max_length=200)
    limit: int = Field(default=10, ge=1, le=50)
    category: Optional[QuestionCategory] = None


# ============ Réponses ============

class ArticleReference(BaseModel):
    """Référence à un article de la loi"""
    numero: int = Field(..., description="Numéro de l'article")
    contenu: str = Field(..., description="Contenu de l'article")
    theme_principal: Optional[str] = None
    score: Optional[float] = Field(None, description="Score de pertinence")


class SuggestedQuestion(BaseModel):
    """Question suggérée"""
    question: str
    category: Optional[str] = None


class AnswerResponse(BaseModel):
    """Réponse à une question"""
    response_id: str = Field(..., description="ID unique de la réponse")
    question: str = Field(..., description="Question posée")
    answer: str = Field(..., description="Réponse générée")
    articles_references: List[ArticleReference] = Field(
        default_factory=list,
        description="Articles de loi référencés"
    )
    suggested_questions: List[SuggestedQuestion] = Field(
        default_factory=list,
        description="Questions suggérées"
    )
    confidence_score: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Score de confiance de la réponse"
    )
    llm_provider: str = Field(..., description="LLM utilisé")
    processing_time_ms: int = Field(..., description="Temps de traitement en ms")
    cached: bool = Field(default=False, description="Réponse depuis le cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(BaseModel):
    """Message dans une conversation"""
    role: str = Field(..., description="Role: user ou assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Historique de conversation"""
    session_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ArticleDetail(BaseModel):
    """Détail complet d'un article"""
    numero: int
    contenu: str
    theme_principal: str
    themes_secondaires: List[str] = Field(default_factory=list)
    mots_cles: List[str] = Field(default_factory=list)
    entites_concernees: List[str] = Field(default_factory=list)
    type_disposition: Optional[str] = None
    valeurs_numeriques: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Résultat de recherche"""
    articles: List[ArticleDetail]
    total_count: int
    query: str


class StatsResponse(BaseModel):
    """Statistiques du système"""
    total_questions: int
    total_articles: int
    avg_response_time_ms: float
    cache_hit_rate: float
    popular_categories: Dict[str, int]
    uptime_seconds: float


class HealthResponse(BaseModel):
    """État de santé du système"""
    status: str
    version: str
    database: bool
    redis: bool
    qdrant: bool
    llm_providers: Dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============ Documents de la loi ============

class LawDocument(BaseModel):
    """Document de la loi"""
    identifiant: str
    titre_complet: str
    titre_court: str
    date_promulgation: str
    pays: str
    autorite_emettrice: str
    total_articles: int


class LawStructure(BaseModel):
    """Structure de la loi (titres)"""
    numero: int
    intitule: str
    articles: List[int]


class LawInfoResponse(BaseModel):
    """Informations sur la loi"""
    document: LawDocument
    structure: List[LawStructure]
    categories_qa: List[str]
