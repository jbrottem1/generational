"""Architecture Directive #1 enforcement — Orchestrator-Only Communication.

Statically proves no engine imports another engine, and dynamically proves
the orchestrator controls execution, ContentPackages flow, missing engines
degrade gracefully, and diagnostics keep working.

See ARCHITECTURE_DIRECTIVES.md. Any change to the allowlists below requires
Agent 1 review.
"""

from __future__ import annotations

import ast
from pathlib import Path

import engines  # noqa: F401 - importing registers all engines
from engines import registry
from engines.base import Engine
from services.orchestrator import (
    ContentPackage,
    Orchestrator,
    StageStatus,
    get_orchestrator,
)
from services.orchestrator.stages import STAGE_GROUPS, register_stage, unregister_stage

ENGINES_DIR = Path(__file__).resolve().parent.parent / "engines"

# Shared foundation modules any engine may import (Directive #1 §1.2).
ALLOWED_SHARED = {
    "engines",            # package itself (registration side effects only)
    "engines.base",
    "engines.contracts",
    "engines.heuristics",
    "engines.analysis",
    "engines.registry",
    "engines.future_stubs",
}

# Stage adapters explicitly granted access to the subsystem package they
# front (same landing zone, same owner — not a cross-engine dependency).
SUBSYSTEM_ACCESS = {
    "engines.image": "engines.render",
    "engines.video": "engines.render",
}

# Modules that are libraries/infrastructure, not engines — they may be
# imported and impose no import rules of their own.
NON_ENGINE_MODULES = {"__init__", "base", "contracts", "heuristics", "analysis", "registry"}


