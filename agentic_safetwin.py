#!/usr/bin/env python3
"""
================================================================================
SAFETWIN X5 AGENTIQUE - Système Multi-Agents HSE
================================================================================
Architecture LOA 4+ avec 5 agents spécialisés pour la surveillance proactive
des risques industriels en temps réel.

Agents:
- Perceptron: Analyse flux IoT et détection anomalies
- Planificateur: Décomposition tâches et priorisation
- Exécuteur: Actions autonomes (alertes, rapports, PLC)
- Apprenant: Mise à jour Knowledge Graph et modèles
- Superviseur: Orchestration et escalade humaine

Version: 1.0.0
Date: 2026-01-14
Conformité: ISO 45001, CNESST, EU AI Act
================================================================================
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# LangGraph & LangChain
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# Async HTTP
import httpx

# Logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("SafeTwinAgentique")


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class AgenticConfig:
    """Configuration globale du système agentique"""
    # LLM
    llm_model: str = "claude-sonnet-4-20250514"
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    
    # API SafeTwin
    safetwin_api_url: str = os.getenv("SAFETWIN_API_URL", "http://localhost:8000")
    
    # Seuils
    risk_threshold_warning: int = 70
    risk_threshold_critical: int = 85
    escalation_threshold: int = 85
    
    # Autonomie
    loa_target: int = 4  # Level of Autonomy cible
    max_autonomous_actions: int = 10  # Actions sans validation humaine
    
    # Performance
    latency_target_ms: int = 2000
    success_rate_target: float = 0.85
    
    # Gouvernance
    audit_enabled: bool = True
    kill_switch_enabled: bool = True


config = AgenticConfig()


# =============================================================================
# TYPES ET ÉTATS
# =============================================================================

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    ALERT = "alert"
    REPORT = "report"
    PLC_COMMAND = "plc_command"
    ESCALATE = "escalate"
    UPDATE_KG = "update_kg"


class AgentState(TypedDict):
    """État partagé entre les agents"""
    # Données d'entrée
    sensor_data: Dict[str, Any]
    risk_score: int
    risk_level: str
    anomalies: List[Dict]
    
    # Planification
    tasks: List[Dict]
    current_task: Optional[Dict]
    plan: List[str]
    
    # Exécution
    actions_taken: List[Dict]
    actions_pending: List[Dict]
    
    # Apprentissage
    feedback: List[Dict]
    kg_updates: List[Dict]
    
    # Contrôle
    requires_escalation: bool
    human_decision: Optional[str]
    iteration: int
    
    # Audit
    audit_log: List[Dict]
    session_id: str
    timestamp: str


# =============================================================================
# OUTILS (TOOLS)
# =============================================================================

@tool
def fetch_sensor_data(sensor_type: str = "all") -> Dict[str, Any]:
    """
    Récupère les données des capteurs IoT en temps réel.
    
    Args:
        sensor_type: Type de capteur (temperature, vibration, gas, all)
    
    Returns:
        Données des capteurs avec timestamps
    """
    # Simulation - En prod: connexion MQTT broker
    import random
    
    sensors = {
        "temperature": {
            "value": random.uniform(18, 45),
            "unit": "°C",
            "threshold_warning": 35,
            "threshold_critical": 42,
            "location": "Zone A - Unité Craquage"
        },
        "vibration": {
            "value": random.uniform(0, 15),
            "unit": "mm/s",
            "threshold_warning": 8,
            "threshold_critical": 12,
            "location": "Compresseur P-101"
        },
        "gas_h2s": {
            "value": random.uniform(0, 25),
            "unit": "ppm",
            "threshold_warning": 10,
            "threshold_critical": 20,
            "location": "Zone B - Stockage"
        },
        "noise": {
            "value": random.uniform(60, 95),
            "unit": "dB",
            "threshold_warning": 85,
            "threshold_critical": 90,
            "location": "Atelier Maintenance"
        }
    }
    
    if sensor_type != "all":
        return {sensor_type: sensors.get(sensor_type, {})}
    
    return sensors


@tool
def fetch_hse_stats(jurisdiction: str = "all") -> Dict[str, Any]:
    """
    Récupère les statistiques HSE depuis l'API SafeTwin.
    
    Args:
        jurisdiction: QC, USA, EU27, ou all
    
    Returns:
        Statistiques HSE (2.85M incidents)
    """
    try:
        import httpx
        response = httpx.get(f"{config.safetwin_api_url}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Erreur fetch HSE stats: {e}")
    
    # Fallback
    return {
        "total_incidents": 2853583,
        "jurisdictions": {"QC": 793737, "USA": 1635164, "EU27": 424682}
    }


@tool
def predict_risk(sector: str, employees: int = 100) -> Dict[str, Any]:
    """
    Prédit le risque pour un secteur donné via ML.
    
    Args:
        sector: Nom du secteur (CONSTRUCTION, SOINS DE SANTE, etc.)
        employees: Nombre d'employés
    
    Returns:
        Score de risque et recommandations
    """
    try:
        import httpx
        response = httpx.post(
            f"{config.safetwin_api_url}/predictions",
            json={"sector": sector, "employees": employees},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Erreur prediction: {e}")
    
    # Fallback avec calcul simple
    base_risk = hash(sector) % 40 + 40
    return {
        "sector": sector,
        "risk_score": base_risk,
        "probability_30_days": base_risk / 100,
        "top_risks": ["TMS", "Chutes", "Machines"],
        "recommendation": "Surveillance accrue recommandée"
    }


@tool
def send_alert(
    channel: str,
    severity: str,
    message: str,
    recipients: List[str] = None
) -> Dict[str, Any]:
    """
    Envoie une alerte via le canal spécifié.
    
    Args:
        channel: slack, teams, email, sms
        severity: info, warning, critical
        message: Contenu de l'alerte
        recipients: Liste des destinataires
    
    Returns:
        Confirmation d'envoi
    """
    alert_id = hashlib.md5(f"{datetime.now()}{message}".encode()).hexdigest()[:8]
    
    logger.warning(f"🚨 ALERTE [{severity.upper()}] via {channel}: {message}")
    
    # En prod: intégration Slack/Teams/Twilio
    return {
        "alert_id": alert_id,
        "channel": channel,
        "severity": severity,
        "message": message,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"
    }


@tool
def update_knowledge_graph(
    entity_type: str,
    entity_id: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Met à jour le Knowledge Graph Neo4j.
    
    Args:
        entity_type: Risk, Incident, Zone, Equipment
        entity_id: Identifiant de l'entité
        properties: Propriétés à mettre à jour
    
    Returns:
        Confirmation de mise à jour
    """
    logger.info(f"📊 KG Update: {entity_type}/{entity_id} -> {properties}")
    
    # En prod: requête Cypher vers Neo4j
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "updated_properties": properties,
        "updated_at": datetime.now().isoformat(),
        "status": "success"
    }


