import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# -------------------------------
# Env & LLM
# -------------------------------
load_dotenv()

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
# Helpers to gather upstream outputs
# -------------------------------
def _safe_get(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def _take(lst, n):
    if not isinstance(lst, list):
        return []
    return lst[:n]

def _extract_inputs(state: Dict[str, Any]) -> Dict[str, Any]:
    # Raw patient context
    symptoms = state.get("symptoms", "")
    age = state.get("age", "")
    # Prefer medicalHistory, fall back to history (back-compat)
    medical_history = state.get("medicalHistory", state.get("history", ""))
    gender = state.get("gender", "")
    current_meds = state.get("currentMedications", "")
    urgency = state.get("urgency", "")
    diagnosis = state.get("diagnosis", "")

    # Symptom Analyzer (top 3)
    diffs = _safe_get(state, ["symptom_analysis", "top_differentials"], []) or []
    top_diffs = _take(diffs, 3)

    # Literature (top 3 summaries)
    lit = state.get("literature", {}) or {}
    lit_articles_container = lit.get("articles", {})
    lit_summaries = []
    if isinstance(lit_articles_container, dict):
        lit_summaries = _take(lit_articles_container.get("summaries", []), 3)
    elif isinstance(lit_articles_container, list):
        # If someone put raw list in there; map to a simple structure
        lit_summaries = _take([
            {
                "pmid": a.get("pmid", ""),
                "title": a.get("title", ""),
                "summary": a.get("abstract_snippet", a.get("abstract", ""))[:600],
            }
            for a in lit_articles_container
        ], 3)

    # Case Matcher (top 3)
    case_matches = _safe_get(state, ["case_matcher", "matched_cases"], []) or []
    case_matches = _take(case_matches, 3)

    # Treatment (top 3)
    treatments = _safe_get(state, ["treatment", "treatments"], []) or []
    treatments = _take(treatments, 3)

    return {
        "patient_context": {
            "symptoms": symptoms,
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
            "current_medications": current_meds,
            "urgency": urgency,
            "working_diagnosis": diagnosis,
        },
        "top_differentials": top_diffs,
        "literature": lit_summaries,
        "case_matches": case_matches,
        "treatments": treatments,
    }

# -------------------------------
# Prompt (STRICT JSON)
# -------------------------------
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a medical report summarizer. 
You will receive patient context and outputs from multiple agents (differentials, literature, case matches, and treatments).
Write two concise summaries and recommended next steps.

Return STRICT JSON ONLY in this schema:
{{
  "summary": {{
    "patient_summary": "string", 
    "clinical_summary": "string",
    "recommendations": [
      {{"type": "next_steps", "content": "string"}}
    ],
    "citations": {{
      "pmids": ["string"],
      "sources": ["string"]
    }}
  }},
  "disclaimer": "This is AI-generated and not medical advice."
}}

Guidance:
- patient_summary: plain language, ≤ 150 words.
- clinical_summary: technical, mention leading differential + ICD codes if available, ≤ 180 words.
- recommendations: 2–4 items, actionable (tests, referrals, monitoring, red flags).
- citations.pmids: collect PMIDs from literature if present (unique, ≤ 5).
- citations.sources: include recognizable guideline sources if present in treatments (e.g., ADA, NICE), ≤ 5.
"""),
    ("user", "Patient & Agent Outputs:\n{payload_json}")
])

# -------------------------------
# Agent node
# -------------------------------
def summarizer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    payload = _extract_inputs(state)

    # Collect PMIDs & sources for hints (the LLM also does this, but we pass along)
    pmids = list({
        (art.get("pmid") or "").strip()
        for art in payload.get("literature", [])
        if art.get("pmid")
    })
    # Add quick hint so LLM doesn't miss them
    payload["_hints"] = {
        "pmids": _take(pmids, 5),
        "sources": _take([
            t.get("source", "")
            for t in payload.get("treatments", [])
            if t.get("source")
        ], 5)
    }

    parsed = None
    try:
        llm = _get_llm()
        if llm is not None:
            chain = summary_prompt | llm
            result = chain.invoke({
                "payload_json": json.dumps(payload, indent=2, ensure_ascii=False)
            })
            raw = (result.content or "").strip()
            parsed = json.loads(raw)
    except Exception as e:
        print(f"❌ Summarizer LLM error: {e}")
        parsed = None

    if parsed is None:
        # Simple deterministic summary for dev mode
        pc = payload.get("patient_context", {})
        parsed = {
            "summary": {
                "patient_summary": f"Patient with symptoms: {pc.get('symptoms', '')}. Age: {pc.get('age', '')}, Gender: {pc.get('gender', '')}.",
                "clinical_summary": "Preliminary outputs provided from placeholder pipelines.",
                "recommendations": [
                    {"type": "next_steps", "content": "Confirm history, perform physical exam, and order basic labs."}
                ],
                "citations": {"pmids": payload.get("_hints", {}).get("pmids", []), "sources": payload.get("_hints", {}).get("sources", [])}
            },
            "disclaimer": "This is AI-generated and not medical advice. In development, LLM outputs may be simplified."
        }

    state["summary"] = parsed.get("summary", {})
    state["summary_disclaimer"] = parsed.get("disclaimer", "This is AI-generated and not medical advice.")
    return state

# -------------------------------
# Build graph (standalone)
# -------------------------------
def build_summarizer_graph():
    graph = StateGraph(dict)
    graph.add_node("summarizer", summarizer_agent)
    graph.set_entry_point("summarizer")
    graph.add_edge("summarizer", END)
    return graph.compile()
