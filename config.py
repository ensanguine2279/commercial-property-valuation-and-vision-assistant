"""Shared configuration for the valuation app."""

from google.genai import types

# Disable automatic function calling warnings for the Gemini SDK.
GEN_CONFIG = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    )
)

VISION_MODEL = "gemini-3.5-flash"
SYNTHESIS_MODEL = "gemini-3.5-flash"