def _engine_imports(path: Path) -> "set[str]":
    """All `engines.*` module names imported by the file at `path`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "engines" or alias.name.startswith("engines."):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "engines" or node.module.startswith("engines."):
                found.add(node.module)
    return found


def _iter_engine_sources():
    """(module_name, subsystem_package, file) for every engine source file."""
    for file in sorted(ENGINES_DIR.glob("*.py")):
        if file.stem not in NON_ENGINE_MODULES:
            yield f"engines.{file.stem}", None, file
    for package_dir in sorted(ENGINES_DIR.iterdir()):
        if package_dir.is_dir() and (package_dir / "__init__.py").exists():
            package = f"engines.{package_dir.name}"
            for file in sorted(package_dir.glob("*.py")):
                yield f"{package}.{file.stem}", package, file


# ------------------------------------------------- static dependency rules


def test_no_engine_imports_another_engine():
    """Directive #1: engine modules import only the shared foundation,
    their own subsystem package, or (for declared adapters) the subsystem
    they front — never another engine."""
    violations = []
    for module, package, file in _iter_engine_sources():
        allowed = set(ALLOWED_SHARED)
        if package:
            allowed.add(package)  # own subsystem internals
            allowed.update(m for m in _all_submodules(package))
        granted = SUBSYSTEM_ACCESS.get(module)
        if granted:
            allowed.add(granted)
            allowed.update(_all_submodules(granted))

        for imported in _engine_imports(file):
            if imported not in allowed:
                violations.append(f"{module} imports {imported}")

    assert not violations, (
        "Architecture Directive #1 violated (engine → engine dependency):\n  "
        + "\n  ".join(violations)
        + "\nMove shared logic to engines/analysis.py or engines/heuristics.py, "
        "or coordinate through the orchestrator + ContentPackage."
    )


def _all_submodules(package: str) -> "set[str]":
    directory = ENGINES_DIR / package.split(".", 1)[1]
    return {f"{package}.{f.stem}" for f in directory.glob("*.py")}


def test_engines_do_not_execute_each_other_through_the_registry():
    """The registry is for registration; `get_engine(...)` inside an engine
    module means one engine is fetching and driving another."""
    offenders = []
    for module, _package, file in _iter_engine_sources():
        source = file.read_text(encoding="utf-8")
        if "get_engine(" in source:
            offenders.append(module)
    assert not offenders, f"Engines calling registry.get_engine(): {offenders}"


def test_orchestrator_does_not_import_engine_modules():
    """The orchestrator coordinates through the registry/workflow layer —
    it must not hardcode engine imports (no hardcoded execution chains)."""
    orch_dir = ENGINES_DIR.parent / "services" / "orchestrator"
    for file in orch_dir.glob("*.py"):
        for imported in _engine_imports(file):
            assert imported in ("engines", "engines.registry"), (
                f"services/orchestrator/{file.name} imports {imported} — "
                "the orchestrator must stay engine-agnostic."
            )


# ------------------------------------------------------ runtime guarantees


def test_every_registered_engine_satisfies_the_engine_interface():
    assert len(registry.all_engines()) >= 30
    for engine in registry.all_engines():
        assert isinstance(engine, Engine), engine
        assert engine.key, engine
        assert callable(engine.run)
        assert isinstance(engine.is_ready(), bool)


def test_orchestrator_controls_execution_and_package_flow(tmp_path, monkeypatch):
    """One command in → orchestrator sequences every stage → ContentPackage
    objects out. No engine was called directly by this test or by another
    engine — the orchestrator did all coordination."""
    from services import knowledge

    monkeypatch.setattr(
        knowledge, "get_knowledge_base", lambda: knowledge.KnowledgeBase(base_dir=tmp_path)
    )

    result = Orchestrator().run_full_pipeline(
        "Create 2 shorts about deep sea creatures", count=2, model="demo"
    )
    assert result.status in (StageStatus.SUCCESS, StageStatus.WARNING)

    executed = [report.stage for report in result.stage_reports]
    assert executed[0] == "trend"
    assert "quality" in executed
    # The integrated production pipeline ends with the distribution stages:
    # packaging → ai_director → creative → character_universe → asset_generation →
    # animation → render → post_production → seo → optimization → publish.
    # Stubs (character_universe, animation, optimization) skip with WARNING.
    # Ends with packaging → distribution → publish → analytics → learning.
    # Stubs (character_universe, animation, optimization) skip with WARNING.
    assert executed[-13:] == [
        "packaging",
        "ai_director",
        "creative",
        "character_universe",
        "asset_generation",
        "animation",
        "render",
        "post_production",
        "seo",
        "optimization",
        "publish",
        "analytics",
        "learning",
    ]

    assert result.packages, "pipeline must emit ContentPackages"
    for package in result.packages:
        assert isinstance(package, ContentPackage)
        assert package.project_id
        assert package.script_package.get("script") is not None

    # Diagnostics: every stage report carries timing + per-engine steps.
    for report in result.stage_reports:
        assert report.started_at and report.finished_at
        assert report.diagnostics or report.stage in ("production", "packaging")


def test_missing_engine_degrades_gracefully_not_fatally():
    orch = get_orchestrator()

    # Unknown stage name → FAILED report with diagnostics, no exception.
    report = orch.run_stage("engine_that_never_existed", {"command": "x"})
    assert report.status == StageStatus.FAILED
    assert report.errors

    # Stage whose engine key is unregistered → skipped WARNING, no crash.
    register_stage("phantom_stage", ["engine_that_never_existed"])
    try:
        report = orch.run_stage("phantom_stage", {"command": "x"})
        assert report.status == StageStatus.WARNING
        assert not report.errors
    finally:
        unregister_stage("phantom_stage")


def test_future_stages_remain_wired_and_safe():
    for stage in (
        "ai_director", "creative", "character_universe", "asset_generation", "animation",
        "render", "post_production", "seo", "optimization", "publish",
        "analytics", "learning", "brand_management",
    ):
        assert stage in STAGE_GROUPS, stage
        report = get_orchestrator().run_stage(stage, {"command": "probe"})
        assert report.status != StageStatus.FAILED, (stage, report.errors)


def test_contract_diagnostics_still_work():
    engine = registry.get_engine("brand_management")
    diag = engine.diagnostics()
    assert diag["engine_id"] == "brand_management"
    assert engine.health_check()["healthy"] is True


# --------------------------------------------- system-wide consistency (v9.6)


def test_capability_index_covers_every_contract_engine():
    index = registry.capability_index()
    assert index, "capability index must not be empty"
    keys = set(registry.engine_keys())
    for capability, engine_keys in index.items():
        assert engine_keys == sorted(engine_keys), capability
        for key in engine_keys:
            assert key in keys, f"{capability} lists unregistered engine {key}"


def test_dependency_graph_targets_are_registered_engines():
    keys = set(registry.engine_keys())
    for engine_key, dependencies in registry.dependency_graph().items():
        for dependency in dependencies:
            assert dependency in keys, (
                f"{engine_key} declares dependency on unregistered engine "
                f"{dependency!r} — fix the dependencies list or register the engine."
            )


def test_every_staged_engine_key_is_registered():
    from core.workflows import WORKFLOWS

    keys = set(registry.engine_keys())
    for stage, engine_keys in STAGE_GROUPS.items():
        for key in engine_keys:
            assert key in keys, f"stage {stage!r} references unregistered engine {key!r}"
    for workflow, engine_keys in WORKFLOWS.items():
        for key in engine_keys:
            assert key in keys, f"workflow {workflow!r} references unregistered engine {key!r}"


def test_describe_all_is_complete_and_uniform():
    infos = registry.describe_all()
    assert len(infos) == len(registry.engine_keys())
    for info in infos:
        for field in ("engine_id", "name", "version", "ready", "input_contract",
                      "output_contract", "dependencies", "capabilities", "description"):
            assert field in info, (info.get("engine_id"), field)


# -------------------------------- ProviderRuntime enforcement (v9.15)


def test_engines_do_not_import_core_ai():
    """Engines must not call core.ai — all LLM traffic goes through ProviderRuntime."""
    violations = []
    for module, _package, file in _iter_engine_sources():
        source = file.read_text(encoding="utf-8")
        if "from core.ai" in source or "import core.ai" in source:
            violations.append(module)
    assert not violations, (
        "Engines must not import core.ai (use services.provider_runtime.engine_api):\n  "
        + "\n  ".join(violations)
    )


def test_engines_do_not_import_vendor_sdks():
    """Engines must not import vendor SDKs directly."""
    banned = (
        "import openai",
        "from openai",
        "import anthropic",
        "from anthropic",
        "import elevenlabs",
        "from elevenlabs",
        "import runwayml",
        "from runwayml",
        "import replicate",
        "from replicate",
    )
    violations = []
    for module, _package, file in _iter_engine_sources():
        source = file.read_text(encoding="utf-8")
        for pattern in banned:
            if pattern in source:
                violations.append(f"{module}: {pattern}")
    assert not violations, (
        "Engines must not import vendor SDKs:\n  " + "\n  ".join(violations)
    )


def test_studio_production_routes_through_workflow_executor():
    """Canonical Studio path is Workflow Executor → Orchestrator."""
    source = (ENGINES_DIR.parent / "services" / "studio" / "production.py").read_text(
        encoding="utf-8"
    )
    assert "get_workflow_executor" in source
    assert "ideation.run_command" not in source
    assert "run_full_pipeline" not in source


def test_workflow_executor_supports_pause_resume_cancel():
    from services.workflow_executor.executor import WorkflowExecutor
    from services.workflow_executor.models import WorkflowStatus

    assert hasattr(WorkflowExecutor, "pause")
    assert hasattr(WorkflowExecutor, "resume")
    assert hasattr(WorkflowExecutor, "cancel")
    assert WorkflowStatus.PAUSED == "paused"


def test_longform_supports_pause_cancel():
    from services.provider_runtime.longform import RuntimeExecutionEngine

    assert hasattr(RuntimeExecutionEngine, "pause_production")
    assert hasattr(RuntimeExecutionEngine, "cancel_production")
    assert hasattr(RuntimeExecutionEngine, "resume_production")
