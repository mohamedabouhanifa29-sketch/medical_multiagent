"""
Serveur MCP — Outils médicaux
==============================

Ce serveur expose deux outils via le protocole MCP (Model Context Protocol) :

    - get_drug_info(drug_name)      : informations sur un médicament
    - get_emergency_level(symptoms) : évaluation du niveau d'urgence

Il tourne en transport stdio et est lancé en sous-processus par le client MCP
du backend (voir backend/app/tools/mcp_client.py). C'est ce client qui est
appelé depuis report_agent — le serveur n'est jamais appelé directement par
le frontend ni par le graphe LangGraph.

Lancement manuel (debug uniquement) :
    python server.py
"""

import json
import unicodedata
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Medical Tools Server")

DATA_DIR = Path(__file__).parent / "data"
DRUGS_DB_PATH = DATA_DIR / "drugs.json"

with open(DRUGS_DB_PATH, "r", encoding="utf-8") as f:
    DRUGS_DB: dict = json.load(f)


def _normalize(text: str) -> str:
    """Retire les accents et met en minuscule, pour un matching robuste
    (ex: 'Paracétamol' et 'paracetamol' doivent matcher la même entrée)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


@mcp.tool()
def get_drug_info(drug_name: str) -> str:
    """Retourne des informations générales sur un médicament à partir de son nom.

    Args:
        drug_name: nom du médicament (français ou commercial), insensible à la casse.

    Returns:
        Une fiche texte avec catégorie, posologie adulte, dose max/jour,
        contre-indications et remarques. Message générique si non trouvé.
    """
    key = _normalize(drug_name)

    match = None
    for db_key, info in DRUGS_DB.items():
        norm_db_key = _normalize(db_key)
        if norm_db_key in key or key in norm_db_key:
            match = info
            break

    if not match:
        return (
            f"Médicament '{drug_name}' non trouvé dans la base locale. "
            "Consulter un pharmacien ou le Vidal avant toute prescription."
        )

    return (
        f"{match['nom']} ({match['categorie']})\n"
        f"Dose adulte : {match['dose_adulte']}\n"
        f"Dose maximale/jour : {match['dose_max_jour']}\n"
        f"Contre-indications : {match['contre_indications']}\n"
        f"Remarque : {match['remarque']}"
    )


@mcp.tool()
def get_emergency_level(symptoms: str) -> str:
    """Évalue un niveau d'urgence indicatif à partir d'une description de symptômes.

    Args:
        symptoms: texte libre décrivant les symptômes du patient.

    Returns:
        Un niveau d'urgence (rouge/orange/vert) avec une recommandation associée.
        Cette évaluation est indicative et ne remplace pas un avis médical.
    """
    symptoms_lower = _normalize(symptoms)

    red_flags = [
        "douleur thoracique", "difficultes a respirer",
        "perte de conscience", "paralysie", "confusion", "saignement",
        "fracture", "accident",
    ]
    orange_flags = [
        "fievre elevee", "vomissements", "douleur intense",
        "vertiges", "infection",
    ]

    for flag in red_flags:
        if flag in symptoms_lower:
            return (
                "🔴 URGENCE ABSOLUE — Appeler le 15 (SAMU) ou se rendre aux urgences "
                "immédiatement. Ne pas attendre."
            )

    for flag in orange_flags:
        if flag in symptoms_lower:
            return (
                "🟠 URGENCE RELATIVE — Consultation médicale recommandée dans les 24 heures."
            )

    return (
        "🟢 NON URGENT — Surveillance à domicile possible. "
        "Consulter un médecin en cas d'aggravation."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
