from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _hash_text(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _collect_markdown_files(root_dir: str = "kiro-steering") -> list[Path]:
    root = Path(root_dir)
    files: list[Path] = []

    if root.exists():
        files.extend(sorted(root.rglob("*.md")))

    for fixed in [Path("README.md"), Path("project_documentation.md")]:
        if fixed.exists():
            files.append(fixed)

    # Deduplicate while preserving order
    dedup: list[Path] = []
    seen: set[str] = set()
    for f in files:
        key = str(f.resolve())
        if key not in seen:
            dedup.append(f)
            seen.add(key)
    return dedup


def _source_meta(path: Path, content: str) -> dict[str, Any]:
    return {
        "path": str(path.as_posix()),
        "last_modified": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
        "hash": _hash_text(content),
    }


def _make_item(
    item_id: str,
    title: str,
    summary: str,
    source_file: str,
    line_no: int,
    item_type: str,
    tags: list[str] | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item_id,
        "title": title,
        "summary": summary,
        "source": {
            "tool": "local-parser",
            "file": source_file,
            "anchor": "",
            "line_range": [line_no, line_no],
        },
        "observed_at": _iso_now(),
    }

    if tags:
        payload["tags"] = tags
    if severity:
        payload["severity"] = severity
    payload["type"] = item_type
    return payload


def _extract_items_from_file(
    path: Path,
    content: str,
    counters: dict[str, int],
) -> dict[str, list[dict[str, Any]]]:
    decisions: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    env_vars: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    section = "general"
    lines = content.splitlines()
    file_name = path.as_posix()

    env_pattern = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()

        if line.startswith("#"):
            normalized = line.lower()
            if any(k in normalized for k in ["architectural", "decision", "החלט", "architecture"]):
                section = "decisions"
            elif any(k in normalized for k in ["rules", "guideline", "הנח", "rtl", "ux", "ui"]):
                section = "rules"
            elif any(k in normalized for k in ["warning", "רגיש", "לא לגעת", "security", "ssl"]):
                section = "warnings"
            elif any(k in normalized for k in ["changelog", "change", "שינוי"]):
                section = "changes"
            else:
                section = "general"
            continue

        # Environment variables extraction
        for var in env_pattern.findall(line):
            if var in {"HTTP", "HTTPS", "JSON", "URL", "UTC"}:
                continue
            counters["env"] += 1
            env_vars.append(
                {
                    "id": f"env-{counters['env']:03d}",
                    "name": var,
                    "summary": "Environment variable reference found in markdown.",
                    "source": {
                        "tool": "local-parser",
                        "file": file_name,
                        "anchor": "",
                        "line_range": [i, i],
                    },
                    "observed_at": _iso_now(),
                }
            )

        if not line.startswith(("- ", "* ")):
            continue

        text = line[2:].strip()
        if not text:
            continue

        if section == "decisions":
            counters["dec"] += 1
            decisions.append(
                _make_item(
                    item_id=f"dec-{counters['dec']:03d}",
                    title=text[:80],
                    summary=text,
                    source_file=file_name,
                    line_no=i,
                    item_type="decision",
                    tags=["architecture"],
                )
            )
        elif section == "rules":
            counters["rule"] += 1
            rules.append(
                _make_item(
                    item_id=f"rule-{counters['rule']:03d}",
                    title=text[:80],
                    summary=text,
                    source_file=file_name,
                    line_no=i,
                    item_type="rule",
                    tags=["policy"],
                )
            )
        elif section == "warnings":
            counters["warn"] += 1
            warnings.append(
                _make_item(
                    item_id=f"warn-{counters['warn']:03d}",
                    title=text[:80],
                    summary=text,
                    source_file=file_name,
                    line_no=i,
                    item_type="warning",
                    severity="high" if "לא" in text or "never" in text.lower() else "medium",
                )
            )
        elif section == "changes":
            counters["chg"] += 1
            changes.append(
                _make_item(
                    item_id=f"chg-{counters['chg']:03d}",
                    title=text[:80],
                    summary=text,
                    source_file=file_name,
                    line_no=i,
                    item_type="change",
                    tags=["timeline"],
                )
            )

    return {
        "decisions": decisions,
        "rules": rules,
        "warnings": warnings,
        "env_vars": env_vars,
        "changes": changes,
    }


def build_structured_data(root_dir: str = "kiro-steering") -> dict[str, Any]:
    files = _collect_markdown_files(root_dir)
    counters = {"dec": 0, "rule": 0, "warn": 0, "env": 0, "chg": 0}

    all_decisions: list[dict[str, Any]] = []
    all_rules: list[dict[str, Any]] = []
    all_warnings: list[dict[str, Any]] = []
    all_env_vars: list[dict[str, Any]] = []
    all_changes: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []

    for path in files:
        content = path.read_text(encoding="utf-8", errors="ignore")
        source_files.append(_source_meta(path, content))
        extracted = _extract_items_from_file(path, content, counters)
        all_decisions.extend(extracted["decisions"])
        all_rules.extend(extracted["rules"])
        all_warnings.extend(extracted["warnings"])
        all_env_vars.extend(extracted["env_vars"])
        all_changes.extend(extracted["changes"])

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso_now(),
        "sources": [
            {
                "tool": "local-parser",
                "root_path": str(Path(root_dir).as_posix()),
                "files": source_files,
            }
        ],
        "items": {
            "decisions": all_decisions,
            "rules": all_rules,
            "warnings": all_warnings,
            "env_vars": all_env_vars,
            "changes": all_changes,
        },
    }


