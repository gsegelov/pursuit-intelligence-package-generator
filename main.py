# main.py
# Terminal entry point for the Pursuit Intelligence Package Generator.
# Takes a PDF file path, runs the full pipeline, writes output to .md file

import asyncio
import os
from pipeline.orchestrator import run_pipeline

def format_package(package) -> str:
    """Format the PursuitIntelligencePackage as a readable markdown document."""

    lines = []
    lines.append(f"# Pursuit Intelligence Package")
    lines.append(f"**Generated:** {package.generated_at}")
    lines.append(f"**Client:** {package.rfp_metadata.client_name}")
    lines.append(f"**Contract Value:** {package.rfp_metadata.contract_value}")
    lines.append(f"**Deadline:** {package.rfp_metadata.submission_deadline}")
    lines.append(f"\n---\n")

    # Client Snapshot
    lines.append(f"## Client Snapshot")
    lines.append(f"{package.client_snapshot.business_description}")
    lines.append(f"\n**Strategic Priorities:**")
    for p in package.client_snapshot.strategic_priorities:
        lines.append(f"- {p}")
    lines.append(f"\n**Recent News:**")
    for n in package.client_snapshot.recent_news:
        lines.append(f"- {n}")
    # Sources — preserves URLs so every claim is traceable
    if package.client_snapshot.sources:
        lines.append(f"\n**Sources:**")
        for s in package.client_snapshot.sources:
            lines.append(f"- {s}")
    lines.append(f"\n---\n")

    # Requirements Register
    lines.append(f"## Requirements Register")
    lines.append(f"**Total:** {len(package.requirements)} requirements")
    for r in package.requirements:
        implied_tag = " *(implied)*" if r.implied else ""
        lines.append(f"\n**{r.req_id}** [{r.req_type.upper()}] [{r.priority}]{implied_tag}")
        lines.append(f"{r.text}")
    lines.append(f"\n---\n")

    # Win Themes
    lines.append(f"## Win Themes")
    for t in package.win_themes:
        lines.append(f"\n### {t.theme_title}")
        lines.append(f"**Rationale:** {t.rationale}")
        lines.append(f"**Evidence:** {t.supporting_evidence}")
        lines.append(f"**Emphasis:** {t.recommended_emphasis}")
    lines.append(f"\n---\n")

    # Response Outline
    lines.append(f"## Response Outline")
    for s in package.response_outline:
        lines.append(f"\n### {s.section_number}. {s.section_title} *({s.estimated_pages})*")
        lines.append(f"**Purpose:** {s.purpose}")
        lines.append(f"**Angle:** {s.recommended_angle}")
        lines.append(f"**Requirements:** {', '.join(s.requirements_addressed)}")
        lines.append(f"**Win Themes:** {', '.join(s.win_themes_applied)}")
    lines.append(f"\n---\n")

    # Compliance Matrix
    lines.append(f"## Compliance Matrix")
    lines.append(f"**Covered:** {package.covered_count} | **Partial:** {package.partial_count} | **Gaps:** {package.gap_count}")
    lines.append(f"\n| REQ ID | Status | Section | Notes |")
    lines.append(f"|--------|--------|---------|-------|")
    for row in package.compliance_matrix:
        lines.append(f"| {row.req_id} | {row.coverage_status} | {row.addressed_in_section} | {row.notes} |")

    return "\n".join(lines)


async def main():
    print("\n=== Pursuit Intelligence Package Generator ===\n")

    # Get PDF path from user
    pdf_path = input("Enter the path to your RFP PDF: ").strip()

    # Validate the file exists before running the pipeline
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found at {pdf_path}")
        return

    print("\nRunning pipeline — this will take 2-4 minutes...\n")

    try:
        # Run the full pipeline
        package = await run_pipeline(pdf_path)

        # Format and write the output file
        output = format_package(package)
        with open("pursuit_intelligence_package.md", "w", encoding="utf-8") as f:
            f.write(output)

        # Print terminal summary
        print("\n=== COMPLETE ===")
        print(f"Client: {package.rfp_metadata.client_name}")
        print(f"Requirements extracted: {len(package.requirements)}")
        print(f"Win themes generated: {len(package.win_themes)}")
        print(f"Response sections: {len(package.response_outline)}")
        print(f"Compliance: {package.covered_count} covered | {package.partial_count} partial | {package.gap_count} gaps")
        print(f"\nOutput written to: pursuit_intelligence_package.md")

    except Exception as e:
        print(f"\nPipeline failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())