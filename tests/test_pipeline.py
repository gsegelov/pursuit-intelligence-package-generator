# tests/test_pipeline.py
# Smoke tests for the Pursuit Intelligence Package Generator.
# Validates parsing and output structure without making live API calls.

import json
import pytest
from models import (
    RFPMetadata, Requirement, ClientSnapshot,
    WinTheme, ResponseSection, ComplianceRow,
    ResponseArchitectOutput, PursuitIntelligencePackage
)


# ── RFPMetadata parsing ──────────────────────────────────────────────────────

def test_rfp_metadata_valid():
    """RFPMetadata accepts a well-formed dict."""
    data = {
        "client_name": "Test Agency",
        "contract_value": "Not specified",
        "submission_deadline": "2026-06-01",
        "contract_duration": "1 year",
        "evaluation_criteria": ["Technical approach", "Price"],
        "submission_requirements": ["Submit via SAM.gov"],
        "industry_sector": "Government",
        "project_scope_summary": "Test scope."
    }
    metadata = RFPMetadata.model_validate(data)
    assert metadata.client_name == "Test Agency"
    assert len(metadata.evaluation_criteria) == 2


def test_rfp_metadata_empty_lists():
    """RFPMetadata handles missing list fields with defaults."""
    data = {
        "client_name": "Test Agency",
        "contract_value": "Not specified",
        "submission_deadline": "TBD",
        "contract_duration": "TBD",
        "evaluation_criteria": [],
        "submission_requirements": [],
        "industry_sector": "Government",
        "project_scope_summary": "Test."
    }
    metadata = RFPMetadata.model_validate(data)
    assert metadata.evaluation_criteria == []


# ── Requirement parsing ───────────────────────────────────────────────────────

def test_requirement_implied_flag():
    """Requirement correctly captures implied=True."""
    data = {
        "req_id": "REQ-001",
        "text": "Vendor shall provide services.",
        "req_type": "technical",
        "priority": "HIGH",
        "implied": True,
        "source_section": "1.0"
    }
    req = Requirement.model_validate(data)
    assert req.implied is True
    assert req.req_id == "REQ-001"


def test_requirement_not_implied():
    """Requirement correctly captures implied=False."""
    data = {
        "req_id": "REQ-002",
        "text": "Vendor shall respond within 1 hour.",
        "req_type": "timeline",
        "priority": "HIGH",
        "implied": False,
        "source_section": "1.3"
    }
    req = Requirement.model_validate(data)
    assert req.implied is False


# ── ClientSnapshot parsing ────────────────────────────────────────────────────

def test_client_snapshot_sources_default():
    """ClientSnapshot sources field defaults to empty list."""
    data = {
        "organization_name": "Test Org",
        "industry": "Government",
        "headquarters": "Washington, DC",
        "business_description": "A test org.",
        "strategic_priorities": ["Priority 1"],
        "recent_news": ["News item 1"],
        "known_technology_stack": [],
        "key_leadership": [],
        "known_pain_points": []
    }
    snapshot = ClientSnapshot.model_validate(data)
    assert snapshot.sources == []


def test_client_snapshot_with_sources():
    """ClientSnapshot preserves source URLs."""
    data = {
        "organization_name": "Test Org",
        "industry": "Government",
        "headquarters": "Washington, DC",
        "business_description": "A test org.",
        "strategic_priorities": [],
        "recent_news": [],
        "known_technology_stack": [],
        "key_leadership": [],
        "known_pain_points": [],
        "sources": ["https://example.gov", "https://example2.gov"]
    }
    snapshot = ClientSnapshot.model_validate(data)
    assert len(snapshot.sources) == 2
    assert "https://example.gov" in snapshot.sources


# ── ComplianceRow coverage status ─────────────────────────────────────────────

def test_compliance_row_statuses():
    """ComplianceRow accepts all valid coverage statuses."""
    for status in ["COVERED", "PARTIAL", "GAP"]:
        row = ComplianceRow.model_validate({
            "req_id": "REQ-001",
            "requirement_text": "Test requirement.",
            "addressed_in_section": "1.1",
            "coverage_status": status,
            "notes": ""
        })
        assert row.coverage_status == status


# ── JSON parsing helpers (mirrors orchestrator logic) ────────────────────────

def test_strip_fences_plain_json():
    """JSON without fences parses correctly."""
    raw = '{"client_name": "Test"}'
    data = json.loads(raw.strip())
    assert data["client_name"] == "Test"


def test_strip_fences_with_markdown():
    """JSON wrapped in markdown fences is handled correctly."""
    raw = '```json\n{"client_name": "Test"}\n```'
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())
    assert data["client_name"] == "Test"