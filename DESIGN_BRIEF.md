# Design Brief
## RFP Intelligence Agent — Pursuit Intelligence Package Generator
**Version:** 1.0  
**Author:** Gila Eliach  
**Status:** Design Complete → Ready for Execution Playbook  
**Framework:** OpenAI Agents SDK + Gemini API  
**Pattern:** Deterministic Pipeline with Orchestrator

---

## 1. Problem Statement

Consulting pursuit teams at firms like Accenture, Deloitte, KPMG, and Capgemini spend
80–150 hours per RFP response on work that is largely extraction, research, and formatting —
leaving almost no time for the strategic differentiation that actually wins contracts. Junior
analysts spend days building requirements registers. Senior consultants spend hours on client
research that could be automated. Compliance gaps are caught late or not at all, costing firms
contracts worth millions.

**This system automates the intelligence layer so pursuit teams spend their hours on strategy,
not synthesis.**

---

## 2. System Output

**The Pursuit Intelligence Package** — a structured `.md` file and terminal summary containing:

1. Client Snapshot — web-researched intelligence on the issuing organization
2. Requirements Register — every stated and implied requirement, tagged and prioritized
3. Win Themes — 3–5 strategic angles derived from client intel and evaluation criteria
4. Response Outline — section-by-section structure with purpose, angle, and requirement mapping
5. Compliance Matrix — every requirement mapped to a response section, with GAP flags

**Sample output file** committed to repo at `sample_outputs/example_pursuit_package.md`

---

## 3. Constraints

| Constraint | Specification |
|---|---|
| Input | PDF file path provided via terminal or Gradio UI |
| Output | `pursuit_intelligence_package.md` written to project root + terminal summary |
| Runtime | End-to-end in under 5 minutes on a standard RFP document |
| Interface v1 | Terminal (`main.py`) |
| Interface v1.1 | Gradio on Hugging Face Spaces (`app.py`) |
| API | Gemini via OpenAI-compatible endpoint |
| Search | DuckDuckGo (no API key required) |
| PDF parsing | pypdf |
| No UI required | for core pipeline to function |

---

## 4. Architecture Decision

**Multi-agent.** Single agent cannot do this work cleanly because:
- Tasks require genuinely different skills (extraction ≠ research ≠ strategic synthesis ≠ compliance mapping)
- Sequential dependencies exist — win themes cannot be written before client research; compliance matrix cannot be built before requirements are extracted
- Different tasks justify different models (flash for retrieval, pro for reasoning)
- Clean specialization makes each agent independently testable

**Pattern: Deterministic Pipeline with Orchestrator.**  
Data flows in a fixed sequence regardless of input. No dynamic routing needed.
The orchestrator coordinates handoffs and assembles the final package.

---

## 5. Agent Specifications

### Agent 1 — PursuitOrchestrator
| Field | Value |
|---|---|
| File | `agents/orchestrator.py` |
| Role | Coordinates the full pipeline. Receives user input, calls workers in sequence, passes outputs forward, assembles and writes the final package. |
| Receives | PDF file path + optional context note from user |
| Returns | Complete `PursuitIntelligencePackage` |
| Model | `gemini-2.5-flash` |
| Why flash | Coordination and sequencing logic — not deep reasoning |
| Tools | None — delegates all work to specialist agents |
| HITL | None in v1 |

**Instructions summary:**  
Step 1 — call RFPParser with the PDF path to extract metadata and full text.  
Step 2 — call RequirementsExtractor with the full RFP text and metadata.  
Step 3 — call ClientResearcher with the client name from metadata.  
Step 4 — call WinThemeStrategist with client snapshot and evaluation criteria.  
Step 5 — call ResponseArchitect with requirements, win themes, and metadata.  
Step 6 — assemble PursuitIntelligencePackage and return it.

---

### Agent 2 — RFPParser
| Field | Value |
|---|---|
| File | `agents/rfp_parser.py` |
| Role | Extracts structured metadata from RFP text. Identifies client name, contract value, deadline, evaluation criteria, and submission requirements. |
| Receives | Raw text extracted from PDF (string) |
| Returns | `RFPMetadata` (Pydantic) |
| Model | `gemini-2.5-flash` |
| Why flash | Structured extraction — pattern recognition, not reasoning |
| Tools | `extract_pdf_text` |

---

