"""Tests for HighScoreTable — construction, add_entry, is_high_score, persistence."""

from __future__ import annotations

import json

from highscores import HighScoreTable


class TestHighScoreTableInit:
    def test_empty_table_no_file(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        assert table.entries == []

    def test_load_from_file(self, tmp_path):
        path = tmp_path / "scores.json"
        path.write_text(json.dumps([{"initials": "AAA", "score": 1000}]))
        table = HighScoreTable(path=str(path))
        assert len(table.entries) == 1
        assert table.entries[0].initials == "AAA"
        assert table.entries[0].score == 1000


class TestIsHighScore:
    def test_empty_table_is_always_high_score(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        assert table.is_high_score(1) is True

    def test_score_beats_lowest(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        for i in range(5):
            table.add_entry("AAA", 1000 + i * 100)
        assert table.is_high_score(1001) is True

    def test_score_does_not_beat_lowest(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        for i in range(5):
            table.add_entry("AAA", 1000 + i * 100)
        # Lowest is 1000; 999 is not a high score
        assert table.is_high_score(999) is False

    def test_table_not_full_always_qualifies(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        table.add_entry("AAA", 5000)
        assert table.is_high_score(1) is True  # only 1 entry, room for 4 more


class TestAddEntry:
    def test_entries_sorted_descending(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        table.add_entry("CCC", 500)
        table.add_entry("AAA", 1000)
        table.add_entry("BBB", 750)
        assert [e.score for e in table.entries] == [1000, 750, 500]

    def test_only_top_5_kept(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        for i in range(7):
            table.add_entry("AAA", (i + 1) * 100)
        assert len(table.entries) == 5
        assert table.entries[0].score == 700
        assert table.entries[-1].score == 300

    def test_initials_truncated_to_3_chars(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        table.add_entry("TOOLONG", 100)
        assert table.entries[0].initials == "TOO"

    def test_initials_uppercased(self, tmp_path):
        table = HighScoreTable(path=str(tmp_path / "scores.json"))
        table.add_entry("abc", 100)
        assert table.entries[0].initials == "ABC"


class TestPersistence:
    def test_entries_saved_to_file(self, tmp_path):
        path = tmp_path / "scores.json"
        table = HighScoreTable(path=str(path))
        table.add_entry("XYZ", 9999)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data[0]["initials"] == "XYZ"
        assert data[0]["score"] == 9999

    def test_entries_reloaded_from_file(self, tmp_path):
        path = tmp_path / "scores.json"
        table1 = HighScoreTable(path=str(path))
        table1.add_entry("JKL", 8888)
        table2 = HighScoreTable(path=str(path))
        assert table2.entries[0].initials == "JKL"
        assert table2.entries[0].score == 8888
