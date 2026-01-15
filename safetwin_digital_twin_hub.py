#!/usr/bin/env python3
"""
================================================================================
SAFETWIN X5 AGENTIQUE - DIGITAL TWIN HUB
================================================================================
Système multi-agents pour jumeaux numériques HSE avec ingestion SGSST

FLUX:
  SGSST Sources → Connecteurs → Normalisation → SafetyGraph → Twin → Playbooks

AGENTS:
  1. SGSSTConnector    - Connecte aux différents SGSST (Intellect, CONFORMiT, etc.)
  2. DataNormalizer    - Normalise vers ontologie SafetyGraph CNESST
  3. TwinBuilder       - Crée/met à jour le jumeau numérique 3D
  4. PlaybookGenerator - Génère playbooks auto-apprenants
  5. TwinOrchestrator  - Orchestre le flux complet

Conformité: Vision Zero, LMRSST Québec, ISO 45001
================================================================================
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid

# LangGraph
from langgraph.graph import StateGraph, END

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger("SafeTwinDigitalTwin")


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class DigitalTwinConfig:
    """Configuration du système Digital Twin"""
    
    # API SafeTwin
    safetwin_api_url: str = os.getenv("SAFETWIN_API_URL", "http://localhost:8000")
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    # SGSST Connectors
    sgsst_sources: Dict[str, Dict] = field(default_factory=lambda: {
        "intellect": {
            "type": "rest_api",
            "base_url": "https://api.intellect.com/v1",
            "auth": "oauth2",
            "data_types": ["audits", "risks", "analytics"]
        },
        "conformit_ai": {
            "type": "rest_api", 
            "base_url": "https://api.conformit.ai/v2",
            "auth": "api_key",
            "data_types": ["permits", "confined_spaces", "inspections"]
        },
        "medial_plus": {
            "type": "rest_api",
            "base_url": "https://api.medialplus.com/v1",
            "auth": "bearer",
            "data_types": ["prevention_plans", "incidents", "training"]
        },
        "sharepoint": {
            "type": "graph_api",
            "base_url": "https://graph.microsoft.com/v1.0",
            "auth": "oauth2",
            "data_types": ["documents", "approvals", "workflows"]
        },
        "sigma_rh": {
            "type": "rest_api",
            "base_url": "https://api.sigma-rh.com/v1",
            "auth": "api_key",
            "data_types": ["near_miss", "mobile_inspections", "iot"]
        },
        "tervene": {
            "type": "rest_api",
            "base_url": "https://api.tervene.com/v1",
            "auth": "api_key",
            "data_types": ["field_observations", "safety_walks"]
        }
    })
    
    # Ontologie CNESST/IRSST
    ontology_version: str = "2.0"
    risk_categories: List[str] = field(default_factory=lambda: [
        "RC1_CHUTES_HAUTEUR",
        "RC2_ENSEVELISSEMENT", 
        "RC3_MACHINES",
        "RC4_VEHICULES",
        "RC5_ESPACES_CLOS",
        "RC6_ELECTRICITE",
        "RC7_CHIMIQUE_BIO",
        "RC8_ERGONOMIE_TMS"
    ])


config = DigitalTwinConfig()


# =============================================================================
# TYPES ET ÉTAT
# =============================================================================

class SGSSTSource(Enum):
    INTELLECT = "intellect"
    CONFORMIT_AI = "conformit_ai"
    MEDIAL_PLUS = "medial_plus"
    SHAREPOINT = "sharepoint"
    SIGMA_RH = "sigma_rh"
    TERVENE = "tervene"
    DOCUMENT_UPLOAD = "document_upload"


class DataType(Enum):
    RISK = "risk"
    INCIDENT = "incident"
    AUDIT = "audit"
    INSPECTION = "inspection"
    NEAR_MISS = "near_miss"
    PERMIT = "permit"
    TRAINING = "training"
    DOCUMENT = "document"
    ZONE = "zone"
    EQUIPMENT = "equipment"


class TwinState(TypedDict):
    """État partagé entre les agents Digital Twin"""
    
    # Session
    session_id: str
    timestamp: str
    
    # Données brutes ingérées
    raw_data: List[Dict]
    source: str
    data_type: str
    
    # Données normalisées
    normalized_entities: List[Dict]
    risks: List[Dict]
    zones: List[Dict]
    equipment: List[Dict]
    
    # SafetyGraph
    kg_nodes_created: int
    kg_relationships_created: int
    cypher_queries: List[str]
    
    # Digital Twin
    twin_id: str
    twin_version: int
    spatial_elements: List[Dict]
    risk_heatmap: Dict
    
    # Playbooks
    playbooks_generated: List[Dict]
    recommendations: List[str]
    
    # Audit
    audit_log: List[Dict]
    processing_time_ms: int


# =============================================================================
# OUTILS SGSST
# =============================================================================

async def fetch_from_intellect(endpoint: str, params: Dict = None) -> Dict:
    """Fetch données depuis Intellect SGSST"""
    logger.info(f"📥 Intellect API: {endpoint}")
    
    # Simulation - En prod: vrai appel API
    mock_data = {
        "audits": [
            {
                "id": "AUD-001",
                "date": "2026-01-15",
                "site": "Chantier Montreal Nord",
                "findings": [
                    {"type": "risk", "category": "RC1", "description": "Garde-corps manquant niveau 3"},
                    {"type": "risk", "category": "RC3", "description": "Protection scie circulaire défectueuse"}
                ],
                "score": 72
            }
        ],
        "risks": [
            {"id": "RSK-101", "category": "RC1_CHUTES_HAUTEUR", "zone": "Zone B", "severity": "high"},
            {"id": "RSK-102", "category": "RC6_ELECTRICITE", "zone": "Zone A", "severity": "medium"}
        ]
    }
    return mock_data.get(endpoint, {})


async def fetch_from_conformit(endpoint: str, params: Dict = None) -> Dict:
    """Fetch données depuis CONFORMiT.ai"""
    logger.info(f"📥 CONFORMiT.ai API: {endpoint}")
    
    mock_data = {
        "permits": [
            {
                "id": "PER-2026-001",
                "type": "confined_space",
                "location": "Réservoir R-101",
                "status": "active",
                "risks": ["RC5_ESPACES_CLOS", "RC7_CHIMIQUE_BIO"],
                "valid_until": "2026-01-16T18:00:00"
            }
        ],
        "inspections": [
            {
                "id": "INS-2026-015",
                "date": "2026-01-15",
                "inspector": "Jean Tremblay",
                "zone": "Atelier Soudure",
                "items_checked": 45,
                "non_conformities": 3
            }
        ]
    }
    return mock_data.get(endpoint, {})


async def fetch_from_sharepoint(library: str) -> Dict:
    """Fetch documents depuis SharePoint"""
    logger.info(f"📥 SharePoint: {library}")
    
    mock_data = {
        "documents": [
            {
                "id": "DOC-SP-001",
                "name": "Programme_Prevention_2026.pdf",
                "path": "/sites/HSE/Documents/Programmes",
                "modified": "2026-01-10",
                "content_type": "application/pdf"
            },
            {
                "id": "DOC-SP-002", 
                "name": "Plan_Urgence_Incendie.pdf",
                "path": "/sites/HSE/Documents/Urgences",
                "modified": "2026-01-05",
                "content_type": "application/pdf"
            }
        ]
    }
    return mock_data


async def parse_document(doc_path: str) -> Dict:
    """Parse un document PDF/BIM et extrait les entités HSE"""
    logger.info(f"📄 Parsing document: {doc_path}")
    
    # Simulation extraction IA - En prod: utiliser Claude/GPT pour extraction
    extracted = {
        "document_id": hashlib.md5(doc_path.encode()).hexdigest()[:8],
        "title": doc_path.split("/")[-1],
        "risks_found": [
            {
                "description": "Travaux en hauteur sans harnais",
                "category": "RC1_CHUTES_HAUTEUR",
                "location": "Toiture bâtiment principal",
                "coordinates": {"x": 45.5, "y": 12.3, "z": 8.0},
                "severity": "critical"
            },
            {
                "description": "Exposition au bruit >85dB",
                "category": "RC8_ERGONOMIE_TMS",
                "location": "Atelier usinage",
                "coordinates": {"x": 20.0, "y": 30.0, "z": 0.0},
                "severity": "high"
            }
        ],
        "zones_found": [
            {"name": "Zone A - Administration", "type": "office", "risk_level": "low"},
            {"name": "Zone B - Production", "type": "industrial", "risk_level": "high"},
            {"name": "Zone C - Stockage", "type": "warehouse", "risk_level": "medium"}
        ],
        "equipment_found": [
            {"id": "EQP-001", "name": "Pont roulant 10T", "zone": "Zone B", "last_inspection": "2025-12-15"},
            {"id": "EQP-002", "name": "Chariot élévateur", "zone": "Zone C", "last_inspection": "2026-01-02"}
        ]
    }
    return extracted


# =============================================================================
# AGENT 1: SGSST CONNECTOR
# =============================================================================

SGSST_CONNECTOR_PROMPT = """Tu es l'Agent SGSSTConnector, responsable de l'ingestion multi-sources.