def ensure_structured_data_file(
    root_dir: str = "kiro-steering",
    output_path: str = "structured_data.json",
) -> str:
    data = build_structured_data(root_dir=root_dir)
    output = Path(output_path)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output.as_posix())


def route_query_mode(query: str) -> str:
    q = query.lower()
    structured_markers = [
        "רשימה",
        "כל ההחלט",
        "הנחיה",
        "עדכני",
        "שבוע",
        "אחרון",
        "רגיש",
        "לא לגעת",
        "משתני סביבה",
        "changelog",
        "rules",
        "decisions",
    ]
    return "structured" if any(marker in q for marker in structured_markers) else "semantic"


def _latest(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return max(items, key=lambda x: x.get("observed_at", ""))


def _format_items(items: list[dict[str, Any]], title: str, limit: int = 20) -> str:
    if not items:
        return f"לא נמצאו פריטים עבור {title}."
    lines = [f"{title} ({len(items)}):"]
    for item in items[:limit]:
        src = item.get("source", {}).get("file", "")
        lines.append(f"- {item.get('summary', '')} | מקור: {src}")
    return "\n".join(lines)


def query_structured_data(query: str, data_path: str = "structured_data.json") -> str:
    path = Path(data_path)
    if not path.exists():
        return "structured_data.json לא קיים. הריצי prepare.py או ensure_structured_data_file()."

    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", {})
    decisions = items.get("decisions", [])
    rules = items.get("rules", [])
    warnings = items.get("warnings", [])
    env_vars = items.get("env_vars", [])
    changes = items.get("changes", [])

    q = query.lower()

    if "רשימה" in q and ("החלט" in q or "decisions" in q):
        return _format_items(decisions, "החלטות טכניות")

    if "rtl" in q or "עברית" in q:
        rtl_rules = [r for r in rules if "rtl" in r.get("summary", "").lower() or "עברית" in r.get("summary", "")]
        latest = _latest(rtl_rules)
        if latest:
            return (
                "הנחיית RTL עדכנית:\n"
                f"- {latest.get('summary', '')}\n"
                f"מקור: {latest.get('source', {}).get('file', '')}"
            )
        return "לא נמצאה הנחיית RTL מובנית כרגע."

    if "שבוע" in q or "last week" in q:
        cutoff = datetime.now(UTC) - timedelta(days=7)
        recent = []
        for item in warnings + changes:
            observed = item.get("observed_at")
            if not observed:
                continue
            try:
                dt = datetime.fromisoformat(observed)
            except ValueError:
                continue
            if dt >= cutoff:
                recent.append(item)
        return _format_items(recent, "פריטים מהשבוע האחרון")

    if "רגיש" in q or "warning" in q or "לא לגעת" in q:
        return _format_items(warnings, "אזהרות/רגישויות")

    if "משתני סביבה" in q or "env" in q:
        return _format_items(env_vars, "משתני סביבה")

    if "שינויים" in q or "changelog" in q:
        return _format_items(changes, "שינויים")

    return "לא נמצאה התאמה חד-משמעית בנתונים המובנים. נסי לנסח שאלה רשימתית/זמנית/עדכנית."


def main() -> None:
    output = ensure_structured_data_file()
    print(f"Structured data generated: {output}")


if __name__ == "__main__":
    main()
