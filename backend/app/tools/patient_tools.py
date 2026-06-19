"""
Tools patient — interaction avec le patient
=============================================

Le cahier des charges exige explicitement (section 4.3 et workflow section 5)
que les questions au patient soient gérées via un TOOL nommé ask_patient,
et non par un appel LLM direct dans le corps du node.

Ces tools sont volontairement simples : générer le texte de la question
suivante à partir du contexte, et formuler la recommandation intermédiaire.
La logique métier (boucle de 5 questions, mise à jour du state) reste dans
le node diagnostic_agent — un tool LangChain n'a pas accès au state du
graphe, il reçoit seulement les arguments qu'on lui passe explicitement.
"""

from langchain_core.tools import tool


@tool
def ask_patient(patient_case: str, previous_answers: str, question_number: int) -> str:
    """Formule la prochaine question à poser au patient dans le cadre du diagnostic.

    Args:
        patient_case: description initiale du cas patient.
        previous_answers: résumé textuel des questions/réponses déjà obtenues.
        question_number: numéro de la question à poser (1 à 5).

    Returns:
        Le texte de la question à poser au patient, sans numérotation.
    """
    return (
        f"[Tool ask_patient] Question {question_number}/5 à formuler pour le cas : "
        f"{patient_case}. Réponses précédentes : {previous_answers or 'aucune'}."
    )


@tool
def recommend_interim_care(diagnostic_summary: str) -> str:
    """Propose une recommandation intermédiaire prudente à partir d'une synthèse clinique.

    La recommandation reste générale (repos, hydratation, surveillance,
    consultation rapide en cas d'aggravation) et ne remplace jamais l'avis
    du médecin traitant.

    Args:
        diagnostic_summary: synthèse clinique préliminaire produite par le DiagnosticAgent.

    Returns:
        Un texte court de recommandation intermédiaire.
    """
    return (
        f"[Tool recommend_interim_care] À partir de la synthèse suivante : "
        f"{diagnostic_summary}, proposer repos, hydratation, surveillance des symptômes, "
        f"et consultation rapide en cas d'aggravation."
    )
