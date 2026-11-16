# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Sūveryn Labs Ltd.
"""Checks that the complete example in writing-a-playbook.md is the deed intake suveryn-core ships.

    python3 playbooks/check_example.py <a suveryn-core checkout>

The page's YAML block that starts with `manifest:` must be the shipped manifest, from its `manifest:` line
to its end, line for line. When core changes its deed intake, this fails until the page follows. CI runs it
against core's main.
"""
import difflib
import sys
from pathlib import Path

PAGE = Path(__file__).with_name("writing-a-playbook.md")
SHIPPED = "packages/playbooks/src/suveryn_playbooks/be_notary/deed-intake.yaml"
FENCE = "```"


def example(page: str) -> list[str] | None:
    """The page's YAML block that starts with `manifest:`."""
    lines = page.splitlines()
    for start, line in enumerate(lines):
        if line == FENCE + "yaml" and lines[start + 1:start + 2] and lines[start + 1].startswith("manifest:"):
            return lines[start + 1:lines.index(FENCE, start + 1)]
    return None


def shipped(text: str) -> list[str] | None:
    """The shipped file from its `manifest:` line, without its opening comment."""
    lines = text.splitlines()
    first = next((i for i, line in enumerate(lines) if line.startswith("manifest:")), None)
    return None if first is None else lines[first:]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    file = Path(sys.argv[1]) / SHIPPED
    if not file.is_file():
        print(f"{file}: not found; give a suveryn-core checkout")
        return 1
    theirs = shipped(file.read_text(encoding="utf-8"))
    ours = example(PAGE.read_text(encoding="utf-8"))
    if theirs is None:
        print(f"{file}: no line starts with 'manifest:'")
        return 1
    if ours is None:
        print(f"{PAGE.name}: no YAML block starts with 'manifest:'")
        return 1
    if ours == theirs:
        print(f"{PAGE.name}: the example is the shipped deed intake ({len(ours)} lines)")
        return 0
    print(f"{PAGE.name}: the example differs from {SHIPPED}:")
    print("\n".join(difflib.unified_diff(ours, theirs, "the page", "shipped", lineterm="", n=1)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
