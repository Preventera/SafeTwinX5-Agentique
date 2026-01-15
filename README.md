# 🤖 SAFETWIN X5 AGENTIQUE

> Transformation de SafeTwin en plateforme multi-agents HSE autonome (LOA 4+)

## 🎯 Vue d'ensemble

SafeTwin X5 Agentique transforme votre plateforme de jumeau numérique en système intelligent autonome capable de :

- 👁️ **Surveiller** les risques HSE 24/7 sans intervention humaine
- 🧠 **Analyser** et prédire les incidents avant qu'ils surviennent
- ⚡ **Agir** automatiquement (alertes, rapports, contrôle équipements)
- 📚 **Apprendre** et s'améliorer continuellement
- 👔 **Escalader** vers l'humain uniquement quand nécessaire

## 📊 Comparaison Avant/Après

| Aspect | SafeTwin Actuel | SafeTwin Agentique |
|--------|-----------------|-------------------|
| Surveillance | Manuel | 24/7 Automatique |
| Détection | Réactive | Proactive (<2s) |
| Décision | Humain | Agent + Escalade |
| Actions | Manuel | Autonome (LOA 4) |
| Apprentissage | Aucun | Continu |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    SAFETWIN X5 AGENTIQUE                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   📡 IoT Sensors ──► 👁️ PERCEPTRON ──► 🧠 PLANIFICATEUR    │
│                              │                  │            │
│   📊 2.85M HSE Data          │                  ▼            │
│   🕸️ Neo4j KG               │         ⚡ EXÉCUTEUR          │
│                              │                  │            │
│                              │                  ▼            │
│                              └──► 📚 APPRENANT              │
│                                        │                     │
│                              👔 SUPERVISEUR ◄──┘             │
│                                   │                          │
│                              [ESCALADE SI SCORE > 85]        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 🤖 Les 5 Agents

| Agent | Rôle | Outils |
|-------|------|--------|
| **Perceptron** | Analyse temps réel capteurs IoT | MQTT, Seuils ML |
| **Planificateur** | Décompose objectifs en tâches | Priorisation risque×impact |
| **Exécuteur** | Actions autonomes | Slack, Rapports, PLC |
| **Apprenant** | Met à jour KG et modèles | Neo4j, Pinecone |
| **Superviseur** | Orchestre et escalade | Kill switch, KPIs |

## 🚀 Démarrage rapide

### 1. Installation

```bash
# Cloner
git clone https://github.com/Preventera/SafeTwinX5-Agentique
cd SafeTwinX5-Agentique

# Environnement
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Dépendances
pip install -r requirements-agentic.txt

# Variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API
```

### 2. Configuration

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
SAFETWIN_API_URL=http://localhost:8000
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379
```

### 3. Exécution

```bash
# Mode démo (un cycle)
python agentic_safetwin.py

# Mode continu (surveillance 24/7)
python -c "from agentic_safetwin import SafeTwinAgentique; import asyncio; asyncio.run(SafeTwinAgentique().run_continuous(60))"
```

### 4. Déploiement Kubernetes

```bash
# Build image
docker build -t preventera/safetwin-agentique:1.0.0 .

# Deploy avec Helm
helm install safetwin-agentique ./helm -f helm/values.yaml
```

## 📁 Structure du projet

```
safetwin-agentique/
├── agentic_safetwin.py      # Code principal multi-agents
├── api_agentic.py           # API FastAPI pour le système
├── requirements-agentic.txt  # Dépendances Python
├── Dockerfile               # Image Docker production
├── ARCHITECTURE.md          # Diagrammes Mermaid
├── GOVERNANCE.md            # Plan gouvernance & sécurité
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml          # Configuration Kubernetes
│   └── templates/
└── tests/
    └── test_scenarios.py    # Tests E2E
```

## 📈 Métriques LOA

| Métrique | Cible | Description |
|----------|-------|-------------|
| **Taux succès** | >85% | Actions réussies sans intervention |
| **F1-Score** | >0.9 | Précision détection anomalies |
| **Latence** | <2s | Temps de réaction |
| **Escalade** | <15% | Taux d'intervention humaine |
| **LOA** | 4+ | Niveau d'autonomie |

## 🛡️ Gouvernance

### Seuils d'escalade

| Score | Niveau | Action |
|-------|--------|--------|
| 0-69 | Normal/Warning | Autonome |
| 70-84 | Élevé | Alerte + Monitoring |
| **85+** | **Critique** | **ESCALADE HUMAINE** |

### Kill Switch

- Activable par Superviseur HSE ou Admin
- Suspend toutes les actions autonomes
- Nécessite validation humaine pour reprise

## 🔐 Conformité

- ✅ **ISO 45001** - Gestion SST
- ✅ **CNESST** - Réglementation Québec
- ✅ **EU AI Act** - High-Risk AI System
- ✅ **RGPD/Loi 25** - Protection données

## 📚 Documentation

- [Architecture détaillée](./ARCHITECTURE.md)
- [Plan de gouvernance](./GOVERNANCE.md)
- [Guide déploiement](./docs/DEPLOYMENT.md)
- [API Reference](./docs/API.md)

## 🤝 Support

- **Issues**: github.com/Preventera/SafeTwinX5-Agentique/issues
- **Email**: support@preventera.com
- **Slack**: #safetwin-agentique

---

**© 2026 Preventera Inc. - SafeTwin X5 Agentique v1.0.0**
