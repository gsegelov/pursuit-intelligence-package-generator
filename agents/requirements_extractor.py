# agents/requirements_extractor.py
# Requirementsextractor agent - reads the full RFP and extracts every
# stated AND implied requirement into a structured register
# Recieves full RFP text + RFPMetadata summary. Returns List[Requirement]

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent

from models import Requirement

# Load API key from .env
load_dotenv()

# Point the OpenAI client at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

requirements_extractor = Agent(
    name="RequirementsExtractor",
    model="gemini-2.5-pro",
    tools=[],
    output_type=list[Requirement],
    instructions="""
You are a specialist in extracting requirements from complex RFP documents.

You will receive the full RFP text and a metadata summary.

Your job:
1. Read the entire RFP text carefully.
2. Extract EVERY stated requirement — anything the vendor must do, provide, or demonstrate.
3. Extract EVERY implied requirement — needs that are strongly suggested by context,
   client priorities, or evaluation criteria even if not explicitly stated.
4. For each requirement assign:
   - A unique req_id starting at REQ-001
   - The full requirement text
   - A type: technical / staffing / timeline / compliance / deliverable / commercial
   - A priority: HIGH / MEDIUM / LOW
   - implied: true if inferred, false if explicitly stated
   - The source section of the RFP where it originated

Be exhaustive. A missed requirement is a compliance gap.
Flag all implied requirements with implied: true.
""",
)