#!/usr/bin/env python3
"""
Script d'indexation des données de la loi L0027 dans Qdrant
Ce script doit être exécuté une fois avant de démarrer le chatbot
"""
import asyncio
import json
import sys
from pathlib import Path
import logging

# Ajoute le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.vector_service import VectorStore
from app.services.llm_service import LLMService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


async def load_json(file_path: str) -> dict:
    """Charge un fichier JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


async def index_articles(
    vector_store: VectorStore,
    llm_service: LLMService,
    articles: list
):
    """Indexe les articles de la loi dans Qdrant"""
    logger.info(f"Indexation de {len(articles)} articles...")
    
    batch = []
    batch_size = 20
    
    for i, article in enumerate(articles):
        numero = article.get("numero")
        contenu = article.get("contenu", "")
        
        # Crée le texte pour l'embedding
        text_for_embedding = f"""Article {numero}: {contenu}
Thème: {article.get('theme_principal', '')}
Mots-clés: {', '.join(article.get('mots_cles', []))}"""
        
        # Génère l'embedding
        try:
            embedding = await llm_service.create_embedding(text_for_embedding)
            
            batch.append({
                "id": numero,
                "embedding": embedding,
                "payload": {
                    "numero": numero,
                    "contenu": contenu,
                    "theme_principal": article.get("theme_principal", ""),
                    "themes_secondaires": article.get("themes_secondaires", []),
                    "mots_cles": article.get("mots_cles", []),
                    "entites_concernees": article.get("entites_concernees", []),
                    "type_disposition": article.get("type_disposition"),
                    "valeurs_numeriques": article.get("valeurs_numeriques", {}),
                    "type": "article"
                }
            })
            
            # Indexe par lots
            if len(batch) >= batch_size:
                await vector_store.upsert_batch(batch)
                logger.info(f"Articles indexés: {i + 1}/{len(articles)}")
                batch = []
                
        except Exception as e:
            logger.error(f"Erreur indexation article {numero}: {e}")
    
    # Indexe le reste
    if batch:
        await vector_store.upsert_batch(batch)
    
    logger.info(f"✅ {len(articles)} articles indexés avec succès")


async def index_qa_pairs(
    vector_store: VectorStore,
    llm_service: LLMService,
    qa_pairs: list
):
    """Indexe les paires Q&A d'entraînement"""
    logger.info(f"Indexation de {len(qa_pairs)} paires Q&A...")
    
    batch = []
    batch_size = 20
    
    for i, qa in enumerate(qa_pairs):
        qa_id = qa.get("id")
        question = qa.get("question", "")
        reponse = qa.get("reponse", "")
        
        # Crée le texte pour l'embedding (basé sur la question)
        text_for_embedding = f"""Question: {question}
Catégorie: {qa.get('categorie', '')}
Mots-clés: {', '.join(qa.get('mots_cles', []))}"""
        
        try:
            embedding = await llm_service.create_embedding(text_for_embedding)
            
            batch.append({
                "id": 10000 + qa_id,  # Offset pour différencier des articles
                "embedding": embedding,
                "payload": {
                    "id": qa_id,
                    "question": question,
                    "reponse": reponse,
                    "categorie": qa.get("categorie", ""),
                    "articles_references": qa.get("articles_references", []),
                    "mots_cles": qa.get("mots_cles", []),
                    "type": "qa"
                }
            })
            
            if len(batch) >= batch_size:
                await vector_store.upsert_batch(batch)
                logger.info(f"Q&A indexées: {i + 1}/{len(qa_pairs)}")
                batch = []
                
        except Exception as e:
            logger.error(f"Erreur indexation Q&A {qa_id}: {e}")
    
    if batch:
        await vector_store.upsert_batch(batch)
    
    logger.info(f"✅ {len(qa_pairs)} paires Q&A indexées avec succès")


async def main():
    """Fonction principale d'indexation"""
    logger.info("=" * 60)
    logger.info("🚀 Démarrage de l'indexation des données L0027")
    logger.info("=" * 60)
    
    # Vérifie les chemins
    data_dir = Path(settings.DATA_DIR)
    law_path = data_dir / settings.LAW_FILE
    qa_path = data_dir / settings.QA_FILE
    
    if not law_path.exists():
        logger.error(f"❌ Fichier de loi non trouvé: {law_path}")
        sys.exit(1)
    
    if not qa_path.exists():
        logger.error(f"❌ Fichier Q&A non trouvé: {qa_path}")
        sys.exit(1)
    
    # Initialise les services
    logger.info("📦 Initialisation des services...")
    
    vector_store = VectorStore()
    await vector_store.connect()
    
    llm_service = LLMService()
    await llm_service.initialize()
    
    if not llm_service.get_available_providers():
        logger.error("❌ Aucun provider LLM disponible pour les embeddings")
        sys.exit(1)
    
    logger.info(f"LLM providers: {llm_service.get_available_providers()}")
    
    # Charge les données
    logger.info("📚 Chargement des données...")
    
    law_data = await load_json(str(law_path))
    qa_data = await load_json(str(qa_path))
    
    articles = law_data.get("articles", [])
    qa_pairs = qa_data.get("questions_reponses", [])
    
    logger.info(f"   - {len(articles)} articles de loi")
    logger.info(f"   - {len(qa_pairs)} paires Q&A")
    
    # Vérification de la collection
    stats = await vector_store.get_collection_stats()
    logger.info(f"📊 État actuel de Qdrant: {stats}")
    
    # Demande confirmation si données existantes
    if stats.get("points_count", 0) > 0:
        logger.warning(f"⚠️ La collection contient déjà {stats['points_count']} points")
        response = input("Voulez-vous réindexer ? (y/n): ")
        if response.lower() != 'y':
            logger.info("Indexation annulée")
            await vector_store.disconnect()
            return
    
    # Indexation
    logger.info("")
    logger.info("📥 Début de l'indexation...")
    logger.info("-" * 40)
    
    await index_articles(vector_store, llm_service, articles)
    await index_qa_pairs(vector_store, llm_service, qa_pairs)
    
    # Statistiques finales
    final_stats = await vector_store.get_collection_stats()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ INDEXATION TERMINÉE")
    logger.info("=" * 60)
    logger.info(f"   - Points totaux: {final_stats.get('points_count', 0)}")
    logger.info(f"   - Vecteurs indexés: {final_stats.get('indexed_vectors_count', 0)}")
    logger.info(f"   - Statut: {final_stats.get('status', 'unknown')}")
    
    # Fermeture
    await vector_store.disconnect()
    logger.info("👋 Terminé!")


if __name__ == "__main__":
    asyncio.run(main())