MISSION: Connecter et extraire les données de tous les SGSST configurés.

SOURCES SUPPORTÉES:
- Intellect: Audits, risques, analytics
- CONFORMiT.ai: Permis, espaces clos, inspections
- MEDIAL+: Plans prévention, incidents
- SharePoint: Documents, workflows
- SIGMA-RH/Tervene: Near-miss, observations terrain

RÈGLES:
1. Toujours vérifier la connexion avant extraction
2. Logger chaque source avec timestamp
3. Gérer les erreurs gracieusement (continuer si une source échoue)
4. Retourner données brutes avec métadonnées source
"""

async def agent_sgsst_connector(state: TwinState) -> TwinState:
    """Agent qui connecte et extrait depuis les SGSST"""
    logger.info("🔌 Agent SGSSTConnector: Ingestion multi-sources...")
    
    start_time = datetime.now()
    raw_data = []
    
    source = state.get("source", "all")
    
    # Intellect
    if source in ["all", "intellect"]:
        try:
            audits = await fetch_from_intellect("audits")
            risks = await fetch_from_intellect("risks")
            raw_data.append({
                "source": "intellect",
                "timestamp": datetime.now().isoformat(),
                "data": {"audits": audits, "risks": risks}
            })
            logger.info("✅ Intellect: Données extraites")
        except Exception as e:
            logger.error(f"❌ Intellect: {e}")
    
    # CONFORMiT.ai
    if source in ["all", "conformit_ai"]:
        try:
            permits = await fetch_from_conformit("permits")
            inspections = await fetch_from_conformit("inspections")
            raw_data.append({
                "source": "conformit_ai",
                "timestamp": datetime.now().isoformat(),
                "data": {"permits": permits, "inspections": inspections}
            })
            logger.info("✅ CONFORMiT.ai: Données extraites")
        except Exception as e:
            logger.error(f"❌ CONFORMiT.ai: {e}")
    
    # SharePoint Documents
    if source in ["all", "sharepoint"]:
        try:
            docs = await fetch_from_sharepoint("HSE")
            raw_data.append({
                "source": "sharepoint",
                "timestamp": datetime.now().isoformat(),
                "data": docs
            })
            logger.info("✅ SharePoint: Documents listés")
        except Exception as e:
            logger.error(f"❌ SharePoint: {e}")
    
    # Document Upload (si fourni)
    if state.get("data_type") == "document_upload":
        doc_path = state.get("raw_data", [{}])[0].get("path", "")
        if doc_path:
            extracted = await parse_document(doc_path)
            raw_data.append({
                "source": "document_upload",
                "timestamp": datetime.now().isoformat(),
                "data": extracted
            })
            logger.info(f"✅ Document parsé: {doc_path}")
    
    state["raw_data"] = raw_data
    
    # Audit log
    state["audit_log"].append({
        "agent": "SGSSTConnector",
        "action": "ingestion_complete",
        "sources_processed": len(raw_data),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"🔌 SGSSTConnector: {len(raw_data)} sources ingérées")
    
    return state


# =============================================================================
# AGENT 2: DATA NORMALIZER
# =============================================================================

DATA_NORMALIZER_PROMPT = """Tu es l'Agent DataNormalizer, expert en ontologie SST.

