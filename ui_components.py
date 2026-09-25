"""On-screen (HTML-in-Streamlit) rendering of the structured reports."""

import html

import streamlit as st

RATING_STYLES = {
    "Poor": ("#b91c1c", "#fee2e2"),
    "Fair": ("#b45309", "#fef3c7"),
    "Good": ("#15803d", "#dcfce7"),
    "Excellent": ("#0f766e", "#ccfbf1"),
}


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
