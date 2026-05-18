"""
Service LLM multi-provider (OpenAI, Anthropic Claude, DeepSeek)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import httpx

from app.core.config import get_settings, SYSTEM_PROMPT, SUGGESTION_PROMPT
from app.models.schemas import LLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseLLM(ABC):
    """Classe abstraite pour les LLM"""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> str:
        """Génère une réponse"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        """Génère une réponse en streaming"""
        pass
    
    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        """Crée un embedding pour le texte"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie la disponibilité du service"""
        pass


class OpenAILLM(BaseLLM):
    """Client OpenAI"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur OpenAI generate: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Erreur OpenAI stream: {e}")
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur OpenAI embedding: {e}")
            raise
    
    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False


class AnthropicLLM(BaseLLM):
    """Client Anthropic Claude"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self._openai_for_embeddings = None
    
    def _get_embedding_client(self):
        """Utilise OpenAI pour les embeddings (Claude n'en a pas)"""
        if not self._openai_for_embeddings and settings.OPENAI_API_KEY:
            self._openai_for_embeddings = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_for_embeddings
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> str:
        try:
            # Sépare le system message
            system_content = ""
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    chat_messages.append(msg)
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_content,
                messages=chat_messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Erreur Anthropic generate: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        try:
            system_content = ""
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    chat_messages.append(msg)
            
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_content,
                messages=chat_messages
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Erreur Anthropic stream: {e}")
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        """Utilise OpenAI pour les embeddings"""
        client = self._get_embedding_client()
        if not client:
            raise ValueError("OpenAI API key required for embeddings with Claude")
        
        try:
            response = await client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur embedding (via OpenAI): {e}")
            raise
    
    async def health_check(self) -> bool:
        try:
            # Test simple
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False