### Agent 3 — RequirementsExtractor
| Field | Value |
|---|---|
| File | `agents/requirements_extractor.py` |
| Role | Reads the full RFP and extracts every stated AND implied requirement into a structured register. Tags each by type and priority. |
| Receives | Full RFP text + `RFPMetadata` summary |
| Returns | `List[Requirement]` (Pydantic) |
| Model | `gemini-2.5-pro` |
| Why pro | Implied requirements require nuanced reading — explicit is easy, implicit is the hard part |
| Tools | None |

**Critical instruction:** Distinguish between stated requirements ("The vendor shall provide...") and implied requirements ("The client's Q3 initiative suggests they will need..."). Flag all implied requirements with `implied: true`.

---

### Agent 4 — ClientResearcher
| Field | Value |
|---|---|
| File | `agents/client_researcher.py` |
| Role | Searches the web for intelligence on the RFP-issuing organization. Returns a structured snapshot of who they are, what they care about, and what's happening with them right now. |
| Receives | `client_name: str` + `industry_sector: str` from RFPMetadata |
| Returns | `ClientSnapshot` (Pydantic) |
| Model | `gemini-2.5-flash` |
| Why flash | Research and retrieval — the search tool does the work |
| Tools | `search_web` |

**Search strategy:** Run at minimum 3 searches — (1) company overview, (2) recent news last 6 months, (3) strategic priorities / annual report / leadership statements. Synthesize into structured snapshot.

---

### Agent 5 — WinThemeStrategist
| Field | Value |
|---|---|
| File | `agents/win_theme_strategist.py` |
| Role | Synthesizes client intelligence and evaluation criteria to generate 3–5 strategic win themes — the angles that will differentiate this response from competitors. |
| Receives | `ClientSnapshot` + `evaluation_criteria: List[str]` from RFPMetadata |
| Returns | `List[WinTheme]` (Pydantic) |
| Model | `gemini-2.5-pro` |
| Why pro | Highest-value output in the package. Pure strategic reasoning — no tools, just synthesis. |
| Tools | None |

**Output standard:** Each win theme must have a title, a rationale grounded in specific client evidence, and a concrete recommendation for how to express it in the response. Generic themes ("demonstrate expertise") are not acceptable output.

---

### Agent 6 — ResponseArchitect
| Field | Value |
|---|---|
| File | `agents/response_architect.py` |
| Role | Designs the complete response structure. Produces a section-by-section outline with purpose, recommended angle, and requirement mapping. Builds the compliance matrix and flags every gap. |
| Receives | `List[Requirement]` + `List[WinTheme]` + `RFPMetadata` |
| Returns | `ResponseOutline` containing `List[ResponseSection]` + `List[ComplianceRow]` |
| Model | `gemini-2.5-pro` |
| Why pro | Complex cross-referencing and judgment — every requirement must land somewhere or be flagged |
| Tools | None |

**Compliance rule:** Every requirement in the register must map to exactly one section or receive a GAP flag. PARTIAL is used when a requirement is addressed but not fully covered. No requirement may be silently ignored.

---

## 6. Tool Specifications

### Tool 1 — extract_pdf_text

```python
# File: tools/pdf_tools.py

from agents import function_tool
import pypdf

@function_tool
def extract_pdf_text(file_path: str) -> str:
    """
    Extract all text content from a PDF RFP document at the given file path.
    Use this once at the start of the pipeline, before any analysis begins.
    Returns the full text of the document as a single string.
    """
    reader = pypdf.PdfReader(file_path)
    return "\n\n".join(
        page.extract_text() for page in reader.pages
        if page.extract_text()
    )
```

**Owner:** RFPParser  
**When called:** Once, at the start of the pipeline  
**Error handling:** Wrap in try/except — if PDF cannot be read, return descriptive error string so orchestrator can surface it cleanly

---

### Tool 2 — search_web

```python
# File: tools/search_tools.py

from agents import function_tool
from duckduckgo_search import DDGS

@function_tool
def search_web(query: str) -> str:
    """
    Search the web for current information about a company, organization, or topic.
    Use this to research the RFP-issuing organization's background, recent news,
    strategic priorities, and technology context. Run multiple targeted queries
    for comprehensive coverage — one query per topic area.
    """
    results = DDGS().text(query, max_results=5)
    if not results:
        return f"No results found for: {query}"
    return "\n\n".join(
        f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r['body']}"
        for r in results
    )
```

**Owner:** ClientResearcher  
**When called:** 3+ times per pipeline run (once per search query)  
**Note:** No API key required. Import: `pip install duckduckgo-search`