MISSION: Transformer les données brutes en entités SafetyGraph standardisées.

ONTOLOGIE CNESST/IRSST:
- Risques: RC1 (Chutes), RC2 (Ensevelissement), RC3 (Machines), etc.
- Zones: Types (bureau, industriel, stockage, extérieur)
- Équipements: Avec dates inspection et risques associés

OUTPUT: Nœuds et relations prêts pour Neo4j
"""

async def agent_data_normalizer(state: TwinState) -> TwinState:
    """Agent qui normalise vers ontologie SafetyGraph"""
    logger.info("📊 Agent DataNormalizer: Normalisation ontologie CNESST...")
    
    normalized_entities = []
    risks = []
    zones = []
    equipment = []
    
    for source_data in state.get("raw_data", []):
        source = source_data.get("source", "unknown")
        data = source_data.get("data", {})
        
        # Normaliser selon la source
        if source == "intellect":
            # Audits → Risques
            for audit in data.get("audits", []):
                for finding in audit.get("findings", []):
                    risk = {
                        "id": f"RSK-{uuid.uuid4().hex[:8]}",
                        "source": "intellect",
                        "source_id": audit.get("id"),
                        "category": finding.get("category", "RC0_AUTRE"),
                        "description": finding.get("description", ""),
                        "severity": "high" if finding.get("type") == "risk" else "medium",
                        "site": audit.get("site", ""),
                        "date_detected": audit.get("date"),
                        "status": "open",
                        "cnesst_code": finding.get("category", "").split("_")[0]
                    }
                    risks.append(risk)
                    normalized_entities.append({"type": "Risk", "data": risk})
        
        elif source == "conformit_ai":
            # Permis → Risques + Zones
            for permit in data.get("permits", []):
                zone = {
                    "id": f"ZON-{uuid.uuid4().hex[:8]}",
                    "name": permit.get("location", ""),
                    "type": permit.get("type", ""),
                    "risk_level": "high" if "confined" in permit.get("type", "") else "medium",
                    "active_permits": [permit.get("id")]
                }
                zones.append(zone)
                normalized_entities.append({"type": "Zone", "data": zone})
                
                for risk_cat in permit.get("risks", []):
                    risk = {
                        "id": f"RSK-{uuid.uuid4().hex[:8]}",
                        "source": "conformit_ai",
                        "source_id": permit.get("id"),
                        "category": risk_cat,
                        "description": f"Risque lié au permis {permit.get('type')}",
                        "zone_id": zone["id"],
                        "severity": "high",
                        "valid_until": permit.get("valid_until")
                    }
                    risks.append(risk)
                    normalized_entities.append({"type": "Risk", "data": risk})
        
        elif source == "document_upload":
            # Document → Risques + Zones + Équipements
            for risk_data in data.get("risks_found", []):
                risk = {
                    "id": f"RSK-{uuid.uuid4().hex[:8]}",
                    "source": "document",
                    "source_id": data.get("document_id"),
                    "category": risk_data.get("category"),
                    "description": risk_data.get("description"),
                    "severity": risk_data.get("severity"),
                    "coordinates": risk_data.get("coordinates"),
                    "location_name": risk_data.get("location")
                }
                risks.append(risk)
                normalized_entities.append({"type": "Risk", "data": risk})
            
            for zone_data in data.get("zones_found", []):
                zone = {
                    "id": f"ZON-{uuid.uuid4().hex[:8]}",
                    "name": zone_data.get("name"),
                    "type": zone_data.get("type"),
                    "risk_level": zone_data.get("risk_level")
                }
                zones.append(zone)
                normalized_entities.append({"type": "Zone", "data": zone})
            
            for equip_data in data.get("equipment_found", []):
                equip = {
                    "id": equip_data.get("id"),
                    "name": equip_data.get("name"),
                    "zone": equip_data.get("zone"),
                    "last_inspection": equip_data.get("last_inspection"),
                    "status": "active"
                }
                equipment.append(equip)
                normalized_entities.append({"type": "Equipment", "data": equip})
    
    state["normalized_entities"] = normalized_entities
    state["risks"] = risks
    state["zones"] = zones
    state["equipment"] = equipment
    
    # Audit log
    state["audit_log"].append({
        "agent": "DataNormalizer",
        "action": "normalization_complete",
        "risks_count": len(risks),
        "zones_count": len(zones),
        "equipment_count": len(equipment),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"📊 DataNormalizer: {len(risks)} risques, {len(zones)} zones, {len(equipment)} équipements")
    
    return state


# =============================================================================
# AGENT 3: TWIN BUILDER
# =============================================================================

TWIN_BUILDER_PROMPT = """Tu es l'Agent TwinBuilder, architecte du jumeau numérique.

