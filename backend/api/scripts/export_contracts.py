import json
from pathlib import Path

from pydantic import SecretStr, TypeAdapter

from app.core.config import Settings
from app.main import create_app
from app.modules.dashboard.domain import DashboardSummaryResponse
from app.modules.selection_skill.domain import OUTPUT_MODELS, CommonCandidateOutput
from app.modules.selection_skill.registry import SkillRegistry


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    output_dir = repository_root / "shared" / "contracts"
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        auth_secret_key=SecretStr("contract-export-only-secret-at-least-32-characters"),
    )
    application = create_app(settings)

    write_json(output_dir / "openapi.v1.json", application.openapi())
    write_json(
        output_dir / "dashboard-summary.schema.json",
        TypeAdapter(DashboardSummaryResponse).json_schema(),
    )
    write_json(
        output_dir / "dashboard-summary.example.json",
        {
            "viewer": {
                "user_id": "10000000-0000-0000-0000-000000000001",
                "username": "operations_demo",
                "display_name": "Operations Demo (DEMO)",
                "roles": ["operations"],
                "modules": ["operations"],
                "permissions": [
                    "operations.dashboard.read",
                    "project.read_assigned",
                ],
                "scope": {
                    "organization_ids": ["org_demo"],
                    "team_ids": ["team_operations"],
                    "store_ids": ["store_operations_demo"],
                },
                "authorization_revision": 1,
            },
            "generated_at": "2026-10-06T00:00:00Z",
            "workspace": "operations",
            "data_status": "demo",
            "disclaimer": "Demo data only; it is not an authoritative operating fact.",
            "counts": {
                "pending_tasks": 0,
                "active_projects": 0,
                "exceptions": 0,
            },
            "work_items": [],
            "projects": [],
            "alerts": [],
        },
    )
    skill_registry = SkillRegistry(settings.selection_skill_assets_path)
    consumables_detail = skill_registry.get_skill("consumables_multipacks")
    if consumables_detail is None:
        raise RuntimeError("Registered consumables_multipacks Skill is missing")
    write_json(
        output_dir / "selection-candidate-output.schema.json",
        {
            "schema_version": "selection-candidate-output.v1",
            "common": CommonCandidateOutput.model_json_schema(),
            "skills": {
                skill_key: model.model_json_schema()
                for skill_key, model in sorted(OUTPUT_MODELS.items())
            },
        },
    )
    examples = {
        "current-user.example.json": {
            "user": {
                "user_id": "10000000-0000-0000-0000-000000000001",
                "username": "operations_demo",
                "display_name": "Operations Demo (DEMO)",
            },
            "roles": ["operations"],
            "modules": ["operations"],
            "permissions": ["operations.dashboard.read", "project.read_assigned"],
            "scopes": {
                "organization_ids": ["org_demo"],
                "team_ids": ["team_operations"],
                "store_ids": ["store_operations_demo"],
            },
            "default_landing": "/operations",
            "authorization_revision": 1,
        },
        "login.example.json": {
            "request": {"username": "operations_demo", "password": "<local-secret>"},
            "response": {
                "user": {
                    "user_id": "10000000-0000-0000-0000-000000000001",
                    "username": "operations_demo",
                    "display_name": "Operations Demo (DEMO)",
                },
                "roles": ["operations"],
                "modules": ["operations"],
                "permissions": ["operations.dashboard.read"],
                "scopes": {
                    "organization_ids": ["org_demo"],
                    "team_ids": ["team_operations"],
                    "store_ids": ["store_operations_demo"],
                },
                "default_landing": "/operations",
                "authorization_revision": 1,
            },
            "session_cookie": {
                "name": "ai_ops_session",
                "http_only": True,
                "secure_in_production": True,
                "same_site": "lax",
            },
        },
        "access-context.example.json": {
            "user": {
                "user_id": "10000000-0000-0000-0000-000000000001",
                "username": "operations_demo",
                "display_name": "Operations Demo (DEMO)",
            },
            "roles": ["operations"],
            "modules": ["operations"],
            "permissions": ["operations.dashboard.read", "listing_copy.read"],
            "scopes": {
                "organization_ids": ["org_demo"],
                "team_ids": ["team_operations"],
                "store_ids": ["store_operations_demo"],
            },
            "default_landing": "/operations",
            "authorization_revision": 1,
        },
        "modules.example.json": {
            "modules": ["operations"],
            "default_landing": "/operations",
        },
        "stores.example.json": {
            "items": [
                {
                    "store_id": "store_operations_demo",
                    "display_name": "Operations Demo Store (DEMO)",
                    "marketplace": "demo",
                    "organization_id": "org_demo",
                    "status": "active",
                    "credential_configured": False,
                    "revision": 1,
                    "created_at": "2026-10-06T00:00:00Z",
                    "updated_at": "2026-10-06T00:00:00Z",
                }
            ],
            "total": 1,
        },
        "admin-user-access.example.json": {
            "user_id": "10000000-0000-0000-0000-000000000001",
            "username": "operations_demo",
            "display_name": "Operations Demo (DEMO)",
            "is_active": True,
            "roles": ["operations"],
            "modules": ["operations"],
            "direct_permissions": ["listing_copy.edit"],
            "effective_permissions": [
                "listing_copy.edit",
                "listing_copy.read",
                "operations.dashboard.read",
            ],
            "scopes": {
                "organization_ids": ["org_demo"],
                "team_ids": ["team_operations"],
                "store_ids": ["store_operations_demo"],
            },
            "authorization_revision": 1,
        },
        "admin-users.example.json": {
            "items": [
                {
                    "user_id": "10000000-0000-0000-0000-000000000001",
                    "username": "operations_demo",
                    "display_name": "Operations Demo (DEMO)",
                    "is_active": True,
                    "roles": ["operations"],
                    "modules": ["operations"],
                    "direct_permissions": [],
                    "effective_permissions": [
                        "operations.dashboard.read",
                        "project.read_assigned",
                    ],
                    "scopes": {
                        "organization_ids": ["org_demo"],
                        "team_ids": ["team_operations"],
                        "store_ids": ["store_operations_demo"],
                    },
                    "authorization_revision": 1,
                }
            ],
            "total": 1,
        },
        "admin-access-updates.example.json": {
            "roles": {
                "roles": ["operations"],
                "permissions": ["listing_copy.edit"],
                "expected_authorization_revision": 1,
            },
            "modules": {
                "modules": ["operations"],
                "expected_authorization_revision": 1,
            },
            "store_scopes": {
                "store_ids": ["store_operations_demo"],
                "expected_authorization_revision": 1,
            },
        },
        "admin-user-create.example.json": {
            "request": {
                "username": "new_operator",
                "display_name": "New Operator",
                "initial_password": "<local-secret-at-least-12-characters>",
            },
            "response": {
                "user_id": "50000000-0000-0000-0000-000000000005",
                "username": "new_operator",
                "display_name": "New Operator",
                "is_active": True,
                "roles": [],
                "modules": [],
                "direct_permissions": [],
                "effective_permissions": [],
                "scopes": {
                    "organization_ids": [],
                    "team_ids": [],
                    "store_ids": [],
                },
                "authorization_revision": 1,
            },
        },
        "admin-user-status.example.json": {
            "enable": {"method": "POST", "path": "/api/v1/admin/users/{user_id}/enable"},
            "disable": {
                "method": "POST",
                "path": "/api/v1/admin/users/{user_id}/disable",
            },
            "response": {
                "user_id": "50000000-0000-0000-0000-000000000005",
                "username": "new_operator",
                "display_name": "New Operator",
                "is_active": False,
                "roles": [],
                "modules": [],
                "direct_permissions": [],
                "effective_permissions": [],
                "scopes": {
                    "organization_ids": [],
                    "team_ids": [],
                    "store_ids": [],
                },
                "authorization_revision": 1,
            },
        },
        "permission-error.example.json": {
            "error": {
                "code": "PERMISSION_DENIED",
                "message": "Permission denied",
                "details": [],
                "request_id": "req_example",
                "trace_id": "trace_example",
            }
        },
        "selection-flow.example.json": {
            "selection": {
                "selection_id": "60000000-0000-0000-0000-000000000006",
                "store_id": "store_operations_demo",
                "marketplace": "amazon-us",
                "product_name": "DEMO candidate",
                "source_type": "ai_skill_sorftime",
                "source_ref": "task://tsk_demo",
                "source_snapshot_ref": "snapshot://market_demo",
                "source_version": "skill-v1",
                "owner_id": "10000000-0000-0000-0000-000000000001",
                "stage": "sourced",
                "revision": 1,
                "created_at": "2026-10-08T00:00:00Z",
                "updated_at": "2026-10-08T00:00:00Z",
            },
            "quotation_update": {
                "supplier_name": "DEMO supplier",
                "unit_cost": "8.2500",
                "currency": "USD",
                "value_status": "confirmed",
                "moq": 100,
                "lead_time_days": 20,
                "freight_per_unit": "1.0000",
                "other_cost_per_unit": None,
                "target_price": "19.9900",
                "notes": "Manually recorded demo quotation",
                "expected_revision": 1,
            },
            "final_selection_update": {
                "decision": "selected",
                "reason": "Manual operations decision",
                "expected_revision": 2,
            },
            "competitors_update": {
                "competitors": [
                    {
                        "title": f"Competitor {index}",
                        "bullets": [f"Point {number}" for number in range(1, 6)],
                    }
                    for index in range(1, 4)
                ],
                "expected_revision": 3,
            },
        },
        "selection-ai-task.example.json": {
            "items": [
                {
                    "task_id": "tsk_demo",
                    "selection_id": "60000000-0000-0000-0000-000000000006",
                    "task_type": "profit_review",
                    "input_version": "quotation:1",
                    "status": "planned",
                    "run_id": None,
                    "result_version": None,
                    "error_code": None,
                    "created_at": "2026-10-08T00:00:00Z",
                    "updated_at": "2026-10-08T00:00:00Z",
                }
            ],
            "total": 1,
            "note": "Boundary example only; it does not claim an AI run succeeded.",
        },
        "selection-export.example.json": {
            "create_requests": {
                "initial_selection": {
                    "stage": "initial_selection",
                    "store_ids": ["store_procurement_demo"],
                    "search": "demo candidate",
                    "marketplace": "amazon-us",
                    "source_type": "ai_skill_sorftime",
                },
                "quotation": {
                    "stage": "quotation",
                    "store_ids": ["store_procurement_demo"],
                    "search": "demo candidate",
                    "marketplace": "amazon-us",
                },
            },
            "job_response": {
                "export_id": "70000000-0000-0000-0000-000000000007",
                "stage": "initial_selection",
                "snapshot_id": "71000000-0000-0000-0000-000000000007",
                "schema_version": "initial_selection.v1",
                "status": "completed",
                "row_count": 1,
                "file_name": "AI选品表_演示店铺_20261009_71000000.xlsx",
                "file_checksum": "0" * 64,
                "error_code": None,
                "trace_id": "trace_demo",
                "created_at": "2026-10-09T00:00:00Z",
                "completed_at": "2026-10-09T00:00:01Z",
                "expires_at": "2026-10-10T00:00:00Z",
            },
            "download": {
                "method": "GET",
                "path": "/api/v1/selection-exports/{export_id}/download",
                "authentication_required": True,
                "public_url": False,
            },
            "permissions": {
                "initial_selection": "selection.export",
                "quotation": "quotation.export",
            },
            "supported_stages": ["initial_selection", "quotation"],
            "quotation_rules": {
                "modules": ["procurement", "admin"],
                "submitted_only": True,
                "operations_allowed": False,
            },
        },
        "selection-skills.example.json": {
            "list": skill_registry.list_skills().model_dump(mode="json"),
            "detail": consumables_detail.model_dump(mode="json"),
            "notes": {
                "read_only": True,
                "creates_selection_task": False,
                "prompt_body_exposed": False,
            },
        },
        "deepseek-status.example.json": {
            "configured": True,
            "reachable": True,
            "status": "available",
            "endpoint_host": "api.deepseek.com",
            "model": "deepseek-chat",
            "latency_ms": 120,
            "error_code": None,
        },
        "listing-copy-permissions.example.json": {
            "operations_default": [
                "listing_copy.read",
                "listing_copy.generate",
                "listing_copy.edit",
                "listing_copy.review",
                "listing_copy.history.read",
            ],
            "procurement_default": [],
            "admin_default": [],
            "rules": {
                "module": (
                    "operations for operators; admin for explicitly authorized administrators"
                ),
                "store_scope_required": True,
                "admin_requires_explicit_permission": True,
            },
        },
        "admin-errors.example.json": {
            "items": [
                {
                    "error_id": "e0000000-0000-0000-0000-000000000001",
                    "category": "integration",
                    "severity": "error",
                    "status": "open",
                    "module": "integration",
                    "task_id": "tsk_demo",
                    "run_id": "run_demo",
                    "action_id": "act_demo",
                    "summary": "Connection failed: [REDACTED]",
                    "occurred_at": "2026-10-06T00:00:00Z",
                    "resolved_at": None,
                    "trace_id": "trace_demo",
                }
            ],
            "total": 1,
        },
        "ai-feedback.example.json": {
            "items": [
                {
                    "feedback_id": "f0000000-0000-0000-0000-000000000001",
                    "task_id": "tsk_demo",
                    "run_id": "run_demo",
                    "capability_id": "listing-copy",
                    "capability_release_id": "rel_demo",
                    "submitted_by": "10000000-0000-0000-0000-000000000001",
                    "feedback_type": "correction",
                    "summary": "DEMO feedback",
                    "status": "new",
                    "created_at": "2026-10-06T00:00:00Z",
                }
            ],
            "total": 1,
        },
        "audit-logs.example.json": {
            "items": [
                {
                    "audit_id": "d0000000-0000-0000-0000-000000000001",
                    "actor_id": "40000000-0000-0000-0000-000000000004",
                    "actor_roles": ["admin"],
                    "action": "admin.error.read",
                    "resource_type": "error",
                    "resource_id": None,
                    "result": "success",
                    "trace_id": "trace_demo",
                    "occurred_at": "2026-10-06T00:00:00Z",
                    "metadata_summary": {"returned_count": "1"},
                }
            ],
            "total": 1,
        },
    }
    for name, content in examples.items():
        write_json(output_dir / name, content)


if __name__ == "__main__":
    main()