---

## 7. Pydantic Model Specifications

```
File: models.py
Purpose: Data contracts between all agents. Create this file before any agent file.
```

### RFPMetadata
| Field | Type | Description |
|---|---|---|
| `client_name` | `str` | Name of the issuing organization |
| `contract_value` | `str` | Stated contract value or "Not specified" |
| `submission_deadline` | `str` | Submission due date |
| `contract_duration` | `str` | Duration of the engagement |
| `evaluation_criteria` | `List[str]` | How responses will be scored |
| `submission_requirements` | `List[str]` | Format/process requirements for submission |
| `industry_sector` | `str` | Client's industry |
| `project_scope_summary` | `str` | 2–3 sentence summary of what is being procured |

---

### Requirement
| Field | Type | Description |
|---|---|---|
| `req_id` | `str` | e.g. "REQ-001" |
| `text` | `str` | Full requirement text |
| `req_type` | `str` | "technical" / "staffing" / "timeline" / "compliance" / "deliverable" / "commercial" |
| `priority` | `str` | "HIGH" / "MEDIUM" / "LOW" |
| `implied` | `bool` | True if inferred rather than explicitly stated |
| `source_section` | `str` | RFP section where this requirement originated |

---

### ClientSnapshot
| Field | Type | Description |
|---|---|---|
| `organization_name` | `str` | Full legal name |
| `industry` | `str` | Industry sector |
| `headquarters` | `str` | HQ location |
| `business_description` | `str` | What the organization does |
| `strategic_priorities` | `List[str]` | Current stated priorities from research |
| `recent_news` | `List[str]` | Significant news items from last 6 months |
| `known_technology_stack` | `List[str]` | Known systems / platforms in use |
| `key_leadership` | `List[str]` | Relevant executives with titles |
| `known_pain_points` | `List[str]` | Inferred or stated operational challenges |

---

### WinTheme
| Field | Type | Description |
|---|---|---|
| `theme_title` | `str` | Short, specific title (not generic) |
| `rationale` | `str` | Why this angle resonates for this specific client |
| `supporting_evidence` | `str` | Specific data point from client research that grounds it |
| `recommended_emphasis` | `str` | How to weave this theme into the response |

---

### ResponseSection
| Field | Type | Description |
|---|---|---|
| `section_number` | `int` | Order in the response |
| `section_title` | `str` | Section heading |
| `purpose` | `str` | What this section must accomplish |
| `recommended_angle` | `str` | How to frame it given win themes |
| `requirements_addressed` | `List[str]` | req_ids covered by this section |
| `win_themes_applied` | `List[str]` | Theme titles expressed in this section |
| `estimated_pages` | `str` | e.g. "2–3 pages" |

---

### ComplianceRow
| Field | Type | Description |
|---|---|---|
| `req_id` | `str` | From requirements register |
| `requirement_text` | `str` | Full requirement text |
| `addressed_in_section` | `str` | Section number/title, or "—" if gap |
| `coverage_status` | `str` | "COVERED" / "PARTIAL" / "GAP" |
| `notes` | `str` | Explanation for PARTIAL or GAP status |

---

### PursuitIntelligencePackage ← final assembled output
| Field | Type | Description |
|---|---|---|
| `rfp_metadata` | `RFPMetadata` | Parsed RFP metadata |
| `requirements` | `List[Requirement]` | Full requirements register |
| `client_snapshot` | `ClientSnapshot` | Web-researched client intel |
| `win_themes` | `List[WinTheme]` | Strategic angles |
| `response_outline` | `List[ResponseSection]` | Section-by-section structure |
| `compliance_matrix` | `List[ComplianceRow]` | Full compliance mapping |
| `gap_count` | `int` | Number of GAP flags |
| `partial_count` | `int` | Number of PARTIAL flags |
| `covered_count` | `int` | Number of COVERED requirements |
| `generated_at` | `str` | Timestamp |

---

## 8. Data Flow