MISSION: Créer et maintenir le Digital Twin 3D avec toutes les entités HSE.

RESPONSABILITÉS:
1. Créer/mettre à jour les nœuds SafetyGraph (Neo4j)
2. Positionner les risques en coordonnées 3D
3. Générer la heatmap de risques
4. Versionner le Twin

OUTPUT: Twin ID + version + éléments spatiaux
"""

async def agent_twin_builder(state: TwinState) -> TwinState:
    """Agent qui construit le Digital Twin"""
    logger.info("🏗️ Agent TwinBuilder: Construction du jumeau numérique...")
    
    twin_id = state.get("twin_id") or f"TWIN-{uuid.uuid4().hex[:8]}"
    twin_version = state.get("twin_version", 0) + 1
    
    cypher_queries = []
    spatial_elements = []
    nodes_created = 0
    rels_created = 0
    
    # Créer les nœuds Zone dans Neo4j
    for zone in state.get("zones", []):
        cypher = f"""
        MERGE (z:Zone {{id: '{zone["id"]}'}})
        SET z.name = '{zone.get("name", "")}',
            z.type = '{zone.get("type", "")}',
            z.risk_level = '{zone.get("risk_level", "medium")}',
            z.twin_id = '{twin_id}',
            z.updated_at = datetime()
        RETURN z
        """
        cypher_queries.append(cypher)
        nodes_created += 1
        
        spatial_elements.append({
            "type": "zone",
            "id": zone["id"],
            "name": zone.get("name"),
            "risk_level": zone.get("risk_level"),
            "geometry": "polygon"
        })
    
    # Créer les nœuds Risk et lier aux Zones
    for risk in state.get("risks", []):
        cypher = f"""
        MERGE (r:Risk {{id: '{risk["id"]}'}})
        SET r.category = '{risk.get("category", "")}',
            r.description = '{risk.get("description", "").replace("'", "''")}',
            r.severity = '{risk.get("severity", "medium")}',
            r.source = '{risk.get("source", "")}',
            r.status = '{risk.get("status", "open")}',
            r.twin_id = '{twin_id}',
            r.updated_at = datetime()
        RETURN r
        """
        cypher_queries.append(cypher)
        nodes_created += 1
        
        # Lier Risk → Zone si zone_id existe
        if risk.get("zone_id"):
            cypher_rel = f"""
            MATCH (r:Risk {{id: '{risk["id"]}'}}), (z:Zone {{id: '{risk["zone_id"]}'}})
            MERGE (r)-[:LOCATED_IN]->(z)
            """
            cypher_queries.append(cypher_rel)
            rels_created += 1
        
        # Élément spatial avec coordonnées 3D
        coords = risk.get("coordinates", {})
        spatial_elements.append({
            "type": "risk_marker",
            "id": risk["id"],
            "category": risk.get("category"),
            "severity": risk.get("severity"),
            "coordinates": {
                "x": coords.get("x", 0),
                "y": coords.get("y", 0),
                "z": coords.get("z", 0)
            },
            "color": "#FF0000" if risk.get("severity") == "critical" else "#FFA500" if risk.get("severity") == "high" else "#FFFF00"
        })
    
    # Créer les nœuds Equipment
    for equip in state.get("equipment", []):
        cypher = f"""
        MERGE (e:Equipment {{id: '{equip["id"]}'}})
        SET e.name = '{equip.get("name", "")}',
            e.zone = '{equip.get("zone", "")}',
            e.last_inspection = '{equip.get("last_inspection", "")}',
            e.status = '{equip.get("status", "active")}',
            e.twin_id = '{twin_id}',
            e.updated_at = datetime()
        RETURN e
        """
        cypher_queries.append(cypher)
        nodes_created += 1
        
        spatial_elements.append({
            "type": "equipment",
            "id": equip["id"],
            "name": equip.get("name"),
            "zone": equip.get("zone"),
            "icon": "machine"
        })
    
    # Générer heatmap de risques
    risk_heatmap = {}
    for risk in state.get("risks", []):
        category = risk.get("category", "OTHER")
        severity = risk.get("severity", "medium")
        
        if category not in risk_heatmap:
            risk_heatmap[category] = {"count": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
        
        risk_heatmap[category]["count"] += 1
        risk_heatmap[category][severity] += 1
    
    state["twin_id"] = twin_id
    state["twin_version"] = twin_version
    state["cypher_queries"] = cypher_queries
    state["kg_nodes_created"] = nodes_created
    state["kg_relationships_created"] = rels_created
    state["spatial_elements"] = spatial_elements
    state["risk_heatmap"] = risk_heatmap
    
    # Audit log
    state["audit_log"].append({
        "agent": "TwinBuilder",
        "action": "twin_built",
        "twin_id": twin_id,
        "version": twin_version,
        "nodes_created": nodes_created,
        "relationships_created": rels_created,
        "spatial_elements": len(spatial_elements),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"🏗️ TwinBuilder: Twin {twin_id} v{twin_version} - {nodes_created} nœuds, {len(spatial_elements)} éléments spatiaux")
    
    return state


# =============================================================================
# AGENT 4: PLAYBOOK GENERATOR
# =============================================================================

PLAYBOOK_GENERATOR_PROMPT = """Tu es l'Agent PlaybookGenerator, créateur de playbooks auto-apprenants.