class DeepSeekLLM(BaseLLM):
    """Client DeepSeek (compatible OpenAI API)"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self.model = settings.DEEPSEEK_MODEL
        self._openai_for_embeddings = None
    
    def _get_embedding_client(self):
        """Utilise OpenAI pour les embeddings"""
        if not self._openai_for_embeddings and settings.OPENAI_API_KEY:
            self._openai_for_embeddings = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_for_embeddings
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erreur DeepSeek generate: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Erreur DeepSeek stream: {e}")
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        """Utilise OpenAI pour les embeddings"""
        client = self._get_embedding_client()
        if not client:
            raise ValueError("OpenAI API key required for embeddings with DeepSeek")
        
        try:
            response = await client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur embedding (via OpenAI): {e}")
            raise
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False


class LLMService:
    """Service de gestion des LLMs"""
    
    def __init__(self):
        self._providers: Dict[str, BaseLLM] = {}
        self._default_provider = settings.DEFAULT_LLM_PROVIDER
        self._embedding_provider: Optional[BaseLLM] = None
    
    async def initialize(self):
        """Initialise les providers LLM disponibles"""
        # OpenAI
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = OpenAILLM()
            # OpenAI est utilisé par défaut pour les embeddings
            self._embedding_provider = self._providers["openai"]
            logger.info("Provider OpenAI initialisé")
        
        # Anthropic
        if settings.ANTHROPIC_API_KEY:
            self._providers["anthropic"] = AnthropicLLM()
            logger.info("Provider Anthropic initialisé")
        
        # DeepSeek
        if settings.DEEPSEEK_API_KEY:
            self._providers["deepseek"] = DeepSeekLLM()
            logger.info("Provider DeepSeek initialisé")
        
        if not self._providers:
            logger.warning("Aucun provider LLM configuré!")
        
        # Vérifie le provider par défaut
        if self._default_provider not in self._providers:
            available = list(self._providers.keys())
            if available:
                self._default_provider = available[0]
                logger.warning(f"Provider par défaut changé pour: {self._default_provider}")
    
    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLM:
        """Récupère un provider LLM"""
        name = provider_name or self._default_provider
        
        if name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Provider '{name}' non disponible. Disponibles: {available}")
        
        return self._providers[name]
    
    def get_available_providers(self) -> List[str]:
        """Liste des providers disponibles"""
        return list(self._providers.keys())
    
    async def check_providers_health(self) -> Dict[str, bool]:
        """Vérifie l'état de tous les providers"""
        health = {}
        for name, provider in self._providers.items():
            try:
                health[name] = await provider.health_check()
            except Exception:
                health[name] = False
        return health
    
    async def generate_response(
        self,
        question: str,
        context: str,
        provider_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Génère une réponse à une question avec contexte RAG
        """
        provider = self.get_provider(provider_name)
        
        # Construit les messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Ajoute l'historique si disponible (augmenté pour meilleur contexte)
        if conversation_history:
            logger.info(f"DEBUG: conversation_history = {conversation_history}")
            messages.extend(conversation_history[-10:])  # Derniers 5 échanges (10 messages)
            logger.info(f"DEBUG: messages after adding history = {messages}")
        
        # Détecte si c'est une salutation
        is_greeting = self._is_greeting(question)
        
        if is_greeting:
            # Pour les salutations, réponse chaleureuse et présentation
            user_prompt = f"""L'utilisateur dit: "{question}"

Réponds de manière chaleureuse et professionnelle. Présente-toi brièvement comme l'assistant Fomba, spécialisé dans la loi L0027 sur le Statut des Agents de l'État de Guinée. Propose ton aide pour répondre aux questions sur cette loi. Sois courtois et concis (2-3 phrases maximum)."""
        else:
            # Pour les questions normales, utilise le contexte
            user_prompt = f"""**Contexte juridique pertinent:**
{context}

**Question de l'utilisateur:**
{question}

Réponds de manière professionnelle, précise et courtoise en citant les articles pertinents. Si c'est une question de suivi dans la conversation, utilise le contexte de l'historique pour donner une réponse cohérente."""
        
        messages.append({"role": "user", "content": user_prompt})
        
        return await provider.generate(messages, max_tokens=settings.MAX_RESPONSE_LENGTH)
    
    def _is_greeting(self, question: str) -> bool:
        """Détecte si la question est une salutation"""
        greetings = [
            'bonjour', 'bonsoir', 'salut', 'bonne journée', 'bonne soirée',
            'bonne nuit', 'bon matin', 'coucou', 'hello', 'hi', 'hey',
            'bonjour monsieur', 'bonjour madame', 'bonsoir monsieur', 'bonsoir madame',
            'allô', 'allo', 'bonjour fomba', 'salut fomba', 'bonjour assistant',
            'bonjour chatbot', 'bonjour bot'
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
    
    async def generate_suggestions(
        self,
        question: str,
        answer: str,
        provider_name: Optional[str] = None
    ) -> List[str]:
        """
        Génère des suggestions de questions complémentaires
        """
        provider = self.get_provider(provider_name)
        
        messages = [
            {"role": "system", "content": SUGGESTION_PROMPT},
            {"role": "user", "content": f"""Question posée: {question}

Réponse donnée: {answer}

Propose 3 questions complémentaires pertinentes."""}
        ]
        
        try:
            response = await provider.generate(messages, max_tokens=300, temperature=0.5)
            
            # Parse les suggestions
            lines = response.strip().split('\n')
            suggestions = []
            for line in lines:
                line = line.strip()
                # Nettoie les numéros et tirets
                for prefix in ['1.', '2.', '3.', '-', '•', '*']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                if line and len(line) > 10:
                    suggestions.append(line)
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Erreur génération suggestions: {e}")
            return []
    
    async def create_embedding(self, text: str) -> List[float]:
        """Crée un embedding pour le texte"""
        if not self._embedding_provider:
            raise ValueError("Aucun provider d'embedding disponible (OpenAI requis)")
        return await self._embedding_provider.create_embedding(text)
    
    async def batch_embeddings(
        self, 
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Crée des embeddings par lot"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.create_embedding(text) for text in batch]
            )
            all_embeddings.extend(batch_embeddings)
            logger.debug(f"Batch embeddings: {i + len(batch)}/{len(texts)}")
        
        return all_embeddings
    
    async def classify_question_relevance(
        self,
        question: str,
        provider_name: Optional[str] = None
    ) -> tuple[bool, float]:
        """
        Vérifie si la question est pertinente pour le chatbot
        Retourne (is_relevant, confidence_score)
        """
        provider = self.get_provider(provider_name)
        
        prompt = f"""Analyse cette question et détermine si elle concerne la fonction publique guinéenne, les agents de l'État, ou des sujets professionnels connexes à la loi L/2019/0027/AN.

Question: "{question}"

Questions acceptables:
- Questions directes sur la loi L0027
- Questions sur la fonction publique guinéenne en général  
- Questions professionnelles contextuelles (RH, administration)
- Questions de suivi de conversation sur ces sujets
- Salutations et politesse professionnelle
- Demandes de clarification ou d'exemples

Réponds UNIQUEMENT avec un JSON dans ce format exact:
{{"relevant": true/false, "confidence": 0.0-1.0, "category": "nom_categorie"}}

Catégories possibles: definitions_generales, recrutement, droits_agents, obligations_agents, conges, discipline_sanctions, recompenses, remuneration, carriere_avancement, positions_administratives, cessation_service, contractuels, fonction_publique_generale, conversation_professionnelle, salutations, clarification, hors_sujet"""
        
        try:
            response = await provider.generate(
                [{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            # Parse le JSON
            import json
            # Nettoie la réponse
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
            
            data = json.loads(response.strip())
            return data.get("relevant", False), data.get("confidence", 0.5)
            
        except Exception as e:
            logger.error(f"Erreur classification question: {e}")
            # Par défaut, on traite la question
            return True, 0.5


# Instance singleton
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Dependency pour obtenir le service LLM"""
    return llm_service
