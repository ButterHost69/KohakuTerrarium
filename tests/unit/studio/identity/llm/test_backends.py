"""Unit tests for :mod:`kohakuterrarium.studio.identity.llm.backends`.

Most functions are thin wrappers over ``kohakuterrarium.llm.profiles``; we
focus on the input-validation logic of ``save_backend_record``, including
the strict checks on configured request headers.
"""

import pytest

from kohakuterrarium.studio.identity.llm import backends as mod
from kohakuterrarium.studio.identity.llm.backends import save_backend_record


@pytest.fixture
def captured_backend(monkeypatch):
    saved = {}
    monkeypatch.setattr(
        mod, "save_backend", lambda backend: saved.update({"backend": backend})
    )
    return saved


class TestSaveBackendRecord:
    def test_missing_name_raises(self):
        with pytest.raises(ValueError, match="Name and backend type"):
            save_backend_record("", "openai")

    def test_unknown_backend_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported backend type"):
            save_backend_record("my", "grpc")

    def test_header_fields_persist(self, captured_backend):
        backend = save_backend_record(
            "opencode-go",
            "openai",
            "https://opencode.ai/inference/go/openai/v1",
            extra_headers={"x-custom": "v", "x-count": 7},
            session_id_header="x-opencode-session",
        )
        assert backend.extra_headers == {"x-custom": "v", "x-count": "7"}
        assert backend.session_id_header == "x-opencode-session"
        assert captured_backend["backend"] is backend

    def test_invalid_header_name_raises(self, captured_backend):
        with pytest.raises(ValueError, match="invalid header name"):
            save_backend_record("my", "openai", extra_headers={"bad name": "v"})

    def test_control_character_value_raises(self, captured_backend):
        with pytest.raises(ValueError, match="control characters"):
            save_backend_record("my", "openai", extra_headers={"x-bad": "v\r\n"})

    def test_invalid_session_header_name_raises(self, captured_backend):
        with pytest.raises(ValueError, match="invalid header name"):
            save_backend_record("my", "openai", session_id_header="not a header")

    def test_empty_header_config_saves_clean(self, captured_backend):
        backend = save_backend_record("my", "openai")
        assert backend.extra_headers == {}
        assert backend.session_id_header == ""
