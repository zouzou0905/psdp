import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_BUNDLE_SHA256 = "864c271c3ebd5830f99016f2ee03725dd395040f2e342d354e63471c35140351"
BUNDLE_VERSION = "2026-10-09"
ARCHIVE_ROOT = f"Amazon精铺选品_六Skill_DeepSeek版_{BUNDLE_VERSION}"

COMMON_DEPENDENCIES = (
    "skills/_amazon-selection-shared/six-agent-control.md",
    "skills/_amazon-selection-shared/common-gates.md",
    "skills/_amazon-selection-shared/market-entry.md",
    "skills/_amazon-selection-shared/candidate-profit-workflow.md",
    "skills/_amazon-selection-shared/batch-review-handoff.md",
    "skills/_amazon-selection-shared/air-small-batch-window.md",
    "skills/_amazon-selection-shared/referral-fees.md",
    "skills/_amazon-selection-shared/selection-fee-policy-2026-09-17.json",
    "skills/_amazon-selection-shared/fba-fees.md",
    "skills/_amazon-selection-shared/fba-fees-2026-09-21.json",
    "skills/_amazon-selection-shared/fba-fees-peak-2026-09-16.json",
    "skills/_amazon-selection-shared/selection-memory.md",
    "skills/_amazon-selection-shared/human-review-memory-2026-09-04.json",
    "skills/_amazon-selection-shared/selection-run-control.md",
    "skills/_amazon-selection-shared/scripts/selection-runtime.mjs",
    "skills/_amazon-selection-shared/scripts/state.schema.json",
)

RULES: dict[str, tuple[str, str]] = {
    "six-agent-control": (
        "six-agent-control-v1.14.0",
        "skills/_amazon-selection-shared/six-agent-control.md",
    ),
    "selection-gates": (
        "selection-gates-v0.10.0",
        "skills/_amazon-selection-shared/common-gates.md",
    ),
    "market-entry": (
        "market-entry-v0.6.0",
        "skills/_amazon-selection-shared/market-entry.md",
    ),
    "candidate-profit-workflow": (
        "candidate-profit-workflow-v1.9.0",
        "skills/_amazon-selection-shared/candidate-profit-workflow.md",
    ),
    "batch-review-handoff": (
        "batch-review-handoff-v2.0.0",
        "skills/_amazon-selection-shared/batch-review-handoff.md",
    ),
    "selection-execution": (
        "selection-execution-v1.2.0",
        "skills/_amazon-selection-shared/six-agent-control.md",
    ),
    "selection-run-control": (
        "selection-run-control-v1.1.0",
        "skills/_amazon-selection-shared/selection-run-control.md",
    ),
    "air-small-batch-window": (
        "air-small-batch-window-v1.0.0",
        "skills/_amazon-selection-shared/air-small-batch-window.md",
    ),
    "fba-fee-snapshot": (
        "fba-fees-2026-09-21",
        "skills/_amazon-selection-shared/fba-fees-2026-09-21.json",
    ),
    "fba-peak-fee-snapshot": (
        "fba-fees-peak-2026-09-16",
        "skills/_amazon-selection-shared/fba-fees-peak-2026-09-16.json",
    ),
    "commission-policy": (
        "selection-fee-policy-2026-09-17",
        "skills/_amazon-selection-shared/selection-fee-policy-2026-09-17.json",
    ),
    "selection-memory": (
        "selection-memory-v0.10.0",
        "skills/_amazon-selection-shared/selection-memory.md",
    ),
}

