"""Sample content fixtures for E2E tests."""

# Sample PDF content (minimal valid PDF structure)
SAMPLE_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
298
%%EOF
"""

# Sample text content for testing
SAMPLE_TEXT = "Hearth is an offline AI assistant for notes and research."

# Sample text with keywords for search testing
KEYWORD_RICH_TEXT = """
Hearth is a powerful AI assistant that helps with research and note-taking.
The search functionality in Hearth uses both keyword matching and semantic search.
Users can upload documents and query them using natural language.
Privacy is a core feature - all processing happens locally on your device.
"""

# Sample text for document lifecycle testing
DOCUMENT_LIFECYCLE_TEXT = "This is a test document for lifecycle testing."

# Sample note content
SAMPLE_NOTE = """
# Test Note

This is a sample note for testing CRUD operations.

## Features
- Create notes
- Read notes
- Update notes
- Delete notes
"""
