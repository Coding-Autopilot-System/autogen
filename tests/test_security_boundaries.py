from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from autogen_dashboard.app import create_app


def test_cors_defaults_to_explicit_loopback_origins() -> None:
    with patch.dict("os.environ", {}, clear=True):
        client = TestClient(create_app())

    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_rejects_wildcard_configuration() -> None:
    with patch.dict("os.environ", {"AUTOGEN_CORS_ORIGINS": "*"}, clear=False):
        with pytest.raises(ValueError, match="wildcard CORS"):
            create_app()
