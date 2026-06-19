"""
État partagé du graphe — MedicalState
========================================

Structure conforme à la section 8 du cahier des charges. Les champs
question_count, interim_care, diagnostic_summary, physician_treatment et
final_report sont ceux explicitement listés par l'énoncé.

patient_case et patient_answers sont des ajouts nécessaires : l'énoncé
décrit un DiagnosticAgent qui "pose 5 questions au patient" et des
"réponses patient [...] intégrées dans l'état du graphe" (section 4.3),
ce qui implique de stocker le cas initial et la liste des Q/R quelque part
dans le state. Ils sont documentés ici pour rester transparents sur cet
écart par rapport à l'exemple minimal de l'énoncé.
"""

from typing import Annotated, Optional

from langgraph.graph.message import add_messages
from typing_extensions import Literal, TypedDict


class MedicalState(TypedDict, total=False):
    # -- Champs imposés par le cahier des charges (section 8) --
    messages: Annotated[list, add_messages]
    next: Literal["diagnostic_agent", "physician_review", "report_agent", "FINISH"]
    question_count: int
    interim_care: str
    diagnostic_summary: str
    physician_treatment: str
    final_report: str

    # -- Champs additionnels nécessaires au workflow patient (section 4.3) --
    patient_case: str
    patient_answers: list
