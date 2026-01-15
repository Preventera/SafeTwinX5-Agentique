# ==============================================================================
# DOCKERFILE - SafeTwin X5 Agentique
# ==============================================================================
# Image de production pour le système multi-agents HSE
# ==============================================================================

FROM python:3.11-slim as builder

# Métadonnées
LABEL maintainer="Preventera <contact@preventera.com>"
LABEL version="1.0.0"
LABEL description="SafeTwin X5 Agentique - Système Multi-Agents HSE LOA 4"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd --create-home --shell /bin/bash safetwin

# Répertoire de travail
WORKDIR /app

# Copier requirements
COPY requirements-agentic.txt .

# Installer dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements-agentic.txt

# ==============================================================================
# Stage de production
# ==============================================================================
FROM python:3.11-slim as production

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    APP_USER=safetwin

# Créer utilisateur non-root
RUN useradd --create-home --shell /bin/bash ${APP_USER}

# Répertoire de travail
WORKDIR ${APP_HOME}

# Copier dépendances depuis builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code
COPY --chown=${APP_USER}:${APP_USER} . .

# Changer d'utilisateur
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Port exposé
EXPOSE 8080

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "api_agentic:app", "--host", "0.0.0.0", "--port", "8080"]

# ==============================================================================
# Stage de développement
# ==============================================================================
FROM production as development

USER root

# Outils de dev
RUN pip install pytest pytest-asyncio httpx black isort mypy

USER ${APP_USER}

# Commande dev avec reload
CMD ["python", "-m", "uvicorn", "api_agentic:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
