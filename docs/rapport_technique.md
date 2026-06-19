# Rapport technique — Système Multi-Agents Médical

**Auteur :** Mohamed Abouhanifa — EMSI Casablanca — IADATA 2025/2026
**Encadrant :** Pr. Mohamed YOUSSFI

## 1. Contexte et objectif

Ce projet implémente un workflow d'orientation clinique préliminaire sous forme
de système multi-agents, conformément au cahier des charges fourni. Le système
recueille les informations d'un patient, produit une synthèse clinique
préliminaire, intègre une validation humaine par un médecin traitant, puis
génère un rapport final structuré. À aucun moment le système ne pose de
diagnostic définitif ni ne se substitue à une consultation médicale — cette
limite est rappelée explicitement dans chaque rapport généré.

## 2. Architecture générale

Le système est découpé en trois composants indépendants, communiquant par
réseau (HTTP) ou par sous-processus (stdio) :

- **Backend** (`backend/`) : le graphe LangGraph et l'API FastAPI qui l'expose.
- **Serveur MCP** (`mcp_server/`) : un serveur d'outils médicaux exposé via le
  protocole MCP, indépendant du backend.
- **Frontend** (`frontend/`) : une interface Streamlit à 4 écrans qui consomme
  l'API REST.

Cette séparation permet de tester chaque brique isolément (le serveur MCP peut
être interrogé sans lancer ni l'API ni le frontend) et reflète l'arborescence
recommandée par le cahier des charges (section 7).

## 3. Modélisation du workflow (LangGraph)

Le graphe est construit autour d'un état partagé unique, `MedicalState`
(`backend/app/state.py`), un `TypedDict` contenant entre autres `next`
(prochain agent à exécuter), `question_count`, `patient_answers`,
`diagnostic_summary`, `interim_care`, `physician_treatment` et `final_report`.

Quatre nœuds composent le graphe :

- **Supervisor** : lit la clé `next` du state et route vers le nœud
  correspondant. Il ne contient aucune décision métier — l'aiguillage est
  entièrement piloté par les `conditional_edges` définis dans `graph.py`.
- **DiagnosticAgent** : boucle jusqu'à 5 fois pour poser une question au
  patient (via le tool `ask_patient`), puis produit une synthèse clinique
  préliminaire et une recommandation intermédiaire (via le tool
  `recommend_interim_care`).
- **PhysicianReview** : nœud de passage représentant le point d'arrêt
  Human-in-the-Loop. Aucune logique active ; le graphe est interrompu juste
  avant ce nœud (voir section 4).
- **ReportAgent** : agrège tout le state et appelle deux outils via MCP
  (`get_drug_info`, `get_emergency_level`) pour enrichir le rapport final.

Le graphe est compilé avec :

```python
builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["diagnostic_agent", "physician_review"],
)
```

## 4. Human-in-the-Loop

Le HITL repose sur deux mécanismes combinés de LangGraph : `interrupt_before`
et un `checkpointer` (`MemorySaver`). Chaque consultation est identifiée par
un `thread_id` ; le state est persisté entre chaque appel HTTP, ce qui permet
de suspendre l'exécution à deux endroits :

- **Avant `diagnostic_agent`** : après chaque question posée, le graphe
  s'arrête. Le frontend récupère la question, attend la réponse de
  l'utilisateur, puis le state est mis à jour (`graph.update_state`) avant de
  relancer le graphe (`graph.invoke(None, config=...)`).
- **Avant `physician_review`** : une fois les 5 questions répondues, le
  graphe s'arrête avant ce nœud. Le médecin reçoit la synthèse clinique et la
  recommandation intermédiaire, saisit son traitement, et le state est de
  nouveau mis à jour avant de poursuivre vers `report_agent`.

Cette double interruption permet d'observer dans LangGraph Studio les deux
points d'arrêt demandés par le cahier des charges (section 12).

## 5. Tools et intégration MCP

Le cahier des charges impose explicitement que l'interaction patient soit
gérée via un tool (section 4.3) et qu'au moins un outil soit intégré via MCP
(section 9). Le projet répond à ces deux exigences séparément :

- **`ask_patient` et `recommend_interim_care`** (`backend/app/tools/patient_tools.py`)
  sont des tools LangChain (`@tool`) appelés depuis `diagnostic_agent`. Ils ne
  contiennent pas de logique métier complexe : ils structurent le contexte
  transmis ensuite au LLM, ce qui rend explicite, traçable et testable
  indépendamment la frontière entre « ce qui est un tool » et « ce qui est un
  appel LLM ».
- **`get_drug_info` et `get_emergency_level`** sont exposés à la fois côté
  serveur MCP (`mcp_server/server.py`, transport stdio, via `FastMCP`) et
  côté backend, sous forme de tools LangChain (`backend/app/tools/care_tools.py`).
  Ces tools n'implémentent aucune logique eux-mêmes : ils délèguent à
  `backend/app/tools/mcp_client.py`, qui lance le serveur MCP en
  sous-processus, envoie la requête via le protocole MCP, récupère le
  résultat, puis ferme la session. Le `report_agent` n'a donc aucune
  connaissance de la base de médicaments ni des règles d'urgence : toute
  cette logique vit exclusivement dans `mcp_server/`.

Ce choix d'architecture rend l'intégration MCP vérifiable de façon directe :
modifier `mcp_server/data/drugs.json` change le contenu du rapport final sans
qu'aucun fichier du backend ne soit touché.

## 6. API FastAPI

L'API (`backend/app/api.py`) expose 5 endpoints :

- `POST /sessions/start` : réserve un identifiant de session sans démarrer le
  graphe (utile si un frontend souhaite obtenir un `thread_id` avant la
  saisie du cas patient).
- `POST /consultation/start` : démarre réellement le workflow.
- `POST /consultation/resume` : reprise après interruption, avec deux usages
  distincts selon le champ fourni (`patient_answer` ou `physician_treatment`).
- `GET /consultation/{thread_id}` : état brut de la consultation.
- `GET /consultation/{thread_id}/report` : rapport final si déjà généré.

## 7. Frontend

L'interface Streamlit (`frontend/streamlit_app.py`) implémente les 4 écrans
minimums requis (section 11.1) : saisie du cas patient, questions/réponses,
revue médecin, rapport final. L'état de navigation est géré via
`st.session_state`, et chaque écran appelle l'API REST correspondante.

## 8. Limites connues

- Le matching de noms de médicaments dans `mcp_server/server.py` reste un
  matching par sous-chaîne (normalisé pour les accents) : un nom mal
  orthographié ou un médicament absent de la base renvoie un message
  générique plutôt qu'une recherche approximative.
- L'extraction du nom de médicament dans `report_agent` suppose que le
  premier mot de la prescription du médecin est le nom du médicament
  (`physician_treatment.split()[0]`) ; une prescription formulée différemment
  (« repos et hydratation ») ne déclenchera pas de fiche médicament adaptée.
- Le client MCP relance un sous-processus à chaque appel plutôt que de
  maintenir une session persistante, ce qui est suffisant pour le volume
  d'un projet académique mais ajoute une latence négligeable à chaque appel.

## 9. Conformité au cahier des charges

L'ensemble des contraintes minimales de la section 15 sont respectées :
usage de LangGraph, présence d'un Supervisor, au moins deux agents métiers
(quatre au total), intégration d'un Human-in-the-Loop, usage d'au moins un
tool via MCP, exposition d'une API FastAPI, présence d'un frontend, et
graphe testable dans LangGraph Studio (voir `docs/demo_langgraph_studio.md`).
