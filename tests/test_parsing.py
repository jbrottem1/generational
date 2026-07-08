from core import parsing


def test_detect_niche_matches_keywords():
    assert parsing.detect_niche("Create 10 psychology shorts") == "Psychology"
    assert parsing.detect_niche("finance tips about money") == "Finance"


def test_detect_niche_falls_back_to_general():
    assert parsing.detect_niche("make some cool stuff") == "General Content"


def test_detect_video_count_digits_and_words():
    assert parsing.detect_video_count("Create 5 shorts") == 5
    assert parsing.detect_video_count("make a week of content") == 7
    assert parsing.detect_video_count("make some videos") == 10


def test_detect_subject_from_about_clause():
    assert parsing.detect_subject("Create 10 shorts about procrastination", fallback="x") == "procrastination"
    assert parsing.detect_subject("no clause here", fallback="psychology") == "psychology"
