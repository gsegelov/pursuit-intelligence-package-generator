# agents/response_architect.py
# ResponseArchitect agent- designs the complete response structure and
# builds the compliance matrix. The final worker in the pipeline.
# Recieves List[Requirement] +List[WinTheme] + RFP Metadata.
# Returns ResponseArchitectOutput (outline + compliance matrix)

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent

from models import ResponseSection, ComplianceRow, ResponseArchitectOutput

# Load API key from .env
load_dotenv()

# Point the OpenAI client at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response_architect = Agent(
    name="ResponseArchitect",
    model="gemini-2.5-pro",
    tools=[],
    instructions="""
You are a senior proposal architect specializing in structured RFP responses.

You will receive a requirements register, win themes, and RFP metadata.

Your job:
1. Design a complete section-by-section response outline.
2. For each section define: purpose, recommended angle, requirements addressed,
   win themes applied, and estimated page count.
3. Build a compliance matrix mapping every requirement to a section.
4. Flag every unaddressed requirement as GAP.
5. Flag partially addressed requirements as PARTIAL with an explanation.

Compliance rule: every requirement must map to exactly one section or receive a GAP flag.
No requirement may be silently ignored.
COVERED / PARTIAL / GAP are the only valid coverage statuses.
Return your response as valid JSON only. No markdown fences, no explanation, just the JSON object.
""",
)