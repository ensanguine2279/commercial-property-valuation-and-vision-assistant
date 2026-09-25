import base64
import html
import json
import re
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st
from google.genai import types
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image

# Define your configuration to disable automatic function calling warnings
gen_config = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    )
)

# Page config
st.set_page_config(
    page_title="Commercial Property Vision & Valuation AI", layout="wide"
)

st.title("Commercial Property Valuation & Vision Assistant")
st.write(
    "Upload a property photo and specify criteria to get an AI-powered"
    " valuation recommendation based on market comps."
)


# ---------------------------------------------------------------------------
# Helpers: content normalization + structured report rendering
# ---------------------------------------------------------------------------

RATING_STYLES = {
    "Poor": ("#b91c1c", "#fee2e2"),
    "Fair": ("#b45309", "#fef3c7"),
    "Good": ("#15803d", "#dcfce7"),
    "Excellent": ("#0f766e", "#ccfbf1"),
}


def extract_text(content) -> str:
  """Normalize LangChain content (str or list-of-parts) to plain text."""
  if isinstance(content, list):
    return "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
    )
  return content


def extract_json(text) -> dict:
  """Unwrap LangChain content parts, then pull out the JSON object."""
  # Case 1: content is a real list of parts
  if isinstance(text, list):
    text = extract_text(text)

  # Case 2: content is a string that holds a serialized parts list
  stripped = text.strip()
  if stripped.startswith("["):
    try:
      parts = json.loads(stripped)
      if isinstance(parts, list):
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except json.JSONDecodeError:
      pass

  # Case 3: find the JSON object inside the text
  match = re.search(r"\{.*\}", text, re.DOTALL)
  if not match:
    raise ValueError("No JSON object found in model response")
  return json.loads(match.group(0))


def render_visual_report(data: dict) -> None:
  """Render the vision JSON as a styled, structured report."""
  condition = str(data.get("maintenance_condition", "N/A"))
  grade = str(data.get("building_grade_tier", "N/A"))
  impact = str(data.get("valuation_impact", "N/A"))
  features = data.get("key_features", [])

  cond_fg, cond_bg = RATING_STYLES.get(condition, ("#334155", "#e2e8f0"))

  feature_items = "".join(
      f"<li style='margin-bottom:6px;'>{html.escape(str(f))}</li>"
      for f in features
  )

  report_html = f"""
    <div style="font-family: 'Segoe UI', Roboto, sans-serif; color:#0f172a;">
      <div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:16px;">
        <div style="flex:1; min-width:200px; background:{cond_bg}; border-radius:12px;
                    padding:16px 20px; border-left:6px solid {cond_fg};">
          <div style="font-size:12px; text-transform:uppercase; letter-spacing:1px;
                      color:#475569;">Maintenance Condition</div>
          <div style="font-size:26px; font-weight:700; color:{cond_fg};">
            {html.escape(condition)}</div>
        </div>
        <div style="flex:1; min-width:200px; background:#f1f5f9; border-radius:12px;
                    padding:16px 20px; border-left:6px solid #1e3a8a;">
          <div style="font-size:12px; text-transform:uppercase; letter-spacing:1px;
                      color:#475569;">Building Grade</div>
          <div style="font-size:26px; font-weight:700; color:#1e3a8a;">
            {html.escape(grade)}</div>
        </div>
      </div>

      <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px;
                  padding:16px 20px; margin-bottom:16px;">
        <div style="font-size:15px; font-weight:600; margin-bottom:8px;">
          Key Architectural &amp; Feature Observations</div>
        <ul style="margin:0; padding-left:20px; color:#334155;">{feature_items}</ul>
      </div>

      <div style="background:#eff6ff; border-radius:12px; padding:16px 20px;
                  border-left:6px solid #2563eb;">
        <div style="font-size:15px; font-weight:600; margin-bottom:6px; color:#1e40af;">
          Valuation Impact</div>
        <div style="color:#1e293b; line-height:1.6;">{html.escape(impact)}</div>
      </div>
    </div>
    """
  st.markdown(report_html, unsafe_allow_html=True)


