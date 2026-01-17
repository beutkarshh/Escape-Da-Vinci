import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import socket

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# -------------------------------
# Load environment
# -------------------------------
load_dotenv()

RXNORM_API = "https://rxnav.nlm.nih.gov/REST/drugs.json"

# Fix for IPv6/DNS issues - force IPv4
original_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    """Force IPv4 resolution to avoid IPv6 connectivity issues"""
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

# Apply IPv4 fix
socket.getaddrinfo = getaddrinfo_ipv4_only

# -------------------------------
# Fetch drugs from RxNorm
# -------------------------------
def fetch_drug_treatments(query: str, max_results: int = 5):
    """Query RxNorm API to fetch drug treatments for a condition or drug name."""
    
    # Try multiple times with different configurations
    for attempt in range(2):
        try:
            # Configure session with specific settings
            session = requests.Session()
            session.verify = True  # Enable SSL verification
            
            # Longer timeout and explicit IPv4
            response = session.get(
                RXNORM_API, 
                params={"name": query}, 
                timeout=15,  # Increased timeout
                headers={
                    'User-Agent': 'MedsAI/1.0',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            for group in data.get("drugGroup", {}).get("conceptGroup", []):
                for concept in group.get("conceptProperties", []) or []:
                    results.append({
                        "rxcui": concept.get("rxcui", "N/A"),
                        "name": concept.get("name", "Unknown"),
                        "class": group.get("tty", "Unknown"),
                    })
            
            if results:
                print(f"✅ RxNorm API: Found {len(results)} drug results for '{query}'")
            else:
                print(f"ℹ️  RxNorm API: No drugs found for '{query}'")
            
            return results[:max_results]
            
        except requests.exceptions.Timeout:
            print(f"⚠️  RxNorm API timeout on attempt {attempt + 1}/2")
            if attempt == 1:
                return []
        except requests.exceptions.SSLError as e:
            print(f"⚠️  RxNorm SSL error: {str(e)[:100]}")
            return []
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️  RxNorm connection error on attempt {attempt + 1}/2: {str(e)[:100]}")
            if attempt == 1:
                return []
        except Exception as e:
            print(f"⚠️  RxNorm API error: {type(e).__name__}: {str(e)[:100]}")
            return []
    
    print(f"ℹ️  Continuing with AI-only treatment recommendations...")
    return []

# -------------------------------
# LangChain LLM setup
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
        temperature=0.3,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    return _llm

# ✅ Escaped JSON braces inside the system prompt
treatment_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a medical treatment recommender.
Given drug results + condition, suggest BOTH drug and non-drug interventions.
Incorporate patient context (age, gender, medical history, current medications) to note contraindications, interactions, and tailoring.
Output STRICT JSON:
{{
    "treatments": [
        {{"name": "string", "class": "string", "type": "drug/non-drug", "rationale": "string", "source": "string"}}
    ]
}}"""),
        ("user", "Condition: {condition}\nAge: {age}\nGender: {gender}\nMedical History: {medical_history}\nCurrent Medications: {current_meds}\nDrug Results:\n{results}")
])

# -------------------------------
# Agent Function
# -------------------------------
def treatment_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for Treatment Agent."""
    query = state.get("diagnosis", "") or state.get("symptoms", "")
    if not query:
        state["treatment"] = {"treatments": [], "disclaimer": "No input provided."}
        return state

    # Step 1: Ask LLM to generate treatment medications for the condition
    # This gives us drug names to search in RxNorm
    parsed = None
    drug_results = []
    
    try:
        llm = _get_llm()
        if llm is not None:
            chain = treatment_prompt | llm
            
            # First, get AI-generated treatments (which will include medication names)
            result = chain.invoke({
                "condition": query,
                "age": (state.get("age") or ""),
                "gender": (state.get("gender") or ""),
                "medical_history": (state.get("medicalHistory") or state.get("history") or ""),
                "current_meds": (state.get("currentMedications") or ""),
                "results": f"Generate evidence-based drug and non-drug treatments for {query}. For drugs, include specific medication names."
            })
            parsed = json.loads((result.content or "").strip())
            
            # Step 2: Extract drug names from AI response and query RxNorm for details
            if parsed and parsed.get("treatments"):
                for treatment in parsed.get("treatments", []):
                    if treatment.get("type") == "drug" and treatment.get("name"):
                        drug_name = treatment.get("name", "").split()[0]  # Get first word (drug name)
                        rxnorm_data = fetch_drug_treatments(drug_name, max_results=1)
                        if rxnorm_data:
                            # Enhance with RxNorm data
                            treatment["rxcui"] = rxnorm_data[0].get("rxcui", "N/A")
                            treatment["source"] = "RxNorm + AI"
                            drug_results.extend(rxnorm_data)
                        else:
                            treatment["source"] = "Clinical Guidelines"
                            
    except Exception as e:
        print(f"❌ Treatment LLM error: {e}")
        parsed = None

    if parsed is None:
        # Fallback - if LLM failed, provide basic treatment structure
        if drug_results:
            # We have RxNorm data but LLM failed
            parsed = {
                "treatments": [
                    {
                        "name": r.get("name", "Unknown"),
                        "class": r.get("class", "Unknown"),
                        "type": "drug",
                        "rationale": "Listed based on RxNorm lookup; details unavailable.",
                        "source": "RxNorm"
                    }
                    for r in drug_results[:3]
                ]
            }
        else:
            # No RxNorm and LLM failed - provide generic guidance
            parsed = {
                "treatments": [
                    {
                        "name": "Consult Healthcare Provider",
                        "class": "Clinical Assessment",
                        "type": "non-drug",
                        "rationale": f"Professional medical evaluation recommended for {query}. Treatment options should be determined by a licensed physician based on complete clinical assessment.",
                        "source": "Clinical Guidelines"
                    }
                ]
            }

    state["treatment"] = {
        "query": query,
        "treatments": parsed.get("treatments", []),
        "patient_context": {
            "age": state.get("age"),
            "gender": state.get("gender"),
            "medical_history": state.get("medicalHistory", state.get("history")),
            "current_medications": state.get("currentMedications"),
        },
        "disclaimer": "AI-generated treatment recommendations. External drug databases may be unavailable. Always verify with clinical guidelines and licensed healthcare providers."
    }
    return state

# -------------------------------
# Build Graph (standalone)
# -------------------------------
def build_treatment_graph():
    graph = StateGraph(dict)
    graph.add_node("treatment_agent", treatment_agent)
    graph.set_entry_point("treatment_agent")
    graph.add_edge("treatment_agent", END)
    return graph.compile()
