from core.storage.json_collection import JsonCollectionStore


def _project(name="Test Project"):
    return {"name": name, "niche": "Psychology", "ideas": [{"title": "t"}]}


def test_project_store_save_load_delete(project_store):
    project_store.save_project(_project())
    loaded = project_store.load_project("Test Project")
    assert loaded["niche"] == "Psychology"
    assert loaded["created_at"] and loaded["updated_at"]

    assert project_store.project_count() == 1
    assert project_store.delete_project("Test Project") is True
    assert project_store.project_count() == 0
    assert project_store.load_project("Test Project") is None


def test_project_store_lists_newest_first(project_store):
    project_store.save_project(_project("First"))
    project_store.save_project(_project("Second"))
    names = [p["name"] for p in project_store.list_projects()]
    assert names[0] == "Second"


def test_json_collection_store_round_trip(tmp_path):
    store = JsonCollectionStore(str(tmp_path / "records"))
    store.save({"name": "Alpha Channel", "niche": "Space"})
    assert store.load("Alpha Channel")["niche"] == "Space"
    assert store.count() == 1
    assert store.delete("Alpha Channel") is True
    assert store.load("Alpha Channel") is None
