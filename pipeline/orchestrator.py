# pipeline/orchestrator.py
# PursuitOrchestrator - coordinates the full pipeline.
# Calls each worker agent in sequence, passes outputs forward,
# and assembles the final PursuitIntelligencePackage.

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, set_default_openai_api
from datetime import datetime
import json
from pydantic import ValidationError

from pipeline.rfp_parser import rfp_parser
from pipeline.requirements_extractor import requirements_extractor
from pipeline.client_researcher import client_researcher
from pipeline.win_theme_strategist import win_theme_strategist
from pipeline.response_architect import response_architect

from models import (
    PursuitIntelligencePackage, RFPMetadata, Requirement,
    ClientSnapshot, WinTheme, ResponseArchitectOutput
)

# Load API key from .env
load_dotenv()

# Point the AsyncOpenAI client at Google's Gemini endpoint
client = AsyncOpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Tell the Agents SDK to use our Gemini-configured client
set_default_openai_client(client)

# Force Chat Completions API — Gemini doesn't support the Responses API
set_default_openai_api("chat_completions")

# Disable tracing — we don't have an OpenAI key for the trace exporter
set_tracing_disabled(True)


async def run_pipeline(pdf_path: str) -> PursuitIntelligencePackage:
    """
    Run the full pursuit intelligence pipeline.
    Accepts a PDF file path, returns a complete PursuitIntelligencePackage.
    """

    def strip_fences(raw: str):
        """Strip markdown fences and parse JSON."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        # Unwrap single-key envelope e.g. {"RFPMetadata": {...}}
        if isinstance(data, dict) and len(data) == 1:
            key = list(data.keys())[0]
            inner = data[key]
            if isinstance(inner, (dict, list)):
                data = inner
        return data

    def parse_metadata(raw: str) -> RFPMetadata:
        """Parse raw agent output into RFPMetadata."""
        data = strip_fences(raw)
        for alt, canonical in [
            ("issuing_organization", "client_name"),
            ("organization_name", "client_name"),
            ("agency", "client_name"),
            ("industry", "industry_sector"),
            ("sector", "industry_sector"),
            ("deadline", "submission_deadline"),
            ("due_date", "submission_deadline"),
            ("duration", "contract_duration"),
            ("scope", "project_scope_summary"),
            ("scope_summary", "project_scope_summary"),
        ]:
            if alt in data and canonical not in data:
                data[canonical] = data.pop(alt)
        # Ensure list fields are actually lists
        for field in ["evaluation_criteria", "submission_requirements"]:
            if field in data and isinstance(data[field], str):
                data[field] = [data[field]]
            if field not in data:
                data[field] = []
        return RFPMetadata.model_validate(data)

    def parse_client_snapshot(raw: str) -> ClientSnapshot:
        """Parse raw agent output into ClientSnapshot."""
        data = strip_fences(raw)
        for alt, canonical in [
            ("client_name", "organization_name"),
            ("name", "organization_name"),
            ("company_name", "organization_name"),
            ("industry_sector", "industry"),
            ("hq_location", "headquarters"),
            ("location", "headquarters"),
            ("hq", "headquarters"),
            ("description", "business_description"),
            ("about", "business_description"),
            ("priorities", "strategic_priorities"),
            ("news", "recent_news"),
            ("technology_stack", "known_technology_stack"),
            ("tech_stack", "known_technology_stack"),
            ("technologies", "known_technology_stack"),
            ("leadership", "key_leadership"),
            ("executives", "key_leadership"),
            ("pain_points", "known_pain_points"),
            ("challenges", "known_pain_points"),
        ]:
            if alt in data and canonical not in data:
                data[canonical] = data.pop(alt)
        # Ensure list fields are actually lists
        for field in ["strategic_priorities", "recent_news", "known_technology_stack",
                      "key_leadership", "known_pain_points"]:
            if field in data and isinstance(data[field], str):
                data[field] = [data[field]]
            if field not in data:
                data[field] = []
        return ClientSnapshot.model_validate(data)

    def parse_list(model_class, raw: str):
        """Parse raw agent output into a list of Pydantic models."""
        data = strip_fences(raw)
        # Unwrap if agent returned {"requirements": [...]}
        if isinstance(data, dict):
            data = list(data.values())[0]
        remapped = []
        for item in data:
            # Requirement remapping
            if "requirement" in item and "text" not in item:
                item["text"] = item.pop("requirement")
            if "type" in item and "req_type" not in item:
                item["req_type"] = item.pop("type")
            # WinTheme remapping
            if "title" in item and "theme_title" not in item:
                item["theme_title"] = item.pop("title")
            if "emphasis" in item and "recommended_emphasis" not in item:
                item["recommended_emphasis"] = item.pop("emphasis")
            if "recommendation" in item and "recommended_emphasis" not in item:
                item["recommended_emphasis"] = item.pop("recommendation")
            if "how_to_emphasize" in item and "recommended_emphasis" not in item:
                item["recommended_emphasis"] = item.pop("how_to_emphasize")
            if "evidence" in item and "supporting_evidence" not in item:
                item["supporting_evidence"] = item.pop("evidence")
            # Convert supporting_evidence to string if it came back as a list
            if "supporting_evidence" in item and isinstance(item["supporting_evidence"], list):
                item["supporting_evidence"] = " ".join(item["supporting_evidence"])
            # ResponseSection remapping
            if "section" in item and "section_title" not in item:
                item["section_title"] = item.pop("section")
            remapped.append(item)
        return [model_class.model_validate(item) for item in remapped]

    def parse_architect(raw: str) -> ResponseArchitectOutput:
        """Parse raw agent output into ResponseArchitectOutput."""
        data = strip_fences(raw)
        # Remap response_outline field name variations
        if "response_outline" in data:
            for section in data["response_outline"]:
                if "section_id" in section and "section_number" not in section:
                    section["section_number"] = int(float(section.pop("section_id")))
                if "number" in section and "section_number" not in section:
                    section["section_number"] = int(section.pop("number"))
                if "estimated_page_count" in section and "estimated_pages" not in section:
                    count = section.pop("estimated_page_count")
                    section["estimated_pages"] = f"{count} pages"
                if "pages" in section and "estimated_pages" not in section:
                    section["estimated_pages"] = str(section.pop("pages"))
                if "page_count" in section and "estimated_pages" not in section:
                    section["estimated_pages"] = f"{section.pop('page_count')} pages"
                # Ensure list fields exist
                for field in ["requirements_addressed", "win_themes_applied"]:
                    if field not in section:
                        section[field] = []
        # Remap compliance_matrix field name variations
        if "compliance_matrix" in data:
            for row in data["compliance_matrix"]:
                if "text" in row and "requirement_text" not in row:
                    row["requirement_text"] = row.pop("text")
                if "requirement" in row and "requirement_text" not in row:
                    row["requirement_text"] = row.pop("requirement")
                if "section" in row and "addressed_in_section" not in row:
                    row["addressed_in_section"] = row.pop("section")
                if "section_reference" in row and "addressed_in_section" not in row:
                    row["addressed_in_section"] = row.pop("section_reference")
                if "section_id" in row and "addressed_in_section" not in row:
                    row["addressed_in_section"] = row.pop("section_id")
                if "status" in row and "coverage_status" not in row:
                    row["coverage_status"] = row.pop("status")
                # Ensure notes field exists
                if "notes" not in row:
                    row["notes"] = ""
                # Ensure addressed_in_section exists
                if "addressed_in_section" not in row:
                    row["addressed_in_section"] = "—"
        return ResponseArchitectOutput.model_validate(data)

    # Step 1 — Parse the RFP and extract metadata
    print("Step 1/5 — Parsing RFP...")
    metadata_result = await Runner.run(rfp_parser, pdf_path)
    metadata = parse_metadata(metadata_result.final_output)

    # Step 2 — Extract all requirements from the full RFP text
    print("Step 2/5 — Extracting requirements...")
    requirements_input = f"RFP File: {pdf_path}\nClient: {metadata.client_name}\nScope: {metadata.project_scope_summary}"
    requirements_result = await Runner.run(requirements_extractor, requirements_input)
    requirements = parse_list(Requirement, requirements_result.final_output)

    # Step 3 — Research the client organization
    print("Step 3/5 — Researching client...")
    research_input = f"Client: {metadata.client_name}\nIndustry: {metadata.industry_sector}"
    research_result = await Runner.run(client_researcher, research_input)
    client_snapshot = parse_client_snapshot(research_result.final_output)

    # Step 4 — Generate win themes from client intel and evaluation criteria
    print("Step 4/5 — Generating win themes...")
    strategy_input = f"Client Snapshot: {client_snapshot.model_dump_json()}\nEvaluation Criteria: {metadata.evaluation_criteria}"
    strategy_result = await Runner.run(win_theme_strategist, strategy_input)
    win_themes = parse_list(WinTheme, strategy_result.final_output)

    # Step 5 — Design response structure and build compliance matrix
    print("Step 5/5 — Designing response structure...")
    architect_input = f"Requirements: {[r.model_dump_json() for r in requirements]}\nWin Themes: {[t.model_dump_json() for t in win_themes]}\nMetadata: {metadata.model_dump_json()}"
    architect_result = await Runner.run(response_architect, architect_input)
    architect_output = parse_architect(architect_result.final_output)

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