from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.capability.router import router as capability_router
from app.modules.dashboard.router import module_router as module_dashboard_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.identity.admin_router import router as identity_admin_router
from app.modules.identity.router import router as identity_router
from app.modules.selection.router import router as selection_router
from app.modules.selection_export.router import router as selection_export_router
from app.modules.selection_skill.router import router as selection_skill_router
from app.modules.store.router import router as store_router
from app.modules.system.router import router as system_router
from app.modules.workspace.router import router as workspace_router

api_v1_router = APIRouter()
api_v1_router.include_router(identity_router)
api_v1_router.include_router(identity_admin_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(module_dashboard_router)
api_v1_router.include_router(workspace_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(capability_router)
api_v1_router.include_router(store_router)
api_v1_router.include_router(selection_router)
api_v1_router.include_router(selection_skill_router)
api_v1_router.include_router(selection_export_router)
