"""Creative Studio service layer (Agent 20).

The UI adapter over Workflow Executor, ProviderRuntime, and project storage.
Production runs: Studio → Workflow Executor → Orchestrator → engines.
Never call engines or vendor SDKs from the UI layer.
"""

from services.studio.dashboard import get_executive_dashboard
from services.studio.library import collect_output_library
from services.studio.models import (
    DEFAULT_STUDIO_SETTINGS,
    STUDIO_EXAMPLE_PROMPTS,
    STUDIO_PIPELINE_STAGES,
    STUDIO_PLATFORMS,
    build_default_settings,
)
from services.studio.pipeline import build_pipeline_view, map_stage_status
from services.studio.previews import extract_previews
from services.studio.production import (
    build_settings_preview,
    is_longform_command,
    result_from_project_run,
    run_studio_production,
    submit_longform_job,
)
from services.studio.projects import (
    archive_project,
    create_studio_project,
    duplicate_project,
    list_studio_projects,
    unarchive_project,
    update_project_metadata,
)
from services.studio.providers import get_provider_dashboard
from services.studio.readiness import get_production_readiness

__all__ = [
    "DEFAULT_STUDIO_SETTINGS",
    "STUDIO_EXAMPLE_PROMPTS",
    "STUDIO_PIPELINE_STAGES",
    "STUDIO_PLATFORMS",
    "archive_project",
    "build_default_settings",
    "build_pipeline_view",
    "build_settings_preview",
    "collect_output_library",
    "create_studio_project",
    "duplicate_project",
    "extract_previews",
    "get_executive_dashboard",
    "get_production_readiness",
    "get_provider_dashboard",
    "is_longform_command",
    "list_studio_projects",
    "map_stage_status",
    "result_from_project_run",
    "run_studio_production",
    "submit_longform_job",
    "unarchive_project",
    "update_project_metadata",
]
