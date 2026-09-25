"""Commercial Property Valuation & Vision Assistant — Streamlit entry point.

All logic lives in dedicated modules; this file only wires the UI together:
  config.py         - shared Gemini configuration
  db.py             - comps database (SQLite from CSV)
  vision.py         - vision model call (photo -> condition analysis)
  appraisal.py      - synthesis model call (-> structured appraisal report)
  parsing.py        - LLM output normalization + JSON extraction
  ui_components.py  - on-screen structured report rendering
  pdf_report.py     - PDF report generation (reportlab)
  email_utils.py    - SMTP email delivery of the PDF
"""

import streamlit as st
from PIL import Image

from appraisal import generate_appraisal_report
from db import get_comps, init_db
from email_utils import send_email_with_pdf
from parsing import extract_json, extract_text
from pdf_report import build_pdf_report
from ui_components import render_appraisal_report, render_visual_report
from vision import analyze_property_image

# Page config
st.set_page_config(
    page_title="Commercial Property Vision & Valuation AI", layout="wide"
)

st.title("Commercial Property Valuation & Vision Assistant")
st.write(
    "Upload a property photo and specify criteria to get an AI-powered"
    " valuation recommendation based on market comps."
)

conn = init_db()

# --- Sidebar User Inputs ---
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

uploaded_file = st.sidebar.file_uploader(
    "Upload Property Photo", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  image = Image.open(uploaded_file)
  st.image(image, caption="Uploaded Property Photo", width="stretch")

# --- Run evaluation ---
if st.button("Evaluate Property Valuation"):
  if not uploaded_file:
    st.warning("Please upload a property photo first.")
  else:
    with st.spinner("Analyzing image features and querying database comps..."):
      # 1. Vision analysis
      visual_analysis = analyze_property_image(image)

      # 2. Market comps
      avg_psm, comp_count = get_comps(conn, region, property_type)
      estimated_valuation = avg_psm * gfa_sqm

      # 3. Appraisal synthesis
      final_report_content = generate_appraisal_report(
          property_type=property_type,
          region=region,
          gfa_sqm=gfa_sqm,
          visual_analysis=visual_analysis,
          avg_psm=avg_psm,
          estimated_valuation=estimated_valuation,
          comp_count=comp_count,
      )

      # Parse both reports once, up front, and persist to session_state so the
      # report survives the rerun triggered by the "Send Email" button below.
      try:
        visual_data = extract_json(visual_analysis)
        visual_raw = None
      except Exception:
        visual_data = None
        visual_raw = extract_text(visual_analysis)

      try:
        appraisal_data = extract_json(extract_text(final_report_content))
        appraisal_raw = None
      except Exception:
        appraisal_data = None
        appraisal_raw = extract_text(final_report_content)

      st.session_state["report_ready"] = True
      st.session_state["region"] = region
      st.session_state["property_type"] = property_type
      st.session_state["gfa_sqm"] = gfa_sqm
      st.session_state["visual_data"] = visual_data
      st.session_state["visual_raw"] = visual_raw
      st.session_state["estimated_valuation"] = estimated_valuation
      st.session_state["comp_count"] = comp_count
      st.session_state["appraisal_data"] = appraisal_data
      st.session_state["appraisal_raw"] = appraisal_raw

# --- Display Structured Results ---
# Reads from session_state so the report (and the email form below it) stays
# visible across reruns, e.g. when the "Send Report" button is clicked.
if st.session_state.get("report_ready"):
  st.subheader("Visual Analysis Report")
  if st.session_state["visual_data"] is not None:
    render_visual_report(st.session_state["visual_data"])
  else:
    st.warning("Could not parse the structured report. Displaying raw analysis:")
    st.write(st.session_state["visual_raw"])

  st.markdown("---")

  st.subheader("Market Comps Benchmark")
  st.metric(
      label="Estimated Valuation (Baseline)",
      value=f"SGD {st.session_state['estimated_valuation']:,.2f}",
      delta=f"Based on {st.session_state['comp_count']} historical market comparables",
  )

  st.markdown("---")

  st.subheader("Appraiser AI Recommendation")
  if st.session_state["appraisal_data"] is not None:
    render_appraisal_report(
        st.session_state["appraisal_data"], st.session_state["estimated_valuation"]
    )
  else:
    st.warning(
        "Could not parse the structured appraisal report. Displaying raw"
        " analysis:"
    )
    st.write(st.session_state["appraisal_raw"])

  # --- PDF export + email ---
  report_parsed_ok = (
      st.session_state["visual_data"] is not None
      and st.session_state["appraisal_data"] is not None
  )

  st.markdown("---")
  st.subheader("Export & Share Report")

  if not report_parsed_ok:
    st.info(
        "PDF export is unavailable because one or more sections could not be"
        " parsed into structured data. Re-run the evaluation to try again."
    )
  else:
    pdf_bytes = build_pdf_report(
        region=st.session_state["region"],
        property_type=st.session_state["property_type"],
        gfa_sqm=st.session_state["gfa_sqm"],
        visual_data=st.session_state["visual_data"],
        estimated_valuation=st.session_state["estimated_valuation"],
        comp_count=st.session_state["comp_count"],
        appraisal_data=st.session_state["appraisal_data"],
    )

    dl_col, email_col = st.columns([1, 2])

    with dl_col:
      st.download_button(
          "Download PDF",
          data=pdf_bytes,
          file_name="property_valuation_report.pdf",
          mime="application/pdf",
      )

    with email_col:
      with st.form("email_report_form"):
        recipient_email = st.text_input("Recipient email address")
        email_subject = st.text_input(
            "Subject",
            value=(
                f"Property Valuation Report — "
                f"{st.session_state['property_type']}, "
                f"{st.session_state['region']}"
            ),
        )
        send_clicked = st.form_submit_button("Send Report as PDF")

      if send_clicked:
        if not recipient_email or "@" not in recipient_email:
          st.error("Please enter a valid recipient email address.")
        else:
          try:
            with st.spinner("Sending email..."):
              send_email_with_pdf(
                  recipient=recipient_email,
                  subject=email_subject,
                  body=(
                      "Please find attached the AI-generated commercial"
                      " property valuation report.\n\nThis report is"
                      " AI-assisted and not a substitute for a physical"
                      " inspection or a licensed appraisal."
                  ),
                  pdf_bytes=pdf_bytes,
                  filename="property_valuation_report.pdf",
              )
            st.success(f"Report sent to {recipient_email}.")
          except Exception as exc:
            st.error(f"Failed to send email: {exc}")
