# tools/pdf_tool.py
# Tool for extracting raw text from a PDF file
# Used once at the start of the pipeline, before any agent analysis begins

import pypdf
from agents import function_tool

@function_tool
def extract_pdf_text(file_path: str) -> str:
    """
    Extract all text content from a PDF RFP document at the given file path.
    Use this once at the start of the pipeline, before any analysis begins.
    Returns the full text of the document as a single string.
    """
    try:
        reader = pypdf.PdfReader(file_path)
        # Join text from all pages, skipping any pages that return no text
        return "\n\n".join(
            page.extract_text() for page in reader.pages
            if page.extract_text()
        )
    except Exception as e:
        # Return a descriptive error string so the orchestrator can surface it cleanly
        return f"ERROR: Could not read PDF at {file_path}. Reason: {str(e)}"