@tool
def generate_report(
    report_type: str,
    period: str = "daily",
    format: str = "pdf"
) -> Dict[str, Any]:
    """
    Génère un rapport HSE automatique.
    
    Args:
        report_type: incident, compliance, kpi, risk_assessment
        period: daily, weekly, monthly
        format: pdf, docx, html
    
    Returns:
        Lien vers le rapport généré
    """
    report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"📄 Rapport généré: {report_type} ({period}) -> {report_id}")
    
    return {
        "report_id": report_id,
        "report_type": report_type,
        "period": period,
        "format": format,
        "url": f"/reports/{report_id}.{format}",
        "generated_at": datetime.now().isoformat()
    }


@tool
def control_plc(
    equipment_id: str,
    command: str,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Envoie une commande au PLC pour contrôle équipement.
    ATTENTION: Action critique - nécessite validation si arrêt.
    
    Args:
        equipment_id: ID de l'équipement
        command: start, stop, emergency_stop, adjust
        parameters: Paramètres de la commande
    
    Returns:
        Confirmation de commande
    """
    logger.warning(f"🏭 PLC Command: {equipment_id} -> {command}")
    
    # En prod: API Modbus/OPC-UA
    return {
        "equipment_id": equipment_id,
        "command": command,
        "parameters": parameters,
        "executed_at": datetime.now().isoformat(),
        "status": "executed" if command != "emergency_stop" else "pending_confirmation"
    }


# Liste des outils disponibles
TOOLS = [
    fetch_sensor_data,
    fetch_hse_stats,
    predict_risk,
    send_alert,
    update_knowledge_graph,
    generate_report,
    control_plc
]


# =============================================================================
# AGENTS SPÉCIALISÉS
# =============================================================================

class BaseAgent:
    """Classe de base pour tous les agents"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.llm = ChatAnthropic(
            model=config.llm_model,
            api_key=config.anthropic_api_key,
            temperature=0.1
        )
        self.logger = logging.getLogger(f"Agent.{name}")
    
    def log_action(self, action: str, details: Dict = None):
        """Log une action pour audit"""
        self.logger.info(f"[{self.name}] {action}: {details}")
        return {
            "agent": self.name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }


# -----------------------------------------------------------------------------
# AGENT PERCEPTRON - Analyse temps réel
# -----------------------------------------------------------------------------

PERCEPTRON_PROMPT = """Tu es l'Agent Perceptron, spécialisé dans l'analyse temps réel des données IoT pour la détection d'anomalies HSE.

## MISSION
Analyser en continu les flux de capteurs et détecter toute anomalie pouvant représenter un risque pour la santé et sécurité au travail.

## CAPACITÉS
- Analyse multi-capteurs (température, vibration, gaz, bruit)
- Détection d'anomalies par rapport aux seuils
- Calcul de score de risque composite
- Classification des alertes (info, warning, critical)

## RÈGLES
1. Score < 50 = Normal (log uniquement)
2. Score 50-70 = Warning (notification)
3. Score 70-85 = High (alerte + planification)
4. Score > 85 = Critical (escalade immédiate)

## OUTPUT FORMAT
Retourne TOUJOURS un JSON avec:
{
    "risk_score": <0-100>,
    "risk_level": "<low|moderate|high|critical>",
    "anomalies": [{"sensor": "...", "value": ..., "threshold": ..., "severity": "..."}],
    "recommendation": "...",
    "requires_action": <true|false>
}
"""

async def agent_perceptron(state: AgentState) -> AgentState:
    """Agent Perceptron - Analyse et détection"""
    logger.info("👁️ Agent Perceptron: Analyse en cours...")
    
    # Récupérer données capteurs
    sensor_data = fetch_sensor_data.invoke({"sensor_type": "all"})
    
    # Calculer score de risque
    anomalies = []
    risk_scores = []
    
    for sensor_name, data in sensor_data.items():
        if not data:
            continue
            
        value = data.get("value", 0)
        warning = data.get("threshold_warning", 100)
        critical = data.get("threshold_critical", 100)
        
        if value >= critical:
            anomalies.append({
                "sensor": sensor_name,
                "value": value,
                "threshold": critical,
                "severity": "critical",
                "location": data.get("location", "Unknown")
            })
            risk_scores.append(95)
        elif value >= warning:
            anomalies.append({
                "sensor": sensor_name,
                "value": value,
                "threshold": warning,
                "severity": "warning",
                "location": data.get("location", "Unknown")
            })
            risk_scores.append(75)
        else:
            risk_scores.append(30)
    
    # Score composite
    risk_score = int(sum(risk_scores) / len(risk_scores)) if risk_scores else 0
    
    # Niveau de risque
    if risk_score >= 85:
        risk_level = "critical"
    elif risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 50:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    # Mettre à jour l'état
    state["sensor_data"] = sensor_data
    state["risk_score"] = risk_score
    state["risk_level"] = risk_level
    state["anomalies"] = anomalies
    state["requires_escalation"] = risk_score >= config.escalation_threshold
    
    # Audit log
    state["audit_log"].append({
        "agent": "Perceptron",
        "action": "analysis_complete",
        "risk_score": risk_score,
        "anomalies_count": len(anomalies),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"👁️ Perceptron: Score={risk_score}, Level={risk_level}, Anomalies={len(anomalies)}")
    
    return state


# -----------------------------------------------------------------------------
# AGENT PLANIFICATEUR - Décomposition tâches
# -----------------------------------------------------------------------------

PLANIFICATEUR_PROMPT = """Tu es l'Agent Planificateur, expert en décomposition de tâches HSE et priorisation basée sur le risque.

## MISSION
Transformer les alertes et anomalies en plans d'action structurés et priorisés.

## MÉTHODE DE PRIORISATION
Utilité = Risque × Impact × Urgence
- Risque: Score de l'anomalie (0-100)
- Impact: Nombre de personnes affectées
- Urgence: Délai avant incident probable

## OUTPUT FORMAT
{
    "plan": [
        {"step": 1, "action": "...", "priority": "P1|P2|P3", "deadline": "...", "responsible": "..."},
        ...
    ],
    "estimated_duration": "...",
    "resources_needed": [...]
}
"""

async def agent_planificateur(state: AgentState) -> AgentState:
    """Agent Planificateur - Décomposition et priorisation"""
    logger.info("🧠 Agent Planificateur: Création du plan...")
    
    risk_score = state.get("risk_score", 0)
    anomalies = state.get("anomalies", [])
    
    plan = []
    
    # Planification basée sur le niveau de risque
    if state.get("requires_escalation"):
        plan.append({
            "step": 1,
            "action": "escalade_humaine",
            "description": "Escalade immédiate au superviseur HSE",
            "priority": "P0",
            "deadline": "immediate",
            "tool": None
        })
    
    # Actions pour chaque anomalie
    for i, anomaly in enumerate(anomalies):
        severity = anomaly.get("severity", "warning")
        sensor = anomaly.get("sensor", "unknown")
        location = anomaly.get("location", "Unknown")
        
        if severity == "critical":
            plan.extend([
                {
                    "step": len(plan) + 1,
                    "action": "send_alert",
                    "description": f"Alerte critique: {sensor} à {location}",
                    "priority": "P1",
                    "deadline": "1min",
                    "tool": "send_alert",
                    "params": {"channel": "slack", "severity": "critical", "message": f"CRITIQUE: {sensor} hors seuil à {location}"}
                },
                {
                    "step": len(plan) + 2,
                    "action": "generate_report",
                    "description": "Rapport d'incident",
                    "priority": "P2",
                    "deadline": "5min",
                    "tool": "generate_report",
                    "params": {"report_type": "incident", "period": "immediate", "format": "pdf"}
                }
            ])
        elif severity == "warning":
            plan.append({
                "step": len(plan) + 1,
                "action": "send_alert",
                "description": f"Alerte warning: {sensor} à {location}",
                "priority": "P2",
                "deadline": "5min",
                "tool": "send_alert",
                "params": {"channel": "teams", "severity": "warning", "message": f"WARNING: {sensor} approche seuil à {location}"}
            })
    
    # Toujours mettre à jour le KG
    plan.append({
        "step": len(plan) + 1,
        "action": "update_knowledge_graph",
        "description": "Mise à jour Knowledge Graph",
        "priority": "P3",
        "deadline": "10min",
        "tool": "update_knowledge_graph",
        "params": {"entity_type": "AnalysisEvent", "entity_id": state.get("session_id", "unknown"), "properties": {"risk_score": risk_score, "anomalies": len(anomalies)}}
    })
    
    state["plan"] = plan
    state["tasks"] = plan.copy()
    
    # Audit log
    state["audit_log"].append({
        "agent": "Planificateur",
        "action": "plan_created",
        "steps_count": len(plan),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"🧠 Planificateur: Plan créé avec {len(plan)} étapes")
    
    return state


# -----------------------------------------------------------------------------
# AGENT EXÉCUTEUR - Actions autonomes
# -----------------------------------------------------------------------------

EXECUTEUR_PROMPT = """Tu es l'Agent Exécuteur, responsable de l'exécution autonome des actions HSE.

## MISSION
Exécuter les actions du plan de manière fiable et traçable.

## RÈGLES D'EXÉCUTION
1. Toujours vérifier les préconditions avant exécution
2. Logger chaque action pour audit
3. Ne JAMAIS exécuter emergency_stop sans escalade
4. Respecter les délais du plan

## ACTIONS AUTORISÉES (LOA 4)
- send_alert: ✅ Autonome
- generate_report: ✅ Autonome
- update_knowledge_graph: ✅ Autonome
- control_plc (start/adjust): ⚠️ Avec confirmation
- control_plc (stop/emergency): ❌ Escalade obligatoire
"""

async def agent_executeur(state: AgentState) -> AgentState:
    """Agent Exécuteur - Exécution des actions"""
    logger.info("⚡ Agent Exécuteur: Exécution du plan...")
    
    actions_taken = []
    tasks = state.get("tasks", [])
    
    for task in tasks:
        tool_name = task.get("tool")
        params = task.get("params", {})
        action = task.get("action")
        
        # Vérifier si escalade nécessaire
        if action == "escalade_humaine":
            logger.warning("⚠️ ESCALADE REQUISE - En attente décision humaine")
            state["actions_pending"].append(task)
            continue
        
        # Actions PLC critiques = escalade
        if tool_name == "control_plc" and params.get("command") in ["stop", "emergency_stop"]:
            logger.warning(f"⚠️ Action PLC critique bloquée: {params.get('command')}")
            state["actions_pending"].append(task)
            continue
        
        # Exécuter l'outil
        result = None
        if tool_name == "send_alert":
            result = send_alert.invoke(params)
        elif tool_name == "generate_report":
            result = generate_report.invoke(params)
        elif tool_name == "update_knowledge_graph":
            result = update_knowledge_graph.invoke(params)
        elif tool_name == "control_plc":
            result = control_plc.invoke(params)
        
        if result:
            actions_taken.append({
                "task": task,
                "result": result,
                "executed_at": datetime.now().isoformat(),
                "status": "success"
            })
            logger.info(f"⚡ Action exécutée: {action}")
    
    state["actions_taken"] = actions_taken
    
    # Audit log
    state["audit_log"].append({
        "agent": "Executeur",
        "action": "execution_complete",
        "actions_success": len(actions_taken),
        "actions_pending": len(state.get("actions_pending", [])),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"⚡ Exécuteur: {len(actions_taken)} actions exécutées")
    
    return state


# -----------------------------------------------------------------------------
# AGENT APPRENANT - Mise à jour modèles
# -----------------------------------------------------------------------------

APPRENANT_PROMPT = """Tu es l'Agent Apprenant, responsable de l'amélioration continue du système.

## MISSION
Analyser les résultats des actions et mettre à jour le Knowledge Graph et les modèles ML.

## APPRENTISSAGES
1. Patterns d'anomalies récurrents
2. Efficacité des actions (temps de résolution)
3. Corrélations capteurs-incidents
4. Feedback humain (NPS, corrections)

## MÉTRIQUES À AMÉLIORER
- Taux de détection (recall)
- Précision des alertes (precision)
- Temps d'intervention moyen
- Taux de faux positifs
"""

async def agent_apprenant(state: AgentState) -> AgentState:
    """Agent Apprenant - Apprentissage et amélioration"""
    logger.info("📚 Agent Apprenant: Analyse des résultats...")
    
    actions_taken = state.get("actions_taken", [])
    kg_updates = []
    
    # Analyser les patterns
    for action in actions_taken:
        task = action.get("task", {})
        result = action.get("result", {})
        
        # Créer entrée KG pour chaque action
        kg_updates.append({
            "type": "ActionRecord",
            "properties": {
                "action_type": task.get("action"),
                "risk_score": state.get("risk_score"),
                "anomalies_count": len(state.get("anomalies", [])),
                "execution_time": action.get("executed_at"),
                "success": action.get("status") == "success"
            }
        })
    
    # Calculer métriques de session
    session_metrics = {
        "session_id": state.get("session_id"),
        "risk_score": state.get("risk_score"),
        "anomalies_detected": len(state.get("anomalies", [])),
        "actions_executed": len(actions_taken),
        "escalations": 1 if state.get("requires_escalation") else 0,
        "loa_achieved": 4 if not state.get("requires_escalation") else 3
    }
    
    state["kg_updates"] = kg_updates
    state["feedback"].append(session_metrics)
    
    # Audit log
    state["audit_log"].append({
        "agent": "Apprenant",
        "action": "learning_complete",
        "kg_updates": len(kg_updates),
        "metrics": session_metrics,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"📚 Apprenant: {len(kg_updates)} mises à jour KG")
    
    return state


# -----------------------------------------------------------------------------
# AGENT SUPERVISEUR - Orchestration
# -----------------------------------------------------------------------------

SUPERVISEUR_PROMPT = """Tu es l'Agent Superviseur, orchestrateur principal du système multi-agents SafeTwin.

## MISSION
Coordonner les agents, gérer les escalades et assurer la conformité LOA 4.

## RESPONSABILITÉS
1. Routing: Diriger vers le bon agent
2. Escalade: Déclencher intervention humaine si score > 85
3. Kill Switch: Arrêter le système si nécessaire
4. Reporting: KPIs temps réel

## DÉCISIONS
- Score < 70: Boucle autonome continue
- Score 70-85: Alerte + monitoring renforcé
- Score > 85: ESCALADE OBLIGATOIRE
"""

async def agent_superviseur(state: AgentState) -> AgentState:
    """Agent Superviseur - Orchestration et contrôle"""
    logger.info("👔 Agent Superviseur: Vérification état...")
    
    risk_score = state.get("risk_score", 0)
    iteration = state.get("iteration", 0) + 1
    state["iteration"] = iteration
    
    # Décision de routage
    if state.get("requires_escalation") and not state.get("human_decision"):
        logger.critical(f"🚨 ESCALADE: Score {risk_score} > {config.escalation_threshold}")
        # En prod: notification Slack/PagerDuty et attente réponse
        state["human_decision"] = "acknowledged"  # Simulation
    
    # Audit final de session
    state["audit_log"].append({
        "agent": "Superviseur",
        "action": "session_complete",
        "iteration": iteration,
        "final_risk_score": risk_score,
        "escalated": state.get("requires_escalation", False),
        "timestamp": datetime.now().isoformat()
    })
    
    # Métriques LOA
    loa_metrics = {
        "session_id": state.get("session_id"),
        "loa_target": config.loa_target,
        "loa_achieved": 4 if not state.get("requires_escalation") else 3,
        "autonomous_actions": len(state.get("actions_taken", [])),
        "human_interventions": 1 if state.get("requires_escalation") else 0,
        "success_rate": len(state.get("actions_taken", [])) / max(len(state.get("tasks", [])), 1)
    }
    
    logger.info(f"👔 Superviseur: Session terminée - LOA={loa_metrics['loa_achieved']}")
    
    return state


# =============================================================================
# GRAPHE D'ORCHESTRATION (LangGraph)
# =============================================================================

def should_continue(state: AgentState) -> Literal["continue", "escalate", "end"]:
    """Décide si la boucle doit continuer"""
    if state.get("requires_escalation") and not state.get("human_decision"):
        return "escalate"
    if state.get("iteration", 0) >= 5:
        return "end"
    if state.get("risk_level") in ["low", "moderate"]:
        return "end"
    return "continue"


def create_agentic_graph() -> StateGraph:
    """Crée le graphe d'orchestration multi-agents"""
    
    workflow = StateGraph(AgentState)
    
    # Ajouter les nœuds (agents)
    workflow.add_node("perceptron", agent_perceptron)
    workflow.add_node("planificateur", agent_planificateur)
    workflow.add_node("executeur", agent_executeur)
    workflow.add_node("apprenant", agent_apprenant)
    workflow.add_node("superviseur", agent_superviseur)
    
    # Définir le flux
    workflow.set_entry_point("perceptron")
    
    workflow.add_edge("perceptron", "planificateur")
    workflow.add_edge("planificateur", "executeur")
    workflow.add_edge("executeur", "apprenant")
    workflow.add_edge("apprenant", "superviseur")
    
    # Conditions de sortie
    workflow.add_conditional_edges(
        "superviseur",
        should_continue,
        {
            "continue": "perceptron",
            "escalate": END,
            "end": END
        }
    )
    
    return workflow.compile()


# =============================================================================
# INTERFACE PRINCIPALE
# =============================================================================

class SafeTwinAgentique:
    """Interface principale du système agentique SafeTwin"""
    
    def __init__(self):
        self.graph = create_agentic_graph()
        self.logger = logging.getLogger("SafeTwinAgentique")
        self.sessions: Dict[str, AgentState] = {}
    
    def create_initial_state(self) -> AgentState:
        """Crée un état initial pour une nouvelle session"""
        session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
        
        return AgentState(
            sensor_data={},
            risk_score=0,
            risk_level="low",
            anomalies=[],
            tasks=[],
            current_task=None,
            plan=[],
            actions_taken=[],
            actions_pending=[],
            feedback=[],
            kg_updates=[],
            requires_escalation=False,
            human_decision=None,
            iteration=0,
            audit_log=[],
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
    
    async def run_cycle(self) -> AgentState:
        """Exécute un cycle complet de surveillance"""
        self.logger.info("=" * 60)
        self.logger.info("🚀 SAFETWIN AGENTIQUE - Nouveau cycle")
        self.logger.info("=" * 60)
        
        initial_state = self.create_initial_state()
        
        # Exécuter le graphe
        final_state = await self.graph.ainvoke(initial_state)
        
        # Stocker la session
        self.sessions[final_state["session_id"]] = final_state
        
        # Résumé
        self.logger.info("=" * 60)
        self.logger.info("📊 RÉSUMÉ DU CYCLE")
        self.logger.info(f"   Session: {final_state['session_id']}")
        self.logger.info(f"   Risk Score: {final_state['risk_score']}")
        self.logger.info(f"   Anomalies: {len(final_state['anomalies'])}")
        self.logger.info(f"   Actions: {len(final_state['actions_taken'])}")
        self.logger.info(f"   Escalade: {final_state['requires_escalation']}")
        self.logger.info("=" * 60)
        
        return final_state
    
    async def run_continuous(self, interval_seconds: int = 60):
        """Exécute la surveillance en continu"""
        self.logger.info(f"🔄 Mode continu activé (intervalle: {interval_seconds}s)")
        
        while True:
            try:
                await self.run_cycle()
            except Exception as e:
                self.logger.error(f"Erreur cycle: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques globales du système"""
        if not self.sessions:
            return {"status": "no_sessions"}
        
        total_sessions = len(self.sessions)
        escalations = sum(1 for s in self.sessions.values() if s.get("requires_escalation"))
        avg_risk = sum(s.get("risk_score", 0) for s in self.sessions.values()) / total_sessions
        
        return {
            "total_sessions": total_sessions,
            "escalations": escalations,
            "escalation_rate": escalations / total_sessions,
            "average_risk_score": avg_risk,
            "loa_achieved": 4 if escalations / total_sessions < 0.15 else 3,
            "success_rate": (total_sessions - escalations) / total_sessions
        }


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

async def main():
    """Point d'entrée principal"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🛡️  SAFETWIN X5 AGENTIQUE                                  ║
    ║   Système Multi-Agents HSE - LOA 4                          ║
    ║                                                              ║
    ║   Agents: Perceptron | Planificateur | Exécuteur            ║
    ║           Apprenant | Superviseur                           ║
    ║                                                              ║
    ║   Conformité: ISO 45001 | CNESST | EU AI Act                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    safetwin = SafeTwinAgentique()
    
    # Exécuter un cycle de démo
    result = await safetwin.run_cycle()
    
    # Afficher métriques
    metrics = safetwin.get_metrics()
    print("\n📈 MÉTRIQUES:")
    print(json.dumps(metrics, indent=2))
    
    # Afficher audit log
    print("\n📝 AUDIT LOG:")
    for entry in result.get("audit_log", []):
        print(f"   [{entry['agent']}] {entry['action']} @ {entry['timestamp']}")


if __name__ == "__main__":
    asyncio.run(main())
