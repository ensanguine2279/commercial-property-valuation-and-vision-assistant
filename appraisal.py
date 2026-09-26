"""Synthesis of the structured appraiser recommendation via LLM."""

from langchain_google_genai import ChatGoogleGenerativeAI

from config import SYNTHESIS_MODEL

SYNTHESIS_PROMPT_TEMPLATE = """
You are a senior commercial real estate appraiser preparing a formal valuation report.

Property Type: {property_type}
Region: {region}
Gross Floor Area (GFA): {gfa_sqm} sqm
Visual Condition Analysis from Photo: {visual_analysis}
Market Benchmark: Average Price per Sqm for similar properties is SGD {avg_psm:,.2f}
Calculated Baseline Valuation (GFA * Avg PSM): SGD {estimated_valuation:,.2f}
Number of Comparable Transactions: {comp_count}

Produce a valuation report and return your response strictly as a valid JSON object
with the following keys, and nothing else (no markdown, no backticks):

1. "executive_summary": (string, 2-3 sentences summarizing the opinion of value)
2. "valuation_approach": (string: name the approach used, e.g. "Sales Comparison Approach", and briefly explain why it fits)
3. "market_analysis": (string: commentary on the comparable transactions and market conditions for this region/type)
4. "condition_adjustment": (object with keys "direction": "premium"|"discount"|"none", "percentage": number, "rationale": string)
5. "final_value_opinion": (number: the final adjusted valuation in SGD, as a plain number with no currency symbol or commas)
6. "confidence_notes": (string: caveats, e.g. limited comp count, photo-only condition assessment, not a substitute for physical inspection)
"""


def generate_appraisal_report(
    property_type: str,
    region: str,
    gfa_sqm: float,
    visual_analysis,
    avg_psm: float,
    estimated_valuation: float,
    comp_count: int,
):
  """Call the synthesis model and return the raw response content.

  Returns the raw `response.content` (str or list-of-parts) exactly as
  LangChain returns it; use parsing.extract_json/extract_text on the result.
  """
  synthesizer = ChatGoogleGenerativeAI(model=SYNTHESIS_MODEL, temperature=0.2)
  prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
      property_type=property_type,
      region=region,
      gfa_sqm=gfa_sqm,
      visual_analysis=visual_analysis,
      avg_psm=avg_psm,
      estimated_valuation=estimated_valuation,
      comp_count=comp_count,
  )
  final_report = synthesizer.invoke(prompt)
  return final_report.content
