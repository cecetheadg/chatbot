"""
Routes API pour le chatbot L0027
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
import time

from app.core.config import get_settings
from app.models.schemas import (
    QuestionRequest, AnswerResponse, FeedbackRequest,
    SearchRequest, SearchResult, ArticleDetail,
    LawInfoResponse, StatsResponse, HealthResponse,
    ErrorResponse, SuggestedQuestion, QuestionCategory
)
from app.services.rag_service import RAGService, get_rag_service
from app.services.cache_service import RedisCache, get_cache
from app.db.database import AsyncSession, get_db

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ============ Endpoints principaux ============

@router.post(
    "/ask",
    response_model=AnswerResponse,
    summary="Poser une question sur la loi L0027",
    description="Endpoint principal pour poser une question sur le Statut Général des Agents de l'État"
)
async def ask_question(
    request: QuestionRequest,
    rag: RAGService = Depends(get_rag_service),
    cache: RedisCache = Depends(get_cache)
):
    """
    Traite une question sur la loi L/2019/0027/AN
    
    - **question**: La question à poser (5-500 caractères)
    - **session_id**: ID de session optionnel pour le suivi de conversation
    - **llm_provider**: Choix du LLM (openai, anthropic, deepseek)
    - **include_suggestions**: Inclure des suggestions de questions (défaut: true)
    """
    try:
        # Rate limiting
        identifier = request.session_id or "anonymous"
        allowed, remaining = await cache.check_rate_limit(identifier)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Limite de requêtes atteinte. Réessayez dans quelques instants."
            )
        
        # Traitement de la question
        response = await rag.process_question(
            question=request.question,
            session_id=request.session_id,
            provider_name=request.llm_provider.value if request.llm_provider else None,
            include_suggestions=request.include_suggestions
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur traitement question: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@router.post(
    "/feedback",
    summary="Soumettre un feedback sur une réponse",
    description="Permet aux utilisateurs de noter une réponse du chatbot"
)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Soumet un feedback sur une réponse
    
    - **response_id**: ID de la réponse à évaluer
    - **rating**: Note de 1 à 5
    - **comment**: Commentaire optionnel
    - **helpful**: La réponse était-elle utile ?
    """
    try:
        # TODO: Enregistrer le feedback en base
        logger.info(f"Feedback reçu: response_id={request.response_id}, rating={request.rating}")
        return {"status": "success", "message": "Merci pour votre feedback !"}
    except Exception as e:
        logger.error(f"Erreur feedback: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement du feedback")


# ============ Recherche ============

@router.get(
    "/search/articles",
    response_model=SearchResult,
    summary="Rechercher dans les articles de la loi",
    description="Recherche sémantique dans les articles de la loi L0027"
)
async def search_articles(
    query: str = Query(..., min_length=3, max_length=200, description="Termes de recherche"),
    limit: int = Query(default=10, ge=1, le=50, description="Nombre maximum de résultats"),
    rag: RAGService = Depends(get_rag_service)
):
    """
    Recherche dans les articles de la loi
    
    - **query**: Termes de recherche (3-200 caractères)
    - **limit**: Nombre de résultats (1-50, défaut: 10)
    """
    try:
        results = await rag.search_articles(query, limit=limit)
        
        articles = [
            ArticleDetail(
                numero=art.get("numero", 0),
                contenu=art.get("contenu", ""),
                theme_principal=art.get("theme_principal", ""),
                themes_secondaires=art.get("themes_secondaires", []),
                mots_cles=art.get("mots_cles", []),
                entites_concernees=art.get("entites_concernees", []),
                type_disposition=art.get("type_disposition"),
                valeurs_numeriques=art.get("valeurs_numeriques")
            )
            for art in results
        ]
        
        return SearchResult(
            articles=articles,
            total_count=len(articles),
            query=query
        )
        
    except Exception as e:
        logger.error(f"Erreur recherche articles: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")


@router.get(
    "/articles/{numero}",
    response_model=ArticleDetail,
    summary="Récupérer un article par son numéro",
    description="Retourne le contenu détaillé d'un article de la loi"
)
async def get_article(
    numero: int,
    rag: RAGService = Depends(get_rag_service)
):
    """
    Récupère un article par son numéro
    
    - **numero**: Numéro de l'article (1-225)
    """
    article = rag.get_article_by_numero(numero)
    
    if not article:
        raise HTTPException(status_code=404, detail=f"Article {numero} non trouvé")
    
    return ArticleDetail(
        numero=article.get("numero", 0),
        contenu=article.get("contenu", ""),
        theme_principal=article.get("theme_principal", ""),
        themes_secondaires=article.get("themes_secondaires", []),
        mots_cles=article.get("mots_cles", []),
        entites_concernees=article.get("entites_concernees", []),
        type_disposition=article.get("type_disposition"),
        valeurs_numeriques=article.get("valeurs_numeriques")
    )


# ============ Suggestions ============

@router.get(
    "/suggestions/popular",
    response_model=List[str],
    summary="Questions les plus populaires",
    description="Retourne les questions les plus fréquemment posées"
)
async def get_popular_questions(
    limit: int = Query(default=10, ge=1, le=50),
    cache: RedisCache = Depends(get_cache)
):
    """Récupère les questions les plus populaires"""
    questions = await cache.get_popular_questions(limit)
    
    # Si pas assez de questions populaires, ajoute des questions par défaut
    if len(questions) < limit:
        defaults = [
            "Qu'est-ce qu'un agent de l'État ?",
            "Quelles sont les conditions pour être recruté dans la fonction publique ?",
            "Quel est l'âge de la retraite pour un fonctionnaire ?",
            "Quels sont les droits syndicaux des agents de l'État ?",
            "Comment se déroule l'avancement de grade ?",
            "Quelle est la durée du stage probatoire ?",
            "Quelles sont les sanctions disciplinaires possibles ?",
            "Comment fonctionne le congé annuel ?",
            "Qu'est-ce que la disponibilité ?",
            "Comment sont classés les fonctionnaires ?"
        ]
        for q in defaults:
            if q not in questions and len(questions) < limit:
                questions.append(q)
    
    return questions[:limit]


