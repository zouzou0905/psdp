import hashlib
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.selection_skill.domain import (
    OUTPUT_MODELS,
    LaunchParameterDefinition,
    SelectionSkillCard,
    SelectionSkillDetail,
    SelectionSkillListResponse,
    SkillDependency,
    SkillExecutionStatus,
    SkillRuleVersion,
)

EXPECTED_SKILL_KEYS = frozenset(
    {
        "evergreen",
        "seasonal",
        "holiday",
        "trending_accessories",
        "consumables_multipacks",
        "validated_variations",
    }
)


class ManifestDependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ManifestRuleVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_key: str
    version: str
    source_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ManifestSkill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_key: str
    package_name: str
    display_name: str
    description: str
    bundle_version: str
    skill_source_path: str
    skill_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    shared_dependency_files: list[ManifestDependency]
    rule_versions: list[ManifestRuleVersion]
    input_schema_version: str
    output_schema_version: str
    enabled: bool
    supports_new_product_discovery: bool
    requires_base_product: bool
    supported_sites: list[Literal["GB", "DE", "JP", "CA"]]
    execution_status: SkillExecutionStatus
    modes: list[str]
    launch_parameters: list[str]


class RegistryManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registry_schema_version: str
    bundle_version: str
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_file_count: int = Field(gt=0)
    skills: list[ManifestSkill]


PARAMETERS: dict[str, LaunchParameterDefinition] = {
    "site": LaunchParameterDefinition(
        name="site",
        value_type="enum",
        required=True,
        description="Amazon site; data from different sites must not be mixed.",
        allowed_values=["GB", "DE", "JP", "CA"],
    ),
    "seed": LaunchParameterDefinition(
        name="seed",
        value_type="string",
        required=False,
        description="Optional keyword, ASIN, category node, or controlled candidate seed.",
    ),
    "analysis_date": LaunchParameterDefinition(
        name="analysis_date",
        value_type="date",
        required=False,
        description="Business analysis date used for evidence freshness.",
    ),
    "depth": LaunchParameterDefinition(
        name="depth",
        value_type="enum",
        required=False,
        description="Requested research depth; it does not authorize execution.",
        allowed_values=["quick_screen", "deep_validation"],
    ),
    "target_window": LaunchParameterDefinition(
        name="target_window",
        value_type="string",
        required=False,
        description="Target seasonal sales window.",
    ),
    "event_name": LaunchParameterDefinition(
        name="event_name",
        value_type="string",
        required=True,
        description="Target holiday or event name for the selected site.",
    ),
    "target_year": LaunchParameterDefinition(
        name="target_year",
        value_type="integer",
        required=True,
        description="Target event year.",
    ),
    "main_product_seed": LaunchParameterDefinition(
        name="main_product_seed",
        value_type="string",
        required=False,
        description="Optional product line, model, ASIN, or installed-base clue.",
    ),
    "accessory_clue": LaunchParameterDefinition(
        name="accessory_clue",
        value_type="string",
        required=False,
        description="Optional accessory or maintenance-use clue.",
    ),
    "selection_mode": LaunchParameterDefinition(
        name="selection_mode",
        value_type="enum",
        required=True,
        description="Independent discovery or review of tags for an existing candidate.",
        allowed_values=["independent_discovery", "tag_review"],
    ),
    "branch_mode": LaunchParameterDefinition(
        name="branch_mode",
        value_type="enum",
        required=True,
        description="Consumables, pack-size, or combined evidence branch.",
        allowed_values=["consumables", "pack_size", "both"],
    ),
    "pack_scope": LaunchParameterDefinition(
        name="pack_scope",
        value_type="enum",
        required=True,
        description="Pack-size comparison scope.",
        allowed_values=["small", "standard", "large_pcs", "multiple_tiers"],
    ),
    "base_asin": LaunchParameterDefinition(
        name="base_asin",
        value_type="string",
        required=True,
        description="ASIN of an already validated base product.",
    ),
    "proposed_dimension": LaunchParameterDefinition(
        name="proposed_dimension",
        value_type="string",
        required=True,
        description="Proposed variation or extension dimension.",
    ),
    "target_offer": LaunchParameterDefinition(
        name="target_offer",
        value_type="string",
        required=True,
        description="Target child or standalone offer definition.",
    ),
}


