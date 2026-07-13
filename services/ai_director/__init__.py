"""AI Director — Agent 18's Studio Director V5.0.

The AI Director receives ideas and determines the optimal production strategy
before assets are generated. V5 emits a complete Production Blueprint plus
structured DirectorPackages — never generating media or duplicating downstream logic.

Public surface:
    from services.ai_director import build_director_package, build_production_blueprint
"""

from services.ai_director.blueprint import build_production_blueprint
from services.ai_director.consumers import apply_blueprint_to_candidate, blueprint_consistency_score
from services.ai_director.competitor import analyze_competitors
from services.ai_director.decisions import select_format
from services.ai_director.models import (
    AI_DIRECTOR_ENGINE_VERSION,
    DIRECTOR_PACKAGE_FIELDS,
    DIRECTOR_PACKAGE_VERSION,
    DIRECTOR_SUMMARY_FIELDS,
    PRODUCTION_BLUEPRINT_FIELDS,
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
from services.ai_director.styles import STYLE_LIBRARY, choose_production_style, list_styles

__all__ = [
    "AI_DIRECTOR_ENGINE_VERSION",
    "DIRECTOR_PACKAGE_FIELDS",
    "DIRECTOR_PACKAGE_VERSION",
    "DIRECTOR_SUMMARY_FIELDS",
    "PRODUCTION_BLUEPRINT_FIELDS",
    "STYLE_LIBRARY",
    "DirectorStatus",
    "ProductionPriority",
    "analyze_competitors",
    "apply_blueprint_to_candidate",
    "apply_learning_feedback",
    "blueprint_consistency_score",
    "build_director_package",
    "build_production_blueprint",
    "choose_production_style",
    "collect_director_items",
    "configure_policies",
    "direct_items",
    "get_policies",
    "list_styles",
    "reset_policies",
    "select_format",
    "validate_director_package",
]
