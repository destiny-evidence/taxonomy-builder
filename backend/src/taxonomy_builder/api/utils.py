"""Utility functions for routers."""

import re


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "-", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")
