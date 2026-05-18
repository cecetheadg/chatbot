# ============================================
# Chatbot L0027 - Dockerfile
# Statut Général des Agents de l'État de Guinée
# ============================================

# Image de base Python
FROM python:3.11-slim-bookworm

# Métadonnées
LABEL maintainer="FUGAS - Ministère de la Fonction Publique"
LABEL description="Chatbot IA pour la loi L/2019/0027/AN - Statut des Agents de l'État"
LABEL version="1.0.0"

# Build argument for worker count
ARG WORKERS=8

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    WORKERS=${WORKERS}

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Création d'un utilisateur non-root
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copie des requirements et installation
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY --chown=appuser:appgroup . .

# Création des répertoires nécessaires
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appgroup /app

# Passage à l'utilisateur non-root
USER appuser

# Exposition du port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande de démarrage (optimized for high concurrency)
# Uses configurable workers or auto-detects CPU count
CMD ["sh", "-c", "WORKERS=${WORKERS:-$(($(nproc) * 2 + 1))} && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $WORKERS --loop uvloop --access-log --log-level info"]
