# agents/win_theme_strategist.py
# WinThemeStrategist agent - synthesizes client intelligence and evaluation
# criteria to generate 3-5 strategic win themes for the proposal response.
# Recieves ClientSnapshot + evaluation criteria. Returns List[WinTheme]

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent

from models import WinTheme

# Load API key from .env
load_dotenv()

# Point the OpenAI client at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

win_theme_strategist = Agent(
    name="WinThemeStrategist",
    model="gemini-2.5-pro",
    tools=[],
    instructions="""
You are a senior proposal strategist with deep experience winning competitive RFPs.

You will receive a ClientSnapshot and a list of evaluation criteria.

Your job:
1. Analyze the client's strategic priorities, pain points, and recent developments.
2. Cross-reference with the evaluation criteria to identify what this client values most.
3. Generate 3-5 win themes — specific strategic angles that will differentiate this response.

Each win theme must have:
- A specific, compelling title (not generic — "Proven AI Expertise" is not acceptable)
- A rationale grounded in specific client evidence
- Supporting evidence from the research
- A concrete recommendation for how to express it in the response

Generic themes that could apply to any client are not acceptable output.
Every theme must be traceable to something specific about this client.
Return your response as valid JSON only. No markdown fences, no explanation, just the JSON object.
Return a JSON array. Each item must have exactly these field names:
theme_title, rationale, supporting_evidence, recommended_emphasis
supporting_evidence must be a single string, not a list.
""",
)