MISSION: Générer des playbooks de prévention basés sur les risques détectés.

PLAYBOOK STRUCTURE:
1. Titre et catégorie CNESST
2. Conditions de déclenchement
3. Actions séquentielles
4. Références réglementaires (LMRSST, Vision Zero)
5. Métriques de succès

AUTO-APPRENTISSAGE:
- Ajuster priorités selon fréquence incidents
- Intégrer feedback terrain
- Optimiser séquences d'actions
"""

async def agent_playbook_generator(state: TwinState) -> TwinState:
    """Agent qui génère les playbooks auto-apprenants"""
    logger.info("📚 Agent PlaybookGenerator: Génération playbooks...")
    
    playbooks = []
    recommendations = []
    
    # Analyser les risques par catégorie
    risk_by_category = {}
    for risk in state.get("risks", []):
        cat = risk.get("category", "OTHER")
        if cat not in risk_by_category:
            risk_by_category[cat] = []
        risk_by_category[cat].append(risk)
    
    # Générer playbook pour chaque catégorie à risque
    playbook_templates = {
        "RC1_CHUTES_HAUTEUR": {
            "title": "Playbook Prévention Chutes de Hauteur",
            "triggers": ["Travaux > 3m", "Échafaudage", "Toiture", "Échelle"],
            "actions": [
                {"step": 1, "action": "Vérifier EPI (harnais, longe, point d'ancrage)", "responsible": "Superviseur"},
                {"step": 2, "action": "Inspecter garde-corps et protections collectives", "responsible": "Préventeur"},
                {"step": 3, "action": "Former travailleurs sur procédure sécuritaire", "responsible": "Formateur HSE"},
                {"step": 4, "action": "Délimiter zone de travail", "responsible": "Chef d'équipe"},
                {"step": 5, "action": "Documenter dans registre SST", "responsible": "Coordonnateur"}
            ],
            "references": ["RSST art. 346-354", "LMRSST art. 51", "Vision Zero - Chutes"]
        },
        "RC5_ESPACES_CLOS": {
            "title": "Playbook Entrée Espaces Clos",
            "triggers": ["Permis espace clos actif", "Réservoir", "Cuve", "Tunnel"],
            "actions": [
                {"step": 1, "action": "Émettre permis d'entrée", "responsible": "Superviseur qualifié"},
                {"step": 2, "action": "Tester atmosphère (O2, LEL, H2S, CO)", "responsible": "Entrant qualifié"},
                {"step": 3, "action": "Positionner surveillant à l'entrée", "responsible": "Surveillant"},
                {"step": 4, "action": "Vérifier équipement de sauvetage", "responsible": "Équipe secours"},
                {"step": 5, "action": "Communication continue pendant travaux", "responsible": "Tous"}
            ],
            "references": ["RSST art. 297-310", "CSA Z1006", "LMRSST art. 51.3"]
        },
        "RC3_MACHINES": {
            "title": "Playbook Sécurité Machines",
            "triggers": ["Maintenance machine", "Cadenassage", "Déblocage"],
            "actions": [
                {"step": 1, "action": "Appliquer procédure LOTO (Lock Out Tag Out)", "responsible": "Opérateur"},
                {"step": 2, "action": "Vérifier absence d'énergie résiduelle", "responsible": "Électricien"},
                {"step": 3, "action": "Installer protecteurs avant remise en marche", "responsible": "Mécanicien"},
                {"step": 4, "action": "Test fonctionnel sécuritaire", "responsible": "Superviseur"},
                {"step": 5, "action": "Documenter intervention", "responsible": "Maintenance"}
            ],
            "references": ["RSST art. 185-195", "CSA Z460", "LMRSST art. 51"]
        },
        "RC8_ERGONOMIE_TMS": {
            "title": "Playbook Prévention TMS",
            "triggers": ["Manutention répétitive", "Postures contraignantes", "Vibrations"],
            "actions": [
                {"step": 1, "action": "Évaluer poste avec grille OSHA/NIOSH", "responsible": "Ergonome"},
                {"step": 2, "action": "Implanter aides mécaniques", "responsible": "Ingénieur"},
                {"step": 3, "action": "Former aux techniques de manutention", "responsible": "Formateur"},
                {"step": 4, "action": "Organiser rotation des tâches", "responsible": "Superviseur"},
                {"step": 5, "action": "Suivi médical préventif", "responsible": "SST"}
            ],
            "references": ["RSST art. 166-170", "Guide IRSST TMS", "Vision Zero - Ergonomie"]
        }
    }
    
    for category, risks_list in risk_by_category.items():
        template = playbook_templates.get(category)
        
        if template:
            playbook = {
                "id": f"PLB-{uuid.uuid4().hex[:8]}",
                "title": template["title"],
                "category": category,
                "triggers": template["triggers"],
                "actions": template["actions"],
                "references": template["references"],
                "risks_covered": [r["id"] for r in risks_list],
                "risk_count": len(risks_list),
                "priority": "P1" if len(risks_list) >= 3 or any(r.get("severity") == "critical" for r in risks_list) else "P2",
                "auto_learning": {
                    "last_update": datetime.now().isoformat(),
                    "effectiveness_score": 0.85,
                    "adjustments": []
                },
                "twin_id": state.get("twin_id"),
                "generated_at": datetime.now().isoformat()
            }
            playbooks.append(playbook)
            
            # Générer recommandation
            recommendations.append(
                f"⚠️ {len(risks_list)} risques {category}: Appliquer '{template['title']}'"
            )
        else:
            recommendations.append(
                f"ℹ️ {len(risks_list)} risques {category}: Créer playbook personnalisé"
            )
    
    # Recommandations globales basées sur heatmap
    heatmap = state.get("risk_heatmap", {})
    total_critical = sum(h.get("critical", 0) for h in heatmap.values())
    
    if total_critical > 0:
        recommendations.insert(0, f"🚨 {total_critical} risques CRITIQUES nécessitent action immédiate!")
    
    state["playbooks_generated"] = playbooks
    state["recommendations"] = recommendations
    
    # Audit log
    state["audit_log"].append({
        "agent": "PlaybookGenerator",
        "action": "playbooks_generated",
        "playbooks_count": len(playbooks),
        "recommendations_count": len(recommendations),
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"📚 PlaybookGenerator: {len(playbooks)} playbooks, {len(recommendations)} recommandations")
    
    return state


# =============================================================================
# AGENT 5: TWIN ORCHESTRATOR
# =============================================================================

TWIN_ORCHESTRATOR_PROMPT = """Tu es l'Agent TwinOrchestrator, chef d'orchestre du Digital Twin.

