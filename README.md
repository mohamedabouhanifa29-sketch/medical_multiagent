# Système Multi-Agents Médical

Application multi-agents basée sur LangGraph pour simuler un workflow d'orientation
clinique préliminaire.

> ⚠️ Ce système est un exercice académique. Il ne doit pas être présenté comme un
> dispositif médical et ne fournit aucun diagnostic définitif. Le rapport final
> mentionne explicitement : « Ce système ne remplace pas une consultation médicale. »

## Architecture

```
medagent_project/
├── backend/
│   ├── app/
│   │   ├── graph.py            # construction du graphe LangGraph
│   │   ├── state.py            # MedicalState (TypedDict)
│   │   ├── api.py              # API FastAPI
│   │   ├── graph_studio.py     # point d'entrée pour LangGraph Studio
│   │   ├── nodes/
│   │   │   ├── supervisor.py
│   │   │   ├── diagnostic_agent.py
│   │   │   ├── physician_review.py
│   │   │   └── report_agent.py
│   │   └── tools/
│   │       ├── patient_tools.py    # ask_patient, recommend_interim_care
│   │       ├── care_tools.py       # get_drug_info, get_emergency_level (via MCP)
│   │       └── mcp_client.py       # client MCP stdio réel
│   ├── langgraph.json
│   ├── requirements.txt
│   └── .env.example
├── mcp_server/
│   ├── server.py               # serveur MCP réel (FastMCP, transport stdio)
│   └── data/
│       └── drugs.json          # base de données médicaments
├── frontend/
│   └── streamlit_app.py        # interface Streamlit, 4 écrans
├── notebooks/
│   ├── 01_state.ipynb
│   ├── 02_graph.ipynb
│   ├── 03_diagnostic.ipynb
│   ├── 04_hitl.ipynb
│   ├── 05_mcp.ipynb
│   └── 06_tests.ipynb
└── docs/
    ├── rapport_technique.md
    └── demo_langgraph_studio.md
```

### Agents

- **Supervisor** : orchestre le workflow, route vers le prochain agent.
- **DiagnosticAgent** : pose 5 questions au patient via le tool `ask_patient`,
  produit une synthèse clinique préliminaire, puis une recommandation
  intermédiaire via le tool `recommend_interim_care`.
- **PhysicianReview** : point de passage Human-in-the-Loop — le graphe s'interrompt
  ici pour attendre la saisie du médecin traitant.
- **ReportAgent** : génère le rapport final, en appelant deux outils via MCP
  (`get_drug_info`, `get_emergency_level`).

### Intégration MCP

Le serveur MCP (`mcp_server/server.py`) tourne en transport **stdio** et est lancé
en sous-processus par le client MCP du backend (`backend/app/tools/mcp_client.py`).
Ce client est l'unique point d'accès aux outils médicaux : `report_agent` ne
contient aucune logique médicale dupliquée, tout passe par le protocole MCP.

## Stack technique

- LangGraph + LangChain
- Groq (`llama-3.1-8b-instant`)
- FastAPI
- Streamlit
- MCP (Model Context Protocol, transport stdio, `fastmcp`)

## Installation

```bash
cd backend
pip install -r requirements.txt
```

Copier `.env.example` en `.env` dans `backend/` et renseigner ta clé :

```
GROQ_API_KEY=ta_cle_ici
GROQ_MODEL=llama-3.1-8b-instant
```

## Lancement

Terminal 1 — API (depuis `backend/`) :

```bash
cd backend
python -m uvicorn app.api:app --reload
```

Terminal 2 — Frontend (depuis `frontend/`) :

```bash
cd frontend
python -m streamlit run streamlit_app.py --server.port 8502
```

Ouvrir **http://localhost:8502**.

## Endpoints API

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/sessions/start` | Réserve un identifiant de session |
| POST | `/consultation/start` | Démarrer une consultation |
| POST | `/consultation/resume` | Répondre / intervention médecin |
| GET | `/consultation/{thread_id}` | État de la consultation |
| GET | `/consultation/{thread_id}/report` | Rapport final |

## Workflow

```
START → Supervisor → DiagnosticAgent (5 questions via ask_patient
        + recommend_interim_care) → Supervisor → PhysicianReview (HITL)
        → Supervisor → ReportAgent (MCP: get_drug_info, get_emergency_level)
        → Supervisor → END
```

## Test dans LangGraph Studio

```bash
cd backend
langgraph dev
```

Voir `docs/demo_langgraph_studio.md` pour le déroulé de démonstration
(transitions, interruptions patient/médecin, états intermédiaires observables).

## Jeux de tests

- **Cas 1** : syndrome respiratoire simple — patient de 35 ans, toux sèche,
  fièvre légère depuis 3 jours.
- **Cas 2** : cas avec red flags — patient de 55 ans, douleur thoracique intense,
  difficultés à respirer, sueurs froides.
- **Cas 3** : cas bénin — patient de 25 ans, léger mal de tête, stress.

Voir `notebooks/06_tests.ipynb` pour l'exécution automatisée des 3 cas.

## Documentation complémentaire

- `docs/rapport_technique.md` — architecture et choix techniques.
- `docs/demo_langgraph_studio.md` — notes pour la démonstration dans Studio.

## Auteur

Mohamed Abouhanifa — EMSI Casablanca — IADATA 2025/2026
Encadrant : Pr. Mohamed YOUSSFI
