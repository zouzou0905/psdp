from dataclasses import dataclass
from enum import StrEnum


class ModuleStatus(StrEnum):
    ACTIVE = "active"
    BOUNDARY_ONLY = "boundary_only"


@dataclass(frozen=True, slots=True)
class ModuleDescriptor:
    name: str
    owner: str
    status: ModuleStatus
    constraints: tuple[str, ...] = ()


MODULES: tuple[ModuleDescriptor, ...] = (
    ModuleDescriptor("identity", "iam", ModuleStatus.ACTIVE),
    ModuleDescriptor("authorization", "iam", ModuleStatus.ACTIVE),
    ModuleDescriptor("product", "catalog", ModuleStatus.BOUNDARY_ONLY),
    ModuleDescriptor("project", "project", ModuleStatus.BOUNDARY_ONLY),
    ModuleDescriptor("selection", "selection", ModuleStatus.ACTIVE),
    ModuleDescriptor(
        "selection_skill_registry",
        "ai",
        ModuleStatus.ACTIVE,
        ("read-only assets; no selection run creation",),
    ),
    ModuleDescriptor("quotation", "quotation", ModuleStatus.ACTIVE),
    ModuleDescriptor(
        "procurement",
        "procurement",
        ModuleStatus.BOUNDARY_ONLY,
        ("ERP remains authoritative", "approval required before external execution"),
    ),
    ModuleDescriptor("content", "content", ModuleStatus.BOUNDARY_ONLY),
    ModuleDescriptor(
        "listing",
        "listing",
        ModuleStatus.BOUNDARY_ONLY,
        ("approval required before marketplace execution",),
    ),
    ModuleDescriptor(
        "workflow",
        "workflow",
        ModuleStatus.BOUNDARY_ONLY,
        ("task_id -> run_id -> action_id -> external_receipt_id",),
    ),
    ModuleDescriptor("approval", "governance", ModuleStatus.BOUNDARY_ONLY),
    ModuleDescriptor(
        "capability",
        "ai",
        ModuleStatus.BOUNDARY_ONLY,
        ("AI and MCP access only through the future capability gateway",),
    ),
    ModuleDescriptor("audit", "governance", ModuleStatus.ACTIVE),
    ModuleDescriptor("workspace", "workspace", ModuleStatus.ACTIVE),
    ModuleDescriptor("health", "platform", ModuleStatus.ACTIVE),
    ModuleDescriptor("system", "platform", ModuleStatus.ACTIVE),
    ModuleDescriptor("dashboard", "workspace", ModuleStatus.ACTIVE),
)