def render_appraisal_report(data: dict, baseline_valuation: float) -> None:
  """Render the appraiser JSON as a structured valuation report."""
  exec_summary = str(data.get("executive_summary", "N/A"))
  approach = str(data.get("valuation_approach", "N/A"))
  market = str(data.get("market_analysis", "N/A"))
  adj = data.get("condition_adjustment", {}) or {}
  adj_dir = str(adj.get("direction", "none")).lower()
  adj_pct = adj.get("percentage", 0)
  adj_rationale = str(adj.get("rationale", "N/A"))
  final_value = data.get("final_value_opinion", baseline_valuation)
  confidence = str(data.get("confidence_notes", "N/A"))

  try:
    final_value = float(final_value)
  except (TypeError, ValueError):
    final_value = baseline_valuation

  delta = final_value - baseline_valuation
  adj_color = {
      "premium": "#15803d",
      "discount": "#b91c1c",
      "none": "#475569",
  }.get(adj_dir, "#475569")
  adj_label = {
      "premium": "▲ Premium Applied",
      "discount": "▼ Discount Applied",
      "none": "No Adjustment",
  }.get(adj_dir, "No Adjustment")

  report_html = f"""
    <div style="font-family:'Segoe UI', Roboto, sans-serif; color:#0f172a;">

      <div style="background:#0f172a; color:#f8fafc; border-radius:12px;
                  padding:24px 28px; margin-bottom:16px;">
        <div style="font-size:12px; text-transform:uppercase; letter-spacing:1.5px;
                    color:#94a3b8;">Final Value Opinion</div>
        <div style="font-size:34px; font-weight:700; margin-top:4px;">
          SGD {final_value:,.2f}</div>
        <div style="font-size:13px; color:#cbd5e1; margin-top:6px;">
          Baseline: SGD {baseline_valuation:,.2f}
          &nbsp;•&nbsp; Adjustment: {'+' if delta >= 0 else ''}SGD {delta:,.2f}
          &nbsp;•&nbsp; <span style="color:{adj_color}; font-weight:600;">{html.escape(adj_label)} ({adj_pct}%)</span>
        </div>
      </div>

      <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                  padding:16px 20px; margin-bottom:14px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:1px;
                    color:#64748b; font-weight:600; margin-bottom:6px;">Executive Summary</div>
        <div style="line-height:1.6;">{html.escape(exec_summary)}</div>
      </div>

      <div style="display:flex; gap:14px; flex-wrap:wrap; margin-bottom:14px;">
        <div style="flex:1; min-width:260px; background:#ffffff; border:1px solid #e2e8f0;
                    border-radius:12px; padding:16px 20px;">
          <div style="font-size:11px; text-transform:uppercase; letter-spacing:1px;
                      color:#64748b; font-weight:600; margin-bottom:6px;">Valuation Approach</div>
          <div style="line-height:1.6;">{html.escape(approach)}</div>
        </div>
        <div style="flex:1; min-width:260px; background:#ffffff; border:1px solid #e2e8f0;
                    border-radius:12px; padding:16px 20px;">
          <div style="font-size:11px; text-transform:uppercase; letter-spacing:1px;
                      color:#64748b; font-weight:600; margin-bottom:6px;">Market Analysis</div>
          <div style="line-height:1.6;">{html.escape(market)}</div>
        </div>
      </div>

      <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:6px solid {adj_color};
                  border-radius:12px; padding:16px 20px; margin-bottom:14px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:1px;
                    color:#64748b; font-weight:600; margin-bottom:6px;">Condition Adjustment Rationale</div>
        <div style="line-height:1.6;">{html.escape(adj_rationale)}</div>
      </div>

      <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:12px;
                  padding:14px 20px; font-size:13px; color:#78350f;">
        <strong>Appraiser Notes &amp; Limitations:</strong> {html.escape(confidence)}
      </div>

    </div>
    """
  st.markdown(report_html, unsafe_allow_html=True)


# Initialize SQLite database from CSV if not already present
@st.cache_resource
def init_db():
  df = pd.read_csv("commercial_property_valuations.csv")
  conn = sqlite3.connect("properties.db", check_same_thread=False)
  df.to_sql("valuations", conn, if_exists="replace", index=False)
  return conn


conn = init_db()

