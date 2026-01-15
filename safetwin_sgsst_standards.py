#!/usr/bin/env python3
"""
================================================================================
SAFETWIN DIGITAL TWIN HUB - STANDARDS D'INGESTION SGSST
================================================================================

Architecture d'ingestion AGNOSTIQUE des plateformes SGSST
Basée sur les 15 dimensions SSE/HSE standardisées (ISO 45001/14001)

PRINCIPE:
  - Ne dépend pas d'une plateforme spécifique
  - Définit les STANDARDS de données pour chaque dimension SSE/HSE
  - Adaptateurs génériques pour n'importe quel SGSST
  - Transformation vers ontologie SafetyGraph unifiée

DIMENSIONS SSE/HSE SUPPORTÉES (15):
  1.  Gouvernance & Politique
  2.  Risques & Opportunités
  3.  Conformité & Exigences
  4.  Santé & Sécurité au Travail
  5.  Environnement
  6.  Produits Chimiques / Dangereux
  7.  Opérations & Contrôles
  8.  Incidents & Non-Conformités
  9.  Changements & Projets
  10. Compétences & Culture
  11. Communication & Participation
  12. Urgences & Crise
  13. Audits, Inspections & Revue
  14. Indicateurs & Reporting
  15. Amélioration Continue

Conformité: ISO 45001, ISO 14001, CNESST/LSST, Vision Zero
================================================================================
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Protocol
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("SafeTwinIngestion")


# =============================================================================
# SECTION 1: LES 15 DIMENSIONS SSE/HSE STANDARDISÉES
# =============================================================================

class SSEDimension(Enum):
    """Les 15 dimensions SSE/HSE standardisées ISO 45001/14001"""
    
    GOVERNANCE_POLICY = "governance_policy"
    RISKS_OPPORTUNITIES = "risks_opportunities"
    COMPLIANCE_REQUIREMENTS = "compliance_requirements"
    OCCUPATIONAL_HEALTH_SAFETY = "occupational_health_safety"
    ENVIRONMENT = "environment"
    HAZARDOUS_MATERIALS = "hazardous_materials"
    OPERATIONS_CONTROLS = "operations_controls"
    INCIDENTS_NONCONFORMITIES = "incidents_nonconformities"
    CHANGE_MANAGEMENT = "change_management"
    COMPETENCIES_CULTURE = "competencies_culture"
    COMMUNICATION_PARTICIPATION = "communication_participation"
    EMERGENCY_CRISIS = "emergency_crisis"
    AUDITS_INSPECTIONS = "audits_inspections"
    INDICATORS_REPORTING = "indicators_reporting"
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"


# =============================================================================
# SECTION 2: SCHÉMAS DE DONNÉES STANDARDISÉS PAR DIMENSION
# =============================================================================

@dataclass
class StandardSchema:
    """Schéma de données standardisé pour une dimension SSE/HSE"""
    dimension: SSEDimension
    required_fields: List[str]
    optional_fields: List[str]
    relationships: List[str]
    neo4j_labels: List[str]
    cnesst_mapping: Optional[str] = None
    iso_clause: Optional[str] = None


# Définition des schémas pour chaque dimension
DIMENSION_SCHEMAS: Dict[SSEDimension, StandardSchema] = {
    
    # 1. Gouvernance & Politique
    SSEDimension.GOVERNANCE_POLICY: StandardSchema(
        dimension=SSEDimension.GOVERNANCE_POLICY,
        required_fields=[
            "policy_id", "title", "version", "effective_date", 
            "approved_by", "scope", "objectives"
        ],
        optional_fields=[
            "review_date", "document_url", "responsibilities", 
            "committee_members", "meeting_frequency"
        ],
        relationships=["APPLIES_TO:Zone", "OWNED_BY:Organization", "REVIEWED_BY:Person"],
        neo4j_labels=["Policy", "Governance", "Committee"],
        iso_clause="ISO 45001:5.1-5.4",
        cnesst_mapping="Programme de prévention"
    ),
    
    # 2. Risques & Opportunités
    SSEDimension.RISKS_OPPORTUNITIES: StandardSchema(
        dimension=SSEDimension.RISKS_OPPORTUNITIES,
        required_fields=[
            "risk_id", "title", "category", "severity", "probability",
            "risk_score", "status", "identified_date"
        ],
        optional_fields=[
            "description", "location", "coordinates", "affected_workers",
            "control_measures", "residual_risk", "review_date", "owner"
        ],
        relationships=[
            "LOCATED_IN:Zone", "AFFECTS:Equipment", "MITIGATED_BY:ControlMeasure",
            "IDENTIFIED_BY:Person", "LINKED_TO:Incident"
        ],
        neo4j_labels=["Risk", "Hazard", "Opportunity"],
        iso_clause="ISO 45001:6.1",
        cnesst_mapping="RC1-RC8 Catégories CNESST"
    ),
    
    # 3. Conformité & Exigences
    SSEDimension.COMPLIANCE_REQUIREMENTS: StandardSchema(
        dimension=SSEDimension.COMPLIANCE_REQUIREMENTS,
        required_fields=[
            "requirement_id", "title", "type", "source", 
            "jurisdiction", "effective_date", "status"
        ],
        optional_fields=[
            "description", "deadline", "responsible_party", 
            "evidence_required", "last_evaluation", "next_evaluation"
        ],
        relationships=[
            "APPLIES_TO:Organization", "EVALUATED_BY:Audit",
            "DOCUMENTED_IN:Document", "ENFORCED_BY:Authority"
        ],
        neo4j_labels=["Requirement", "Regulation", "Standard", "Obligation"],
        iso_clause="ISO 45001:6.1.3",
        cnesst_mapping="LSST, RSST, CNESST"
    ),
    
    # 4. Santé & Sécurité au Travail
    SSEDimension.OCCUPATIONAL_HEALTH_SAFETY: StandardSchema(
        dimension=SSEDimension.OCCUPATIONAL_HEALTH_SAFETY,
        required_fields=[
            "record_id", "type", "worker_id", "date", "status"
        ],
        optional_fields=[
            "description", "body_part", "injury_type", "days_lost",
            "treatment", "restrictions", "return_to_work_date",
            "exposure_type", "exposure_level", "medical_surveillance"
        ],
        relationships=[
            "INVOLVES:Worker", "OCCURRED_AT:Zone", "CAUSED_BY:Risk",
            "TREATED_BY:MedicalProvider", "REPORTED_TO:Authority"
        ],
        neo4j_labels=["HealthRecord", "Injury", "Exposure", "Ergonomic"],
        iso_clause="ISO 45001:8.1.2",
        cnesst_mapping="Lésions professionnelles, AT/MP"
    ),
    
    # 5. Environnement
    SSEDimension.ENVIRONMENT: StandardSchema(
        dimension=SSEDimension.ENVIRONMENT,
        required_fields=[
            "aspect_id", "type", "impact_type", "significance", "status"
        ],
        optional_fields=[
            "description", "location", "measurement_value", "unit",
            "threshold", "monitoring_frequency", "mitigation_measures"
        ],
        relationships=[
            "LOCATED_AT:Zone", "MONITORED_BY:Equipment",
            "REGULATED_BY:Requirement", "REPORTED_IN:Report"
        ],
        neo4j_labels=["EnvironmentalAspect", "Emission", "Waste", "Energy"],
        iso_clause="ISO 14001:6.1.2",
        cnesst_mapping="Aspects environnementaux"
    ),
    
    # 6. Produits Chimiques / Dangereux
    SSEDimension.HAZARDOUS_MATERIALS: StandardSchema(
        dimension=SSEDimension.HAZARDOUS_MATERIALS,
        required_fields=[
            "material_id", "name", "cas_number", "hazard_class",
            "quantity", "location", "sds_available"
        ],
        optional_fields=[
            "supplier", "sds_date", "storage_requirements", "ppe_required",
            "exposure_limits", "first_aid", "spill_procedure"
        ],
        relationships=[
            "STORED_IN:Zone", "USED_BY:Process", "REQUIRES:PPE",
            "DOCUMENTED_IN:SDS", "REGULATED_BY:Requirement"
        ],
        neo4j_labels=["HazardousMaterial", "Chemical", "SDS"],
        iso_clause="ISO 45001:8.1.2",
        cnesst_mapping="SIMDUT, SGH"
    ),
    
    # 7. Opérations & Contrôles
    SSEDimension.OPERATIONS_CONTROLS: StandardSchema(
        dimension=SSEDimension.OPERATIONS_CONTROLS,
        required_fields=[
            "control_id", "type", "title", "status", "effective_date"
        ],
        optional_fields=[
            "description", "procedure_url", "responsible", "frequency",
            "verification_method", "deviation_handling"
        ],
        relationships=[
            "APPLIES_TO:Process", "DOCUMENTED_IN:Procedure",
            "VERIFIED_BY:Inspection", "MITIGATES:Risk"
        ],
        neo4j_labels=["Control", "Procedure", "Permit", "LOTO"],
        iso_clause="ISO 45001:8.1",
        cnesst_mapping="Procédures de travail sécuritaire"
    ),
    
    # 8. Incidents & Non-Conformités
    SSEDimension.INCIDENTS_NONCONFORMITIES: StandardSchema(
        dimension=SSEDimension.INCIDENTS_NONCONFORMITIES,
        required_fields=[
            "incident_id", "type", "date", "time", "location",
            "severity", "status"
        ],
        optional_fields=[
            "description", "immediate_cause", "root_cause", "witnesses",
            "injuries", "damages", "corrective_actions", "preventive_actions",
            "investigation_date", "closure_date", "lessons_learned"
        ],
        relationships=[
            "OCCURRED_AT:Zone", "INVOLVED:Worker", "CAUSED_BY:Risk",
            "INVESTIGATED_BY:Person", "RESULTED_IN:Action"
        ],
        neo4j_labels=["Incident", "NearMiss", "NonConformity", "Accident"],
        iso_clause="ISO 45001:10.2",
        cnesst_mapping="Déclaration CNESST, ADR"
    ),
    
    # 9. Changements & Projets
    SSEDimension.CHANGE_MANAGEMENT: StandardSchema(
        dimension=SSEDimension.CHANGE_MANAGEMENT,
        required_fields=[
            "change_id", "title", "type", "status", "requested_date",
            "requestor"
        ],
        optional_fields=[
            "description", "justification", "risk_assessment",
            "affected_areas", "implementation_date", "approval_status",
            "approvers", "rollback_plan"
        ],
        relationships=[
            "AFFECTS:Zone", "ASSESSED_FOR:Risk", "APPROVED_BY:Person",
            "DOCUMENTED_IN:Document", "TRIGGERS:Action"
        ],
        neo4j_labels=["Change", "MOC", "Project"],
        iso_clause="ISO 45001:8.1.3",
        cnesst_mapping="Gestion des changements"
    ),
    
    # 10. Compétences & Culture
    SSEDimension.COMPETENCIES_CULTURE: StandardSchema(
        dimension=SSEDimension.COMPETENCIES_CULTURE,
        required_fields=[
            "training_id", "title", "type", "status", "target_audience"
        ],
        optional_fields=[
            "description", "duration", "provider", "certification",
            "validity_period", "completion_date", "score", "refresher_date"
        ],
        relationships=[
            "COMPLETED_BY:Worker", "REQUIRED_FOR:Job", "COVERS:Risk",
            "PROVIDED_BY:Trainer", "DOCUMENTED_IN:Certificate"
        ],
        neo4j_labels=["Training", "Competency", "Certification", "Awareness"],
        iso_clause="ISO 45001:7.2-7.3",
        cnesst_mapping="Formation SST obligatoire"
    ),
    
    # 11. Communication & Participation
    SSEDimension.COMMUNICATION_PARTICIPATION: StandardSchema(
        dimension=SSEDimension.COMMUNICATION_PARTICIPATION,
        required_fields=[
            "communication_id", "type", "date", "participants", "status"
        ],
        optional_fields=[
            "subject", "summary", "decisions", "action_items",
            "next_meeting", "attachments"
        ],
        relationships=[
            "ATTENDED_BY:Person", "DISCUSSED:Risk", "RESULTED_IN:Action",
            "DOCUMENTED_IN:Minutes", "RELATED_TO:Incident"
        ],
        neo4j_labels=["Meeting", "Communication", "Consultation", "Observation"],
        iso_clause="ISO 45001:7.4",
        cnesst_mapping="CSS, Comité SST"
    ),
    
    # 12. Urgences & Crise
    SSEDimension.EMERGENCY_CRISIS: StandardSchema(
        dimension=SSEDimension.EMERGENCY_CRISIS,
        required_fields=[
            "plan_id", "title", "type", "version", "effective_date", "status"
        ],
        optional_fields=[
            "description", "scope", "responsibilities", "resources",
            "evacuation_routes", "assembly_points", "communication_tree",
            "drill_frequency", "last_drill_date", "next_drill_date"
        ],
        relationships=[
            "APPLIES_TO:Zone", "INVOLVES:Equipment", "COORDINATED_BY:Person",
            "TESTED_BY:Drill", "DOCUMENTED_IN:Procedure"
        ],
        neo4j_labels=["EmergencyPlan", "Drill", "Crisis", "Evacuation"],
        iso_clause="ISO 45001:8.2",
        cnesst_mapping="Plan d'urgence, Évacuation"
    ),
    
    # 13. Audits, Inspections & Revue
    SSEDimension.AUDITS_INSPECTIONS: StandardSchema(
        dimension=SSEDimension.AUDITS_INSPECTIONS,
        required_fields=[
            "audit_id", "type", "date", "auditor", "scope", "status"
        ],
        optional_fields=[
            "checklist_used", "findings", "score", "non_conformities",
            "observations", "recommendations", "follow_up_date",
            "closure_date", "report_url"
        ],
        relationships=[
            "AUDITED:Zone", "CONDUCTED_BY:Auditor", "FOUND:NonConformity",
            "DOCUMENTED_IN:Report", "RESULTED_IN:Action"
        ],
        neo4j_labels=["Audit", "Inspection", "Review", "Assessment"],
        iso_clause="ISO 45001:9.2-9.3",
        cnesst_mapping="Audit interne, Inspection CNESST"
    ),
    
    # 14. Indicateurs & Reporting
    SSEDimension.INDICATORS_REPORTING: StandardSchema(
        dimension=SSEDimension.INDICATORS_REPORTING,
        required_fields=[
            "kpi_id", "name", "type", "value", "unit", "period", "target"
        ],
        optional_fields=[
            "description", "formula", "data_source", "frequency",
            "trend", "benchmark", "responsible", "dashboard_url"
        ],
        relationships=[
            "MEASURES:Process", "REPORTED_TO:Stakeholder",
            "COMPARED_TO:Benchmark", "VISUALIZED_IN:Dashboard"
        ],
        neo4j_labels=["KPI", "Metric", "Report", "Dashboard"],
        iso_clause="ISO 45001:9.1",
        cnesst_mapping="TRIR, LTIFR, Fréquence/Gravité"
    ),
    
    # 15. Amélioration Continue
    SSEDimension.CONTINUOUS_IMPROVEMENT: StandardSchema(
        dimension=SSEDimension.CONTINUOUS_IMPROVEMENT,
        required_fields=[
            "action_id", "type", "title", "status", "created_date", "owner"
        ],
        optional_fields=[
            "description", "source", "priority", "target_date",
            "completion_date", "effectiveness", "lessons_learned",
            "related_incidents", "cost_savings"
        ],
        relationships=[
            "ADDRESSES:Risk", "ASSIGNED_TO:Person", "ORIGINATED_FROM:Incident",
            "DOCUMENTED_IN:Report", "VERIFIED_BY:Audit"
        ],
        neo4j_labels=["Action", "CAPA", "Improvement", "LessonLearned"],
        iso_clause="ISO 45001:10.3",
        cnesst_mapping="Actions correctives/préventives"
    ),
}


# =============================================================================
# SECTION 3: INTERFACE ADAPTATEUR SGSST (PROTOCOLE)
# =============================================================================

class SGSSTAdapter(Protocol):
    """
    Interface standard pour tout adaptateur SGSST.
    Toute plateforme SGSST doit implémenter cette interface.
    """
    
    @property
    def platform_name(self) -> str:
        """Nom de la plateforme SGSST"""
        ...
    
    @property
    def supported_dimensions(self) -> List[SSEDimension]:
        """Liste des dimensions SSE/HSE supportées par cette plateforme"""
        ...
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """Établir la connexion à la plateforme"""
        ...
    
    def fetch_data(self, dimension: SSEDimension, filters: Dict = None) -> List[Dict]:
        """Récupérer les données brutes pour une dimension"""
        ...
    
    def transform_to_standard(self, dimension: SSEDimension, raw_data: List[Dict]) -> List[Dict]:
        """Transformer les données vers le schéma standard SafeTwin"""
        ...


# =============================================================================
# SECTION 4: ADAPTATEUR GÉNÉRIQUE (TEMPLATE)
# =============================================================================

class GenericSGSSTAdapter(ABC):
    """
    Classe de base pour créer un adaptateur SGSST.
    Héritez de cette classe pour intégrer une nouvelle plateforme.
    """
    
    def __init__(self, platform_name: str, base_url: str, auth_type: str):
        self._platform_name = platform_name
        self.base_url = base_url
        self.auth_type = auth_type
        self.connected = False
        self.credentials = {}
        self._supported_dimensions: List[SSEDimension] = []
    
    @property
    def platform_name(self) -> str:
        return self._platform_name
    
    @property
    def supported_dimensions(self) -> List[SSEDimension]:
        return self._supported_dimensions
    
    @abstractmethod
    def connect(self, credentials: Dict[str, str]) -> bool:
        """À implémenter: logique de connexion spécifique à la plateforme"""
        pass
    
    @abstractmethod
    def fetch_data(self, dimension: SSEDimension, filters: Dict = None) -> List[Dict]:
        """À implémenter: logique de récupération spécifique"""
        pass
    
    def transform_to_standard(self, dimension: SSEDimension, raw_data: List[Dict]) -> List[Dict]:
        """
        Transforme les données brutes vers le schéma standard.
        Peut être surchargé pour des transformations spécifiques.
        """
        schema = DIMENSION_SCHEMAS.get(dimension)
        if not schema:
            raise ValueError(f"Dimension inconnue: {dimension}")
        
        standardized = []
        for record in raw_data:
            std_record = {
                "id": record.get("id") or str(uuid.uuid4()),
                "source_platform": self.platform_name,
                "dimension": dimension.value,
                "imported_at": datetime.now().isoformat(),
                "data": {}
            }
            
            # Mapper les champs requis
            for field in schema.required_fields:
                std_record["data"][field] = record.get(field) or self._map_field(field, record)
            
            # Mapper les champs optionnels présents
            for field in schema.optional_fields:
                if field in record or self._has_mapped_field(field, record):
                    std_record["data"][field] = record.get(field) or self._map_field(field, record)
            
            standardized.append(std_record)
        
        return standardized
    
    def _map_field(self, standard_field: str, record: Dict) -> Any:
        """
        À surcharger: mapping des noms de champs plateforme → standard.
        Par défaut, retourne None.
        """
        return None
    
    def _has_mapped_field(self, standard_field: str, record: Dict) -> bool:
        """Vérifie si un champ mappé existe"""
        return self._map_field(standard_field, record) is not None


# =============================================================================
# SECTION 5: NORMALIZER VERS SAFETYGRAPH
# =============================================================================

class SafetyGraphNormalizer:
    """
    Normalise les données standardisées vers l'ontologie SafetyGraph Neo4j.
    Génère les requêtes Cypher pour ingestion dans le Knowledge Graph.
    """
    
    # Mapping catégories CNESST
    CNESST_RISK_CATEGORIES = {
        "fall_height": "RC1_CHUTES_HAUTEUR",
        "burial": "RC2_ENSEVELISSEMENT",
        "machine": "RC3_MACHINES",
        "vehicle": "RC4_VEHICULES",
        "confined_space": "RC5_ESPACES_CLOS",
        "electrical": "RC6_ELECTRICITE",
        "chemical": "RC7_CHIMIQUE_BIO",
        "ergonomic": "RC8_ERGONOMIE_TMS",
    }
    
    def __init__(self):
        self.cypher_queries = []
        self.nodes_created = 0
        self.relationships_created = 0
    
    def normalize(self, standardized_data: List[Dict]) -> Dict[str, Any]:
        """
        Normalise les données standardisées vers SafetyGraph.
        
        Returns:
            Dict avec cypher_queries, nodes, relationships, summary
        """
        self.cypher_queries = []
        self.nodes_created = 0
        self.relationships_created = 0
        
        nodes = []
        relationships = []
        
        for record in standardized_data:
            dimension = SSEDimension(record.get("dimension"))
            schema = DIMENSION_SCHEMAS.get(dimension)
            data = record.get("data", {})
            
            # Créer le nœud principal
            primary_label = schema.neo4j_labels[0] if schema.neo4j_labels else "Entity"
            node_id = data.get(schema.required_fields[0]) if schema.required_fields else str(uuid.uuid4())
            
            node = {
                "id": node_id,
                "labels": schema.neo4j_labels,
                "properties": {
                    **data,
                    "source_platform": record.get("source_platform"),
                    "dimension": dimension.value,
                    "imported_at": record.get("imported_at"),
                    "cnesst_mapping": schema.cnesst_mapping,
                    "iso_clause": schema.iso_clause
                }
            }
            nodes.append(node)
            self.nodes_created += 1
            
            # Générer Cypher pour le nœud
            props_str = ", ".join([f'{k}: ${k}' for k in node["properties"].keys()])
            labels_str = ":".join(schema.neo4j_labels)
            cypher = f"MERGE (n:{labels_str} {{id: $id}}) SET n += {{{props_str}}}"
            self.cypher_queries.append({
                "query": cypher,
                "params": {"id": node_id, **node["properties"]}
            })
            
            # Extraire et créer les relations
            for rel_def in schema.relationships:
                rel_type, target_label = rel_def.split(":")
                # Chercher les références dans les données
                target_field = target_label.lower() + "_id"
                if target_field in data and data[target_field]:
                    rel = {
                        "from_id": node_id,
                        "from_label": primary_label,
                        "type": rel_type,
                        "to_id": data[target_field],
                        "to_label": target_label
                    }
                    relationships.append(rel)
                    self.relationships_created += 1
                    
                    cypher_rel = f"""
                    MATCH (a:{primary_label} {{id: $from_id}}), (b:{target_label} {{id: $to_id}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """
                    self.cypher_queries.append({
                        "query": cypher_rel,
                        "params": {"from_id": node_id, "to_id": data[target_field]}
                    })
        
        return {
            "nodes": nodes,
            "relationships": relationships,
            "cypher_queries": self.cypher_queries,
            "summary": {
                "nodes_created": self.nodes_created,
                "relationships_created": self.relationships_created,
                "dimensions_processed": len(set(r.get("dimension") for r in standardized_data))
            }
        }
    
    def map_to_cnesst_category(self, risk_type: str) -> str:
        """Mappe un type de risque vers la catégorie CNESST"""
        risk_lower = risk_type.lower()
        for key, category in self.CNESST_RISK_CATEGORIES.items():
            if key in risk_lower:
                return category
        return "RC0_AUTRE"


# =============================================================================
# SECTION 6: INGESTION MANAGER
# =============================================================================

class SGSSTIngestionManager:
    """
    Gestionnaire central d'ingestion SGSST.
    Orchestre les adaptateurs, la normalisation et l'ingestion SafetyGraph.
    """
    
    def __init__(self):
        self.adapters: Dict[str, GenericSGSSTAdapter] = {}
        self.normalizer = SafetyGraphNormalizer()
        self.ingestion_history: List[Dict] = []
    
    def register_adapter(self, adapter: GenericSGSSTAdapter) -> None:
        """Enregistre un adaptateur SGSST"""
        self.adapters[adapter.platform_name] = adapter
        logger.info(f"✅ Adaptateur enregistré: {adapter.platform_name}")
        logger.info(f"   Dimensions supportées: {[d.value for d in adapter.supported_dimensions]}")
    
    def list_adapters(self) -> List[Dict]:
        """Liste les adaptateurs enregistrés"""
        return [
            {
                "platform": name,
                "connected": adapter.connected,
                "dimensions": [d.value for d in adapter.supported_dimensions]
            }
            for name, adapter in self.adapters.items()
        ]
    
    async def ingest_from_platform(
        self,
        platform_name: str,
        dimensions: List[SSEDimension] = None,
        filters: Dict = None
    ) -> Dict[str, Any]:
        """
        Ingère les données d'une plateforme SGSST vers SafetyGraph.
        
        Args:
            platform_name: Nom de la plateforme
            dimensions: Liste des dimensions à ingérer (toutes si None)
            filters: Filtres à appliquer
            
        Returns:
            Résultat de l'ingestion avec statistiques
        """
        adapter = self.adapters.get(platform_name)
        if not adapter:
            raise ValueError(f"Adaptateur non trouvé: {platform_name}")
        
        if not adapter.connected:
            raise ConnectionError(f"Adaptateur non connecté: {platform_name}")
        
        # Dimensions à traiter
        dims_to_process = dimensions or adapter.supported_dimensions
        
        ingestion_id = f"ING-{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        all_standardized = []
        dimension_stats = {}
        
        for dimension in dims_to_process:
            if dimension not in adapter.supported_dimensions:
                logger.warning(f"⚠️ Dimension {dimension.value} non supportée par {platform_name}")
                continue
            
            try:
                # 1. Fetch données brutes
                raw_data = adapter.fetch_data(dimension, filters)
                
                # 2. Transformer vers standard
                standardized = adapter.transform_to_standard(dimension, raw_data)
                
                all_standardized.extend(standardized)
                dimension_stats[dimension.value] = {
                    "raw_count": len(raw_data),
                    "standardized_count": len(standardized)
                }
                
                logger.info(f"📥 {dimension.value}: {len(standardized)} enregistrements")
                
            except Exception as e:
                logger.error(f"❌ Erreur {dimension.value}: {e}")
                dimension_stats[dimension.value] = {"error": str(e)}
        
        # 3. Normaliser vers SafetyGraph
        safetygraph_result = self.normalizer.normalize(all_standardized)
        
        # Résultat
        result = {
            "ingestion_id": ingestion_id,
            "platform": platform_name,
            "timestamp": start_time.isoformat(),
            "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            "dimensions_processed": len(dimension_stats),
            "dimension_stats": dimension_stats,
            "total_records": len(all_standardized),
            "safetygraph": safetygraph_result["summary"],
            "status": "success"
        }
        
        self.ingestion_history.append(result)
        
        return result
    
    async def ingest_from_all(self, filters: Dict = None) -> Dict[str, Any]:
        """Ingère depuis toutes les plateformes connectées"""
        results = {}
        for platform_name, adapter in self.adapters.items():
            if adapter.connected:
                try:
                    result = await self.ingest_from_platform(platform_name, filters=filters)
                    results[platform_name] = result
                except Exception as e:
                    results[platform_name] = {"error": str(e)}
        
        return {
            "platforms_processed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# SECTION 7: EXEMPLE D'ADAPTATEUR (TEMPLATE)
# =============================================================================

class ExampleSGSSTAdapter(GenericSGSSTAdapter):
    """
    Exemple d'adaptateur SGSST.
    Utilisez ce template pour créer un adaptateur pour votre plateforme.
    """
    
    def __init__(self):
        super().__init__(
            platform_name="ExampleSGSST",
            base_url="https://api.example-sgsst.com/v1",
            auth_type="api_key"
        )
        
        # Définir les dimensions supportées par cette plateforme
        self._supported_dimensions = [
            SSEDimension.RISKS_OPPORTUNITIES,
            SSEDimension.INCIDENTS_NONCONFORMITIES,
            SSEDimension.AUDITS_INSPECTIONS,
            SSEDimension.OCCUPATIONAL_HEALTH_SAFETY,
        ]
        
        # Mapping des champs plateforme → standard
        self._field_mappings = {
            # Risques
            "risk_id": ["id", "risk_id", "riskId"],
            "title": ["name", "title", "description"],
            "category": ["type", "category", "risk_type"],
            "severity": ["level", "severity", "impact"],
            
            # Incidents
            "incident_id": ["id", "incident_id", "incidentId"],
            "date": ["occurrence_date", "date", "incident_date"],
            "location": ["site", "location", "area"],
        }
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """Connexion à la plateforme"""
        # En production: vrai appel API d'authentification
        api_key = credentials.get("api_key")
        if api_key:
            self.credentials = credentials
            self.connected = True
            logger.info(f"✅ Connecté à {self.platform_name}")
            return True
        return False
    
    def fetch_data(self, dimension: SSEDimension, filters: Dict = None) -> List[Dict]:
        """Récupère les données brutes"""
        # En production: appel API réel
        # Simulation de données
        if dimension == SSEDimension.RISKS_OPPORTUNITIES:
            return [
                {"id": "RSK-001", "name": "Chute échafaudage", "type": "fall_height", "level": "high"},
                {"id": "RSK-002", "name": "Exposition bruit", "type": "ergonomic", "level": "medium"},
            ]
        elif dimension == SSEDimension.INCIDENTS_NONCONFORMITIES:
            return [
                {"id": "INC-001", "occurrence_date": "2026-01-15", "site": "Zone A", "type": "near_miss"},
            ]
        return []
    
    def _map_field(self, standard_field: str, record: Dict) -> Any:
        """Mappe les champs de la plateforme vers le standard"""
        possible_fields = self._field_mappings.get(standard_field, [])
        for field in possible_fields:
            if field in record:
                return record[field]
        return None


# =============================================================================
# SECTION 8: DIGITAL TWIN BUILDER (INTÉGRATION)
# =============================================================================

class DigitalTwinBuilder:
    """
    Construit le Digital Twin 3D à partir des données SafetyGraph.
    Intègre les 15 dimensions SSE/HSE dans une représentation spatiale.
    """
    
    def __init__(self, twin_id: str = None):
        self.twin_id = twin_id or f"TWIN-{uuid.uuid4().hex[:8]}"
        self.version = 1
        self.zones: List[Dict] = []
        self.risks: List[Dict] = []
        self.equipment: List[Dict] = []
        self.layers: Dict[str, List[Dict]] = {}
    
    def build_from_safetygraph(self, safetygraph_data: Dict) -> Dict:
        """
        Construit le Twin à partir des données SafetyGraph normalisées.
        
        Chaque dimension SSE/HSE devient une COUCHE du Digital Twin:
        - Couche Risques (RC1-RC8)
        - Couche Conformité
        - Couche Incidents
        - Couche Équipements
        - Couche Zones
        - etc.
        """
        nodes = safetygraph_data.get("nodes", [])
        
        # Organiser par dimension/label
        for node in nodes:
            dimension = node.get("properties", {}).get("dimension")
            labels = node.get("labels", [])
            
            # Créer la couche si nécessaire
            if dimension not in self.layers:
                self.layers[dimension] = []
            
            # Ajouter à la couche appropriée
            spatial_element = {
                "id": node.get("id"),
                "type": labels[0] if labels else "Unknown",
                "dimension": dimension,
                "properties": node.get("properties", {}),
                "coordinates": self._extract_coordinates(node),
                "visibility": True,
                "style": self._get_style_for_dimension(dimension)
            }
            
            self.layers[dimension].append(spatial_element)
            
            # Catégoriser spécifiquement
            if "Risk" in labels or "Hazard" in labels:
                self.risks.append(spatial_element)
            elif "Zone" in labels:
                self.zones.append(spatial_element)
            elif "Equipment" in labels:
                self.equipment.append(spatial_element)
        
        return {
            "twin_id": self.twin_id,
            "version": self.version,
            "layers": self.layers,
            "summary": {
                "total_layers": len(self.layers),
                "total_elements": sum(len(l) for l in self.layers.values()),
                "risks_count": len(self.risks),
                "zones_count": len(self.zones),
                "equipment_count": len(self.equipment)
            }
        }
    
    def _extract_coordinates(self, node: Dict) -> Dict:
        """Extrait ou génère les coordonnées spatiales"""
        props = node.get("properties", {})
        return {
            "x": props.get("x", props.get("longitude", 0)),
            "y": props.get("y", props.get("latitude", 0)),
            "z": props.get("z", props.get("elevation", 0))
        }
    
    def _get_style_for_dimension(self, dimension: str) -> Dict:
        """Retourne le style visuel pour une dimension"""
        styles = {
            "risks_opportunities": {"color": "#FF4444", "icon": "warning", "opacity": 0.8},
            "incidents_nonconformities": {"color": "#FF8800", "icon": "alert", "opacity": 0.9},
            "compliance_requirements": {"color": "#4444FF", "icon": "check", "opacity": 0.7},
            "audits_inspections": {"color": "#00AA00", "icon": "clipboard", "opacity": 0.7},
            "emergency_crisis": {"color": "#FF0000", "icon": "siren", "opacity": 1.0},
        }
        return styles.get(dimension, {"color": "#888888", "icon": "circle", "opacity": 0.5})


# =============================================================================
# SECTION 9: API PUBLIQUE
# =============================================================================

class SafeTwinDigitalTwinHubAPI:
    """
    API publique du SafeTwin Digital Twin Hub.
    Point d'entrée unique pour toutes les opérations.
    """
    
    def __init__(self):
        self.ingestion_manager = SGSSTIngestionManager()
        self.normalizer = SafetyGraphNormalizer()
        self.twins: Dict[str, DigitalTwinBuilder] = {}
    
    # --- Gestion des adaptateurs ---
    
    def register_sgsst_platform(self, adapter: GenericSGSSTAdapter) -> Dict:
        """Enregistre une nouvelle plateforme SGSST"""
        self.ingestion_manager.register_adapter(adapter)
        return {
            "status": "registered",
            "platform": adapter.platform_name,
            "dimensions": [d.value for d in adapter.supported_dimensions]
        }
    
    def connect_platform(self, platform_name: str, credentials: Dict) -> Dict:
        """Connecte une plateforme SGSST"""
        adapter = self.ingestion_manager.adapters.get(platform_name)
        if not adapter:
            return {"error": f"Plateforme inconnue: {platform_name}"}
        
        success = adapter.connect(credentials)
        return {
            "platform": platform_name,
            "connected": success
        }
    
    def list_platforms(self) -> List[Dict]:
        """Liste toutes les plateformes enregistrées"""
        return self.ingestion_manager.list_adapters()
    
    # --- Ingestion ---
    
    async def ingest(
        self,
        platform_name: str = None,
        dimensions: List[str] = None,
        filters: Dict = None
    ) -> Dict:
        """
        Ingère les données SGSST.
        
        Args:
            platform_name: Nom de la plateforme (toutes si None)
            dimensions: Liste des dimensions à ingérer
            filters: Filtres à appliquer
        """
        dim_enums = [SSEDimension(d) for d in dimensions] if dimensions else None
        
        if platform_name:
            return await self.ingestion_manager.ingest_from_platform(
                platform_name, dim_enums, filters
            )
        else:
            return await self.ingestion_manager.ingest_from_all(filters)
    
    # --- Digital Twin ---
    
    def create_twin(self, safetygraph_data: Dict, twin_id: str = None) -> Dict:
        """Crée un Digital Twin à partir des données SafetyGraph"""
        builder = DigitalTwinBuilder(twin_id)
        twin = builder.build_from_safetygraph(safetygraph_data)
        self.twins[twin["twin_id"]] = builder
        return twin
    
    def get_twin(self, twin_id: str) -> Optional[Dict]:
        """Récupère un Digital Twin"""
        builder = self.twins.get(twin_id)
        if builder:
            return {
                "twin_id": builder.twin_id,
                "version": builder.version,
                "layers": builder.layers
            }
        return None
    
    # --- Schémas et référentiels ---
    
    def get_dimension_schema(self, dimension: str) -> Dict:
        """Retourne le schéma d'une dimension SSE/HSE"""
        dim_enum = SSEDimension(dimension)
        schema = DIMENSION_SCHEMAS.get(dim_enum)
        if schema:
            return {
                "dimension": dimension,
                "required_fields": schema.required_fields,
                "optional_fields": schema.optional_fields,
                "relationships": schema.relationships,
                "neo4j_labels": schema.neo4j_labels,
                "cnesst_mapping": schema.cnesst_mapping,
                "iso_clause": schema.iso_clause
            }
        return {"error": f"Dimension inconnue: {dimension}"}
    
    def list_dimensions(self) -> List[Dict]:
        """Liste toutes les dimensions SSE/HSE supportées"""
        return [
            {
                "id": dim.value,
                "name": dim.name.replace("_", " ").title(),
                "iso_clause": DIMENSION_SCHEMAS[dim].iso_clause,
                "cnesst_mapping": DIMENSION_SCHEMAS[dim].cnesst_mapping
            }
            for dim in SSEDimension
        ]


# =============================================================================
# SECTION 10: EXEMPLE D'UTILISATION
# =============================================================================

async def main():
    """Exemple d'utilisation du SafeTwin Digital Twin Hub"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║   🏗️  SAFETWIN DIGITAL TWIN HUB                                      ║
    ║   Standards d'Ingestion SGSST Universels                            ║
    ║                                                                      ║
    ║   15 Dimensions SSE/HSE (ISO 45001/14001)                           ║
    ║   Adaptateurs génériques multi-plateformes                          ║
    ║   Normalisation SafetyGraph Neo4j                                   ║
    ║                                                                      ║
    ║   Conformité: CNESST/LSST | Vision Zero | ISO 45001                 ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Initialiser l'API
    api = SafeTwinDigitalTwinHubAPI()
    
    # 2. Lister les dimensions disponibles
    print("\n📋 DIMENSIONS SSE/HSE SUPPORTÉES:")
    print("-" * 60)
    for dim in api.list_dimensions():
        print(f"  • {dim['name']}")
        print(f"    ISO: {dim['iso_clause']} | CNESST: {dim['cnesst_mapping']}")
    
    # 3. Enregistrer un adaptateur exemple
    print("\n\n🔌 ENREGISTREMENT ADAPTATEUR:")
    print("-" * 60)
    example_adapter = ExampleSGSSTAdapter()
    api.register_sgsst_platform(example_adapter)
    
    # 4. Connecter la plateforme
    api.connect_platform("ExampleSGSST", {"api_key": "demo-key-123"})
    
    # 5. Ingérer les données
    print("\n\n📥 INGESTION DONNÉES:")
    print("-" * 60)
    result = await api.ingest(platform_name="ExampleSGSST")
    print(f"  Résultat: {result['status']}")
    print(f"  Dimensions traitées: {result['dimensions_processed']}")
    print(f"  Enregistrements: {result['total_records']}")
    
    # 6. Afficher un schéma de dimension
    print("\n\n📊 SCHÉMA DIMENSION 'RISQUES':")
    print("-" * 60)
    schema = api.get_dimension_schema("risks_opportunities")
    print(f"  Champs requis: {schema['required_fields']}")
    print(f"  Labels Neo4j: {schema['neo4j_labels']}")
    print(f"  Relations: {schema['relationships'][:3]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
