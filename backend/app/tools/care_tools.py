"""
Tools de soin — médicaments et urgence (via MCP)
===================================================

Ces tools encapsulent les appels au serveur MCP réel (mcp_server/server.py)
à travers mcp_client.py. C'est l'unique chemin par lequel le graphe accède
aux informations médicaments et au niveau d'urgence : aucune logique
médicale n'est dupliquée ici, tout passe par le protocole MCP.
"""

from langchain_core.tools import tool

from .mcp_client import get_drug_info_via_mcp, get_emergency_level_via_mcp


@tool
def get_drug_info(drug_name: str) -> str:
    """Retourne des informations générales sur un médicament via le serveur MCP.

    Args:
        drug_name: nom du médicament à rechercher.

    Returns:
        Fiche médicament (posologie, contre-indications) ou message générique.
    """
    return get_drug_info_via_mcp(drug_name)


@tool
def get_emergency_level(symptoms: str) -> str:
    """Évalue un niveau d'urgence indicatif via le serveur MCP.

    Args:
        symptoms: description textuelle des symptômes.

    Returns:
        Niveau d'urgence (rouge/orange/vert) avec recommandation associée.
    """
    return get_emergency_level_via_mcp(symptoms)
