"""
Supervisor — orchestre le workflow et décide de l'étape suivante.
"""

from ..state import MedicalState


def supervisor(state: MedicalState) -> MedicalState:
    """Route vers le prochain agent en fonction de la clé 'next' du state.

    Le Supervisor ne contient aucune logique métier : il lit la décision
    déjà posée par le node précédent (via 'next') et la retransmet. C'est
    l'aiguillage explicite demandé par le cahier des charges (section 4.1),
    matérialisé par les conditional_edges du graphe (voir graph.py).
    """
    return {"next": state.get("next", "diagnostic_agent")}
