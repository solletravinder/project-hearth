from __future__ import annotations

import pytest


@pytest.fixture
def sample_text() -> str:
    return """This is a sample document text for testing purposes.
It contains multiple lines of text that can be used to test chunking,
storage, and retrieval functionality in the Hearth application.

The quick brown fox jumps over the lazy dog. This sentence contains
every letter of the alphabet at least once, making it useful for
testing text processing algorithms.

Machine learning and natural language processing are fascinating fields
that combine computer science with linguistics and statistics."""  # noqa: E501


@pytest.fixture
def sample_pii_text() -> str:
    return """
Hello, my email is john.doe@example.com and my phone number is (555) 123-4567.
My SSN is 123-45-6789. Please contact me at jane@test.org if you have questions.
Reach me at +1-800-555-0199.
"""
