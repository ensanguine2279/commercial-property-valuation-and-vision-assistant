"""Vision analysis of the uploaded property photo."""

import base64
from io import BytesIO

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image

from config import GEN_CONFIG, VISION_MODEL

VISION_PROMPT_TEXT = (
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
)


def analyze_property_image(image: Image.Image):
  """Send the uploaded photo to the vision model.

  Returns the raw `response.content` (str or list-of-parts) exactly as
  LangChain returns it; use parsing.extract_json/extract_text on the result.
  """
  vision_llm = ChatGoogleGenerativeAI(
      model=VISION_MODEL, temperature=0, generation_config=GEN_CONFIG
  )

  buffered = BytesIO()
  image.save(buffered, format="JPEG")
  img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
  image_url = f"data:image/jpeg;base64,{img_str}"

  image_prompt = [
      {"type": "image_url", "image_url": {"url": image_url}},
      {"type": "text", "text": VISION_PROMPT_TEXT},
  ]

  vision_response = vision_llm.invoke([HumanMessage(content=image_prompt)])
  return vision_response.content
