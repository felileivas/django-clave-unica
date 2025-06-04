import uuid
from unittest import mock

import pytest

from clave_unica_auth.lib.utils import oauth2_claveunica as cu


def test_generate_state_unique_and_uuid4():
    state1 = cu.generate_state()
    state2 = cu.generate_state()
    assert state1 != state2
    # validate uuid4 format
    uuid.UUID(state1)
    uuid.UUID(state2)


def test_encode_dict_to_uri():
    params = {"a": "1", "b": "test"}
    encoded = cu.encode_dict_to_uri(params)
    assert "a=1" in encoded
    assert "b=test" in encoded


def test_join_url_with_params():
    result = cu.join_url_with_params("https://example.com", "a=1")
    assert result == "https://example.com?a=1"


def test_get_url_params_authorization_code_generates_state_when_none():
    params = cu.get_url_params_authorization_code("client", "https://redirect")
    assert "client_id=client" in params
    assert "redirect_uri=https%3A%2F%2Fredirect" in params
    assert "response_type=code" in params
    # state should be populated with a uuid
    state_value = dict(item.split("=") for item in params.split("&"))[
        "state"
    ]
    uuid.UUID(state_value)


def test_get_url_params_authorization_code_uses_given_state():
    state = "abc"
    params = cu.get_url_params_authorization_code(
        "client", "https://redirect", state=state
    )
    assert f"state={state}" in params


def test_get_params_access_token_default_state():
    params = cu.get_params_access_token(
        "cid", "secret", "https://redir", "code"
    )
    assert params["client_id"] == "cid"
    assert params["client_secret"] == "secret"
    assert params["redirect_uri"] == "https://redir"
    assert params["code"] == "code"
    assert params["grant_type"] == "authorization_code"
    uuid.UUID(str(params["state"]))


def test_get_headers_authorization_code():
    headers = cu.get_headers_authorization_code()
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert headers["Accept"] == "application/json"


def test_get_headers_bearer_token():
    headers = cu.get_headers_bearer_token("token")
    assert headers["Authorization"] == "Bearer token"
    assert headers["Accept"] == "application/json"


def test_get_url_login_claveunica_includes_state():
    result = cu.get_url_login_claveunica(
        "https://login", "cid", "https://redir", state="fixed"
    )
    assert result.startswith("https://login?")
    assert "state=fixed" in result


def make_response(status=200, json_data=None):
    mock_resp = mock.Mock()
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data or {"ok": True}
    return mock_resp


def test_request_authorization_code_success():
    with mock.patch("requests.post", return_value=make_response()) as post:
        data = cu.request_authorization_code(
            "https://token", "cid", "sec", "https://redir", "code", state="s"
        )
        assert data == {"ok": True}
        post.assert_called_once()


def test_request_authorization_code_error():
    with mock.patch("requests.post", return_value=make_response(status=500)):
        with pytest.raises(Exception):
            cu.request_authorization_code(
                "https://token", "cid", "sec", "https://redir", "code", state="s"
            )


def test_request_info_user_success():
    with mock.patch("requests.post", return_value=make_response()) as post:
        data = cu.request_info_user("https://info", "acc")
        assert data == {"ok": True}
        post.assert_called_once()


def test_request_info_user_error():
    with mock.patch("requests.post", return_value=make_response(status=404)):
        with pytest.raises(Exception):
            cu.request_info_user("https://info", "acc")

