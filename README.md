# Commercial Property Valuation and Vision Asistant

This repo aims to prototype a web application that evaluates commercial properties using both conventional structured data in CSV and uploaded user photos (unstructured). The prototyped is implemented as a lightweight Streamlit app powered by a multimodal Gemini3.5 model.

The application architecture involves three main steps:

1. **Visual Analysis**: The user upload photos of the property and inputs basic filters (e.g., region, property type). A multimodal model evaluates the photo to score its condition and exterior quality.

2. **Data Lookup & Hybrid Matching**: The app queries the local SQLite database (populated from the CSV) to find comparable properties based on matching filters and the AI-derived condition score.

3. **Valuation Recommendation**: The LLM synthesizes the visual assessment and database comparables to output a recommended valuation range with supporting rationale.

## Deploy on Streamlit Community Cloud

1. Create an account with [Streamlit Community Cloud](https://streamlit.io/cloud).

2. Login and click on the `Create app` button.

![Streamlit - Create app](./assets/images/streamlit-create-app.png)

3. Select deploy from [GitHub](https://github.com/ensanguine2279/commercial-property-valuation-and-vision-assistant/).

![Streamlit - Deploy from GitHub](./assets/images/streamlit-github.png)

4. Link the [GitHub repo](https://github.com/ensanguine2279/commercial-property-valuation-and-vision-assistant/) to the app.

![Streamlit - Deployment Settings](./assets/images/streamlit-deploy.png)

5. Click in `Advanced Settings` to enter the Google API key. Click `Save` button.

![Streamlit - Advanced Settings](./assets/images/streamlit-advanced-settings.png)

6. Click the `Deploy` button.


## Running locally

Ensure you have your Google API key configured (`export GOOGLE_API_KEY="your-api-key"`).

Run the prototype locally using `uv`:

```bash
uv run streamlit run app.py
```
