# import the libraries form ptcharm 

import json
from langgraph.graph import StateGraph, END   # ✅ fixed import

# Import agents
from agents.symptom_analyzer import symptom_analyzer_agent
from agents.literature_agent import literature_agent
from agents.case_matcher import case_matcher_agent
from agents.treatment_agent import treatment_agent
from agents.summarizer_agent import summarizer_agent   # ✅ new import

# -------------------------------
# Orchestrator Graph
# -------------------------------
def build_orchestrator_graph():
    graph = StateGraph(dict)

    # Add agents as nodes
    graph.add_node("symptom_analyzer", symptom_analyzer_agent)
    graph.add_node("literature_agent", literature_agent)
    graph.add_node("case_matcher", case_matcher_agent)
    graph.add_node("treatment_agent", treatment_agent)
    graph.add_node("summarizer_agent", summarizer_agent)   # ✅ new

    # Flow: Entry → Symptom Analyzer → Literature Agent → Case Matcher → Treatment Agent → Summarizer Agent → End
    graph.set_entry_point("symptom_analyzer")
    graph.add_edge("symptom_analyzer", "literature_agent")
    graph.add_edge("literature_agent", "case_matcher")
    graph.add_edge("case_matcher", "treatment_agent")
    graph.add_edge("treatment_agent", "summarizer_agent")   # ✅ added
    graph.add_edge("summarizer_agent", END)                 # ✅ final step

    return graph.compile()
