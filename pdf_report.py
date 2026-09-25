"""PDF rendering of the valuation report, mirroring the on-screen layout."""

import html
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _build_styles():
  base_styles = getSampleStyleSheet()
  return {
      "title": ParagraphStyle(
          "ReportTitle", parent=base_styles["Title"], fontSize=18, spaceAfter=4
      ),
      "subtitle": ParagraphStyle(
          "ReportSubtitle",
          parent=base_styles["Normal"],
          textColor=colors.HexColor("#64748b"),
          fontSize=10,
          spaceAfter=18,
      ),
      "heading": ParagraphStyle(
          "SectionHeading",
          parent=base_styles["Heading2"],
          fontSize=13,
          textColor=colors.HexColor("#0f172a"),
          spaceBefore=14,
          spaceAfter=8,
      ),
      "label": ParagraphStyle(
          "Label",
          parent=base_styles["Normal"],
          fontSize=9,
          textColor=colors.HexColor("#64748b"),
      ),
      "body": ParagraphStyle(
          "Body",
          parent=base_styles["Normal"],
          fontSize=10.5,
          leading=15,
          alignment=TA_LEFT,
      ),
      "value": ParagraphStyle(
          "BigValue",
          parent=base_styles["Normal"],
          fontSize=22,
          textColor=colors.HexColor("#0f172a"),
          spaceAfter=4,
      ),
  }


def build_pdf_report(
    region: str,
    property_type: str,
    gfa_sqm: float,
    visual_data: dict,
    estimated_valuation: float,
    comp_count: int,
    appraisal_data: dict,
) -> bytes:
  """Render the same report content shown on-screen as a downloadable PDF."""
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=A4,
      topMargin=2 * cm,
      bottomMargin=2 * cm,
      leftMargin=2 * cm,
      rightMargin=2 * cm,
      title="Commercial Property Valuation Report",
  )

  s = _build_styles()
  story = []

  # --- Header ---
  story.append(Paragraph("Commercial Property Valuation Report", s["title"]))
  story.append(
      Paragraph(
          "AI-assisted valuation based on visual condition analysis and"
          " market comparables. Not a substitute for a physical inspection.",
          s["subtitle"],
      )
  )

  # --- Property parameters ---
  param_table = Table(
      [
          ["Region", region],
          ["Property Type", property_type],
          ["Gross Floor Area", f"{gfa_sqm:,.0f} sqm"],
          ["Comparable Transactions Used", str(comp_count)],
      ],
      colWidths=[6 * cm, 10 * cm],
  )
  param_table.setStyle(
      TableStyle([
          ("FONTSIZE", (0, 0), (-1, -1), 10),
          ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
          ("TOPPADDING", (0, 0), (-1, -1), 6),
          ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
      ])
  )
  story.append(param_table)

  # --- Visual analysis ---
  story.append(Paragraph("Visual Analysis Report", s["heading"]))
  story.append(
      Paragraph(
          f"<b>Maintenance Condition:</b> "
          f"{html.escape(str(visual_data.get('maintenance_condition', 'N/A')))}"
          f" &nbsp;&nbsp; <b>Building Grade:</b> "
          f"{html.escape(str(visual_data.get('building_grade_tier', 'N/A')))}",
          s["body"],
      )
  )
  story.append(Spacer(1, 6))

  features = visual_data.get("key_features", [])
  if features:
    story.append(Paragraph("Key Architectural &amp; Feature Observations:", s["label"]))
    story.append(
        ListFlowable(
            [ListItem(Paragraph(html.escape(str(f)), s["body"])) for f in features],
            bulletType="bullet",
            leftIndent=14,
        )
    )
    story.append(Spacer(1, 6))

  story.append(
      Paragraph(
          f"<b>Valuation Impact:</b> "
          f"{html.escape(str(visual_data.get('valuation_impact', 'N/A')))}",
          s["body"],
      )
  )

  # --- Market comps benchmark ---
  story.append(Paragraph("Market Comps Benchmark", s["heading"]))
  story.append(Paragraph(f"SGD {estimated_valuation:,.2f}", s["value"]))
  story.append(
      Paragraph(
          f"Estimated Valuation (Baseline) — based on {comp_count} historical"
          " market comparables matching the selected region and property"
          " type.",
          s["body"],
      )
  )

  # --- Appraiser recommendation ---
  story.append(Paragraph("Appraiser AI Recommendation", s["heading"]))

  final_value = appraisal_data.get("final_value_opinion", estimated_valuation)
  try:
    final_value = float(final_value)
  except (TypeError, ValueError):
    final_value = estimated_valuation
  delta = final_value - estimated_valuation

  story.append(Paragraph(f"SGD {final_value:,.2f}", s["value"]))
  story.append(
      Paragraph(
          f"Final Value Opinion &nbsp;•&nbsp; Adjustment from baseline: "
          f"{'+' if delta >= 0 else ''}SGD {delta:,.2f}",
          s["label"],
      )
  )
  story.append(Spacer(1, 8))

  story.append(Paragraph("Executive Summary", s["label"]))
  story.append(
      Paragraph(
          html.escape(str(appraisal_data.get("executive_summary", "N/A"))),
          s["body"],
      )
  )
  story.append(Spacer(1, 6))

  story.append(Paragraph("Valuation Approach", s["label"]))
  story.append(
      Paragraph(
          html.escape(str(appraisal_data.get("valuation_approach", "N/A"))),
          s["body"],
      )
  )
  story.append(Spacer(1, 6))

  story.append(Paragraph("Market Analysis", s["label"]))
  story.append(
      Paragraph(
          html.escape(str(appraisal_data.get("market_analysis", "N/A"))),
          s["body"],
      )
  )
  story.append(Spacer(1, 6))

  adj = appraisal_data.get("condition_adjustment", {}) or {}
  story.append(Paragraph("Condition Adjustment Rationale", s["label"]))
  story.append(
      Paragraph(
          f"{html.escape(str(adj.get('direction', 'none')).title())} of "
          f"{adj.get('percentage', 0)}% — "
          f"{html.escape(str(adj.get('rationale', 'N/A')))}",
          s["body"],
      )
  )
  story.append(Spacer(1, 6))

  story.append(Paragraph("Appraiser Notes &amp; Limitations", s["label"]))
  story.append(
      Paragraph(
          html.escape(str(appraisal_data.get("confidence_notes", "N/A"))),
          s["body"],
      )
  )

  doc.build(story)
  buffer.seek(0)
  return buffer.getvalue()