SKILLS: dict[str, dict[str, Any]] = {
    "evergreen": {
        "package_name": "select-sorftime-amazon-evergreen",
        "display_name": "日常微蓝海选品",
        "type_rule_version": "evergreen-demand-v0.7.0",
        "supports_new_product_discovery": True,
        "requires_base_product": False,
        "modes": ["independent_discovery"],
        "launch_parameters": ["site", "seed", "analysis_date", "depth"],
    },
    "seasonal": {
        "package_name": "select-sorftime-amazon-seasonal",
        "display_name": "季节窗口品选品",
        "type_rule_version": "seasonal-window-v0.5.0",
        "supports_new_product_discovery": True,
        "requires_base_product": False,
        "modes": ["independent_discovery"],
        "launch_parameters": ["site", "seed", "analysis_date", "target_window", "depth"],
    },
    "holiday": {
        "package_name": "select-sorftime-amazon-holiday",
        "display_name": "节日事件品选品",
        "type_rule_version": "holiday-window-v0.7.0",
        "supports_new_product_discovery": True,
        "requires_base_product": False,
        "modes": ["independent_discovery"],
        "launch_parameters": ["site", "seed", "event_name", "target_year", "depth"],
    },
    "trending_accessories": {
        "package_name": "select-sorftime-amazon-trending-accessories",
        "display_name": "热点母体衍生配件选品",
        "type_rule_version": "hot-accessory-v1.0.0",
        "supports_new_product_discovery": True,
        "requires_base_product": False,
        "modes": ["independent_discovery"],
        "launch_parameters": ["site", "main_product_seed", "accessory_clue", "analysis_date"],
    },
    "consumables_multipacks": {
        "package_name": "select-sorftime-amazon-consumables-multipacks",
        "display_name": "消耗品与包装规格选品",
        "type_rule_version": "consumables-packs-v0.5.0",
        "supports_new_product_discovery": True,
        "requires_base_product": False,
        "modes": ["independent_discovery", "tag_review"],
        "launch_parameters": ["site", "seed", "selection_mode", "branch_mode", "pack_scope"],
    },
    "validated_variations": {
        "package_name": "select-sorftime-amazon-validated-variations",
        "display_name": "已验证产品扩展",
        "type_rule_version": "validated-variations-v0.4.1",
        "supports_new_product_discovery": False,
        "requires_base_product": True,
        "modes": ["base_product_expansion"],
        "launch_parameters": ["site", "base_asin", "proposed_dimension", "target_offer"],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(name: str) -> Path:
    archive_path = PurePosixPath(name)
    if archive_path.is_absolute() or ".." in archive_path.parts:
        raise ValueError(f"Unsafe archive entry: {name}")
    if not archive_path.parts or archive_path.parts[0] != ARCHIVE_ROOT:
        raise ValueError(f"Unexpected archive root: {name}")
    relative = PurePosixPath(*archive_path.parts[1:])
    if not relative.parts:
        raise ValueError(f"Invalid archive entry: {name}")
    return Path(*relative.parts)


def extract_description(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"Missing description in {skill_file.name}")
    return match.group(1).strip()


def dependency(path: Path, relative_path: str) -> dict[str, str]:
    return {"path": relative_path, "sha256": sha256(path / relative_path)}


def build_registry(bundle_root: Path, source_file_count: int) -> dict[str, Any]:
    rule_records = {
        key: {
            "rule_key": key,
            "version": version,
            "source_path": relative_path,
            "sha256": sha256(bundle_root / relative_path),
        }
        for key, (version, relative_path) in RULES.items()
    }
    registrations: list[dict[str, Any]] = []
    for skill_key, metadata in SKILLS.items():
        package_name = str(metadata["package_name"])
        source_path = f"skills/{package_name}/SKILL.md"
        type_rules_path = f"skills/{package_name}/references/type-rules.md"
        type_rule_key = f"{skill_key}-type-rules"
        skill_rules = [*rule_records.values()]
        skill_rules.append(
            {
                "rule_key": type_rule_key,
                "version": metadata["type_rule_version"],
                "source_path": type_rules_path,
                "sha256": sha256(bundle_root / type_rules_path),
            }
        )
        registrations.append(
            {
                "skill_key": skill_key,
                "package_name": package_name,
                "display_name": metadata["display_name"],
                "description": extract_description(bundle_root / source_path),
                "bundle_version": BUNDLE_VERSION,
                "skill_source_path": source_path,
                "skill_file_sha256": sha256(bundle_root / source_path),
                "shared_dependency_files": [
                    dependency(bundle_root, item)
                    for item in (*COMMON_DEPENDENCIES, type_rules_path)
                ],
                "rule_versions": skill_rules,
                "input_schema_version": "selection-skill-launch.v1",
                "output_schema_version": f"selection-candidate.{skill_key}.v1",
                "enabled": True,
                "supports_new_product_discovery": metadata[
                    "supports_new_product_discovery"
                ],
                "requires_base_product": metadata["requires_base_product"],
                "supported_sites": ["GB", "DE", "JP", "CA"],
                "execution_status": "registered_not_executable",
                "modes": metadata["modes"],
                "launch_parameters": metadata["launch_parameters"],
            }
        )
    return {
        "registry_schema_version": "selection-skill-registry.v1",
        "bundle_version": BUNDLE_VERSION,
        "bundle_sha256": EXPECTED_BUNDLE_SHA256,
        "source_file_count": source_file_count,
        "skills": registrations,
    }


def import_bundle(source: Path, target_root: Path) -> Path:
    actual_hash = sha256(source)
    if actual_hash != EXPECTED_BUNDLE_SHA256:
        raise ValueError(
            f"Bundle SHA-256 mismatch: expected {EXPECTED_BUNDLE_SHA256}, got {actual_hash}"
        )
    bundle_root = target_root / "bundles" / BUNDLE_VERSION
    registry_path = target_root / "registry.json"
    if bundle_root.exists() or registry_path.exists():
        raise FileExistsError(
            "Versioned bundle or registry already exists; verify it instead of overwriting history"
        )
    files: list[tuple[zipfile.ZipInfo, Path]] = []
    with zipfile.ZipFile(source) as archive:
        for item in archive.infolist():
            relative_path = safe_relative_path(item.filename)
            if item.is_dir():
                continue
            files.append((item, relative_path))
        for item, relative_path in files:
            destination = bundle_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(item))
    registry = build_registry(bundle_root, len(files))
    target_root.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return registry_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the verified six-Skill bundle")
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "ai" / "skills" / "amazon-selection",
    )
    args = parser.parse_args()
    registry_path = import_bundle(args.source.resolve(), args.target.resolve())
    print(f"Imported verified registry: {registry_path}")


if __name__ == "__main__":
    main()