@router.get(
    "/suggestions/category/{category}",
    response_model=List[str],
    summary="Questions suggérées par catégorie",
    description="Retourne des questions suggérées pour une catégorie spécifique"
)
async def get_category_suggestions(
    category: QuestionCategory,
    limit: int = Query(default=5, ge=1, le=20),
    rag: RAGService = Depends(get_rag_service)
):
    """Récupère des suggestions de questions pour une catégorie"""
    suggestions = await rag.get_suggested_questions_for_category(
        category=category.value,
        limit=limit
    )
    return suggestions


@router.get(
    "/suggestions/starter",
    response_model=List[SuggestedQuestion],
    summary="Questions de démarrage",
    description="Retourne des questions pour démarrer une conversation"
)
async def get_starter_questions():
    """Retourne des questions de démarrage pour le chatbot"""
    starters = [
        SuggestedQuestion(
            question="Qu'est-ce qu'un agent de l'État selon la loi guinéenne ?",
            category="definitions_generales"
        ),
        SuggestedQuestion(
            question="Quelles sont les conditions pour être recruté dans la fonction publique ?",
            category="recrutement"
        ),
        SuggestedQuestion(
            question="Quels sont les droits fondamentaux des agents de l'État ?",
            category="droits_agents"
        ),
        SuggestedQuestion(
            question="Comment fonctionne l'avancement d'échelon et de grade ?",
            category="carriere_avancement"
        ),
        SuggestedQuestion(
            question="Quelles sont les positions administratives possibles ?",
            category="positions_administratives"
        ),
        SuggestedQuestion(
            question="Quel est l'âge de la retraite selon la hiérarchie ?",
            category="cessation_service"
        )
    ]
    return starters


# ============ Informations ============

@router.get(
    "/law/info",
    response_model=LawInfoResponse,
    summary="Informations sur la loi",
    description="Retourne les métadonnées et la structure de la loi L0027"
)
async def get_law_info(
    rag: RAGService = Depends(get_rag_service)
):
    """Récupère les informations générales sur la loi"""
    info = rag.get_law_info()
    
    if not info:
        raise HTTPException(status_code=500, detail="Données de la loi non chargées")
    
    return LawInfoResponse(
        document=info.get("document", {}),
        structure=[
            {
                "numero": t.get("numero", 0),
                "intitule": t.get("intitule", ""),
                "articles": t.get("articles", [])
            }
            for t in info.get("structure", [])
        ],
        categories_qa=[
            "definitions_generales", "recrutement", "droits_agents",
            "obligations_agents", "conges", "discipline_sanctions",
            "recompenses", "remuneration", "carriere_avancement",
            "positions_administratives", "cessation_service", "contractuels"
        ]
    )


@router.get(
    "/categories",
    response_model=List[dict],
    summary="Liste des catégories de questions",
    description="Retourne la liste des catégories de questions disponibles"
)
async def get_categories():
    """Liste des catégories avec descriptions"""
    return [
        {"id": "definitions_generales", "label": "Définitions générales", "icon": "📖"},
        {"id": "recrutement", "label": "Recrutement", "icon": "📋"},
        {"id": "droits_agents", "label": "Droits des agents", "icon": "⚖️"},
        {"id": "obligations_agents", "label": "Obligations des agents", "icon": "📜"},
        {"id": "conges", "label": "Congés et permissions", "icon": "🏖️"},
        {"id": "discipline_sanctions", "label": "Discipline et sanctions", "icon": "⚠️"},
        {"id": "recompenses", "label": "Récompenses", "icon": "🏆"},
        {"id": "remuneration", "label": "Rémunération", "icon": "💰"},
        {"id": "carriere_avancement", "label": "Carrière et avancement", "icon": "📈"},
        {"id": "positions_administratives", "label": "Positions administratives", "icon": "🔄"},
        {"id": "cessation_service", "label": "Cessation de service", "icon": "🚪"},
        {"id": "contractuels", "label": "Agents contractuels", "icon": "📝"}
    ]


# ============ Administration ============

@router.delete(
    "/cache/clear",
    summary="Vider le cache",
    description="Vide tout le cache des réponses (admin uniquement)"
)
async def clear_cache(
    cache: RedisCache = Depends(get_cache)
):
    """Vide le cache des réponses"""
    await cache.clear_all_cache()
    return {"status": "success", "message": "Cache vidé avec succès"}


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Statistiques du système",
    description="Retourne les statistiques d'utilisation du chatbot"
)
async def get_stats(
    cache: RedisCache = Depends(get_cache),
    rag: RAGService = Depends(get_rag_service)
):
    """Récupère les statistiques du système"""
    try:
        redis_stats = await cache.get_stats()
        
        return StatsResponse(
            total_questions=redis_stats.get("total_questions", 0),
            total_articles=225,
            avg_response_time_ms=redis_stats.get("avg_response_time", 0),
            cache_hit_rate=0.0,  # TODO: calculer
            popular_categories={},  # TODO: récupérer
            uptime_seconds=0  # TODO: calculer
        )
    except Exception as e:
        logger.error(f"Erreur stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération statistiques")
