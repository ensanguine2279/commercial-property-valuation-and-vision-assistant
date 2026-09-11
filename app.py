import base64
from io import BytesIO
import os
import sqlite3
import pandas as pd
from PIL import Image
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

# Page config
st.set_page_config(
    page_title="Commercial Property Vision & Valuation AI", layout="wide"
)

st.title("Commercial Property Valuation & Vision Assistant")
st.write(
    "Upload a property photo and specify criteria to get an AI-powered"
    " valuation recommendation based on market comps."
)


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
      use_container_width=True,
  )

if st.button("Evaluate Property Valuation"):
  if not uploaded_file:
    st.warning("Please upload a property photo first.")
  else:
    with st.spinner("Analyzing image features and querying database comps..."):
      # 1. Analyze image with Vision Model
      vision_llm = ChatGoogleGenerativeAI(
          model="gemini-3.5-flash", temperature=0
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
                  " structural and visual condition assessment: rate its"
                  " apparent maintenance condition (Poor, Fair, Good,"
                  " Excellent), note its apparent building grade tier, and"
                  " identify exterior/interior features that could impact its"
                  " valuation."
              ),
          },
      ]

      vision_response = vision_llm.invoke([HumanMessage(content=image_prompt)])
      visual_analysis = vision_response.content

      # 2. Query Database for comparable properties using SQLite
      query = f"""
                SELECT AVG(PricePerSqmSGD) as avg_psm, AVG(CapRatePct) as avg_cap, COUNT(*) as comp_count
                FROM valuations 
                WHERE Region = '{region}' AND PropertyType = '{property_type}'
            """
      comp_df = pd.read_sql(query, conn)

      avg_psm = (
          comp_df["avg_psm"].iloc[0] if not comp_df.empty else 2000.0
      )
      estimated_valuation = avg_psm * gfa_sqm
      comp_count = comp_df["comp_count"].iloc[0] if not comp_df.empty else 0

      # 3. Synthesize recommendation via LLM
      synthesizer = ChatGoogleGenerativeAI(
          model="gemini-3.5-flash", temperature=0.2
      )
      synthesis_prompt = f"""
            You are a senior commercial real estate appraiser. 
            Synthesize a valuation recommendation based on the following data:
            - Property Type: {property_type}
            - Region: {region}
            - Gross Floor Area (GFA): {gfa_sqm} sqm
            - Visual Condition Analysis from Photo: {visual_analysis}
            - Market Benchmark: Average Price per Sqm for similar properties is SGD {avg_psm:,.2f}
            - Calculated Baseline Valuation (GFA * Avg PSM): SGD {estimated_valuation:,.2f}

            Provide a professional valuation report summary, adjusting the baseline valuation slightly if the visual condition warrants a premium or discount, and explain your rationale.
            """
      final_report = synthesizer.invoke(synthesis_prompt)

      # Display Results
      st.subheader("Visual Analysis Report")
      st.write(visual_analysis)

      st.subheader("Market Comps Benchmark")
      st.metric(
          label="Estimated Valuation (Baseline)",
          value=f"SGD {estimated_valuation:,.2f}",
          delta=f"Based on {comp_count} historical market comparables",
      )

      st.subheader("Appraiser AI Recommendation")
      st.markdown(final_report.content)