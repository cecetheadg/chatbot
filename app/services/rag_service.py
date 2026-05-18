"""
Service RAG (Retrieval-Augmented Generation) - Orchestration principale
"""
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path

from app.core.config import get_settings, OFF_TOPIC_RESPONSE
from app.services.cache_service import RedisCache, redis_cache
from app.services.vector_service import VectorStore, vector_store
from app.services.llm_service import LLMService, llm_service
from app.models.schemas import (
    AnswerResponse, ArticleReference, SuggestedQuestion,
    QuestionCategory
)

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGService:
    """
    Service RAG pour le chatbot L0027
    Orchestre la recherche vectorielle, le cache et la génération LLM
    """
    
    def __init__(
        self,
        cache: RedisCache,
        vector_db: VectorStore,
        llm: LLMService
    ):
        self.cache = cache
        self.vector_db = vector_db
        self.llm = llm
        self._law_data: Optional[Dict] = None
        self._qa_data: Optional[Dict] = None
    
    async def initialize(self, law_path: str, qa_path: str):
        """Charge les données de la loi et Q&A"""
        try:
            # Charge la loi
            with open(law_path, 'r', encoding='utf-8') as f:
                self._law_data = json.load(f)
            logger.info(f"Loi chargée: {len(self._law_data.get('articles', []))} articles")
            
            # Charge les Q&A
            with open(qa_path, 'r', encoding='utf-8') as f:
                self._qa_data = json.load(f)
            logger.info(f"Q&A chargées: {len(self._qa_data.get('questions_reponses', []))} paires")
            
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            raise
    
    def get_law_info(self) -> Dict[str, Any]:
        """Retourne les informations sur la loi"""
        if not self._law_data:
            return {}
        return {
            "document": self._law_data.get("document", {}),
            "structure": self._law_data.get("structure", {}).get("titres", [])
        }
    
    def get_article_by_numero(self, numero: int) -> Optional[Dict[str, Any]]:
        """Récupère un article par son numéro"""
        if not self._law_data:
            return None
        
        for article in self._law_data.get("articles", []):
            if article.get("numero") == numero:
                return article
        return None
    
    async def process_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        include_suggestions: bool = True
    ) -> AnswerResponse:
        """
        Traite une question et génère une réponse
        Pipeline complet: Cache -> Relevance -> RAG -> LLM -> Cache
        """
        start_time = time.time()
        response_id = str(uuid.uuid4())
        provider_used = provider_name or settings.DEFAULT_LLM_PROVIDER
        
        # 0. Récupérer l'historique de conversation pour le contexte
        conversation_history = await self.cache.get_conversation_history(session_id or "anonymous", limit=3)
        is_follow_up = self.cache._is_follow_up_question(question, conversation_history)
        
        # Enrichir la question avec le contexte si c'est un suivi
        contextual_question = question
        if is_follow_up and conversation_history:
            last_exchange = conversation_history[0]  # Le plus récent
            contextual_question = f"Contexte: {last_exchange.get('question', '')[:100]} -> {last_exchange.get('answer', '')[:200]}\n\nQuestion actuelle: {question}"
            logger.info(f"Question de suivi détectée avec contexte pour: {question[:50]}...")
        
        # 1. Vérifie le cache
        cached = await self.cache.get_cached_response(question)
        if cached:
            logger.info(f"Réponse trouvée en cache pour: {question[:50]}...")
            processing_time = int((time.time() - start_time) * 1000)
            
            # Sauvegarder l'échange même pour les réponses en cache
            if session_id:
                await self.cache.save_conversation_turn(session_id, question, cached["answer"])
            
            return AnswerResponse(
                response_id=response_id,
                question=question,
                answer=cached["answer"],
                articles_references=[
                    ArticleReference(**art) for art in cached.get("articles", [])
                ],
                suggested_questions=[
                    SuggestedQuestion(question=q) for q in cached.get("suggestions", [])
                ],
                confidence_score=cached.get("confidence", 0.9),
                llm_provider=cached.get("provider", provider_used),
                processing_time_ms=processing_time,
                cached=True
            )
        
        # 2. Détecte les salutations (ne pas les traiter comme hors sujet)
        is_greeting = self._is_greeting(question)
        
        # 2.5. Détecte les demandes d'articles spécifiques
        article_requested = self._is_article_request(question)
        if article_requested:
            logger.info(f"Demande d'article spécifique détectée: Article {article_requested}")
            
            # Récupérer l'article
            article_data = self.get_article_by_numero(article_requested)
            
            if article_data:
                answer = self._format_article_response(article_data)
                
                # Suggestions d'articles connexes basées sur le thème
                suggestions = self._get_related_article_suggestions(article_data)
                
                # Créer la référence d'article
                article_ref = ArticleReference(
                    numero=article_requested,
                    contenu=article_data.get("contenu", ""),
                    theme_principal=article_data.get("theme_principal"),
                    score=1.0
                )
                
                # Sauvegarder l'échange dans l'historique
                if session_id:
                    await self.cache.save_conversation_turn(session_id, question, answer)
                
                processing_time = int((time.time() - start_time) * 1000)
                logger.info(f"Article {article_requested} retourné en {processing_time}ms")
                
                return AnswerResponse(
                    response_id=response_id,
                    question=question,
                    answer=answer,
                    articles_references=[article_ref],
                    suggested_questions=suggestions,
                    confidence_score=1.0,
                    llm_provider=provider_used,
                    processing_time_ms=processing_time,
                    cached=False
                )
            else:
                # Article non trouvé
                error_msg = f"L'article {article_requested} n'a pas été trouvé dans la loi L/2019/0027/AN. Cette loi comprend les articles 1 à 225."
                
                if session_id:
                    await self.cache.save_conversation_turn(session_id, question, error_msg)
                
                processing_time = int((time.time() - start_time) * 1000)
                
                return AnswerResponse(
                    response_id=response_id,
                    question=question,
                    answer=error_msg,
                    articles_references=[],
                    suggested_questions=self._get_starter_questions(),
                    confidence_score=1.0,
                    llm_provider=provider_used,
                    processing_time_ms=processing_time,
                    cached=False
                )
        
        # 3. Vérifie la pertinence de la question (sauf pour les salutations)
        if not is_greeting:
            is_relevant, relevance_score = await self.llm.classify_question_relevance(
                question, provider_name
            )
            
            if not is_relevant or relevance_score < 0.2:
                logger.info(f"Question hors sujet détectée: {question[:50]}...")
                processing_time = int((time.time() - start_time) * 1000)
                
                # Sauvegarder même les réponses hors sujet pour le contexte
                if session_id:
                    await self.cache.save_conversation_turn(session_id, question, OFF_TOPIC_RESPONSE)
                
                return AnswerResponse(
                    response_id=response_id,
                    question=question,
                    answer=OFF_TOPIC_RESPONSE,
                    articles_references=[],
                    suggested_questions=self._get_starter_questions(),
                    confidence_score=1.0,
                    llm_provider=provider_used,
                    processing_time_ms=processing_time,
                    cached=False
                )
        else:
            # Pour les salutations, on continue sans vérifier la pertinence
            is_relevant = True
            relevance_score = 1.0
            logger.info(f"Salutation détectée: {question[:50]}...")
        
        # 4. Crée l'embedding de la question (même pour les salutations)
        question_embedding = await self.llm.create_embedding(question)
        
        # 5. Recherche hybride (articles + Q&A) - sauf pour les salutations simples
        if is_greeting:
            # Pour les salutations, pas besoin de recherche vectorielle
            context = ""
            articles_refs = []
            search_results = {"articles": [], "qa_pairs": []}  # Initialiser pour éviter l'erreur
        else:
            search_results = await self.vector_db.hybrid_search(
                query_embedding=question_embedding,
                article_limit=settings.RAG_TOP_K,
                qa_limit=2
            )
            # Construit le contexte
            context, articles_refs = self._build_context(search_results)
        
        # 6. Génère la réponse avec le LLM
        conversation_history = []
        if session_id:
            conversation_history = await self.cache.get_session_history(session_id)
        
        answer = await self.llm.generate_response(
            question=question,
            context=context,
            provider_name=provider_name,
            conversation_history=conversation_history
        )
        
        # 6.5. Enrichir la réponse avec les citations d'articles automatiques
        enriched_answer, enriched_articles_refs = await self._enrich_response_with_citations(
            response_text=answer,
            existing_articles_refs=articles_refs
        )
        
        # Utiliser la réponse et références enrichies
        answer = enriched_answer
        articles_refs = enriched_articles_refs
        
        # 7. Génère les suggestions
        suggestions = []
        if include_suggestions:
            suggestion_texts = await self.llm.generate_suggestions(
                question=question,
                answer=answer,
                provider_name=provider_name
            )
            suggestions = [SuggestedQuestion(question=q) for q in suggestion_texts]
        
        # 8. Calcule le score de confiance
        confidence_score = self._calculate_confidence(search_results, relevance_score)
        
        # 9. Met en cache
        await self.cache.set_cached_response(
            question=question,
            response={
                "answer": answer,
                "articles": [art.model_dump() for art in articles_refs],
                "suggestions": [s.question for s in suggestions],
                "confidence": confidence_score,
                "provider": provider_used
            }
        )
        
        # 10. Enregistre dans l'historique de session
        if session_id:
            await self.cache.update_session_history(session_id, "user", question)
            await self.cache.update_session_history(session_id, "assistant", answer)
        
        # 11. Track pour les stats
        await self.cache.track_question(question)
        
        # 12. Sauvegarder l'échange dans l'historique de conversation
        if session_id:
            await self.cache.save_conversation_turn(session_id, question, answer)
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Question traitée en {processing_time}ms")
        
        return AnswerResponse(
            response_id=response_id,
            question=question,
            answer=answer,
            articles_references=articles_refs,
            suggested_questions=suggestions,
            confidence_score=confidence_score,
            llm_provider=provider_used,
            processing_time_ms=processing_time,
            cached=False
        )
    
    def _build_context(
        self,
        search_results: Dict[str, List[Dict]]
    ) -> Tuple[str, List[ArticleReference]]:
        """
        Construit le contexte RAG à partir des résultats de recherche
        """
        context_parts = []
        articles_refs = []
        seen_articles = set()
        
        # Ajoute les articles pertinents
        for result in search_results.get("articles", []):
            payload = result.get("payload", {})
            numero = payload.get("numero")
            
            if numero and numero not in seen_articles:
                seen_articles.add(numero)
                
                article_text = f"""**Article {numero}** ({payload.get('theme_principal', 'N/A')}):
{payload.get('contenu', '')}"""
                context_parts.append(article_text)
                
                articles_refs.append(ArticleReference(
                    numero=numero,
                    contenu=payload.get("contenu", ""),
                    theme_principal=payload.get("theme_principal"),
                    score=result.get("score", 0)
                ))
        
        # Ajoute les Q&A similaires comme référence
        qa_context = []
        for result in search_results.get("qa_pairs", []):
            payload = result.get("payload", {})
            if payload.get("question") and payload.get("reponse"):
                qa_context.append(f"""Q: {payload['question']}
R: {payload['reponse']}""")
        
        if qa_context:
            context_parts.append("\n**Exemples de réponses similaires:**\n" + "\n\n".join(qa_context))
        
        context = "\n\n".join(context_parts)
        
        # Tronque si trop long
        if len(context) > settings.MAX_CONTEXT_LENGTH:
            context = context[:settings.MAX_CONTEXT_LENGTH] + "..."
        
        return context, articles_refs
    
    def _calculate_confidence(
        self,
        search_results: Dict[str, List[Dict]],
        relevance_score: float
    ) -> float:
        """Calcule un score de confiance pour la réponse"""
        # Score basé sur la pertinence
        base_score = relevance_score * 0.4
        
        # Score basé sur les résultats de recherche
        articles = search_results.get("articles", [])
        if articles:
            avg_article_score = sum(r.get("score", 0) for r in articles) / len(articles)
            base_score += avg_article_score * 0.4
        
        # Bonus si des Q&A similaires ont été trouvées
        qa_pairs = search_results.get("qa_pairs", [])
        if qa_pairs:
            avg_qa_score = sum(r.get("score", 0) for r in qa_pairs) / len(qa_pairs)
            base_score += avg_qa_score * 0.2
        
        return min(max(base_score, 0.0), 1.0)
    
    def _is_greeting(self, question: str) -> bool:
        """Détecte si la question est une salutation"""
        greetings = [
            'bonjour', 'bonsoir', 'salut', 'bonne journée', 'bonne soirée',
            'bonne nuit', 'bon matin', 'coucou', 'hello', 'hi', 'hey',
            'bonjour monsieur', 'bonjour madame', 'bonsoir monsieur', 'bonsoir madame',
            'allô', 'allo', 'bonjour fomba', 'salut fomba', 'bonjour assistant',
            'bonjour chatbot', 'bonjour bot', 'bonjour monsieur', 'bonsoir monsieur'
        ]
        
        # Vérifie si la question commence par une salutation
        question_lower = question.lower().strip()
        for greeting in greetings:
            if question_lower.startswith(greeting) or question_lower == greeting:
                return True
        
        # Vérifie si c'est juste une salutation courte (moins de 30 caractères)
        if len(question_lower) < 30 and any(word in question_lower for word in ['bonjour', 'bonsoir', 'salut', 'hello', 'hi', 'coucou']):
            return True
        
        return False
    
    def _get_starter_questions(self) -> List[SuggestedQuestion]:
        """Questions de départ suggérées pour les questions hors sujet"""
        starters = [
            "Quelles sont les conditions pour être recruté dans la fonction publique ?",
            "Quel est l'âge de la retraite pour un fonctionnaire ?",
            "Quels sont les droits syndicaux des agents de l'État ?"
        ]
        return [SuggestedQuestion(question=q) for q in starters]
    
    async def search_articles(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recherche des articles par similarité"""
        embedding = await self.llm.create_embedding(query)
        results = await self.vector_db.search_articles(embedding, limit=limit)
        return [r.get("payload", {}) for r in results]
    
    async def get_popular_questions(self, limit: int = 10) -> List[str]:
        """Récupère les questions populaires"""
        return await self.cache.get_popular_questions(limit)
    
    async def get_suggested_questions_for_category(
        self,
        category: str,
        limit: int = 5
    ) -> List[str]:
        """Retourne des questions suggérées pour une catégorie"""
        if not self._qa_data:
            return []
        
        questions = [
            qa["question"]
            for qa in self._qa_data.get("questions_reponses", [])
            if qa.get("categorie") == category
        ]
        
        return questions[:limit]
    
    def _extract_mentioned_articles(self, response_text: str) -> List[int]:
        """
        Extrait tous les numéros d'articles mentionnés dans la réponse LLM
        Retourne une liste unique des numéros d'articles trouvés
        """
        import re
        
        if not response_text:
            return []
        
        mentioned_articles = set()
        
        # Patterns pour détecter les mentions d'articles dans les réponses
        patterns = [
            r"(?:selon|conformément à|d'après|en vertu de|aux termes de|comme le précise|comme stipule|tel que défini par)?\s*l['']?article\s*(\d+)",
            r"(?:selon|conformément à|d'après|en vertu de|aux termes de|comme le précise|comme stipule|tel que défini par)?\s*art(?:icle)?\s*\.?\s*(\d+)",
            r"(?:selon|conformément à|d'après|en vertu de|aux termes de|comme le précise|comme stipule|tel que défini par)?\s*l['']?art\s*\.?\s*(\d+)",
            r"l['']?article\s*n°?\s*(\d+)",
            r"l['']?art\s*\.?\s*n°?\s*(\d+)",
            r"article\s*numero\s*(\d+)",
            r"au\s*sens\s*de\s*l['']?article\s*(\d+)",
            r"prévoit\s*l['']?article\s*(\d+)",
            r"dispose\s*l['']?article\s*(\d+)"
        ]
        
        # Rechercher tous les patterns
        for pattern in patterns:
            matches = re.findall(pattern, response_text.lower())
            for match in matches:
                try:
                    article_num = int(match)
                    # Vérifier que l'article existe dans la loi (1 à 225)
                    if 1 <= article_num <= 225:
                        mentioned_articles.add(article_num)
                except ValueError:
                    continue
        
        return sorted(list(mentioned_articles))
    
    async def _enrich_response_with_citations(
        self, 
        response_text: str, 
        existing_articles_refs: List[ArticleReference]
    ) -> Tuple[str, List[ArticleReference]]:
        """
        Enrichit la réponse avec les citations complètes des articles mentionnés
        Retourne (réponse_enrichie, articles_references_complètes)
        """
        # Extraire les articles mentionnés dans la réponse
        mentioned_articles = self._extract_mentioned_articles(response_text)
        
        if not mentioned_articles:
            return response_text, existing_articles_refs
        
        # Récupérer les numéros déjà présents pour éviter les doublons
        existing_numbers = {ref.numero for ref in existing_articles_refs}
        
        # Traiter les nouveaux articles à citer
        new_articles_refs = []
        citations_to_add = []
        
        for article_num in mentioned_articles:
            if article_num not in existing_numbers:
                # Récupérer l'article depuis la base de données
                article_data = self.get_article_by_numero(article_num)
                
                if article_data:
                    # Créer la référence d'article
                    article_ref = ArticleReference(
                        numero=article_num,
                        contenu=article_data.get("contenu", ""),
                        theme_principal=article_data.get("theme_principal"),
                        score=1.0  # Score parfait car explicitement mentionné
                    )
                    new_articles_refs.append(article_ref)
                    
                    # Créer la citation formatée
                    citation = self._format_article_citation(article_data)
                    citations_to_add.append((article_num, citation))
        
        # Enrichir la réponse avec les citations si nécessaire
        enriched_response = response_text
        
        if citations_to_add:
            enriched_response += "\n\n---\n\n"
            enriched_response += "## 📋 **Articles Cités**\n\n"
            
            for article_num, citation in sorted(citations_to_add):
                enriched_response += citation + "\n\n"
            
            enriched_response += "*💡 Ces articles sont automatiquement affichés car ils sont mentionnés dans ma réponse.*"
        
        # Combiner les références existantes et nouvelles
        all_articles_refs = existing_articles_refs + new_articles_refs
        
        return enriched_response, all_articles_refs
    
    def _format_article_citation(self, article: Dict[str, Any]) -> str:
        """
        Formate une citation d'article pour l'affichage dans la réponse
        Version compacte par rapport à _format_article_response()
        """
        if not article:
            return ""
        
        numero = article.get("numero")
        contenu = article.get("contenu", "")
        theme_principal = article.get("theme_principal", "")
        
        citation = f"### **📜 Article {numero}**"
        
        if theme_principal:
            theme_formatted = theme_principal.replace('_', ' ').title()
            citation += f" - *{theme_formatted}*"
        
        citation += f"\n\n{contenu}"
        
        return citation
    
    def _is_article_request(self, question: str) -> Optional[int]:
        """
        Détecte si la question demande un article spécifique
        Retourne le numéro de l'article si trouvé, sinon None
        """
        import re
        
        question_lower = question.lower().strip()
        
        # Patterns pour détecter les demandes d'articles
        patterns = [
            r"(?:parle(?:[-\s]*moi)?|dis[-\s]*moi|explique[-\s]*moi|montre[-\s]*moi)?\s*(?:de\s*)?l['']?article\s*(\d+)",
            r"article\s*(\d+)",
            r"art(?:icle)?\s*\.?\s*(\d+)",
            r"(?:que\s*dit|contenu\s*de|texte\s*de)\s*l['']?article\s*(\d+)",
            r"l['']?article\s*numero?\s*(\d+)",
            r"l['']?article\s*n°?\s*(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                try:
                    article_num = int(match.group(1))
                    # Vérifier que l'article existe (entre 1 et 225)
                    if 1 <= article_num <= 225:
                        return article_num
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _format_article_response(self, article: Dict[str, Any]) -> str:
        """
        Formate la réponse pour un article spécifique avec toutes les métadonnées
        """
        if not article:
            return "Article non trouvé dans la base de données."
        
        numero = article.get("numero")
        contenu = article.get("contenu", "")
        theme_principal = article.get("theme_principal", "")
        themes_secondaires = article.get("themes_secondaires", [])
        mots_cles = article.get("mots_cles", [])
        entites_concernees = article.get("entites_concernees", [])
        type_disposition = article.get("type_disposition", "")
        
        response = f"## **Article {numero}** - Loi L/2019/0027/AN\n\n"
        
        # Contenu principal
        response += f"### 📄 **Contenu:**\n{contenu}\n\n"
        
        # Métadonnées enrichies
        if theme_principal:
            response += f"**🎯 Thème principal:** {theme_principal.replace('_', ' ').title()}\n\n"
        
        if themes_secondaires:
            themes_formatted = ", ".join([t.replace('_', ' ').title() for t in themes_secondaires])
            response += f"**📋 Thèmes secondaires:** {themes_formatted}\n\n"
        
        if entites_concernees:
            entites_formatted = ", ".join(entites_concernees)
            response += f"**👥 Entités concernées:** {entites_formatted}\n\n"
        
        if mots_cles:
            mots_formatted = ", ".join(mots_cles)
            response += f"**🔍 Mots-clés:** {mots_formatted}\n\n"
        
        if type_disposition:
            response += f"**⚖️ Type de disposition:** {type_disposition.replace('_', ' ').title()}\n\n"
        
        # Informations contextuelles
        response += "---\n"
        response += f"*Cet article fait partie de la **Loi L/2019/0027/AN** portant Statut Général des Agents de l'État de la République de Guinée.*\n\n"
        response += "**💡 Besoin de plus d'informations ?** N'hésitez pas à me poser des questions complémentaires sur cet article ou des sujets connexes !"
        
        return response
    
    def _get_related_article_suggestions(self, article: Dict[str, Any]) -> List[SuggestedQuestion]:
        """
        Génère des suggestions de questions sur des articles connexes
        """
        theme_principal = article.get("theme_principal", "")
        numero = article.get("numero", 0)
        
        suggestions = []
        
        # Suggestions génériques toujours utiles
        suggestions.extend([
            f"Qu'est-ce que cela implique concrètement dans l'article {numero} ?",
            f"Y a-t-il des exceptions à l'article {numero} ?",
            "Quels sont mes droits en tant qu'agent de l'État ?"
        ])
        
        # Suggestions spécifiques selon le thème
        theme_suggestions = {
            "retraite": ["À quel âge peut-on prendre sa retraite ?", "Comment calculer sa pension de retraite ?"],
            "conges": ["Quels sont les différents types de congés ?", "Comment demander un congé ?"],
            "discipline": ["Quelles sont les sanctions possibles ?", "Comment contester une sanction ?"],
            "remuneration": ["Comment est calculé mon traitement ?", "Quelles sont les primes possibles ?"],
            "avancement": ["Comment évoluer dans ma carrière ?", "Quels sont les critères d'avancement ?"],
            "recrutement": ["Comment devenir fonctionnaire ?", "Quelles sont les conditions de recrutement ?"]
        }
        
        # Ajouter suggestions thématiques si disponibles
        for theme_key, theme_questions in theme_suggestions.items():
            if theme_key in theme_principal.lower():
                suggestions.extend(theme_questions[:2])
                break
        
        # Limiter à 3 suggestions
        return [SuggestedQuestion(question=q) for q in suggestions[:3]]


# Instance du service RAG
rag_service: Optional[RAGService] = None


async def initialize_rag_service(law_path: str, qa_path: str):
    """Initialise le service RAG"""
    global rag_service
    
    rag_service = RAGService(
        cache=redis_cache,
        vector_db=vector_store,
        llm=llm_service
    )
    
    await rag_service.initialize(law_path, qa_path)
    logger.info("Service RAG initialisé")


async def get_rag_service() -> RAGService:
    """Dependency pour obtenir le service RAG"""
    if not rag_service:
        raise RuntimeError("Service RAG non initialisé")
    return rag_service
