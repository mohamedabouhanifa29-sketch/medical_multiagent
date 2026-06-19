"""
PhysicianReview — étape Human-in-the-Loop représentant le médecin traitant
(section 4.1 et 4.2 du cahier des charges).

Ce node ne fait rien d'actif : c'est un point de passage. Toute la logique
HITL réside dans la compilation du graphe (interrupt_before=["physician_review"]
dans graph.py), qui suspend l'exécution avant ce node pour laisser le temps
au médecin de consulter la synthèse clinique et la recommandation
intermédiaire, puis de saisir son traitement via l'API (endpoint
/consultation/resume avec physician_treatment).
"""

from ..state import MedicalState


def physician_review(state: MedicalState) -> MedicalState:
    """Point de passage HITL. Le state est inchangé ; physician_treatment
    est injecté de l'extérieur via graph.update_state() avant la reprise.
    """
    return state