MISSION: Coordonner tous les agents et assurer la cohérence du système.

RESPONSABILITÉS:
1. Valider la qualité des données
2. Déclencher les mises à jour appropriées
3. Générer le rapport de synthèse
4. Notifier les parties prenantes
"""

async def agent_twin_orchestrator(state: TwinState) -> TwinState:
    """Agent orchestrateur principal"""
    logger.info("🎯 Agent TwinOrchestrator: Finalisation...")
    
    # Calculer temps de traitement
    start_time = datetime.fromisoformat(state.get("timestamp", datetime.now().isoformat()))
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # Synthèse
    summary = {
        "session_id": state.get("session_id"),
        "twin_id": state.get("twin_id"),
        "twin_version": state.get("twin_version"),
        "sources_ingested": len(state.get("raw_data", [])),
        "total_risks": len(state.get("risks", [])),
        "total_zones": len(state.get("zones", [])),
        "total_equipment": len(state.get("equipment", [])),
        "kg_nodes": state.get("kg_nodes_created", 0),
        "kg_relationships": state.get("kg_relationships_created", 0),
        "playbooks": len(state.get("playbooks_generated", [])),
        "processing_time_ms": processing_time,
        "status": "success"
    }
    
    state["processing_time_ms"] = processing_time
    
    # Audit log final
    state["audit_log"].append({
        "agent": "TwinOrchestrator",
        "action": "orchestration_complete",
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info("=" * 60)
    logger.info("📊 SYNTHÈSE DIGITAL TWIN")
    logger.info(f"   Twin ID: {state.get('twin_id')}")
    logger.info(f"   Version: {state.get('twin_version')}")
    logger.info(f"   Risques: {len(state.get('risks', []))}")
    logger.info(f"   Zones: {len(state.get('zones', []))}")
    logger.info(f"   Équipements: {len(state.get('equipment', []))}")
    logger.info(f"   Playbooks: {len(state.get('playbooks_generated', []))}")
    logger.info(f"   Temps: {processing_time}ms")
    logger.info("=" * 60)
    
    return state


# =============================================================================
# GRAPHE D'ORCHESTRATION
# =============================================================================

def create_digital_twin_graph() -> StateGraph:
    """Crée le graphe d'orchestration Digital Twin"""
    
    workflow = StateGraph(TwinState)
    
    # Ajouter les agents
    workflow.add_node("sgsst_connector", agent_sgsst_connector)
    workflow.add_node("data_normalizer", agent_data_normalizer)
    workflow.add_node("twin_builder", agent_twin_builder)
    workflow.add_node("playbook_generator", agent_playbook_generator)
    workflow.add_node("twin_orchestrator", agent_twin_orchestrator)
    
    # Flux linéaire
    workflow.set_entry_point("sgsst_connector")
    workflow.add_edge("sgsst_connector", "data_normalizer")
    workflow.add_edge("data_normalizer", "twin_builder")
    workflow.add_edge("twin_builder", "playbook_generator")
    workflow.add_edge("playbook_generator", "twin_orchestrator")
    workflow.add_edge("twin_orchestrator", END)
    
    return workflow.compile()


