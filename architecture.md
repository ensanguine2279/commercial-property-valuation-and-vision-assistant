# System Architecture — Commercial Property Valuation & Vision Assistant

This diagram shows how the Streamlit app's modules interact with each other
and with the two external services: the Google Gemini API (LLM calls) and
an SMTP server (email delivery).

```mermaid
flowchart TD
    User(["User<br/>(Browser)"]) -->|"Uploads photo,<br/>sets parameters"| Sidebar

    subgraph App["app.py"]
        Sidebar["Sidebar inputs<br/>region, type, GFA, photo"]
        Button["Evaluate button"]
        Sidebar --> Button
    end

    subgraph Vision["vision.py"]
        VisionCall["analyze_property_image()<br/><i>uses config.VISION_MODEL</i>"]
    end

    subgraph DB["db.py"]
        Comps["init_db() / get_comps()<br/>SQLite loaded from CSV"]
    end

    subgraph Appraisal["appraisal.py"]
        SynthCall["generate_appraisal_report()<br/><i>uses config.SYNTHESIS_MODEL</i>"]
    end

    Gemini[("Google Gemini API")]

    subgraph Parsing["parsing.py"]
        Parse["extract_text()<br/>extract_json()"]
    end

    State["<b>app.py</b><br/>st.session_state<br/>(persisted report data)"]

    subgraph UI["ui_components.py"]
        Render["render_visual_report()<br/>render_appraisal_report()"]
    end

    subgraph PDF["pdf_report.py"]
        BuildPDF["build_pdf_report()<br/>(reportlab)"]
    end

    Display["<b>app.py</b><br/>Report display +<br/>Export / Email UI"]

    subgraph Email["email_utils.py"]
        SendEmail["send_email_with_pdf()<br/>(smtplib)"]
    end

    SMTP[("SMTP server<br/>e.g. Gmail")]
    Recipient(["Report recipient<br/>(email inbox)"])

    Button --> VisionCall
    Button --> Comps

    VisionCall ---|"photo + prompt"| Gemini
    Gemini ---|"raw JSON response"| VisionCall
    Comps -->|"avg price/sqm,<br/>comp count"| SynthCall
    VisionCall -->|"visual analysis"| SynthCall
    SynthCall ---|"prompt / raw JSON response"| Gemini

    VisionCall --> Parse
    SynthCall --> Parse
    Parse -->|"parsed dicts"| State

    State --> Render --> Display
    State --> BuildPDF -->|"PDF bytes"| Display

    Display -->|"recipient email +<br/>PDF bytes"| SendEmail
    SendEmail -->|"SMTP + STARTTLS"| SMTP -->|"delivers PDF attachment"| Recipient
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Streamlit UI flow: sidebar inputs, button handling, session-state persistence, orchestration of all other modules |
| `config.py` | Shared model name constants |
| `db.py` | Loads the comps CSV into SQLite once (`init_db`) and queries it (`get_comps`) |
| `vision.py` | Sends the uploaded photo + prompt to the Gemini vision model |
| `appraisal.py` | Sends the visual analysis + comps data to the Gemini synthesis model for the structured appraisal |
| `parsing.py` | Normalizes LLM response content and extracts the JSON object from it |
| `ui_components.py` | Renders the parsed JSON as styled HTML report cards in Streamlit |
| `pdf_report.py` | Renders the same report content as a downloadable PDF (reportlab) |
| `email_utils.py` | Sends the PDF as an email attachment over SMTP |

## Data flow summary

1. The user uploads a photo and sets region / property type / GFA in the sidebar, then clicks **Evaluate**.
2. `vision.py` sends the photo to Gemini and gets back a visual condition analysis.
3. `db.py` queries SQLite for comparable transactions and computes the baseline valuation.
4. `appraisal.py` sends the visual analysis + baseline data to Gemini, which returns a structured appraisal (executive summary, adjustment, final value opinion, etc.).
5. `parsing.py` extracts clean JSON from both Gemini responses; the parsed data is stored in `st.session_state` so it survives Streamlit's rerun cycle.
6. `ui_components.py` renders the stored data as on-screen report cards.
7. `pdf_report.py` renders the same data as a PDF, available for direct download.
8. If the user enters a recipient email, `email_utils.py` sends that PDF as an attachment via SMTP.
