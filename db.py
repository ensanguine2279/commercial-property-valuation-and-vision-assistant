"""Comparable-property database: load from CSV and query for averages."""

import sqlite3

import pandas as pd
import streamlit as st

DEFAULT_AVG_PSM = 2000.0


@st.cache_resource
def init_db():
  """Load the comps CSV into a SQLite database once per session."""
  df = pd.read_csv("commercial_property_valuations.csv")
  conn = sqlite3.connect("properties.db", check_same_thread=False)
  df.to_sql("valuations", conn, if_exists="replace", index=False)
  return conn


def get_comps(conn, region: str, property_type: str) -> tuple[float, int]:
  """Return (avg_price_per_sqm, comp_count) for the given region/type.

  Falls back to DEFAULT_AVG_PSM when there are no matching comps (the
  average would otherwise come back as NULL/None from SQL).
  """
  query = """
            SELECT AVG(PricePerSqmSGD) as avg_psm, AVG(CapRatePct) as avg_cap, COUNT(*) as comp_count
            FROM valuations
            WHERE Region = ? AND PropertyType = ?
        """
  comp_df = pd.read_sql(query, conn, params=(region, property_type))

  avg_psm = (
      comp_df["avg_psm"].iloc[0]
      if not comp_df.empty and comp_df["avg_psm"].iloc[0] is not None
      else DEFAULT_AVG_PSM
  )
  comp_count = int(comp_df["comp_count"].iloc[0]) if not comp_df.empty else 0
  return avg_psm, comp_count
