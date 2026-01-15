# ==============================================================================
# PLAN DE GOUVERNANCE - SafeTwin X5 Agentique
# ==============================================================================
# Conformité: ISO 45001 | CNESST | EU AI Act | RGPD/Loi 25
# ==============================================================================

## 1. NIVEAUX D'ESCALADE

### Seuils automatiques

| Score Risque | Niveau | Action | Délai |
|--------------|--------|--------|-------|
| 0-49 | 🟢 Normal | Log uniquement | - |
| 50-69 | 🟡 Attention | Notification Teams | 5 min |
| 70-84 | 🟠 Élevé | Alerte Slack + Rapport | 2 min |
| 85-94 | 🔴 Critique | ESCALADE HUMAINE | Immédiat |
| 95-100 | ⚫ Urgence | KILL SWITCH disponible | Immédiat |

### Matrice d'escalade

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATRICE D'ESCALADE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Score 50-69    →  Superviseur HSE (notification)              │
│  Score 70-84    →  Superviseur HSE (action requise)            │
│  Score 85+      →  Directeur HSE + Ops (décision immédiate)    │
│  Emergency Stop →  Directeur Usine + CEO (validation)          │
│                                                                 │
│  Délai réponse maximal: 15 minutes (critique)                  │
│  Délai réponse souhaité: 5 minutes (critique)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. KILL SWITCH

### Conditions d'activation

- Score risque > 95 pendant > 60 secondes
- Échec de 3 actions consécutives
- Perte de connexion aux capteurs critiques
- Demande manuelle autorisée (RBAC)

### Procédure

1. **Détection** → Agent Superviseur détecte condition
2. **Notification** → Alerte immédiate tous canaux
3. **Arrêt** → Suspension de toutes les actions autonomes
4. **Log** → Enregistrement audit complet
5. **Reprise** → Validation humaine requise pour redémarrage

### Accès Kill Switch

| Rôle | Peut activer | Peut désactiver |
|------|--------------|-----------------|
| Opérateur | ❌ | ❌ |
| Superviseur HSE | ✅ | ❌ |
| Directeur HSE | ✅ | ✅ |
| Admin Système | ✅ | ✅ |

## 3. MONITORING (Prometheus/Grafana)

### Métriques temps réel

```yaml
# prometheus/safetwin_metrics.yaml

- name: safetwin_risk_score
  type: gauge
  help: "Score de risque actuel (0-100)"
  labels: [zone, sensor_type]

- name: safetwin_anomalies_total
  type: counter
  help: "Nombre total d'anomalies détectées"
  labels: [severity, zone]

- name: safetwin_actions_total
  type: counter
  help: "Nombre total d'actions exécutées"
  labels: [action_type, status]

- name: safetwin_escalations_total
  type: counter
  help: "Nombre d'escalades humaines"
  labels: [reason]

- name: safetwin_latency_seconds
  type: histogram
  help: "Latence de traitement"
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0]

- name: safetwin_loa_current
  type: gauge
  help: "Niveau d'autonomie actuel (1-5)"
```

### Alertes Prometheus

```yaml
# prometheus/alerts.yaml

groups:
  - name: safetwin
    rules:
      - alert: HighRiskScore
        expr: safetwin_risk_score > 85
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Score de risque critique détecté"
          
      - alert: HighLatency
        expr: safetwin_latency_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latence supérieure à 2s"
          
      - alert: LowLOA
        expr: safetwin_loa_current < 3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Niveau d'autonomie dégradé"
          
      - alert: HighEscalationRate
        expr: rate(safetwin_escalations_total[1h]) > 0.2
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Taux d'escalade élevé (>20%/h)"
```

## 4. AUDIT ET TRAÇABILITÉ

### Logs immuables (ELK Stack)

```json
{
  "timestamp": "2026-01-14T17:30:00Z",
  "session_id": "abc123def456",
  "agent": "Executeur",
  "action": "send_alert",
  "input": {
    "channel": "slack",
    "severity": "critical",
    "message": "Température critique Zone A"
  },
  "output": {
    "alert_id": "ALT-001",
    "status": "sent"
  },
  "duration_ms": 234,
  "user_context": null,
  "risk_score_at_action": 87,
  "hash": "sha256:abc123..."
}
```

### Rétention

