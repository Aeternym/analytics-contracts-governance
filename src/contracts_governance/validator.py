from __future__ import annotations

import json
import re
from pathlib import Path

from .parser import Contract, parse_contract


PREFIX = {"metric": "MET", "dimension": "DIM", "segment": "SEG", "domain": "DOMAIN", "owner": "OWNER"}
STATUSES = {
    "metric": {"draft", "review", "approved", "deprecated"},
    "dimension": {"draft", "review", "approved", "deprecated"},
    "segment": {"draft", "review", "approved", "deprecated"},
    "domain": {"active", "archived"},
    "owner": {"active", "archived"},
}
REFERENCE_TYPES = {
    "dimension_ids": "dimension",
    "segment_ids": "segment",
    "owner_id": "owner",
    "approver_ids": "owner",
    "primary_domain_id": "domain",
    "domain_ids": "domain",
}


def _issue(path: str, rule: str, message: str) -> dict:
    return {"severity": "ERROR", "path": path, "rule": rule, "message": message}


def _report(root: Path, files: list[Path], contracts: list[Contract], issues: list[dict], allow_empty: bool) -> dict:
    return {
        "root": str(root),
        "source_exists": root.exists(),
        "source_is_directory": root.is_dir(),
        "empty_catalog_allowed": allow_empty,
        "files_scanned": len(files),
        "contracts_parsed": len(contracts),
        "contracts_by_type": {
            kind: sum(1 for item in contracts if item.metadata.get("contract_type") == kind)
            for kind in PREFIX
        },
        "issues": issues,
        "errors": sum(1 for item in issues if item["severity"] == "ERROR"),
        "verdict": "PASS" if not issues else "NOT_READY",
    }


def _reference_values(contract: Contract, key: str, rel: str, issues: list[dict]) -> list[str]:
    value = contract.metadata.get(key)
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    issues.append(_issue(rel, "metadata_shape", f"{key} must be a string, a list of strings, or null"))
    return []


def validate_directory(root: Path, *, allow_empty: bool = False) -> dict:
    root = Path(root)
    if not root.exists():
        return _report(root, [], [], [_issue(".", "source_missing", "Contract source directory does not exist")], allow_empty)
    if not root.is_dir():
        return _report(root, [], [], [_issue(".", "source_not_directory", "Contract source path is not a directory")], allow_empty)

    files = sorted(path for path in root.rglob("*.md") if path.name != "README.md")
    if not files and not allow_empty:
        return _report(root, [], [], [_issue(".", "empty_catalog", "No contract files were found; use --allow-empty only for an intentional empty catalog")], allow_empty)

    contracts: list[Contract] = []
    issues: list[dict] = []
    for path in files:
        try:
            contracts.append(parse_contract(path))
        except (OSError, UnicodeError, ValueError) as exc:
            issues.append(_issue(str(path.relative_to(root)), "front_matter", str(exc)))

    ids: dict[str, tuple[str, str]] = {}
    for contract in contracts:
        meta = contract.metadata
        rel = str(contract.path.relative_to(root))
        contract_type = meta.get("contract_type")
        contract_id = meta.get("id")
        status = meta.get("status")
        if contract_type not in PREFIX:
            issues.append(_issue(rel, "contract_type", "Unknown contract type"))
            continue
        if not isinstance(contract_id, str) or not re.fullmatch(rf"{PREFIX[contract_type]}-\d{{4}}", contract_id):
            issues.append(_issue(rel, "stable_id", "ID does not match the contract type"))
        elif contract_id in ids:
            issues.append(_issue(rel, "unique_id", f"Duplicate ID also used by {ids[contract_id][1]}"))
        else:
            ids[contract_id] = (contract_type, rel)
        if status not in STATUSES[contract_type]:
            issues.append(_issue(rel, "status", "Status is not allowed for the contract type"))
        if status in {"review", "approved"} and not meta.get("owner_id"):
            issues.append(_issue(rel, "owner", "Review and approved contracts require an owner"))
        if contract_type == "metric" and status in {"review", "approved"} and not meta.get("acceptance_criteria"):
            issues.append(_issue(rel, "acceptance_criteria", "Review and approved metrics require machine-readable acceptance criteria"))

    for contract in contracts:
        rel = str(contract.path.relative_to(root))
        for key in ("related_contract_ids", *REFERENCE_TYPES):
            references = _reference_values(contract, key, rel, issues)
            for reference in references:
                target = ids.get(reference)
                if target is None:
                    issues.append(_issue(rel, "reference", f"Unknown contract ID in {key}: {reference}"))
                    continue
                expected_type = REFERENCE_TYPES.get(key)
                if expected_type and target[0] != expected_type:
                    issues.append(_issue(
                        rel,
                        "reference_type",
                        f"{key} expects {expected_type}, but {reference} is {target[0]}",
                    ))

    return _report(root, files, contracts, issues, allow_empty)


def save_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