```
USER INPUT
└── PDF file path (terminal prompt or Gradio upload)
    │
    ▼
RFPParser  [tool: extract_pdf_text]
└── Output: RFPMetadata
    • client_name, contract_value, deadline
    • evaluation_criteria, submission_requirements
    • industry_sector, project_scope_summary
    │
    ├─────────────────────────────┐
    ▼                             ▼
RequirementsExtractor        ClientResearcher  [tool: search_web x3+]
Input: full RFP text         Input: client_name, industry_sector
       + RFPMetadata         Output: ClientSnapshot
Output: List[Requirement]
    │                             │
    └──────────────┬──────────────┘
                   ▼
            WinThemeStrategist
            Input: ClientSnapshot
                   + evaluation_criteria
            Output: List[WinTheme]
                   │
                   ▼
            ResponseArchitect
            Input: List[Requirement]
                   + List[WinTheme]
                   + RFPMetadata
            Output: List[ResponseSection]
                    + List[ComplianceRow]
                   │
                   ▼
            main.py / app.py
            └── Assemble PursuitIntelligencePackage
                Write → pursuit_intelligence_package.md
                Print summary → terminal
```

**v1.1 parallel optimization:** RequirementsExtractor and ClientResearcher both depend only on RFPParser output. Wrap both in `asyncio.gather()` to halve pipeline runtime. Note in README.

---

## 9. File Structure

```
rfp-intelligence-agent/
├── .env                          ← GEMINI_API_KEY (never commit)
├── .env.example                  ← variable names only (safe to commit)
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                       ← terminal entry point
├── app.py                        ← Gradio UI (v1.1)
├── models.py                     ← all Pydantic models (build first)
├── tools/
│   ├── __init__.py
│   ├── pdf_tools.py              ← extract_pdf_text
│   └── search_tools.py           ← search_web
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── rfp_parser.py
│   ├── requirements_extractor.py
│   ├── client_researcher.py
│   ├── win_theme_strategist.py
│   └── response_architect.py
└── sample_outputs/
    └── example_pursuit_package.md  ← committed sample output
```

---

## 10. HITL Decision

**None in v1.**

Natural insertion point identified: after WinThemeStrategist, before ResponseArchitect. A partner or pursuit lead would logically review and edit win themes before the response structure is built around them.

Implement in v1.1 as: print generated win themes → `input("Approve themes? Press Enter to continue or type edits: ")` → pass approved/edited themes to ResponseArchitect.

Document this decision point in the README. It demonstrates you know where human judgment belongs in an agentic workflow — this distinction matters to employers.

---

## 11. Enhancement Roadmap

| Version | Enhancement | Business Value |
|---|---|---|
| v1.1 | Gradio UI on Hugging Face Spaces | Usable by non-technical pursuit teams |
| v1.1 | Parallel execution (asyncio.gather) | ~50% runtime reduction |
| v1.1 | HITL win theme approval gate | Partner review before architecture is locked |
| v1.2 | Competitor intelligence agent | Adds a 7th agent researching known competing firms |
| v1.2 | Export to formatted PDF output | Pursuit package looks like a real deliverable |
| v1.3 | Past proposals vector store (RAG) | Agent pulls relevant past wins to inform new responses |

---

## 12. Business Case (for README and interviews)

**The problem in numbers:**
- Average RFP response: 80–150 hours of labor
- Senior consultant billing rate: $300–500/hour
- Compliance gap caught at submission: lost contract

**What this system automates:**
- Requirements register: 1–2 days → ~90 seconds
- Client research brief: 3–4 hours → ~2 minutes
- Response outline with compliance mapping: 4–6 hours → ~1 minute

**What it does not automate:**
- The actual writing of proposal content
- Final strategic judgment on positioning
- Relationship context a consultant brings from prior engagements

This framing matters. The system is positioned as a force multiplier for experienced consultants, not a replacement. That is the correct AI implementation framing for enterprise buyers — and it is the answer you give in every interview.

---

## 13. Handoff Checklist

- [x] Problem sentence written
- [x] Output format specified (.md file + terminal summary)
- [x] Constraints listed
- [x] Multi-agent chosen and justified
- [x] Pattern selected: Deterministic Pipeline
- [x] 6 agents confirmed (1 orchestrator + 5 workers)
- [x] Every agent has a name and one-sentence role
- [x] Model choice made and justified for each agent
- [x] 2 tools designed with complete docstrings
- [x] Each tool mapped to its agent
- [x] Input defined (PDF path)
- [x] Every agent's output defined with Pydantic model specs
- [x] Output/input match verified (data flow diagram)
- [x] HITL placement decided (none v1, noted for v1.1)
- [x] No orphaned agents or tools
- [x] File structure defined
- [x] Enhancement roadmap documented

**All boxes checked. Open the Execution Playbook. Start at Phase 1.**