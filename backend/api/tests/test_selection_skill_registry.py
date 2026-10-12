import json
import shutil
from pathlib import Path

import httpx
import pytest

from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import RoleName
from app.modules.selection_skill.registry import EXPECTED_SKILL_KEYS, SkillRegistry
from scripts.import_selection_skill_bundle import import_bundle

EXPECTED_BUNDLE_SHA256 = "864c271c3ebd5830f99016f2ee03725dd395040f2e342d354e63471c35140351"


async def test_procurement_can_list_exactly_six_registered_skills(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
    audit_repository: InMemoryAuditRepository,
) -> None:
    response = await client.get(
        "/api/v1/selection-skills", headers=auth_headers[RoleName.PROCUREMENT]
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 6
    assert {item["skill_key"] for item in payload["items"]} == EXPECTED_SKILL_KEYS
    assert all(item["execution_status"] == "registered_not_executable" for item in payload["items"])
    assert audit_repository.events[-1].action == "selection_skill.registry.list"


async def test_registry_requires_authentication_and_procurement_or_admin_access(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    client.cookies.clear()
    unauthenticated = await client.get("/api/v1/selection-skills")
    operations = await client.get(
        "/api/v1/selection-skills", headers=auth_headers[RoleName.OPERATIONS]
    )
    admin = await client.get(
        "/api/v1/selection-skills", headers=auth_headers[RoleName.ADMIN]
    )

    assert unauthenticated.status_code == 401
    assert operations.status_code == 403
    assert admin.status_code == 200


async def test_skill_detail_is_sanitized_and_exposes_contract_metadata(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    response = await client.get(
        "/api/v1/selection-skills/validated_variations",
        headers=auth_headers[RoleName.PROCUREMENT],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requires_base_product"] is True
    assert payload["supports_new_product_discovery"] is False
    assert payload["output_schema_version"] == (
        "selection-candidate.validated_variations.v1"
    )
    assert {item["name"] for item in payload["launch_parameters"]} >= {
        "site",
        "base_asin",
    }
    assert "candidate_id" in payload["output_schema"]["properties"]
    assert "extension" in payload["output_schema"]["properties"]
    serialized = json.dumps(payload).lower()
    for forbidden in (
        "skill_source_path",
        "source_path",
        "authorization",
        "api_key",
        "c:\\users",
        "d:\\tf",
        "完整读取",
    ):
        assert forbidden not in serialized


async def test_consumables_exposes_independent_and_tag_review_modes(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    response = await client.get(
        "/api/v1/selection-skills/consumables_multipacks",
        headers=auth_headers[RoleName.PROCUREMENT],
    )

    assert response.status_code == 200
    assert set(response.json()["modes"]) == {"independent_discovery", "tag_review"}


async def test_unknown_and_traversal_skill_keys_do_not_read_files(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    unknown = await client.get(
        "/api/v1/selection-skills/not-a-skill",
        headers=auth_headers[RoleName.PROCUREMENT],
    )
    traversal = await client.get(
        "/api/v1/selection-skills/%2e%2e%2f.env",
        headers=auth_headers[RoleName.PROCUREMENT],
    )

    assert unknown.status_code == 404
    assert traversal.status_code == 404
    assert "DATABASE_URL" not in traversal.text


def test_registry_verifies_bundle_hash_metadata_and_every_dependency() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    assets_root = repository_root / "ai" / "skills" / "amazon-selection"
    manifest = json.loads((assets_root / "registry.json").read_text(encoding="utf-8"))

    registry = SkillRegistry(assets_root)

    assert manifest["bundle_sha256"] == EXPECTED_BUNDLE_SHA256
    assert manifest["source_file_count"] == 38
    assert registry.list_skills().total == 6
    assert all(registry.get_skill(key) is not None for key in EXPECTED_SKILL_KEYS)


def test_registry_rejects_dependency_path_traversal(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    source = repository_root / "ai" / "skills" / "amazon-selection"
    destination = tmp_path / "amazon-selection"
    shutil.copytree(source, destination)
    manifest_path = destination / "registry.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["skills"][0]["skill_source_path"] = "../../outside.md"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="path is not allowed"):
        SkillRegistry(destination)


def test_registry_rejects_duplicate_skill_keys(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    source = repository_root / "ai" / "skills" / "amazon-selection"
    destination = tmp_path / "amazon-selection"
    shutil.copytree(source, destination)
    manifest_path = destination / "registry.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["skills"][1]["skill_key"] = manifest["skills"][0]["skill_key"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="must be unique"):
        SkillRegistry(destination)


def test_bundle_import_stops_before_extraction_on_checksum_mismatch(tmp_path: Path) -> None:
    invalid_bundle = tmp_path / "invalid.zip"
    invalid_bundle.write_bytes(b"not the approved bundle")
    target = tmp_path / "target"

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        import_bundle(invalid_bundle, target)

    assert not target.exists()
