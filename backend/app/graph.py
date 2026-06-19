"""
Construction du graphe LangGraph — Système Multi-Agents Médical.

Workflow conforme à la section 5 du cahier des charges :

    START -> Supervisor -> DiagnosticAgent (boucle ask_patient x5
              + recommend_interim_care) -> Supervisor -> PhysicianReview
              (HITL) -> Supervisor -> ReportAgent -> Supervisor -> END

Ce module expose build_graph(checkpointer=None), utilisé à deux endroits :

    - backend/app/api.py    : avec un MemorySaver, pour persister les
                              consultations entre les appels HTTP.
    - langgraph.json        : sans checkpointer explicite, car LangGraph
                              Studio gère sa propre persistance.
"""

from langgraph.graph import END, StateGraph

from .nodes.diagnostic_agent import diagnostic_agent
from .nodes.physician_review import physician_review
from .nodes.report_agent import report_agent
from .nodes.supervisor import supervisor
from .state import MedicalState


def build_graph(checkpointer=None):
    """Construit et compile le graphe MedicalState.

    Args:
        checkpointer: un checkpointer LangGraph (ex. MemorySaver) pour
            persister l'état entre les appels. None pour LangGraph Studio,
            qui gère sa propre persistance.
    """
    builder = StateGraph(MedicalState)

    builder.add_node("supervisor", supervisor)
    builder.add_node("diagnostic_agent", diagnostic_agent)
    builder.add_node("physician_review", physician_review)
    builder.add_node("report_agent", report_agent)

    builder.set_entry_point("supervisor")

    builder.add_conditional_edges(
        "supervisor",
        lambda s: s.get("next"),
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_review": "physician_review",
            "report_agent": "report_agent",
            "FINISH": END,
        },
    )
    builder.add_edge("diagnostic_agent", "supervisor")
    builder.add_edge("physician_review", "supervisor")
    builder.add_edge("report_agent", "supervisor")

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["diagnostic_agent", "physician_review"],
    )
