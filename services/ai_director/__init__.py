"""AI Director — Agent 18's executive creative decision layer.

The AI Director receives ideas and determines the optimal production strategy
before assets are generated. It orchestrates Agents 12–17 by emitting structured
DirectorPackages — never generating media or duplicating downstream logic.

Public surface:
    from services.ai_director import build_director_package, direct_items
"""

from services.ai_director.decisions import select_format
from services.ai_director.models import (
    AI_DIRECTOR_ENGINE_VERSION,
    DIRECTOR_PACKAGE_FIELDS,
    DIRECTOR_PACKAGE_VERSION,
    DIRECTOR_SUMMARY_FIELDS,
    DirectorStatus,
    ProductionPriority,
)
from services.ai_director.package import (
    build_director_package,
    collect_director_items,
    direct_items,
)
from services.ai_director.policies import (
    apply_learning_feedback,
    configure_policies,
    get_policies,
    reset_policies,
)
from services.ai_director.quality import validate_director_package

__all__ = [
    "AI_DIRECTOR_ENGINE_VERSION",
    "DIRECTOR_PACKAGE_FIELDS",
    "DIRECTOR_PACKAGE_VERSION",
    "DIRECTOR_SUMMARY_FIELDS",
    "DirectorStatus",
    "ProductionPriority",
    "apply_learning_feedback",
    "build_director_package",
    "collect_director_items",
    "configure_policies",
    "direct_items",
    "get_policies",
    "reset_policies",
    "select_format",
    "validate_director_package",
]
