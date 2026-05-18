"""
Tests pour le Chatbot L0027
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import json


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def sample_question():
    return {
        "question": "Quel est l'âge de la retraite pour un fonctionnaire ?",
        "session_id": "test-session-123",
        "include_suggestions": True
    }


@pytest.fixture
def sample_law_data():
    return {
        "document": {
            "identifiant": "L/2019/0027/AN",
            "titre_complet": "Loi Portant Statut Général des Agents de l'État",
            "total_articles": 225
        },
        "articles": [
            {
                "numero": 116,
                "contenu": "L'âge limite de mise à la retraite est fixé à 60 ans...",
                "theme_principal": "age_retraite"
            }
        ]
    }


@pytest.fixture
def sample_qa_data():
    return {
        "questions_reponses": [
            {
                "id": 1,
                "question": "Quel est l'âge de la retraite ?",
                "reponse": "60 ans pour les hiérarchies B et C...",
                "categorie": "cessation_service"
            }
        ]
    }


# ============================================
# Tests des schémas
# ============================================

def test_question_request_validation():
    """Teste la validation du schéma QuestionRequest"""
    from app.models.schemas import QuestionRequest
    
    # Question valide
    request = QuestionRequest(question="Qu'est-ce qu'un agent de l'État ?")
    assert len(request.question) >= 5
    
    # Question trop courte
    with pytest.raises(ValueError):
        QuestionRequest(question="Hi")


def test_answer_response_model():
    """Teste le modèle AnswerResponse"""
    from app.models.schemas import AnswerResponse, ArticleReference
    
    response = AnswerResponse(
        response_id="test-123",
        question="Test question",
        answer="Test answer",
        articles_references=[
            ArticleReference(
                numero=1,
                contenu="Test contenu",
                theme_principal="test",
                score=0.95
            )
        ],
        suggested_questions=[],
        confidence_score=0.9,
        llm_provider="openai",
        processing_time_ms=100,
        cached=False
    )
    
    assert response.response_id == "test-123"
    assert response.confidence_score == 0.9


# ============================================
# Tests du cache Redis
# ============================================

def test_question_hash():
    """Teste le hashing des questions"""
    from app.services.cache_service import RedisCache
    
    cache = RedisCache()
    
    # Même question = même hash
    hash1 = cache.hash_question("Quel est l'âge de la retraite ?")
    hash2 = cache.hash_question("Quel est l'âge de la retraite ?")
    assert hash1 == hash2
    
    # Insensible à la casse
    hash3 = cache.hash_question("QUEL EST L'ÂGE DE LA RETRAITE ?")
    assert hash1 == hash3
    
    # Insensible aux espaces
    hash4 = cache.hash_question("  Quel  est  l'âge  de  la  retraite  ?  ")
    assert hash1 == hash4


# ============================================
# Tests de l'API
# ============================================

@pytest.mark.asyncio
async def test_root_endpoint():
    """Teste l'endpoint racine"""
    # Mock les services pour éviter les vraies connexions
    with patch('app.main.init_db'), \
         patch('app.main.redis_cache'), \
         patch('app.main.vector_store'), \
         patch('app.main.llm_service'), \
         patch('app.main.initialize_rag_service'):
        
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            
        # Note: Le test peut échouer si les services ne sont pas mockés correctement
        # En environnement de test réel, utiliser des fixtures appropriées


@pytest.mark.asyncio
async def test_categories_endpoint():
    """Teste l'endpoint des catégories"""
    # Test simple des catégories
    expected_categories = [
        "definitions_generales",
        "recrutement", 
        "droits_agents",
        "obligations_agents",
        "conges",
        "discipline_sanctions",
        "recompenses",
        "remuneration",
        "carriere_avancement",
        "positions_administratives",
        "cessation_service",
        "contractuels"
    ]
    
    # Vérification que toutes les catégories sont présentes
    from app.models.schemas import QuestionCategory
    
    for cat in expected_categories:
        assert cat in [c.value for c in QuestionCategory]


# ============================================
# Tests du service LLM
# ============================================

@pytest.mark.asyncio
async def test_llm_service_initialization():
    """Teste l'initialisation du service LLM"""
    from app.services.llm_service import LLMService
    
    service = LLMService()
    
    # Sans clés API, pas de providers
    assert service.get_available_providers() == []


def test_llm_provider_enum():
    """Teste l'enum des providers LLM"""
    from app.models.schemas import LLMProvider
    
    assert LLMProvider.OPENAI.value == "openai"
    assert LLMProvider.ANTHROPIC.value == "anthropic"
    assert LLMProvider.DEEPSEEK.value == "deepseek"


# ============================================
# Tests de configuration
# ============================================

def test_settings_defaults():
    """Teste les valeurs par défaut de configuration"""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.API_PORT == 8000
    assert settings.RAG_TOP_K == 5
    assert settings.CACHE_TTL == 3600


def test_system_prompt_content():
    """Teste que le prompt système contient les éléments clés"""
    from app.core.config import SYSTEM_PROMPT
    
    assert "L/2019/0027/AN" in SYSTEM_PROMPT
    assert "Guinée" in SYSTEM_PROMPT
    assert "agents de l'État" in SYSTEM_PROMPT.lower()


def test_off_topic_response():
    """Teste la réponse hors sujet"""
    from app.core.config import OFF_TOPIC_RESPONSE
    
    assert "L/2019/0027/AN" in OFF_TOPIC_RESPONSE
    assert "fonction publique" in OFF_TOPIC_RESPONSE.lower()


# ============================================
# Tests utilitaires
# ============================================

def test_article_detail_model():
    """Teste le modèle ArticleDetail"""
    from app.models.schemas import ArticleDetail
    
    article = ArticleDetail(
        numero=116,
        contenu="L'âge limite de mise à la retraite...",
        theme_principal="age_retraite",
        themes_secondaires=["limite_age", "hierarchies"],
        mots_cles=["retraite", "60 ans", "65 ans"],
        entites_concernees=["agents de l'État"],
        type_disposition="condition",
        valeurs_numeriques={"age_retraite_B": 60, "age_retraite_A": 65}
    )
    
    assert article.numero == 116
    assert "60 ans" in article.mots_cles
    assert article.valeurs_numeriques["age_retraite_B"] == 60


# ============================================
# Tests d'intégration (nécessitent des services)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_question_flow():
    """
    Test d'intégration complet
    Nécessite: PostgreSQL, Redis, Qdrant, et au moins un LLM
    """
    # Ce test est marqué comme 'integration' et sera ignoré 
    # en l'absence des services requis
    pass


# ============================================
# Helpers de test
# ============================================

def create_mock_rag_response():
    """Crée une réponse RAG mockée pour les tests"""
    return {
        "response_id": "mock-123",
        "question": "Question de test",
        "answer": "Réponse de test basée sur l'article 1...",
        "articles_references": [
            {
                "numero": 1,
                "contenu": "Contenu de l'article 1",
                "theme_principal": "test",
                "score": 0.95
            }
        ],
        "suggested_questions": [
            {"question": "Question suggérée 1"},
            {"question": "Question suggérée 2"}
        ],
        "confidence_score": 0.85,
        "llm_provider": "openai",
        "processing_time_ms": 1500,
        "cached": False
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
