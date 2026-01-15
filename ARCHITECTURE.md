# 🏗️ ARCHITECTURE SAFETWIN X5 AGENTIQUE

## Diagramme Principal

```mermaid
flowchart TB
    subgraph PERCEPTION["🔍 COUCHE PERCEPTION"]
        IoT[("📡 Capteurs IoT<br/>MQTT Broker")]
        API_EXT["🌐 APIs Externes<br/>CNESST/OSHA/Eurostat"]
        DOC["📄 Documents<br/>PDF/BIM/CAD"]
    end

    subgraph AGENTS["🤖 COUCHE AGENTS (LangGraph)"]
        PERCEPTRON["👁️ Agent Perceptron<br/>Analyse temps réel"]
        PLANIFICATEUR["🧠 Agent Planificateur<br/>Décomposition tâches"]
        EXECUTEUR["⚡ Agent Exécuteur<br/>Actions autonomes"]
        APPRENANT["📚 Agent Apprenant<br/>Mise à jour KG"]
        SUPERVISEUR["👔 Agent Superviseur<br/>Orchestration"]
    end

    subgraph MEMOIRE["💾 COUCHE MÉMOIRE"]
        VECTOR[("🧮 Pinecone<br/>Mémoire vectorielle")]
        KG[("🕸️ Neo4j<br/>Knowledge Graph")]
        POSTGRES[("🐘 PostgreSQL<br/>2.85M incidents")]
        REDIS[("⚡ Redis<br/>Cache temps réel")]
    end

    subgraph ACTIONS["🎯 COUCHE ACTIONS"]
        ALERT["🚨 Alertes<br/>Slack/Teams/SMS"]
        RAPPORT["📊 Rapports<br/>Auto-générés"]
        PLC["🏭 Contrôle PLC<br/>Arrêt machine"]
        ESCALADE["👤 Escalade Humaine<br/>Décisions critiques"]
    end

    subgraph GOUVERNANCE["🛡️ GOUVERNANCE"]
        RBAC["🔐 RBAC/JWT"]
        AUDIT["📝 Logs ELK"]
        KILL["🛑 Kill Switch"]
        METRICS["📈 Prometheus"]
    end

    %% Flux données
    IoT --> PERCEPTRON
    API_EXT --> PERCEPTRON
    DOC --> PERCEPTRON
    
    PERCEPTRON --> PLANIFICATEUR
    PLANIFICATEUR --> EXECUTEUR
    EXECUTEUR --> APPRENANT
    APPRENANT --> KG
    
    SUPERVISEUR --> PERCEPTRON
    SUPERVISEUR --> PLANIFICATEUR
    SUPERVISEUR --> EXECUTEUR
    SUPERVISEUR --> APPRENANT
    
    %% Mémoire
    PERCEPTRON <--> REDIS
    PLANIFICATEUR <--> VECTOR
    APPRENANT <--> KG
    APPRENANT <--> POSTGRES
    
    %% Actions
    EXECUTEUR --> ALERT
    EXECUTEUR --> RAPPORT
    EXECUTEUR --> PLC
    EXECUTEUR --> ESCALADE
    
    %% Gouvernance
    GOUVERNANCE --> AGENTS
```

## Boucle ReAct (Reason-Act-Observe)

```mermaid
stateDiagram-v2
    [*] --> Percevoir
    Percevoir --> Raisonner: Données collectées
    Raisonner --> Planifier: Anomalie détectée
    Planifier --> Agir: Plan validé
    Agir --> Observer: Action exécutée
    Observer --> Apprendre: Résultat mesuré
    Apprendre --> Percevoir: Modèle mis à jour
    
    Raisonner --> Escalader: Risque critique >85
    Escalader --> [*]: Humain intervient
```

## Flux Multi-Agents

```mermaid
sequenceDiagram
    participant IoT as 📡 Capteurs IoT
    participant P as 👁️ Perceptron
    participant PL as 🧠 Planificateur
    participant E as ⚡ Exécuteur
    participant A as 📚 Apprenant
    participant S as 👔 Superviseur
    participant H as 👤 Humain

    IoT->>P: Données temps réel
    P->>P: Détection anomalie
    P->>S: Alerte: Risque score 78
    S->>PL: Planifier intervention
    PL->>PL: Décomposer tâches
    PL->>E: Plan d'action validé
    E->>E: Exécuter actions
    E-->>H: Notification Slack
    E->>A: Résultat action
    A->>A: Mise à jour KG
    A->>S: Feedback apprentissage
    
    Note over S: Si score >85
    S->>H: ESCALADE OBLIGATOIRE
    H->>S: Décision humaine
```

## Niveaux d'Autonomie (LOA)

| LOA | Description | SafeTwin X5 |
|-----|-------------|-------------|
| 1 | Assistance humaine | ❌ Dépassé |
| 2 | Assistance partielle | ❌ Dépassé |
| 3 | Autonomie conditionnelle | ❌ Dépassé |
| **4** | **Haute autonomie** | ✅ **CIBLE** |
| 5 | Autonomie totale | ⚠️ Futur (avec validation) |

### LOA 4 = Agent autonome AVEC :
- Escalade humaine si risque >85
- Kill switch accessible
- Audit complet des décisions
- Supervision dashboard temps réel
