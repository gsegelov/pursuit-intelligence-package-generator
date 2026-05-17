# models.py
# Pydantic data models for the Pursuit Intelligence Package Generator
# These are the data contracts between all agents in the pipeline
# Build and verify this file before writing any agent

from pydantic import BaseModel
from typing import List

class RFPMetadata(BaseModel):
    """Structured metadata extracted from the RFP document by RFPParser."""
    client_name: str                    # Name of the issuing organization
    contract_value: str                 # Stated value or "Not Specified"
    submission_deadline: str            # Submission due date
    contract_duration: str              # Length of the engagement
    evaluation_criteria: List[str]      # How responses will be scored
    submission_requirements: List[str]  # Format/process requirements
    industry_sector: str                # Client's industry
    project_scope_summary: str          # 2-3 sentence summary of what is being procured

class Requirement(BaseModel):
    """A single extracted requirement from the RFP, stated or implied."""
    req_id: str             # Unique identifier e.g."REQ-001"
    text: str               # Full requirement text
    req_type: str           # "technical" / "staffing" / "timeline" / "compliance" / "deliverable" / "commercial"
    priority: str           # "HIGH" / "MEDIUM" / "LOW"
    implied: bool           # True if inferred rather than explicitly stated
    source_section: str     # RFP section where this requirement originated

class ClientSnapshot(BaseModel):
    """Web-researched intelligence on the RFP-issuing organization."""
    organization_name: str              # Full legal name
    industry: str                       # Industry sector
    headquarters: str                   # HQ location
    business_description: str           # What the organization does
    strategic_priorities: List[str]     # Current stated priorities from research
    recent_news: List[str]              # Significant news items from the last 6 months
    known_technology_stack: List[str]   # Known systems / platforms in use
    key_leadership: List[str]           # Relevant executives with titles
    known_pain_points: List[str]        # Inferred or stated operational challenges

class WinTheme(BaseModel):
    """A strategic angle for differentiating the proposal response"""
    theme_title: str            # Short, specific title - not generic
    rationale: str              # Why this angle resonates for this specific client
    supporting_evidence: str    # Specific data points from client research that grounds it
    recommended_emphasis: str   # How to weave this theme into the response

class ResponseSection(BaseModel):
    """A single section in the proposed response outline"""
    section_number: int                 # Order in the response
    section_title: str                  # Section heading
    purpose: str                        # What this section must accomplish
    recommended_angle: str              # How to frame it given win themes
    requirements_addressed: List[str]   # req_ids covered by this section
    win_themes_applied: List[str]       # Theme titles expressed in this section
    estimated_pages: str                # e.g. "2-3 pages"

class ComplianceRow(BaseModel):
    """A single row in the compliance matrix - maps one requirement to a response section"""
    req_id: str                 # From the requirements register
    requirement_text: str       # Full requirement text
    addressed_in_section: str   # Section number/title, or "—" if gap
    coverage_status: str        # "COVERED" / "PARTIAL" / "GAP"
    notes: str                  # Explanation for PARTIAL or GAP status

class PursuitIntelligencePackage(BaseModel):
    """The complete output of the pipeline — all agents' work assembled into one package"""
    rfp_metadata: RFPMetadata                   # Parsed RFP metadata
    requirements: List[Requirement]             # Full requirements register
    client_snapshot: ClientSnapshot             # Web-researched client intel
    win_themes: List[WinTheme]                  # Strategic angles
    response_outline: List[ResponseSection]     # Section-by-section structure
    compliance_matrix: List[ComplianceRow]      # Full compliance mapping
    gap_count: int                              # Number of GAP flags
    partial_count: int                          # Number of PARTIAL flags
    covered_count: int                          # Number of COVERED Requirements
    generated_at: str                           # Timestamp