#!/usr/bin/env python3
"""Try prompts/refine.md against Ollama outside n8n.

Usage: scripts/try-refine.py <issue-number> <title> <body> [--model qwen3:8b] [--think]
Prints the spec and the time it took. Uses only the standard library.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLLAMA = "http://localhost:11434/api/chat"


def system_prompt() -> str:
    prompt = (ROOT / "prompts/refine.md").read_text()
    template = (ROOT / "templates/spec-template.md").read_text()
    return prompt.replace("{{SPEC_TEMPLATE}}", template.strip())


def user_message(issue: int, title: str, body: str) -> str:
    return (
        f"ISSUE #{issue}: {title}\n{body}\n\n"
        "PREVIOUS SPEC:\nNone\n\n"
        "COMMENTS:\nNone"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("issue", type=int)
    p.add_argument("title")
    p.add_argument("body")
    p.add_argument("--model", default="qwen3:8b")
    p.add_argument("--think", action="store_true", help="let qwen3 reason first")
    a = p.parse_args()

    payload = {
        "model": a.model,
        "stream": False,
        "think": a.think,
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": user_message(a.issue, a.title, a.body)},
        ],
    }
    req = urllib.request.Request(
        OLLAMA, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.load(resp)
    print(out["message"]["content"])
    print(f"\n--- {a.model}, think={a.think}, {time.time() - start:.1f} s")


if __name__ == "__main__":
    main()
