import os
import json
import re
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from state import VerificationReport
from tools import search_web
from database import claim_exists, get_existing_claim, insert_claim

load_dotenv()

# Use a current Groq model
llm = ChatGroq(
    model="llama-3.1-8b-instant",   # or "mixtral-8x7b-32768"
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def extract_json_from_response(text: str) -> dict:
    """Robustly extract JSON from LLM response that may contain extra text or markdown."""
    # Remove markdown code blocks
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    # Find the first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        return json.loads(json_str)
    raise ValueError("No JSON object found in response")

def agent_investigator(claim: str) -> VerificationReport:
    """
    Use Tavily search + LLM to investigate a claim and produce
    a structured verification report.
    """
    search_results = search_web(claim)

    # Strong system prompt forcing JSON-only output
    system_prompt = """
You are a professional fact-checker. Based on the search evidence below,
determine the veracity of the user's claim.

You MUST output ONLY a single JSON object. Do not include any other text, explanation, or markdown.
The JSON must contain exactly these fields:

{
  "verdict": "TRUE" or "FALSE" or "INSUFFICIENT_EVIDENCE",
  "confidence": a number between 0 and 1,
  "evidence_summary": "a short sentence summarizing the evidence",
  "sources": ["url1", "url2", ...]
}

Example valid output:
{"verdict": "FALSE", "confidence": 0.95, "evidence_summary": "No record of India winning FIFA World Cup.", "sources": ["https://example.com"]}
"""

    user_prompt = f"""
Claim to check: {claim}

Search evidence:
{search_results}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    raw_content = response.content.strip()
    if not raw_content:
        raise ValueError("LLM returned empty response")

    # Debug: print raw response to terminal (helps diagnose JSON issues)
    print("\n[DEBUG] Raw LLM response:\n", raw_content, "\n")

    try:
        data = extract_json_from_response(raw_content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing failed: {e}")
        return VerificationReport(
            claim=claim,
            verdict="INSUFFICIENT_EVIDENCE",
            confidence=0.0,
            evidence_summary=f"Could not parse LLM response. Raw: {raw_content[:200]}",
            sources=["Error: JSON parse failed"]
        )

    # Validate required keys
    required = ["verdict", "confidence", "evidence_summary", "sources"]
    for key in required:
        if key not in data:
            raise KeyError(f"Missing key '{key}' in LLM response: {data}")

    # Ensure sources is a list
    if not isinstance(data["sources"], list):
        data["sources"] = [str(data["sources"])]

    return VerificationReport(
        claim=claim,
        verdict=data["verdict"],
        confidence=float(data["confidence"]),
        evidence_summary=data["evidence_summary"],
        sources=data["sources"]
    )

def agent_archivist(report: VerificationReport) -> str:
    """
    Decide what to do with the verification report:
    - INSERT if new and verified (verdict TRUE, confidence >= 0.7)
    - DISCARD if already present or not verifiably true
    - FLAG if contradiction with existing claim
    """
    claim = report.claim

    if claim_exists(claim):
        existing = get_existing_claim(claim)
        if existing:
            _, _, existing_verdict, _, _, _, _ = existing
            if existing_verdict != report.verdict:
                return "FLAG"   # contradiction
            else:
                return "DISCARD"  # duplicate
    else:
        # Only insert if the claim is verified as TRUE with reasonable confidence
        if report.verdict == "TRUE" and report.confidence >= 0.7:
            insert_claim(
                claim=claim,
                verdict=report.verdict,
                confidence=report.confidence,
                evidence_summary=report.evidence_summary,
                sources=report.sources
            )
            return "INSERT"
        else:
            return "DISCARD"

    return "DISCARD"