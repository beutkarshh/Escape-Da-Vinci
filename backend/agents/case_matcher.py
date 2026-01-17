import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()
BIOPORTAL_API_KEY = os.getenv("BIOPORTAL_API_KEY")  # ✅ Must be set in .env

BIOPORTAL_API_URL = "https://data.bioontology.org/search"

# -------------------------------
# Fetch Case Matches from BioPortal
# -------------------------------
def calculate_match_score(query: str, result_name: str, match_type: str = "prefLabel") -> float:
    """Calculate a match score based on query similarity"""
    query_lower = query.lower()
    name_lower = result_name.lower()
    
    # Exact match
    if query_lower == name_lower:
        return 95.0
    
    # Query is substring of result or vice versa
    if query_lower in name_lower or name_lower in query_lower:
        return 85.0
    
    # Word overlap scoring
    query_words = set(query_lower.split())
    name_words = set(name_lower.split())
    
    if not query_words or not name_words:
        return 60.0
    
    common_words = query_words & name_words
    overlap_ratio = len(common_words) / max(len(query_words), len(name_words))
    
    # Match type bonus
    match_type_bonus = 10.0 if match_type == "prefLabel" else 0.0
    
    # Calculate score: 60-90% based on word overlap + bonus
    score = 60.0 + (overlap_ratio * 30.0) + match_type_bonus
    
    return min(95.0, score)  # Cap at 95%

def fetch_case_matches(query: str, max_results: int = 5):
    """Search BioPortal API for ICD/SNOMED/MeSH terms related to query."""
    if not BIOPORTAL_API_KEY:
        # Dev fallback without external call
        return []
    params = {
        "q": query,
        "ontologies": "ICD10CM,SNOMEDCT,MSH",
        "apikey": BIOPORTAL_API_KEY,
        "pagesize": max_results,
    }
    try:
        response = requests.get(BIOPORTAL_API_URL, params=params, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching BioPortal results: {e}")
        return []

    data = response.json()
    
    results = []
    for idx, item in enumerate(data.get("collection", [])):
        # Extract code from @id URL (e.g., SNOMEDCT/73211009 or ICD10CM/E11)
        code_id = item.get("@id", "")
        code = code_id.split("/")[-1] if code_id else "N/A"
        
        # Try to get the ontology source (SNOMEDCT, ICD10CM, etc.)
        ontology_link = item.get("links", {}).get("ontology", "")
        ontology_source = ontology_link.split("/")[-1] if ontology_link else "Unknown"
        
        # Get definition - it might be a string or list
        definition = item.get("definition")
        if isinstance(definition, list) and definition:
            description = definition[0]
        elif isinstance(definition, str):
            description = definition
        else:
            # Use synonym as fallback description
            synonyms = item.get("synonym", [])
            description = synonyms[0] if synonyms else "No description available"
        
        # Calculate match score
        match_type = item.get("matchType", "")
        result_name = item.get("prefLabel", "Unknown")
        match_score = calculate_match_score(query, result_name, match_type)
        
        # Reduce score for subsequent results (rank penalty)
        rank_penalty = idx * 5.0
        final_score = max(60.0, match_score - rank_penalty)
        
        results.append({
            "icd_code": f"{ontology_source}:{code}",  # e.g., "SNOMEDCT:73211009"
            "name": result_name,
            "description": description,
            "score": round(final_score, 1),  # Now a meaningful percentage
            "cui": item.get("cui", ["N/A"])[0] if item.get("cui") else "N/A",
        })

    return results[:max_results]

# -------------------------------
# LangChain LLM Setup
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

# Prompt for refinement
matcher_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a clinical case matcher AI.
Given ontology results, pick the **top 3 most relevant matches**.
Return STRICT JSON in this schema:
{{
  "matched_cases": [
    {{"icd_code": "string", "name": "string", "description": "string", "match_score": float}}
  ]
}}"""),   # 👈 Escaped curly braces
    ("user", "Ontology results:\n{results}")
])

# -------------------------------
# Agent Function
# -------------------------------
def case_matcher_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for Case Matcher Agent (BioPortal + LLM refinement)."""
    symptoms = (state.get("symptoms") or "").strip()
    diagnosis = (state.get("diagnosis") or "").strip()
    age = (state.get("age") or "").__str__().strip()
    gender = (state.get("gender") or "").strip()
    medical_history = (state.get("medicalHistory") or state.get("history") or "").strip()

    # Build a focused query - prioritize diagnosis, then symptoms
    # Don't make it too long or it won't match anything in BioPortal
    if diagnosis:
        query = diagnosis
    elif symptoms:
        # Take first few symptoms only
        symptom_list = symptoms.split(",")[:2]
        query = ", ".join(symptom_list).strip()
    else:
        query = ""
    
    if not query:
        state["case_matcher"] = {
            "matched_cases": [],
            "disclaimer": "No query provided."
        }
        return state

    raw_results = fetch_case_matches(query)
    
    # Debug output
    print(f"🔍 Case Matcher Query: {query}")
    print(f"📊 BioPortal returned {len(raw_results)} results")
    if raw_results:
        print(f"First result: {raw_results[0]}")

    if not raw_results:
        state["case_matcher"] = {
            "matched_cases": [],
            "disclaimer": "No matches found from BioPortal."
        }
        return state

    # Send ontology results to LLM for ranking & selection
    parsed = None
    try:
        llm = _get_llm()
        if llm is not None:
            chain = matcher_prompt | llm
            result = chain.invoke({"results": json.dumps(raw_results, indent=2)})
            parsed = json.loads((result.content or "").strip())
    except Exception as e:
        print(f"❌ Case matcher LLM error: {e}")
        parsed = None
    if parsed is None:
        # Simple passthrough of top 3 with basic mapping
        parsed = {
            "matched_cases": [
                {
                    "icd_code": r.get("icd_code", "N/A"),
                    "name": r.get("name", "Unknown"),
                    "description": r.get("description", ""),
                    "match_score": r.get("score", 0)
                }
                for r in raw_results[:3]
            ]
        }

    state["case_matcher"] = {
        "query": query,
        "matched_cases": parsed.get("matched_cases", []),
        "patient_context": {
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
        },
        "disclaimer": "Ontology matches are retrieved via BioPortal (ICD/SNOMED/MeSH) and AI-refined. Verify clinically."
    }
    return state

# -------------------------------
# Build Graph (standalone version)
# -------------------------------
def build_case_matcher_graph():
    graph = StateGraph(dict)
    graph.add_node("case_matcher", case_matcher_agent)
    graph.set_entry_point("case_matcher")
    graph.add_edge("case_matcher", END)
    return graph.compile()
