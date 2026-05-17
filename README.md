# Pursuit Intelligence Package Generator

An AI-powered multi-agent system that automates the intelligence layer of RFP response preparation for consulting pursuit teams.

## The Problem

Consulting pursuit teams at firms like Accenture, Deloitte, KPMG, and Capgemini spend 80–150 hours per RFP response on work that is largely extraction, research, and formatting — leaving almost no time for the strategic differentiation that actually wins contracts.

- Requirements register: 1–2 days of analyst work → ~90 seconds
- Client research brief: 3–4 hours → ~2 minutes  
- Response outline with compliance mapping: 4–6 hours → ~1 minute

**This system automates the intelligence layer so pursuit teams spend their hours on strategy, not synthesis.**

## What It Produces

A structured Pursuit Intelligence Package containing:

1. **Client Snapshot** — web-researched intelligence on the issuing organization
2. **Requirements Register** — every stated and implied requirement, tagged by type and priority
3. **Win Themes** — 3–5 strategic angles derived from client intel and evaluation criteria
4. **Response Outline** — section-by-section structure with purpose, angle, and requirement mapping
5. **Compliance Matrix** — every requirement mapped to a response section, with GAP flags

See `sample_outputs/example_pursuit_package.md` for a real example generated against a US Air Force RFP.

## Architecture

**Pattern:** Deterministic Pipeline with Orchestrator  
**Framework:** OpenAI Agents SDK + Gemini API (via OpenAI-compatible endpoint)

```
PDF Input → RFPParser → RequirementsExtractor → ClientResearcher
                                              ↓
                                    WinThemeStrategist
                                              ↓
                                    ResponseArchitect
                                              ↓
                              pursuit_intelligence_package.md
```

### Agents

| Agent | Model | Role |
|-------|-------|------|
| RFPParser | Gemini 2.5 Flash | Extracts structured metadata from RFP text |
| RequirementsExtractor | Gemini 2.5 Pro | Extracts stated and implied requirements |
| ClientResearcher | Gemini 2.5 Flash | Web research on issuing organization |
| WinThemeStrategist | Gemini 2.5 Pro | Generates strategic win themes |
| ResponseArchitect | Gemini 2.5 Pro | Designs response structure and compliance matrix |

Flash is used for retrieval and extraction tasks. Pro is used where strategic reasoning is required.

### Tools

- `extract_pdf_text` — PDF parsing via pypdf
- `search_web` — Web search via DuckDuckGo (no API key required)

## Setup

**Prerequisites:** Python 3.11+, Gemini API key from [Google AI Studio](https://aistudio.google.com)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/pursuit-intelligence-package-generator
cd pursuit-intelligence-package-generator

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
python -m pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

## Usage

```bash
python main.py
```

When prompted, enter the path to your RFP PDF. The pipeline runs in approximately 2–4 minutes and writes output to `pursuit_intelligence_package.md`.

## Design Decisions

**Why deterministic pipeline over dynamic routing?** The task sequence has fixed dependencies — win themes cannot be written before client research; the compliance matrix cannot be built before requirements are extracted. Dynamic routing adds complexity without benefit here.

**Why Flash for some agents and Pro for others?** Extraction and retrieval tasks (parsing, research) don't require deep reasoning — Flash is faster and cheaper. Strategic synthesis (win themes, response architecture) justifies Pro's reasoning depth.

**Why no HITL in v1?** The natural insertion point is after WinThemeStrategist — a pursuit lead would logically review win themes before the response structure is built around them. Implemented in v1.1 as an approval gate.

**Why manual JSON parsing instead of output_type?** The OpenAI Agents SDK uses the Responses API by default, which Gemini's OpenAI-compatible endpoint does not support. Switching to Chat Completions mode (`set_default_openai_api("chat_completions")`) and parsing structured JSON output manually resolves this — and reflects a pattern common in production agentic systems where output validation cannot be delegated to the framework.

## Roadmap

| Version | Enhancement | Business Value |
|---------|-------------|----------------|
| v1.1 | Gradio UI on Hugging Face Spaces | Usable by non-technical pursuit teams |
| v1.1 | Parallel execution (asyncio.gather) | ~50% runtime reduction |
| v1.1 | HITL win theme approval gate | Partner review before architecture is locked |
| v1.2 | Competitor intelligence agent | Researches known competing firms |
| v1.2 | PDF export | Package looks like a real deliverable |
| v1.3 | Past proposals RAG | Agent pulls relevant past wins to inform new responses |

## Skills Demonstrated

`Python` `OpenAI Agents SDK` `Gemini API` `Multi-agent orchestration` `Pydantic` `Async programming` `PDF parsing` `Web search integration` `Prompt engineering` `Structured output validation`
```