"""
DiagnosticAgent — pose 5 questions au patient et produit une synthèse clinique
préliminaire (section 4.1 et 4.3 du cahier des charges).

Conformément à la section 4.3 ("Ces questions doivent être gérées via un tool"),
la formulation de chaque question passe par le tool ask_patient, et la
recommandation intermédiaire passe par le tool recommend_interim_care
(tous deux dans backend/app/tools/patient_tools.py).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from ..state import MedicalState
from ..tools.patient_tools import ask_patient, recommend_interim_care

# Chemin explicite vers backend/.env, indépendant du répertoire d'exécution
# (utile si l'app est lancée depuis VS Code, un autre dossier, ou en tant que module)
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

llm = ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), temperature=0)

TOTAL_QUESTIONS = 5


def diagnostic_agent(state: MedicalState) -> MedicalState:
    """Boucle de 5 questions, puis synthèse clinique + recommandation intermédiaire.

    Tant que question_count < 5 : on appelle le tool ask_patient pour obtenir
    le contexte de la question à poser, puis on demande au LLM de formuler le
    texte exact de la question. La réponse du patient est marquée EN_ATTENTE
    dans le state ; le graphe est interrompu (interrupt_before) avant ce node
    pour laisser le frontend récupérer la réponse réelle.

    Une fois les 5 questions répondues : on produit une synthèse clinique
    PRUDENTE (jamais un diagnostic définitif, conformément à la section 2 du
    cahier des charges), puis une recommandation intermédiaire via le tool
    recommend_interim_care.
    """
    question_count = state.get("question_count", 0)
    patient_answers = state.get("patient_answers", [])
    patient_case = state.get("patient_case", "")

    if question_count < TOTAL_QUESTIONS:
        # Tool ask_patient : prépare le contexte de la question (exigence 4.3)
        tool_context = ask_patient.invoke({
            "patient_case": patient_case,
            "previous_answers": "; ".join(patient_answers) if patient_answers else "",
            "question_number": question_count + 1,
        })

        prompt = (
            "Tu es un agent médical assistant un médecin pour une orientation clinique "
            "préliminaire. Pose UNE SEULE question courte et claire au patient, sans la "
            f"numéroter. Contexte : {tool_context}"
        )
        question = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        new_answers = patient_answers + [f"Q{question_count + 1}: {question} → EN_ATTENTE"]
        return {
            "question_count": question_count + 1,
            "patient_answers": new_answers,
            "next": "diagnostic_agent",
        }

    # Les 5 questions ont été répondues : synthèse + recommandation
    synthese_prompt = (
        "Rédige une synthèse clinique PRÉLIMINAIRE et PRUDENTE, en 3-4 phrases. "
        "N'émets jamais de diagnostic définitif, utilise le terme 'synthèse clinique "
        "préliminaire'. "
        f"Cas patient : {patient_case}. Réponses du patient : {patient_answers}."
    )
    synthese = llm.invoke([HumanMessage(content=synthese_prompt)]).content

    # Tool recommend_interim_care : formalise la demande de recommandation (exigence 4.4)
    tool_context_care = recommend_interim_care.invoke({"diagnostic_summary": synthese})
    interim = llm.invoke([HumanMessage(content=tool_context_care)]).content

    return {
        "diagnostic_summary": synthese,
        "interim_care": interim,
        "next": "physician_review",
    }
