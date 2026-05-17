# agents/orchestrator.py
# PursuitOrchestrator - coordinates the full pipeline.
# Calls each worker agent in sequence, passes outputs forward,
# and assembles the final PursuitIntelligencePackage.

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, Runner
from datetime import datetime

from agents.rfp_parser import rfp_parser
from agents.requirements_extractor import requirements_extractor
from agents.client_researcher import client_researcher
from agents.win_theme_strategist import win_theme_strategist
from agents.response_architect import response_architect
from models import PursuitIntelligencePackage

# Load API key from .env
load_dotenv()

# Point the OpenAI client at Google's Gemini endpoint
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

async def run_pipeline(pdf_path: str) -> PursuitIntelligencePackage:
    """
    Run the full pursuit intelligence pipeline.
    Accepts a PDF file path, returns a complete PursuitIntelligencePackage.
    """

    # Step 1 - Parse the RFP and extract metadata
    print("Step 1/5 - Parsing RFP...")
    metadata_result = await Runner.run(rfp_parser, pdf_path)
    metadata = metadata_result.final_output
    
    # Step 2 - Extract all requirements from the full RFP text
    print("Step 2/5 - Extracting requirements...")
    requirements_input = f"RFP File: {pdf_path}\nClient: {metadata.client_name}\nScope: {metadata.project_scope_summary}"
    requirements_result = await Runner.run(requirements_extractor, requirements_input)
    requirements = requirements_result.final_output

    # Step 3 — Research the client organization
    print("Step 3/5 — Researching client...")
    research_input = f"Client: {metadata.client_name}\nIndustry: {metadata.industry_sector}"
    research_result = await Runner.run(client_researcher, research_input)
    client_snapshot = research_result.final_output

    # Step 4 — Generate win themes from client intel and evaluation criteria
    print("Step 4/5 — Generating win themes...")
    strategy_input = f"Client Snapshot: {client_snapshot.model_dump_json()}\nEvaluation Criteria: {metadata.evaluation_criteria}"
    strategy_result = await Runner.run(win_theme_strategist, strategy_input)
    win_themes = strategy_result.final_output

    # Step 5 — Design response structure and build compliance matrix
    print("Step 5/5 — Designing response structure...")
    architect_input = f"Requirements: {[r.model_dump_json() for r in requirements]}\nWin Themes: {[t.model_dump_json() for t in win_themes]}\nMetadata: {metadata.model_dump_json()}"
    architect_result = await Runner.run(response_architect, architect_input)
    architect_output = architect_result.final_output

    # Count compliance statuses
    gap_count = sum(1 for row in architect_output.compliance_matrix if row.coverage_status == "GAP")
    partial_count = sum(1 for row in architect_output.compliance_matrix if row.coverage_status == "PARTIAL")
    covered_count = sum(1 for row in architect_output.compliance_matrix if row.coverage_status == "COVERED")

    # Assemble and return the final package
    return PursuitIntelligencePackage(
        rfp_metadata=metadata,
        requirements=requirements,
        client_snapshot=client_snapshot,
        win_themes=win_themes,
        response_outline=architect_output.response_outline,
        compliance_matrix=architect_output.compliance_matrix,
        gap_count=gap_count,
        partial_count=partial_count,
        covered_count=covered_count,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )