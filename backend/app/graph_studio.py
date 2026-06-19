"""
Point d'entrée pour LangGraph Studio (section 12 du cahier des charges).

Studio gère sa propre persistance, donc on compile sans checkpointer
explicite ici. Toute la logique du graphe vient de build_graph() dans
graph.py : ce fichier n'est qu'un point d'entrée minimal pour langgraph.json.
"""

from .graph import build_graph

graph = build_graph(checkpointer=None)