# Sidebar User Inputs
st.sidebar.header("Property Parameters")
region = st.sidebar.selectbox(
    "Region", [
        "Core Central Region",
        "Rest of Central Region",
        "Outside Central Region",
    ]
)
property_type = st.sidebar.selectbox(
    "Property Type",
    [
        "Office",
        "Retail/Shop",
        "Industrial/Warehouse",
        "Business Park/Mixed-Use",
    ],
)
gfa_sqm = st.sidebar.number_input("Floor Area (GFA sqm)", value=500.0, step=50.0)

# Image Upload
uploaded_file = st.sidebar.file_uploader(
    "Upload Property Photo", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  image = Image.open(uploaded_file)
  st.image(
      image,
      caption="Uploaded Property Photo",
      width="stretch",
  )

if st.button("Evaluate Property Valuation"):
  if not uploaded_file:
    st.warning("Please upload a property photo first.")
  else:
    with st.spinner("Analyzing image features and querying database comps..."):
      # 1. Analyze image with Vision Model
      vision_llm = ChatGoogleGenerativeAI(
          model="gemini-3.5-flash", temperature=0, generation_config=gen_config
      )

      # Convert PIL Image to Base64 string for LangChain multimodal input
      buffered = BytesIO()
      image.save(buffered, format="JPEG")
      img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
      image_url = f"data:image/jpeg;base64,{img_str}"

      image_prompt = [
          {
              "type": "image_url",
              "image_url": {"url": image_url},
          },
          {
              "type": "text",
              "text": (
                  "Analyze this commercial property photo. Provide a short"
                  " structural and visual condition assessment and return your response"
                  " strictly as a valid JSON object with the following keys:\n"
                  '1. "maintenance_condition": (string: rate as Poor, Fair,'
                  " Good, or Excellent)\n"
                  '2. "building_grade_tier": (string: e.g., Basic, Standard,'
                  " Premium)\n"
                  '3. "key_features": (list of strings highlighting key'
                  " exterior/interior features observed)\n"
                  '4. "valuation_impact": (string summarizing how these visual'
                  " observations could impact market valuation)\n"
                  "Do not include markdown code block backticks around the JSON"
                  " if possible, just output raw JSON."
              ),
          },
      ]

      vision_response = vision_llm.invoke([HumanMessage(content=image_prompt)])
      visual_analysis = vision_response.content

      # 2. Query Database for comparable properties using SQLite
      query = """
                SELECT AVG(PricePerSqmSGD) as avg_psm, AVG(CapRatePct) as avg_cap, COUNT(*) as comp_count
                FROM valuations
                WHERE Region = ? AND PropertyType = ?
            """
      comp_df = pd.read_sql(query, conn, params=(region, property_type))

      avg_psm = (
          # Use the average price per sqm from comparable properties, or default to 2000.0 if no comps are found
          comp_df["avg_psm"].iloc[0]
          if not comp_df.empty and comp_df["avg_psm"].iloc[0] is not None
          else 2000.0
      )
      estimated_valuation = avg_psm * gfa_sqm
      comp_count = comp_df["comp_count"].iloc[0] if not comp_df.empty else 0

      # 3. Synthesize recommendation via LLM (structured JSON, appraisal-style)
      synthesizer = ChatGoogleGenerativeAI(
          model="gemini-3.5-flash", temperature=0.2, generation_config=gen_config
      )
      synthesis_prompt = f"""
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
      final_report = synthesizer.invoke(synthesis_prompt)

      # --- Display Structured Results ---
      st.subheader("Visual Analysis Report")

      try:
        data = extract_json(visual_analysis)
        render_visual_report(data)
      except Exception:
        st.warning(
            "Could not parse the structured report. Displaying raw analysis:"
        )
        st.write(extract_text(visual_analysis))

      st.markdown("---")

      st.subheader("Market Comps Benchmark")
      st.metric(
          label="Estimated Valuation (Baseline)",
          value=f"SGD {estimated_valuation:,.2f}",
          delta=f"Based on {comp_count} historical market comparables",
      )

      st.markdown("---")

      st.subheader("Appraiser AI Recommendation")
      try:
        report_text = extract_text(final_report.content)
        report_data = extract_json(report_text)
        render_appraisal_report(report_data, estimated_valuation)
      except Exception:
        st.warning(
            "Could not parse the structured appraisal report. Displaying raw"
            " analysis:"
        )
        st.write(extract_text(final_report.content))