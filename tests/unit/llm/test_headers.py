"""Unit tests for ``llm/headers.py`` — validation and merge rules."""

import pytest

from kohakuterrarium.llm.headers import (
    merge_header_maps,
    normalize_header_map,
    normalize_header_name,
    validate_header_map,
    validate_header_name,
)


class TestNormalizeHeaderMap:
    def test_non_mapping_input_returns_empty(self):
        assert normalize_header_map(None) == {}
        assert normalize_header_map(["a: b"]) == {}
        assert normalize_header_map("x-session: v") == {}

    def test_valid_rows_kept_and_scalars_stringified(self):
        assert normalize_header_map({"x-custom": "v", "x-count": 7}) == {
            "x-custom": "v",
            "x-count": "7",
        }

    def test_invalid_names_and_none_values_dropped(self):
        raw = {"bad name": "v", "": "v", None: "v", "x-ok": None}
        assert normalize_header_map(raw) == {}

    def test_control_characters_drop_the_row(self):
        assert normalize_header_map({"x-bad": "a\r\nb", "x-ok": "fine"}) == {
            "x-ok": "fine"
        }

    def test_documented_session_header_name_is_valid(self):
        assert normalize_header_name("x-opencode-session") == "x-opencode-session"

    def test_empty_and_non_string_names_rejected(self):
        assert normalize_header_name("") == ""
        assert normalize_header_name(None) == ""
        assert normalize_header_name(7) == ""


class TestValidateHeaderMap:
    def test_none_returns_empty(self):
        assert validate_header_map(None) == {}

    def test_non_mapping_raises(self):
        with pytest.raises(ValueError, match="mapping"):
            validate_header_map(["x"])

    def test_invalid_name_raises(self):
        with pytest.raises(ValueError, match="invalid header name"):
            validate_header_map({"bad name": "v"})

    def test_control_character_value_raises(self):
        with pytest.raises(ValueError, match="control characters"):
            validate_header_map({"x-bad": "v\r\n"})

    def test_validate_header_name_raises_on_bad_token(self):
        with pytest.raises(ValueError, match="invalid header name"):
            validate_header_name("x session")


class TestMergeHeaderMaps:
    def test_empty_maps_return_empty(self):
        assert merge_header_maps(None, {}) == {}

    def test_later_map_wins(self):
        assert merge_header_maps({"a": "1"}, {"a": "2"}) == {"a": "2"}

    def test_case_insensitive_dedup_keeps_winner_casing(self):
        merged = merge_header_maps({"X-Session": "old"}, {"x-session": "new"})
        assert merged == {"x-session": "new"}

    def test_disjoint_names_all_kept(self):
        assert merge_header_maps({"a": "1"}, {"b": "2"}) == {"a": "1", "b": "2"}
