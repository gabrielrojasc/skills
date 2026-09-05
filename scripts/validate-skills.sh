#!/usr/bin/env bash

set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
failed=0
skill_count=0

fail() {
  printf 'error: %s\n' "$1" >&2
  failed=1
}

has_description_shape() {
  case "$1" in
    ?*". Use when "?*.) return 0 ;;
    *) return 1 ;;
  esac
}

if ! git -C "$repo_root" diff --quiet --exit-code --; then
  fail "working tree differs from the staged snapshot; stage or restore changes before validation"
fi

if git -C "$repo_root" ls-files --others --exclude-standard -- README.md scripts skills | grep -q .; then
  fail "untracked validation inputs exist; stage or remove them before validation"
fi

validate_openai_metadata() {
  awk '
    BEGIN {
      section = ""
      interface_seen = 0
      display_seen = 0
      description_seen = 0
      policy_seen = 0
      implicit_seen = 0
    }

    /^[[:space:]]*$/ { next }
    /\t/ { exit 1 }

    $0 == "interface:" && !interface_seen {
      interface_seen = 1
      section = "interface"
      next
    }

    $0 == "policy:" && !policy_seen {
      policy_seen = 1
      section = "policy"
      next
    }

    section == "interface" && $0 ~ /^  display_name: "[^"]+"$/ && !display_seen {
      display_seen = 1
      next
    }

    section == "interface" && $0 ~ /^  short_description: "[^"]+"$/ && !description_seen {
      description_seen = 1
      next
    }

    section == "policy" && $0 ~ /^  allow_implicit_invocation: (true|false)$/ && !implicit_seen {
      implicit_seen = 1
      next
    }

    { exit 1 }

    END {
      if (!interface_seen || !display_seen || !description_seen) {
        exit 1
      }
      if (policy_seen && !implicit_seen) {
        exit 1
      }
    }
  ' "$1"
}

for skill_dir in "${repo_root}"/skills/*; do
  [ -d "$skill_dir" ] || continue
  skill_count=$((skill_count + 1))
  folder_name="${skill_dir##*/}"
  skill_file="${skill_dir}/SKILL.md"
  metadata_file="${skill_dir}/agents/openai.yaml"

  if [ ! -f "$skill_file" ]; then
    fail "${folder_name} is missing SKILL.md"
    continue
  fi

  declared_name="$(awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && $0 ~ /^name:[[:space:]]*/ {
      sub(/^name:[[:space:]]*/, "")
      print
      exit
    }
  ' "$skill_file")"

  if [ "$declared_name" != "$folder_name" ]; then
    fail "${folder_name} declares name '${declared_name}'"
  fi

  declared_description="$(awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && $0 ~ /^description:[[:space:]]+/ {
      sub(/^description:[[:space:]]+/, "")
      print
      exit
    }
  ' "$skill_file")"

  if [ -z "$declared_description" ]; then
    fail "${folder_name} must declare a single-line description"
  else
    case "$declared_description" in
      \"*|*\"|\'*|*\')
        fail "${folder_name} description must be an unquoted YAML scalar"
        ;;
      *)
        if ! has_description_shape "$declared_description"; then
          fail "${folder_name} description must use '<what it does>. Use when <trigger>.'"
        elif [ "${#declared_description}" -lt 25 ] || [ "${#declared_description}" -gt 64 ]; then
          fail "${folder_name} description must be 25-64 characters"
        fi
        ;;
    esac
  fi

  if [ ! -f "$metadata_file" ]; then
    fail "${folder_name} is missing agents/openai.yaml"
  elif ! validate_openai_metadata "$metadata_file"; then
    fail "${folder_name} has invalid agents/openai.yaml structure"
  else
    metadata_description="$(awk '
      /^  short_description: "[^"]+"$/ {
        sub(/^  short_description: "/, "")
        sub(/"$/, "")
        print
        exit
      }
    ' "$metadata_file")"
    if [ "$declared_description" != "$metadata_description" ]; then
      fail "${folder_name} description differs between SKILL.md and agents/openai.yaml"
    fi

    skill_disables_implicit=false
    metadata_disables_implicit=false
    if awk '
        NR == 1 && $0 == "---" { in_frontmatter = 1; next }
        in_frontmatter && $0 == "---" { exit }
        in_frontmatter && $0 ~ /^disable-model-invocation:[[:space:]]*true[[:space:]]*$/ { found = 1 }
        END { exit !found }
      ' "$skill_file"; then
      skill_disables_implicit=true
    fi
    if rg -q '^  allow_implicit_invocation: false$' "$metadata_file"; then
      metadata_disables_implicit=true
    fi
    if [ "$skill_disables_implicit" != "$metadata_disables_implicit" ]; then
      fail "${folder_name} invocation policy disagrees between SKILL.md and agents/openai.yaml"
    fi
  fi

  if ! rg -Fq "skills/${folder_name}/" "${repo_root}/README.md"; then
    fail "README.md does not link skills/${folder_name}/"
  fi
done

if [ "$skill_count" -eq 0 ]; then
  fail "no skills found"
fi

while IFS= read -r script; do
  [ -n "$script" ] || continue
  if [ ! -x "$script" ]; then
    fail "script is not executable: ${script#${repo_root}/}"
  fi
  case "$script" in
    *.sh)
      bash -n "$script" || fail "shell syntax failed: ${script#${repo_root}/}"
      ;;
    *.py)
      python3 - "$script" <<'PY' || fail "python syntax failed: ${script#${repo_root}/}"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
compile(path.read_text(), str(path), "exec")
PY
      ;;
  esac
done < <(find "${repo_root}/scripts" "${repo_root}/skills" -type f \( -name '*.sh' -o -name '*.py' \) -print)

if find "${repo_root}/skills" -mindepth 1 -maxdepth 1 -type d -name 'af-*' | grep -q .; then
  fail "retired af-* skill directories remain"
fi

git -C "$repo_root" diff --check || failed=1
git -C "$repo_root" diff --cached --check || failed=1

if [ "$failed" -ne 0 ]; then
  exit 1
fi

printf 'Validated %d skill(s).\n' "$skill_count"
