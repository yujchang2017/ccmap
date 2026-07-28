"""Offline unit tests for app.utils.validators (no network / DB required)."""
import pytest
from marshmallow import ValidationError

from app.utils.validators import (
    InputSanitizer,
    StageQuerySchema,
    SearchQuerySchema,
    ALL_STAGES,
    ALL_DOMAINS,
)

VALID_UUID = "490d1fd7-0bb1-45d7-9451-bdac3b32d332"


class TestInputSanitizer:
    def test_strips_script_tags(self):
        out = InputSanitizer.sanitize_string("<script>alert(1)</script>hello")
        assert "<script>" not in out
        assert "hello" in out

    def test_removes_javascript_scheme_and_event_handlers(self):
        out = InputSanitizer.sanitize_string('javascript:alert(1) onclick=hack')
        assert "javascript:" not in out.lower()
        assert "onclick=" not in out.lower()

    def test_truncates_to_max_length(self):
        assert len(InputSanitizer.sanitize_string("a" * 5000, max_length=100)) <= 100

    def test_non_string_returns_empty(self):
        assert InputSanitizer.sanitize_string(12345) == ""
        assert InputSanitizer.sanitize_string(None) == ""

    def test_blocks_mongodb_operators(self):
        dirty = {"$where": "1==1", "name": {"$ne": None}, "ok": "value"}
        clean = InputSanitizer.sanitize_mongodb_query(dirty)
        assert "$where" not in clean
        assert "$ne" not in clean["name"]
        assert clean["ok"] == "value"

    def test_sanitizes_nested_lists(self):
        clean = InputSanitizer.sanitize_mongodb_query(["<b>x</b>", {"$or": []}])
        assert clean[0] == "x"
        assert "$or" not in clean[1]


class TestStageQuerySchema:
    def test_valid_stage_and_domain(self):
        data = StageQuerySchema().load({"stage": "II", "domain": "自然"})
        assert data["stage"] == "II"

    @pytest.mark.parametrize("stage", ["VI", "0", "abc", ""])
    def test_invalid_stage_rejected(self, stage):
        with pytest.raises(ValidationError):
            StageQuerySchema().load({"stage": stage, "domain": "自然"})

    def test_invalid_domain_rejected(self):
        with pytest.raises(ValidationError):
            StageQuerySchema().load({"stage": "II", "domain": "不存在的領域"})

    def test_all_configured_domains_accepted(self):
        for domain in ALL_DOMAINS:
            StageQuerySchema().load({"stage": "I", "domain": domain})


class TestSearchQuerySchema:
    def _base(self, **over):
        d = {
            "uuid": VALID_UUID,
            "stage": "II",
            "domain": "自然",
            "selected_content": "天氣與氣候",
        }
        d.update(over)
        return d

    def test_valid_query(self):
        data = SearchQuerySchema().load(self._base())
        assert data["uuid"] == VALID_UUID

    def test_requires_some_content(self):
        with pytest.raises(ValidationError):
            SearchQuerySchema().load(self._base(selected_content="", additional_input=""))

    def test_free_text_only_is_allowed(self):
        data = SearchQuerySchema().load(
            self._base(selected_content="", additional_input="極端降雨")
        )
        assert data["additional_input"] == "極端降雨"

    def test_invalid_uuid_rejected(self):
        with pytest.raises(ValidationError):
            SearchQuerySchema().load(self._base(uuid="not-a-uuid"))

    def test_wildcard_stage_allowed(self):
        data = SearchQuerySchema().load(self._base(stage="不拘", domain="不拘"))
        assert data["stage"] == "不拘"

    def test_all_stages_accepted(self):
        for stage in ALL_STAGES:
            SearchQuerySchema().load(self._base(stage=stage))