| Type de log | Rétention | Stockage |
|-------------|-----------|----------|
| Audit actions | 7 ans | S3 Glacier |
| Métriques | 2 ans | TimescaleDB |
| Incidents | 10 ans | PostgreSQL |
| KG Updates | Permanent | Neo4j |

## 5. CONFORMITÉ RÉGLEMENTAIRE

### EU AI Act (High-Risk AI System)

| Exigence | Implémentation SafeTwin |
|----------|------------------------|
| Évaluation risques | ✅ Score 0-100 en temps réel |
| Qualité données | ✅ 2.85M incidents validés |
| Documentation | ✅ Audit log complet |
| Transparence | ✅ Explainability via KG |
| Surveillance humaine | ✅ LOA 4 avec escalade |
| Robustesse | ✅ Tests unitaires + E2E |

### RGPD / Loi 25

| Exigence | Implémentation |
|----------|---------------|
| Minimisation données | ✅ Capteurs anonymisés |
| Droit d'accès | ✅ API /audit/user/{id} |
| Portabilité | ✅ Export JSON/CSV |
| Effacement | ✅ Soft delete + anonymisation |
| Consentement | N/A (données industrielles) |

### ISO 45001

| Clause | Couverture SafeTwin |
|--------|---------------------|
| 6.1 Risques & opportunités | ✅ Prédiction ML |
| 8.1 Planification opérationnelle | ✅ Agent Planificateur |
| 9.1 Surveillance & mesure | ✅ Métriques temps réel |
| 10.2 Incidents & actions | ✅ Workflow automatisé |

## 6. TESTS ET VALIDATION

### Scénarios de test

```python
# tests/test_scenarios.py

async def test_scenario_temperature_critique():
    """Scénario: Température critique détectée"""
    # Given
    mock_sensor_data = {"temperature": {"value": 45, "threshold_critical": 42}}
    
    # When
    result = await safetwin.run_cycle(sensor_data=mock_sensor_data)
    
    # Then
    assert result["risk_score"] >= 85
    assert result["requires_escalation"] == True
    assert any(a["action"] == "send_alert" for a in result["actions_taken"])


async def test_scenario_resolution_autonome():
    """Scénario: Résolution autonome sans escalade"""
    # Given
    mock_sensor_data = {"vibration": {"value": 9, "threshold_warning": 8}}
    
    # When
    result = await safetwin.run_cycle(sensor_data=mock_sensor_data)
    
    # Then
    assert result["risk_score"] < 85
    assert result["requires_escalation"] == False
    assert len(result["actions_taken"]) > 0


async def test_kill_switch_activation():
    """Scénario: Activation kill switch"""
    # Given
    extremely_high_risk = {"all_sensors": {"value": 100}}
    
    # When/Then
    with pytest.raises(KillSwitchActivated):
        await safetwin.run_cycle(sensor_data=extremely_high_risk)
```

### Métriques de validation

| Métrique | Cible | Mesure |
|----------|-------|--------|
| Taux succès actions | >85% | actions_success / actions_total |
| F1-Score détection | >0.9 | Precision × Recall |
| Latence P95 | <2s | Prometheus histogram |
| Taux faux positifs | <5% | false_alerts / total_alerts |
| Disponibilité | 99.9% | uptime / total_time |
| LOA moyen | >3.5 | Moyenne sessions |

## 7. ROADMAP ITÉRATIVE

### Semaine 1 (Actuel)
- [x] Architecture multi-agents
- [x] Code Python LangGraph
- [x] Dockerfile + Helm
- [x] Plan gouvernance

### Semaine 2
- [ ] Intégration MQTT réel (capteurs IoT)
- [ ] Connexion Pinecone (mémoire vectorielle)
- [ ] Tests E2E complets

### Semaine 3
- [ ] Déploiement Kubernetes staging
- [ ] Dashboard Grafana
- [ ] Alertes PagerDuty

### Semaine 4
- [ ] Déploiement production
- [ ] Formation équipes
- [ ] Go-live monitored

### Mois 2-3
- [ ] Fine-tuning modèles ML
- [ ] Ajout capteurs (gaz, bruit)
- [ ] Intégration PLC réelle

### Mois 4-6
- [ ] LOA 4+ validation
- [ ] Certification EU AI Act
- [ ] Scale multi-sites
