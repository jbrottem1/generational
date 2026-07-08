import pytest

from services.knowledge import CATEGORY


def test_add_and_list_entries_newest_first(knowledge_base):
    knowledge_base.add_entry(CATEGORY.HOOKS, "Hook one", {"niche": "Psychology"})
    knowledge_base.add_entry(CATEGORY.HOOKS, "Hook two", {"niche": "Psychology"})

    entries = knowledge_base.list_entries(CATEGORY.HOOKS)
    assert [e["content"] for e in entries] == ["Hook two", "Hook one"]
    assert entries[0]["id"] and entries[0]["created_at"]


def test_search_is_case_insensitive(knowledge_base):
    knowledge_base.add_entry(CATEGORY.TITLES, "The Truth About Procrastination")
    knowledge_base.add_entry(CATEGORY.TITLES, "Space Facts")

    matches = knowledge_base.search(CATEGORY.TITLES, "procrastination")
    assert len(matches) == 1
    assert "Procrastination" in matches[0]["content"]


def test_counts_across_categories(knowledge_base):
    knowledge_base.add_entry(CATEGORY.HOOKS, "h")
    knowledge_base.add_entry(CATEGORY.SEO_KEYWORDS, "focus tips")
    knowledge_base.add_entry(CATEGORY.PERFORMANCE, {"video": "abc", "views": 1000})

    assert knowledge_base.count() == 3
    assert knowledge_base.count(CATEGORY.HOOKS) == 1
    assert knowledge_base.counts_by_category()[CATEGORY.SEO_KEYWORDS] == 1


def test_unknown_category_rejected(knowledge_base):
    with pytest.raises(ValueError):
        knowledge_base.add_entry("nonsense", "content")


def test_clear_category(knowledge_base):
    knowledge_base.add_entry(CATEGORY.SCRIPTS, "script text")
    knowledge_base.clear(CATEGORY.SCRIPTS)
    assert knowledge_base.count(CATEGORY.SCRIPTS) == 0
