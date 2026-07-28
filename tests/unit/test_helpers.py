"""Offline unit tests for app.utils.helpers."""
import numpy as np

from app.utils.helpers import (
    convert_to_native,
    get_concept_theme,
    parse_topic_info,
    CONCEPT_NAMES,
)


class TestConvertToNative:
    def test_numpy_scalars(self):
        assert convert_to_native(np.float32(0.5)) == 0.5
        assert isinstance(convert_to_native(np.int64(3)), int)

    def test_nested_structures(self):
        out = convert_to_native({"a": [np.float64(1.5), {"b": np.int32(2)}]})
        assert out == {"a": [1.5, {"b": 2}]}
        assert isinstance(out["a"][0], float)

    def test_passthrough_native_types(self):
        assert convert_to_native("text") == "text"
        assert convert_to_native(7) == 7


class TestParseTopicInfo:
    def test_full_topic_string(self):
        info = parse_topic_info("1.2.溫室效應")
        assert info["concept_id"] == "1"
        assert info["topic_prefix"] == "1.2"
        assert info["topic_label"] == "溫室效應"

    def test_topic_without_prefix(self):
        info = parse_topic_info("無編號主題")
        assert info["concept_id"] is None
        assert info["topic_prefix"] is None
        assert info["topic_label"] == "無編號主題"


class TestGetConceptTheme:
    def test_known_concepts_have_colors(self):
        for prefix in CONCEPT_NAMES:
            theme = get_concept_theme(prefix)
            assert theme["bg"].startswith("#")
            assert theme["text"].startswith("#")

    def test_unknown_concept_falls_back(self):
        assert get_concept_theme("99") == {"bg": "#ffffff", "text": "#333"}
