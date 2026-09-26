"""Shared configuration for the valuation app."""

# Note: this app never binds tools to the models below, so there is no
# automatic-function-calling (AFC) behavior to configure. Recent versions of
# langchain-google-genai (v4.x) also no longer accept a raw
# google.genai.types.GenerateContentConfig via a `generation_config` kwarg —
# use the flat constructor arguments (temperature, thinking_budget, etc.)
# documented on ChatGoogleGenerativeAI instead.

# from google.genai import types

# Disable automatic function calling warnings for the Gemini SDK.
# GEN_CONFIG = types.GenerateContentConfig(
#    automatic_function_calling=types.AutomaticFunctionCallingConfig(
#        disable=True
#    )
# )

VISION_MODEL = "gemini-3.5-flash"
SYNTHESIS_MODEL = "gemini-3.5-flash"
