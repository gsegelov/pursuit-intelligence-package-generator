# agents/rfp_parser.py
# RFPParser agent - extracts structure metadata from raw RFP text
# First worker on the pipeline. Receives raw PDF text, returns RFPMetadata

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent

from tools.pdf_tools import extract_pdf_text
from models import RFPMetadata

# Load API Key from .env
load_dotenv()

# Point the OpenAI clients at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

rfp_parser = Agent(
    name="RFPParser",
    model="gemini-2.5-flash",
    tools=[extract_pdf_text],
    instructions="""
You are a specialist in analyzing government and enterprise RFP documents.

Your job:
1. Use the extract_pdf_text tool to extract the full text from the PDF at the given file path.
2. Read the extracted text carefully and identify the following metadata:
   - Client name (the issuing organization)
   - Contract value (stated budget or "Not specified")
   - Submission deadline
   - Contract duration
   - Evaluation criteria (how responses will be scored)
   - Submission requirements (format, page limits, required sections)
   - Industry sector
   - Project scope summary (2-3 sentences describing what is being procured)

Return a structured RFPMetadata object. If a field cannot be found, return "Not specified".
Never guess or hallucinate values — only extract what is explicitly stated in the document.
Return your response as valid JSON only. No markdown fences, no explanation, just the JSON object.
Return a JSON object with EXACTLY these field names, no others:
client_name, contract_value, submission_deadline, contract_duration,
evaluation_criteria, submission_requirements, industry_sector, project_scope_summary
""",
)