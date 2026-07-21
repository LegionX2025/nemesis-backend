import os

if os.path.exists("requirements.txt"):
    os.remove("requirements.txt")
    print("Deleted requirements.txt")

import json
toml_content = """[project]
name = "nemesis-python-worker"
version = "0.1.0"
description = "Nemesis OmniChain Intelligence Backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "pydantic",
    "aiohttp",
    "google-genai",
    "python-multipart",
    "python-dotenv",
    "PyPDF2",
    "python-docx",
    "openpyxl",
    "requests",
    "beautifulsoup4",
    "Jinja2",
    "markupsafe",
    "PyJWT"
]

[dependency-groups]
dev = [
    "workers-py",
    "workers-runtime-sdk"
]
"""

with open("pyproject.toml", "w") as f:
    f.write(toml_content)
    print("Updated pyproject.toml")