class SkillRegistry:
    """Validated, file-backed registry that never returns Skill prompt bodies."""

    def __init__(self, assets_root: Path) -> None:
        self._assets_root = assets_root.resolve()
        self._manifest = self._load_manifest()
        self._skills = {item.skill_key: item for item in self._manifest.skills}

    def list_skills(self) -> SelectionSkillListResponse:
        cards = [self._to_card(self._skills[key]) for key in sorted(self._skills)]
        return SelectionSkillListResponse(items=cards, total=len(cards))

    def get_skill(self, skill_key: str) -> SelectionSkillDetail | None:
        registration = self._skills.get(skill_key)
        if registration is None:
            return None
        card = self._to_card(registration)
        return SelectionSkillDetail(
            **card.model_dump(),
            launch_parameters=[PARAMETERS[name] for name in registration.launch_parameters],
            shared_dependency_files=[
                SkillDependency(file_name=Path(item.path).name, sha256=item.sha256)
                for item in registration.shared_dependency_files
            ],
            rule_versions=[
                SkillRuleVersion(
                    rule_key=item.rule_key,
                    version=item.version,
                    sha256=item.sha256,
                )
                for item in registration.rule_versions
            ],
            output_schema=OUTPUT_MODELS[skill_key].model_json_schema(),
        )

    def _load_manifest(self) -> RegistryManifest:
        manifest_path = self._safe_path("registry.json")
        manifest = RegistryManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        keys = [item.skill_key for item in manifest.skills]
        if len(keys) != len(set(keys)):
            raise ValueError("Selection Skill keys must be unique")
        if set(keys) != EXPECTED_SKILL_KEYS or len(keys) != 6:
            raise ValueError("Selection Skill registry must contain exactly the approved six keys")
        for skill in manifest.skills:
            if skill.bundle_version != manifest.bundle_version:
                raise ValueError("Skill bundle version does not match registry bundle version")
            self._verify_file(skill.skill_source_path, skill.skill_file_sha256, manifest)
            for item in skill.shared_dependency_files:
                self._verify_file(item.path, item.sha256, manifest)
            for rule in skill.rule_versions:
                self._verify_file(rule.source_path, rule.sha256, manifest)
            if skill.skill_key not in OUTPUT_MODELS:
                raise ValueError(f"Missing output schema for {skill.skill_key}")
            for parameter in skill.launch_parameters:
                if parameter not in PARAMETERS:
                    raise ValueError(f"Unknown launch parameter: {parameter}")
        validated = self._skills_by_key(manifest)
        variations = validated["validated_variations"]
        if not variations.requires_base_product or variations.supports_new_product_discovery:
            raise ValueError("validated_variations discovery constraints are invalid")
        consumables = validated["consumables_multipacks"]
        if set(consumables.modes) != {"independent_discovery", "tag_review"}:
            raise ValueError("consumables_multipacks must expose both approved modes")
        return manifest

    @staticmethod
    def _skills_by_key(manifest: RegistryManifest) -> dict[str, ManifestSkill]:
        return {item.skill_key: item for item in manifest.skills}

    def _verify_file(
        self, relative_path: str, expected_sha256: str, manifest: RegistryManifest
    ) -> None:
        path = self._safe_path(f"bundles/{manifest.bundle_version}/{relative_path}")
        if not path.is_file():
            raise ValueError(f"Registered Skill dependency is missing: {Path(relative_path).name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise ValueError(f"Registered Skill dependency checksum changed: {path.name}")

    def _safe_path(self, relative_path: str) -> Path:
        pure_path = PurePosixPath(relative_path)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or "\\" in relative_path
            or ":" in relative_path
        ):
            raise ValueError("Selection Skill asset path is not allowed")
        resolved = (self._assets_root / Path(*pure_path.parts)).resolve()
        if not resolved.is_relative_to(self._assets_root):
            raise ValueError("Selection Skill asset path escapes the controlled root")
        return resolved

    @staticmethod
    def _to_card(registration: ManifestSkill) -> SelectionSkillCard:
        return SelectionSkillCard(
            skill_key=registration.skill_key,
            package_name=registration.package_name,
            display_name=registration.display_name,
            description=registration.description,
            bundle_version=registration.bundle_version,
            skill_file_sha256=registration.skill_file_sha256,
            input_schema_version=registration.input_schema_version,
            output_schema_version=registration.output_schema_version,
            enabled=registration.enabled,
            supports_new_product_discovery=registration.supports_new_product_discovery,
            requires_base_product=registration.requires_base_product,
            supported_sites=registration.supported_sites,
            execution_status=registration.execution_status,
            modes=registration.modes,
        )
