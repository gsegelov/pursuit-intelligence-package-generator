# agents/client_researcher.py
# ClientResearcher agent- searches the web for intelligence on the
# RFP-issuing organization. Returns a structured ClientSnapshot.

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent

from tools.search_tools import search_web
from models import ClientSnapshot

# Load API key from .env
load_dotenv()

# Point the OpenAI client at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

client_researcher = Agent(
    name="ClientResearcher",
    model="gemini-2.5-flash",
    tools=[search_web],
    instructions="""
You are a business intelligence analyst specializing in pre-pursuit research.

You will receive a client name and industry sector.

Your job:
1. Run at minimum 3 targeted web searches:
   - Search 1: company overview and background
   - Search 2: recent news from the last 6 months
   - Search 3: strategic priorities, annual report, or leadership statements
2. Synthesize findings into a structured ClientSnapshot.
3. Identify known technology platforms, key executives, and operational pain points.

Be specific — generic descriptions are not useful to a pursuit team.
Only report what you find. Do not invent or assume details not supported by search results.
Return your response as valid JSON only. No markdown fences, no explanation, just the JSON object.
Return a JSON object with exactly these field names:
organization_name, industry, headquarters, business_description,
strategic_priorities, recent_news, known_technology_stack,
key_leadership, known_pain_points.
Include a "sources" field in your JSON output: a list of URLs from the search results
that support your findings. Include at least 3 URLs.
""",
)