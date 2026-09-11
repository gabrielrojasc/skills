#!/usr/bin/env python3
"""Validate this repository's restricted skill metadata and staged inputs."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        for key, pattern in (("name", r"^name:\s*(.*)$"),
                             ("description", r"^description:\s+(.*)$")):
            match = re.match(pattern, line)
            if match and key not in fields:
                fields[key] = match.group(1)
        if re.fullmatch(r"disable-model-invocation:\s*true\s*", line):
            fields["disable-model-invocation"] = "true"
    return fields


def parse_openai_metadata(text: str) -> dict[str, str]:
    # This is the repository's small line-based schema, not a YAML parser.
    fields: dict[str, str] = {}
    sections: set[str] = set()
    section = ""
    for line in text.splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            raise ValueError("tabs are not allowed")
        if line in {"interface:", "policy:"}:
            section = line[:-1]
            if section in sections:
                raise ValueError(f"duplicate section: {section}")
            sections.add(section)
            continue
        match = None
        if section == "interface":
            match = re.fullmatch(r'  (display_name|short_description): "([^"]+)"', line)
        elif section == "policy":
            match = re.fullmatch(r"  (allow_implicit_invocation): (true|false)", line)
        if match is None:
            raise ValueError(f"unsupported metadata line: {line!r}")
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"duplicate metadata field: {key}")
        fields[key] = value
    if not {"display_name", "short_description"} <= fields.keys():
        raise ValueError("interface requires display_name and short_description")
    if "policy" in sections and "allow_implicit_invocation" not in fields:
        raise ValueError("policy requires allow_implicit_invocation")
    return fields


class Validator:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)
        print(f"error: {message}", file=sys.stderr)

    def command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, cwd=self.root, capture_output=True, text=True)

    def check_snapshot(self) -> None:
        result = self.command(["git", "diff", "--quiet", "--exit-code", "--"])
        if result.returncode:
            if result.returncode == 1:
                self.fail("working tree differs from the staged snapshot; stage or restore changes before validation")
            else:
                self.fail(f"git diff failed: {result.stderr.strip()}")
        result = self.command(["git", "ls-files", "--others", "--exclude-standard", "-z", "--", "README.md", "scripts", "skills"])
        if result.returncode:
            self.fail(f"git ls-files failed: {result.stderr.strip()}")
        elif result.stdout:
            self.fail("untracked validation inputs exist; stage or remove them before validation")

    def validate_skill(self, skill_dir: Path, readme: str) -> None:
        name = skill_dir.name
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            self.fail(f"{name} is missing SKILL.md")
            return
        try:
            fields = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            self.fail(f"{name} has invalid SKILL.md frontmatter: {exc}")
            return
        if fields.get("name", "") != name:
            self.fail(f"{name} declares name {fields.get('name', '')!r}")
        description = fields.get("description", "")
        if not description:
            self.fail(f"{name} must declare a single-line description")
        elif description.startswith(('"', "'")) or description.endswith(('"', "'")):
            self.fail(f"{name} description must be an unquoted YAML scalar")
        elif not re.fullmatch(r".+\. Use when .+\.", description):
            self.fail(f"{name} description must use '<what it does>. Use when <trigger>.'")
        elif not 25 <= len(description) <= 64:
            self.fail(f"{name} description must be 25-64 characters")
        metadata_file = skill_dir / "agents" / "openai.yaml"
        if not metadata_file.is_file():
            self.fail(f"{name} is missing agents/openai.yaml")
        else:
            try:
                metadata = parse_openai_metadata(metadata_file.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError) as exc:
                self.fail(f"{name} has invalid agents/openai.yaml structure: {exc}")
            else:
                if description != metadata["short_description"]:
                    self.fail(f"{name} description differs between SKILL.md and agents/openai.yaml")
                disabled = fields.get("disable-model-invocation") == "true"
                if disabled != (metadata.get("allow_implicit_invocation") == "false"):
                    self.fail(f"{name} invocation policy disagrees between SKILL.md and agents/openai.yaml")
        relative = skill_dir.relative_to(self.root).as_posix()
        if f"{relative}/" not in readme:
            self.fail(f"README.md does not link {relative}/")

    def validate_scripts(self) -> None:
        for directory in (self.root / "scripts", self.root / "skills"):
            if not directory.is_dir():
                self.fail(f"missing directory: {directory.name}")
                continue
            for current, _, files in os.walk(directory, onerror=lambda exc: self.fail(str(exc))):
                for filename in sorted(files):
                    path = Path(current) / filename
                    if path.suffix not in {".sh", ".py"} or path.is_symlink():
                        continue
                    relative = path.relative_to(self.root)
                    if not os.access(path, os.X_OK):
                        self.fail(f"script is not executable: {relative}")
                    if path.suffix == ".sh":
                        result = self.command(["bash", "-n", str(path)])
                        if result.returncode:
                            self.fail(f"shell syntax failed: {relative}: {result.stderr.strip()}")
                    else:
                        try:
                            compile(path.read_text(encoding="utf-8"), str(path), "exec")
                        except (OSError, UnicodeError, SyntaxError) as exc:
                            self.fail(f"python syntax failed: {relative}: {exc}")

    def run(self) -> int:
        self.check_snapshot()
        try:
            readme = (self.root / "README.md").read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.fail(f"cannot read README.md: {exc}")
            readme = ""
        skill_root = self.root / "skills"
        skill_dirs = []
        categories = []
        for path in sorted(skill_root.iterdir()) if skill_root.is_dir() else []:
            if not path.is_dir():
                continue
            children = sorted(child for child in path.iterdir() if child.is_dir())
            if (path / "SKILL.md").is_file() or (path / "agents").is_dir() or not children:
                skill_dirs.append(path)
            else:
                categories.append(path)
                skill_dirs.extend(children)
        names: set[str] = set()
        for skill_dir in skill_dirs:
            if skill_dir.name in names:
                self.fail(f"duplicate skill name: {skill_dir.name}")
            names.add(skill_dir.name)
            self.validate_skill(skill_dir, readme)
        if any(path.name.startswith("af-") for path in skill_dirs + categories):
            self.fail("retired af-* skill directories remain")
        if not skill_dirs:
            self.fail("no skills found")
        self.validate_scripts()
        for args in (["git", "diff", "--check"], ["git", "diff", "--cached", "--check"]):
            result = self.command(args)
            if result.returncode:
                self.fail(f"{' '.join(args)} failed: {(result.stdout + result.stderr).strip()}")
        if self.errors:
            return 1
        print(f"Validated {len(skill_dirs)} skill(s).")
        return 0


def main() -> int:
    try:
        return Validator(Path(__file__).resolve().parent.parent).run()
    except (OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
