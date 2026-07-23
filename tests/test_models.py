from core.models import build_result, project_from_result, result_from_project


def _sample_result():
    return build_result(
        command="cmd",
        niche="Psychology",
        video_count=5,
        goal="goal",
        ideas=[{"title": "t"}],
        demo_mode=True,
        model="gpt-4o-mini",
    )


def test_project_round_trip_preserves_fields():
    result = _sample_result()
    project = project_from_result("  My Project ", result)
    assert project["name"] == "My Project"
    assert project.get("project_id")  # stable id assigned on persist

    rehydrated = result_from_project(project)
    for key, value in result.items():
        assert rehydrated[key] == value
    assert rehydrated.get("project_id") == project["project_id"]


def test_result_from_project_tolerates_missing_fields():
    result = result_from_project({"name": "Old", "ideas": [{}, {}]})
    assert result["niche"] == "General Content"
    assert result["video_count"] == 2
    assert result["demo_mode"] is True


def test_project_round_trip_preserves_production_artifacts():
    """RC1: Successful runs must leave unified packages / publish / analytics visible after reload."""
    result = _sample_result()
    result["unified_packages"] = [{"project_id": "p1", "status": "published"}]
    result["publishing_result"] = {"status": "SUCCESS", "jobs_created": 1, "publish_mode": "dry_run"}
    result["analytics_summary"] = {"collected": 1}
    result["learning_report"] = {"status": "SUCCESS", "records_analyzed": 1}
    result["workflow_run_id"] = "run_abc"
    project = project_from_result("Persist Me", result)
    rehydrated = result_from_project(project)
    assert rehydrated["unified_packages"][0]["project_id"] == "p1"
    assert rehydrated["publishing_result"]["publish_mode"] == "dry_run"
    assert rehydrated["analytics_summary"]["collected"] == 1
    assert rehydrated["learning_report"]["records_analyzed"] == 1
    assert rehydrated["workflow_run_id"] == "run_abc"
