"""
API FastAPI — Système Multi-Agents Médical.

Endpoints conformes à la section 10 du cahier des charges :

    POST /sessions/start                    — initialise une session vide
    POST /consultation/start                 — démarre une consultation (cas patient)
    POST /consultation/resume                — répond à une question / valide un traitement
    GET  /consultation/{thread_id}           — état courant de la consultation
    GET  /consultation/{thread_id}/report     — rapport final

Distinction /sessions/start vs /consultation/start :
    /sessions/start crée un identifiant de session côté serveur SANS lancer
    le graphe (utile pour un frontend qui veut réserver un thread_id avant
    même que l'utilisateur ait saisi son cas, ou pour de futurs usages comme
    l'authentification/l'historique). /consultation/start, lui, exige un
    patient_case et lance immédiatement le graphe jusqu'à la première
    question. Dans cette implémentation, /consultation/start peut aussi
    réutiliser un thread_id déjà réservé via /sessions/start.
"""

import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from .graph import build_graph

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

app = FastAPI(title="Système Multi-Agents Médical")

memory = MemorySaver()
graph = build_graph(checkpointer=memory)

# Sessions réservées via /sessions/start mais pas encore démarrées dans le graphe
_reserved_sessions: set[str] = set()


# ── Modèles Pydantic ───────────────────────────────────
class SessionStartResponse(BaseModel):
    thread_id: str
    status: str = "session_reservee"


class StartRequest(BaseModel):
    patient_case: str
    thread_id: Optional[str] = None  # permet de réutiliser une session réservée


class ResumeRequest(BaseModel):
    thread_id: str
    patient_answer: Optional[str] = None
    physician_treatment: Optional[str] = None


# ── Helper ─────────────────────────────────────────────
def run_until_question_or_pause(config: dict):
    """Avance le graphe jusqu'à une question patient EN_ATTENTE ou jusqu'à
    l'interruption avant physician_review, sans dépasser 10 itérations
    (garde-fou contre une boucle infinie en cas d'état incohérent).
    """
    for _ in range(10):
        state = graph.get_state(config)
        next_tasks = list(state.next) if state.next else []
        if "physician_review" in next_tasks:
            return state
        answers = state.values.get("patient_answers", [])
        if answers and "EN_ATTENTE" in answers[-1]:
            return state
        if not next_tasks:
            return state
        graph.invoke(None, config=config)
    return graph.get_state(config)


# ── Endpoints ──────────────────────────────────────────
@app.post("/sessions/start", response_model=SessionStartResponse)
def start_session():
    """Réserve un identifiant de session, sans démarrer le graphe."""
    thread_id = str(uuid.uuid4())
    _reserved_sessions.add(thread_id)
    return SessionStartResponse(thread_id=thread_id)


@app.post("/consultation/start")
def start_consultation(req: StartRequest):
    """Démarre une consultation : lance le graphe jusqu'à la première question."""
    thread_id = req.thread_id or str(uuid.uuid4())
    _reserved_sessions.discard(thread_id)

    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(
        {
            "patient_case": req.patient_case,
            "question_count": 0,
            "patient_answers": [],
            "next": "diagnostic_agent",
        },
        config=config,
    )
    state = run_until_question_or_pause(config)
    answers = state.values.get("patient_answers", [])
    current_q = next((a for a in reversed(answers) if "EN_ATTENTE" in a), "")
    return {
        "thread_id": thread_id,
        "question_count": state.values.get("question_count", 0),
        "current_question": current_q,
        "status": "en_cours",
    }


@app.post("/consultation/resume")
def resume_consultation(req: ResumeRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    state = graph.get_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")

    if req.patient_answer is not None:
        answers = list(state.values.get("patient_answers", []))
        for i in range(len(answers) - 1, -1, -1):
            if "EN_ATTENTE" in answers[i]:
                answers[i] = answers[i].replace("EN_ATTENTE", req.patient_answer)
                break
        graph.update_state(config, {"patient_answers": answers})
        new_state = run_until_question_or_pause(config)
        new_answers = new_state.values.get("patient_answers", [])
        next_tasks = list(new_state.next) if new_state.next else []
        if "physician_review" in next_tasks:
            return {
                "status": "attente_medecin",
                "diagnostic_summary": new_state.values.get("diagnostic_summary"),
                "interim_care": new_state.values.get("interim_care"),
            }
        current_q = next((a for a in reversed(new_answers) if "EN_ATTENTE" in a), "")
        return {
            "status": "en_cours",
            "question_count": new_state.values.get("question_count"),
            "current_question": current_q,
        }

    if req.physician_treatment is not None:
        graph.update_state(
            config,
            {"physician_treatment": req.physician_treatment, "next": "report_agent"},
        )
        graph.invoke(None, config=config)
        graph.invoke(None, config=config)
        final_state = graph.get_state(config)
        return {
            "status": "termine",
            "final_report": final_state.values.get("final_report"),
        }

    raise HTTPException(status_code=400, detail="Fournir patient_answer ou physician_treatment")


@app.get("/consultation/{thread_id}")
def get_consultation(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail="Consultation non trouvée")
    return state.values


@app.get("/consultation/{thread_id}/report")
def get_report(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    report = state.values.get("final_report")
    if not report:
        raise HTTPException(status_code=404, detail="Rapport pas encore généré")
    return {"report": report}


@app.get("/")
def root():
    return {"message": "Système Multi-Agents Médical — API opérationnelle"}
