"""
Client MCP — pont vers le serveur d'outils médicaux
=====================================================

Ce module est le SEUL point d'accès au serveur MCP (mcp_server/server.py).
Il lance le serveur en sous-processus via stdio, appelle un outil, puis
ferme la session — à chaque appel. C'est volontairement simple (pas de
session MCP persistante) car le volume d'appels d'un projet académique
ne le justifie pas, mais le wrapper est isolé ici pour qu'on puisse passer
à une session persistante sans toucher au reste du code.

Le protocole MCP est asynchrone (asyncio). LangGraph et FastAPI exécutent
ici du code synchrone (les nodes du graphe sont des fonctions sync), donc
on expose des fonctions synchrones qui pilotent l'event loop en interne.
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Chemin absolu vers le serveur MCP, indépendant du répertoire d'exécution
_SERVER_PATH = str((Path(__file__).resolve().parent.parent.parent.parent / "mcp_server" / "server.py"))


async def _call_tool_async(tool_name: str, arguments: dict) -> str:
    """Lance le serveur MCP en sous-processus, appelle un outil, récupère le texte."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[_SERVER_PATH],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if result.content and hasattr(result.content[0], "text"):
                return result.content[0].text
            return str(result.content)


def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Version synchrone, utilisable directement dans un node LangGraph.

    En cas d'échec de connexion au serveur MCP (process introuvable, crash, etc.),
    retourne un message de repli plutôt que de faire planter le graphe — un outil
    MCP indisponible ne doit pas bloquer la génération du rapport final.
    """
    try:
        return asyncio.run(_call_tool_async(tool_name, arguments))
    except Exception as exc:  # noqa: BLE001 — on veut un repli générique ici
        return f"[MCP indisponible : {exc}]"


def get_drug_info_via_mcp(drug_name: str) -> str:
    """Appelle l'outil MCP get_drug_info."""
    return call_mcp_tool("get_drug_info", {"drug_name": drug_name})


def get_emergency_level_via_mcp(symptoms: str) -> str:
    """Appelle l'outil MCP get_emergency_level."""
    return call_mcp_tool("get_emergency_level", {"symptoms": symptoms})