# =============================================================================
# INTERFACE PRINCIPALE
# =============================================================================

class SafeTwinDigitalTwinHub:
    """Interface principale du système Digital Twin Agentique"""
    
    def __init__(self):
        self.graph = create_digital_twin_graph()
        self.twins: Dict[str, TwinState] = {}
    
    def create_initial_state(
        self,
        source: str = "all",
        data_type: str = "auto",
        document_path: str = None
    ) -> TwinState:
        """Crée un état initial"""
        
        session_id = f"DT-{uuid.uuid4().hex[:12]}"
        
        state = TwinState(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            raw_data=[{"path": document_path}] if document_path else [],
            source=source,
            data_type="document_upload" if document_path else data_type,
            normalized_entities=[],
            risks=[],
            zones=[],
            equipment=[],
            kg_nodes_created=0,
            kg_relationships_created=0,
            cypher_queries=[],
            twin_id="",
            twin_version=0,
            spatial_elements=[],
            risk_heatmap={},
            playbooks_generated=[],
            recommendations=[],
            audit_log=[],
            processing_time_ms=0
        )
        
        return state
    
    async def ingest_from_sgsst(self, sources: List[str] = None) -> TwinState:
        """Ingérer depuis les SGSST configurés"""
        source = "all" if not sources else sources[0]
        state = self.create_initial_state(source=source)
        result = await self.graph.ainvoke(state)
        self.twins[result["twin_id"]] = result
        return result
    
    async def ingest_document(self, document_path: str) -> TwinState:
        """Ingérer depuis un document PDF/BIM"""
        state = self.create_initial_state(document_path=document_path)
        result = await self.graph.ainvoke(state)
        self.twins[result["twin_id"]] = result
        return result
    
    async def update_twin(self, twin_id: str, source: str = "all") -> TwinState:
        """Mettre à jour un twin existant"""
        existing = self.twins.get(twin_id)
        state = self.create_initial_state(source=source)
        
        if existing:
            state["twin_id"] = twin_id
            state["twin_version"] = existing.get("twin_version", 0)
        
        result = await self.graph.ainvoke(state)
        self.twins[result["twin_id"]] = result
        return result
    
    def get_twin(self, twin_id: str) -> Optional[TwinState]:
        """Récupérer un twin"""
        return self.twins.get(twin_id)
    
    def list_twins(self) -> List[Dict]:
        """Lister tous les twins"""
        return [
            {
                "twin_id": t["twin_id"],
                "version": t["twin_version"],
                "risks": len(t.get("risks", [])),
                "zones": len(t.get("zones", []))
            }
            for t in self.twins.values()
        ]


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

