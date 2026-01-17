import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END   # ✅ works in 0.6.7

# Load environment variables
load_dotenv()

# -------------------------------
# Define Model (LangChain wrapper for OpenRouter)
# -------------------------------
_llm = None


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    _llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    return _llm

# -------------------------------
# Prompt Template (with ICD-10-CM India requirement)
# -------------------------------
prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a medical reasoning assistant.
For each differential diagnosis, return the official ICD-10-CM (India edition) code along with rationale.

Return STRICT JSON only in this schema:
{{
    "top_differentials": [
        {{
            "name": "string",
            "rationale": "string",
            "icd10cm_code": "string"
        }}
    ],
    "risk_level": "low|moderate|high",
    "disclaimer": "This is AI-generated and not medical advice."
}}
"""),
        ("user", "Patient input:\nSymptoms: {symptoms}\nAge: {age}\nGender: {gender}\nMedical History: {medicalHistory}\nCurrent Medications: {currentMedications}\nUrgency: {urgency}")
])

# -------------------------------
# Agent Function
# -------------------------------
def symptom_analyzer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for Symptom Analyzer"""
    # Dev fallback when LLM key missing
    llm = _get_llm()
    if llm is None:
        state["symptom_analysis"] = {
            "top_differentials": [],
            "risk_level": "low",
            "disclaimer": "LLM unavailable in development (OPENROUTER_API_KEY missing). Returning placeholder results."
        }
        return state

    try:
        chain = prompt | llm
        result = chain.invoke({
            "symptoms": state.get("symptoms", ""),
            "age": state.get("age", ""),
            # Back-compat: prefer medicalHistory, fallback to history
            "medicalHistory": state.get("medicalHistory", state.get("history", "")),
            "gender": state.get("gender", ""),
            "currentMedications": state.get("currentMedications", ""),
            "urgency": state.get("urgency", ""),
        })

        raw_content = (result.content or "").strip()
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            parsed = {"raw_output": raw_content}
    except Exception as e:
        parsed = {
            "top_differentials": [],
            "risk_level": "low",
            "error": str(e),
            "disclaimer": "Symptom analyzer failed to run. Placeholder returned."
        }

    # Add output back into state
    state["symptom_analysis"] = parsed
    
    # Extract diagnosis for other agents to use
    top_differentials = parsed.get("top_differentials", [])
    if top_differentials and len(top_differentials) > 0:
        top_diagnosis = top_differentials[0].get("name", "")
        if top_diagnosis:
            state["diagnosis"] = top_diagnosis
            print(f"✅ Extracted diagnosis: {top_diagnosis}")
    
    return state

# -------------------------------
# Build Graph (compile workflow)
# -------------------------------
def build_symptom_graph():
    graph = StateGraph(dict)

    # Add Symptom Analyzer node
    graph.add_node("symptom_analyzer", symptom_analyzer_agent)

    # Entry → Symptom Analyzer → End
    graph.set_entry_point("symptom_analyzer")
    graph.add_edge("symptom_analyzer", END)

    return graph.compile()
# (Removed duplicate block)
