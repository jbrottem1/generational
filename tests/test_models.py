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

    rehydrated = result_from_project(project)
    assert rehydrated == result


def test_result_from_project_tolerates_missing_fields():
    result = result_from_project({"name": "Old", "ideas": [{}, {}]})
    assert result["niche"] == "General Content"
    assert result["video_count"] == 2
    assert result["demo_mode"] is True