async def main():
    """Point d'entrée principal"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🏗️  SAFETWIN X5 - DIGITAL TWIN AGENTIQUE                   ║
    ║   Ingestion Multi-Sources SGSST + Jumeaux Numériques HSE    ║
    ║                                                              ║
    ║   Agents: SGSSTConnector | DataNormalizer | TwinBuilder     ║
    ║           PlaybookGenerator | TwinOrchestrator              ║
    ║                                                              ║
    ║   Sources: Intellect | CONFORMiT.ai | MEDIAL+ | SharePoint  ║
    ║                                                              ║
    ║   Conformité: Vision Zero | LMRSST | ISO 45001              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    hub = SafeTwinDigitalTwinHub()
    
    # Démo 1: Ingestion depuis SGSST
    print("\n📥 DÉMO 1: Ingestion depuis sources SGSST\n")
    result1 = await hub.ingest_from_sgsst()
    
    print(f"\n✅ Twin créé: {result1['twin_id']}")
    print(f"   Risques: {len(result1['risks'])}")
    print(f"   Zones: {len(result1['zones'])}")
    print(f"   Playbooks: {len(result1['playbooks_generated'])}")
    
    # Démo 2: Ingestion depuis document
    print("\n\n📄 DÉMO 2: Ingestion depuis document PDF\n")
    result2 = await hub.ingest_document("/docs/Programme_Prevention_2026.pdf")
    
    print(f"\n✅ Twin créé: {result2['twin_id']}")
    print(f"   Risques extraits: {len(result2['risks'])}")
    print(f"   Zones identifiées: {len(result2['zones'])}")
    print(f"   Équipements: {len(result2['equipment'])}")
    
    # Afficher recommandations
    print("\n\n📋 RECOMMANDATIONS:")
    for rec in result2.get("recommendations", []):
        print(f"   {rec}")
    
    # Afficher playbooks
    print("\n\n📚 PLAYBOOKS GÉNÉRÉS:")
    for pb in result2.get("playbooks_generated", []):
        print(f"   [{pb['priority']}] {pb['title']} - {pb['risk_count']} risques couverts")


if __name__ == "__main__":
    asyncio.run(main())
