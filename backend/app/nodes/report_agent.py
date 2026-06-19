"""
ReportAgent — génère le rapport final structuré (section 4.1 du cahier des charges).

C'est ici que l'intégration MCP (section 9, obligatoire) est réellement
utilisée dans le workflow : get_drug_info et get_emergency_level sont
appelés via les tools de care_tools.py, qui passent par le client MCP
(backend/app/tools/mcp_client.py) qui lance le serveur MCP réel
(mcp_server/server.py) en sous-processus stdio. Ce n'est pas une logique
dupliquée localement : si le serveur MCP est modifié, le rapport change.
"""

from ..state import MedicalState
from ..tools.care_tools import get_drug_info, get_emergency_level

DISCLAIMER = "⚠️ Ce système ne remplace pas une consultation médicale."


def report_agent(state: MedicalState) -> MedicalState:
    """Construit le rapport clinique final en agrégeant tout le state, et en
    enrichissant via deux appels MCP réels : info médicament (à partir du
    traitement saisi par le médecin) et niveau d'urgence (à partir du cas
    + de la synthèse clinique).
    """
    answers_text = "\n".join(state.get("patient_answers", []))
    physician_treatment = state.get("physician_treatment", "")
    symptoms_text = f"{state.get('patient_case', '')} {state.get('diagnostic_summary', '')}"

    drug_info = ""
    if physician_treatment:
        drug_name = physician_treatment.split()[0]
        # Appel MCP réel (tool LangChain -> mcp_client -> serveur MCP stdio)
        drug_info = get_drug_info.invoke({"drug_name": drug_name})

    # Appel MCP réel pour le niveau d'urgence
    urgency = get_emergency_level.invoke({"symptoms": symptoms_text})

    rapport = f"""RAPPORT CLINIQUE PRÉLIMINAIRE

CAS : {state.get('patient_case')}

RÉPONSES PATIENT :
{answers_text}

SYNTHÈSE CLINIQUE :
{state.get('diagnostic_summary')}

RECOMMANDATION INTERMÉDIAIRE :
{state.get('interim_care')}

TRAITEMENT MÉDECIN :
{physician_treatment}

INFORMATION MÉDICAMENT (via MCP) :
{drug_info}

NIVEAU D'URGENCE (via MCP) :
{urgency}

{DISCLAIMER}"""

    return {"final_report": rapport, "next": "FINISH"}
